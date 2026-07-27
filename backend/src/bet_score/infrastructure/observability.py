import logging
import re
from collections import Counter, defaultdict
from threading import Lock
from time import perf_counter
from uuid import UUID, uuid4

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import RequestResponseEndpoint

from bet_score.application.outbox import OutboxStats

logger = logging.getLogger("bet_score.access")

REQUEST_ID_HEADER = "X-Request-ID"
CORRELATION_ID_HEADER = "X-Correlation-ID"
_UNKNOWN_ROUTE = "unmatched"
_SAFE_METHOD = re.compile(r"^[A-Z]{1,16}$")
_DURATION_BUCKETS = (0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, float("inf"))


class HttpMetrics:
    def __init__(self, *, live_connection_limit: int) -> None:
        self._requests: Counter[tuple[str, str, int]] = Counter()
        self._duration_seconds: dict[tuple[str, str], float] = defaultdict(float)
        self._duration_count: Counter[tuple[str, str]] = Counter()
        self._duration_buckets: Counter[tuple[str, str, float]] = Counter()
        self._live_connections = 0
        self._live_attempts = 0
        self._live_rejections = 0
        self._live_connection_limit = live_connection_limit
        self._lock = Lock()

    def observe(self, method: str, route: str, status_code: int, duration: float) -> None:
        safe_method = method if _SAFE_METHOD.fullmatch(method) else "UNKNOWN"
        with self._lock:
            self._requests[(safe_method, route, status_code)] += 1
            self._duration_seconds[(safe_method, route)] += duration
            self._duration_count[(safe_method, route)] += 1
            for bucket in _DURATION_BUCKETS:
                if duration <= bucket:
                    self._duration_buckets[(safe_method, route, bucket)] += 1

    def render(self, outbox: OutboxStats | None = None) -> str:
        lines = [
            "# HELP bet_score_http_requests_total Total HTTP requests.",
            "# TYPE bet_score_http_requests_total counter",
        ]
        with self._lock:
            requests = sorted(self._requests.items())
            durations = sorted(self._duration_seconds.items())
            duration_counts = sorted(self._duration_count.items())
            duration_buckets = sorted(self._duration_buckets.items())
            live_connections = self._live_connections
            live_attempts = self._live_attempts
            live_rejections = self._live_rejections
        for (method, route, status), count in requests:
            lines.append(
                "bet_score_http_requests_total"
                f'{{method="{method}",route="{route}",status="{status}"}} {count}'
            )
        lines.extend(
            [
                "# HELP bet_score_http_request_duration_seconds_total "
                "Total HTTP request duration in seconds.",
                "# TYPE bet_score_http_request_duration_seconds_total counter",
            ]
        )
        for (method, route), duration in durations:
            lines.append(
                "bet_score_http_request_duration_seconds_total"
                f'{{method="{method}",route="{route}"}} {duration:.9f}'
            )
        lines.extend(
            [
                "# HELP bet_score_http_request_duration_seconds HTTP request duration.",
                "# TYPE bet_score_http_request_duration_seconds histogram",
            ]
        )
        for (method, route, bucket), count in duration_buckets:
            le = "+Inf" if bucket == float("inf") else f"{bucket:g}"
            lines.append(
                "bet_score_http_request_duration_seconds_bucket"
                f'{{method="{method}",route="{route}",le="{le}"}} {count}'
            )
        for (method, route), duration in durations:
            lines.append(
                "bet_score_http_request_duration_seconds_sum"
                f'{{method="{method}",route="{route}"}} {duration:.9f}'
            )
        for (method, route), count in duration_counts:
            lines.append(
                "bet_score_http_request_duration_seconds_count"
                f'{{method="{method}",route="{route}"}} {count}'
            )
        lines.extend(
            [
                "# HELP bet_score_live_connections Active LIVE WebSocket connections.",
                "# TYPE bet_score_live_connections gauge",
                f"bet_score_live_connections {live_connections}",
                "# HELP bet_score_live_connection_limit Configured LIVE connection limit.",
                "# TYPE bet_score_live_connection_limit gauge",
                f"bet_score_live_connection_limit {self._live_connection_limit}",
                "# HELP bet_score_live_connection_attempts_total "
                "Trusted-origin LIVE connection attempts.",
                "# TYPE bet_score_live_connection_attempts_total counter",
                f"bet_score_live_connection_attempts_total {live_attempts}",
                "# HELP bet_score_live_connection_rejections_total "
                "LIVE connections rejected by capacity limits.",
                "# TYPE bet_score_live_connection_rejections_total counter",
                f"bet_score_live_connection_rejections_total {live_rejections}",
            ]
        )
        outbox_available = int(outbox is not None)
        outbox = outbox or OutboxStats(0, 0, 0, 0)
        lines.extend(
            [
                "# HELP bet_score_outbox_available Whether outbox metrics are available.",
                "# TYPE bet_score_outbox_available gauge",
                f"bet_score_outbox_available {outbox_available}",
                "# HELP bet_score_outbox_pending Pending outbox messages.",
                "# TYPE bet_score_outbox_pending gauge",
                f"bet_score_outbox_pending {outbox.pending}",
                "# HELP bet_score_outbox_oldest_pending_seconds "
                "Age of the oldest pending outbox message.",
                "# TYPE bet_score_outbox_oldest_pending_seconds gauge",
                f"bet_score_outbox_oldest_pending_seconds {outbox.oldest_pending_seconds:.6f}",
                "# HELP bet_score_outbox_delivered_total Delivered outbox messages.",
                "# TYPE bet_score_outbox_delivered_total counter",
                f"bet_score_outbox_delivered_total {outbox.delivered}",
                "# HELP bet_score_outbox_retries_total Retried outbox deliveries.",
                "# TYPE bet_score_outbox_retries_total counter",
                f"bet_score_outbox_retries_total {outbox.retries}",
            ]
        )
        return "\n".join(lines) + "\n"

    def set_live_connections(self, value: int) -> None:
        with self._lock:
            self._live_connections = value

    def attempt_live_connection(self) -> None:
        with self._lock:
            self._live_attempts += 1

    def reject_live_connection(self) -> None:
        with self._lock:
            self._live_rejections += 1


def _request_id(request: Request) -> str:
    supplied = request.headers.get(CORRELATION_ID_HEADER)
    if supplied is not None:
        try:
            return str(UUID(supplied))
        except ValueError:
            pass
    return str(uuid4())


def _route_template(request: Request) -> str:
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    return path if isinstance(path, str) else _UNKNOWN_ROUTE


def configure_observability(application: FastAPI, metrics: HttpMetrics) -> None:
    @application.middleware("http")
    async def observe_request(request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = _request_id(request)
        request.state.request_id = request_id
        started_at = perf_counter()
        status_code = 500
        response: Response | None = None
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration = perf_counter() - started_at
            route = _route_template(request)
            metrics.observe(request.method, route, status_code, duration)
            logger.info(
                "request_completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "route": route,
                    "status_code": status_code,
                    "duration_ms": round(duration * 1000, 3),
                },
            )
            if response is not None:
                response.headers[REQUEST_ID_HEADER] = request_id
