"""Shared metrics and random helpers for MAC simulations."""
from dataclasses import dataclass, field
from typing import Any
import numpy as np

@dataclass
class Station:
    """Minimal per-station state used by the slot simulators."""
    queue: list[float] = field(default_factory=list)
    backoff: int = 0
    stage: int = 0
    attempts: int = 0
    successes: int = 0
    drops: int = 0
    delays: list[float] = field(default_factory=list)

def jains_index(counts) -> float:
    """Jain's fairness index; zero when no station has delivered traffic."""
    x = np.asarray(counts, dtype=float)
    denom = len(x) * float(x @ x) if len(x) else 0.0
    return float(x.sum() ** 2 / denom) if denom else 0.0

def metric_summary(*, payload_bits: int, rate_bps: float, elapsed_s: float,
                   successes: list[int], delays: list[float], attempts: int,
                   collisions: int, drops: int, success_s: float,
                   collision_s: float, idle_s: float) -> dict[str, Any]:
    """Build comparable protocol metrics from accumulated event totals."""
    total = max(elapsed_s, 1e-15)
    return {
        "throughput": min(1.0, sum(successes) * payload_bits / (total * rate_bps)),
        "mean_delay_s": float(np.mean(delays)) if delays else 0.0,
        "p95_delay_s": float(np.percentile(delays, 95)) if delays else 0.0,
        "collision_probability": collisions / attempts if attempts else 0.0,
        "drop_rate": drops / max(attempts, 1),
        "success_fraction": success_s / total,
        "collision_fraction": collision_s / total,
        "idle_fraction": idle_s / total,
        "fairness": jains_index(successes),
        "per_station_successes": list(successes),
        "per_station_throughput": [x * payload_bits / total for x in successes],
        "elapsed_s": elapsed_s,
        "attempts": attempts,
        "collisions": collisions,
        "drops": drops,
    }
