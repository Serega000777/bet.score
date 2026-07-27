import logging
import re
from collections import Counter, defaultdict
from threading import Lock
from time import perf_counter
from uuid import UUID, uuid4

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import RequestResponseEndpoint

logger = logging.getLogger("bet_score.access")

REQUEST_ID_HEADER = "X-Request-ID"
CORRELATION_ID_HEADER = "X-Correlation-ID"
_UNKNOWN_ROUTE = "unmatched"
_SAFE_METHOD = re.compile(r"^[A-Z]{1,16}$")


class HttpMetrics:
    def __init__(self) -> None:
        self._requests: Counter[tuple[str, str, int]] = Counter()
        self._duration_seconds: dict[tuple[str, str], float] = defaultdict(float)
        self._live_connections = 0
        self._live_rejections = 0
        self._lock = Lock()

    def observe(self, method: str, route: str, status_code: int, duration: float) -> None:
        safe_method = method if _SAFE_METHOD.fullmatch(method) else "UNKNOWN"
        with self._lock:
            self._requests[(safe_method, route, status_code)] += 1
            self._duration_seconds[(safe_method, route)] += duration

    def render(self) -> str:
        lines = [
            "# HELP bet_score_http_requests_total Total HTTP requests.",
            "# TYPE bet_score_http_requests_total counter",
        ]
        with self._lock:
            requests = sorted(self._requests.items())
            durations = sorted(self._duration_seconds.items())
            live_connections = self._live_connections
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
                "# HELP bet_score_live_connections Active LIVE WebSocket connections.",
                "# TYPE bet_score_live_connections gauge",
                f"bet_score_live_connections {live_connections}",
                "# HELP bet_score_live_connection_rejections_total "
                "LIVE connections rejected by capacity limits.",
                "# TYPE bet_score_live_connection_rejections_total counter",
                f"bet_score_live_connection_rejections_total {live_rejections}",
            ]
        )
        return "\n".join(lines) + "\n"

    def set_live_connections(self, value: int) -> None:
        with self._lock:
            self._live_connections = value

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
