"""
AEGIS Predictive Network Degradation Engine
Forecasting link saturation, buffer exhaustion, and SLA violations before packet loss occurs
using sliding-window linear regression and trend analysis.
"""
from typing import Dict, List, Optional, Any
from ...telemetry.metrics.definitions import NetworkGlobalSnapshot
from ...telemetry.time_series.buffer import TimeSeriesBuffer


class DegradationPredictor:
    def __init__(
        self,
        saturation_threshold: float = 0.88,
        lookback_window: int = 6,
        prediction_horizon_steps: int = 5,
        min_trend_slope: float = 0.03,  # +3% per interval min to trigger
    ):
        self.saturation_threshold = saturation_threshold
        self.lookback_window = lookback_window
        self.horizon_steps = prediction_horizon_steps
        self.min_trend_slope = min_trend_slope

    def predict_degradations(
        self,
        snapshot: NetworkGlobalSnapshot,
        time_series: TimeSeriesBuffer
    ) -> List[Dict[str, Any]]:
        """
        Scans all links and nodes for rising trends that will cross saturation thresholds
        within the prediction horizon.
        """
        predictions: List[Dict[str, Any]] = []

        for lid, link in snapshot.links.items():
            if link.status == "DOWN":
                continue

            series_key = f"link:{lid}:utilization"
            history = time_series.get_series(series_key)
            if len(history) < self.lookback_window:
                continue

            recent_pts = history[-self.lookback_window:]
            n = len(recent_pts)
            
            # Compute Ordinary Least Squares (OLS) Linear Regression: y = m*x + c
            x_vals = list(range(n))
            x_mean = sum(x_vals) / n
            y_mean = sum(recent_pts) / n
            
            denom = sum((x - x_mean) ** 2 for x in x_vals)
            if denom == 0:
                continue
            slope = sum((x_vals[i] - x_mean) * (recent_pts[i] - y_mean) for i in range(n)) / denom
            intercept = y_mean - slope * x_mean

            current_val = recent_pts[-1]

            # If trend is clearly positive and current utilization is already elevated
            if slope >= self.min_trend_slope and current_val >= 0.60:
                # Forecast value at horizon
                forecasted_val = current_val + (slope * self.horizon_steps)
                
                # Estimated intervals until saturation threshold crossing
                if current_val < self.saturation_threshold:
                    steps_to_cross = (self.saturation_threshold - current_val) / slope
                else:
                    steps_to_cross = 0.0

                if steps_to_cross <= self.horizon_steps:
                    risk = "CRITICAL" if steps_to_cross <= 2 else ("HIGH" if steps_to_cross <= 4 else "MEDIUM")
                    time_to_breach_ms = steps_to_cross * 100.0  # 100ms per step

                    predictions.append({
                        "resource": lid,
                        "resource_type": "LINK",
                        "current_utilization": round(current_val, 4),
                        "slope_per_interval": round(slope, 4),
                        "estimated_steps_to_crossing": round(steps_to_cross, 1),
                        "estimated_time_to_crossing_ms": round(time_to_breach_ms, 1),
                        "forecasted_utilization": round(forecasted_val, 4),
                        "risk_level": risk,
                        "reason": f"Utilization on link {lid} is ramping rapidly (+{round(slope * 100, 1)}%/step, currently {round(current_val * 100, 1)}%).",
                        "expected_consequence": "Imminent buffer exhaustion, tail drop, and SLA violations within ~" + str(round(steps_to_cross, 1)) + " intervals.",
                        "recommended_preventive_action": "Proactively reroute low-priority BULK flows or apply traffic shaping to prevent packet drop.",
                    })

        return predictions
