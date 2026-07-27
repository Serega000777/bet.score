import asyncio
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass

DependencyProbe = Callable[[], Awaitable[None]]


@dataclass(frozen=True, slots=True)
class ReadinessResult:
    ready: bool
    checks: Mapping[str, bool]


class ReadinessService:
    def __init__(
        self,
        probes: Mapping[str, DependencyProbe],
        *,
        timeout_seconds: float,
    ) -> None:
        self._probes = dict(probes)
        self._timeout_seconds = timeout_seconds

    async def check(self) -> ReadinessResult:
        names = tuple(self._probes)
        results = await asyncio.gather(
            *(self._run_probe(self._probes[name]) for name in names),
        )
        checks = dict(zip(names, results, strict=True))
        return ReadinessResult(ready=all(checks.values()), checks=checks)

    async def _run_probe(self, probe: DependencyProbe) -> bool:
        try:
            async with asyncio.timeout(self._timeout_seconds):
                await probe()
        except Exception:
            return False
        return True
