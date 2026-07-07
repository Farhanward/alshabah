from __future__ import annotations

import json
import statistics
import time
import tracemalloc
from pathlib import Path

from .planner import load_policy, plan_task


def _p(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(round((pct / 100) * (len(ordered) - 1))))]


def evaluate(path: str | Path, policy_path: str | Path, *, repeat: int = 1) -> dict:
    policy = load_policy(policy_path)
    rows = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    allowed = blocked = errors = steps = 0
    latencies = []
    started = time.perf_counter()
    tracemalloc.start()
    for _ in range(repeat):
        for row in rows:
            t0 = time.perf_counter()
            try:
                result = plan_task(str(row.get("task") or ""), url=str(row.get("url") or ""), policy=policy)
                allowed += 1 if result["allowed"] else 0
                blocked += 0 if result["allowed"] else 1
                steps += len(result["steps"])
            except Exception:
                errors += 1
            latencies.append((time.perf_counter() - t0) * 1000)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {
        "processed": len(rows) * repeat,
        "allowed": allowed,
        "blocked": blocked,
        "errors": errors,
        "steps": steps,
        "latency_ms": {"mean": statistics.fmean(latencies) if latencies else 0.0, "p99": _p(latencies, 99), "max": max(latencies) if latencies else 0.0},
        "memory_mb": {"current": current / 1_000_000, "peak": peak / 1_000_000},
        "elapsed_seconds": time.perf_counter() - started,
        "collapse_check": {"passed": errors == 0, "criteria": "errors == 0"},
    }

