"""
AEGIS Time-Series Ring Buffer
Sliding window storage for telemetry metric streams with statistical and trend analytics.
"""
from collections import deque
from typing import List, Dict, Any, Optional
import math


class TimeSeriesBuffer:
    def __init__(self, max_points: int = 300):
        self.max_points = max_points
        self.timestamps: deque[float] = deque(maxlen=max_points)
        # metric_key -> deque of float values
        self.series: Dict[str, deque[float]] = {}

    def append_point(self, timestamp_ms: float, metrics: Dict[str, float]) -> None:
        self.timestamps.append(timestamp_ms)
        for key, val in metrics.items():
            if key not in self.series:
                self.series[key] = deque(maxlen=self.max_points)
            self.series[key].append(float(val))

    def get_series(self, key: str) -> List[float]:
        return list(self.series.get(key, []))

    def get_timestamps(self) -> List[float]:
        return list(self.timestamps)

    def mean(self, key: str, window: Optional[int] = None) -> float:
        s = self.series.get(key)
        if not s:
            return 0.0
        pts = list(s)[-window:] if window else list(s)
        return sum(pts) / len(pts)

    def std(self, key: str, window: Optional[int] = None) -> float:
        s = self.series.get(key)
        if not s or len(s) < 2:
            return 0.0
        pts = list(s)[-window:] if window else list(s)
        m = sum(pts) / len(pts)
        variance = sum((x - m) ** 2 for x in pts) / (len(pts) - 1)
        return math.sqrt(variance)

    def rate_of_change(self, key: str, steps: int = 3) -> float:
        """Computes recent derivative d(metric)/dt per interval."""
        s = self.series.get(key)
        if not s or len(s) <= steps:
            return 0.0
        pts = list(s)
        delta_val = pts[-1] - pts[-1 - steps]
        return delta_val / float(steps)

    def to_dict(self, max_history: int = 60) -> Dict[str, Any]:
        """Exports data for frontend charts."""
        ts = list(self.timestamps)[-max_history:]
        return {
            "timestamps": ts,
            "metrics": {k: list(v)[-max_history:] for k, v in self.series.items()}
        }
