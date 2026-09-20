"""
AEGIS Anomaly Detection Engine
Multi-metric statistical and deterministic anomaly detector inspecting link utilization,
packet loss, queue occupancy, latency degradation, and rate of change.
"""
from typing import Dict, List, Optional, Tuple, Any
from ...telemetry.metrics.definitions import NetworkGlobalSnapshot, LinkMetricSnapshot
from ...telemetry.time_series.buffer import TimeSeriesBuffer


class AnomalyDetector:
    def __init__(
        self,
        utilization_threshold: float = 0.85,
        loss_threshold: float = 0.02,
        queue_occupancy_threshold: float = 0.70,
        latency_multiplier_threshold: float = 1.8,
        rate_of_change_threshold: float = 0.20,
    ):
        self.util_thresh = utilization_threshold
        self.loss_thresh = loss_threshold
        self.queue_thresh = queue_occupancy_threshold
        self.lat_mult_thresh = latency_multiplier_threshold
        self.roc_thresh = rate_of_change_threshold

    def analyze_snapshot(
        self,
        snapshot: NetworkGlobalSnapshot,
        time_series: TimeSeriesBuffer
    ) -> List[Dict[str, Any]]:
        """
        Analyzes the latest snapshot and historical buffer to find anomalies.
        Returns a list of detected anomaly reports with evidence and composite scores.
        """
        anomalies: List[Dict[str, Any]] = []

        # 1. Inspect Links
        for lid, link in snapshot.links.items():
            if link.status == "DOWN":
                # Hard link failure
                anomalies.append({
                    "resource": lid,
                    "resource_type": "LINK",
                    "anomaly_type": "HARD_LINK_FAILURE",
                    "anomaly_score": 1.0,
                    "severity": "CRITICAL",
                    "evidence": {
                        "status": "DOWN",
                        "utilization": 0.0,
                        "recent_loss": 1.0,
                    },
                    "reason": f"Physical or operational link failure on {lid}",
                })
                continue

            evidence: Dict[str, Any] = {}
            score_components: List[float] = []

            # 1a. Utilization threshold check
            if link.utilization >= self.util_thresh:
                excess = (link.utilization - self.util_thresh) / (1.0 - self.util_thresh)
                score_components.append(0.35 + (0.65 * excess))
                evidence["utilization"] = f"{round(link.utilization * 100, 1)}% (threshold: {int(self.util_thresh * 100)}%)"

            # 1b. Packet loss check
            if link.loss_rate >= self.loss_thresh:
                loss_severity = min(1.0, link.loss_rate / 0.10)
                score_components.append(0.50 + (0.50 * loss_severity))
                evidence["packet_loss"] = f"{round(link.loss_rate * 100, 2)}% (threshold: {round(self.loss_thresh * 100, 1)}%)"

            # 1c. Queue occupancy check
            queue_ratio = link.queue_depth / 200.0  # standard buffer capacity
            if queue_ratio >= self.queue_thresh:
                score_components.append(0.40 + (0.60 * queue_ratio))
                evidence["queue_occupancy"] = f"{round(queue_ratio * 100, 1)}% ({link.queue_depth} packets)"

            # 1d. Rate of change (derivative)
            roc = time_series.rate_of_change(f"link:{lid}:utilization", steps=3)
            if roc >= self.roc_thresh:
                score_components.append(0.60)
                evidence["rate_of_change"] = f"+{round(roc * 100, 1)}% per interval (surging traffic)"

            # 1e. Latency surge vs baseline
            baseline_latency = time_series.mean(f"link:{lid}:latency", window=10)
            if baseline_latency > 0 and (link.latency_ms / baseline_latency) >= self.lat_mult_thresh:
                surge_ratio = link.latency_ms / baseline_latency
                score_components.append(min(1.0, 0.40 * surge_ratio))
                evidence["latency_surge"] = f"{round(link.latency_ms, 1)}ms vs baseline {round(baseline_latency, 1)}ms"

            if score_components:
                # Composite multi-metric anomaly score
                composite_score = min(1.0, sum(score_components) / len(score_components) + (0.15 * (len(score_components) - 1)))
                
                if composite_score >= 0.50:
                    severity = "CRITICAL" if composite_score >= 0.85 else ("HIGH" if composite_score >= 0.70 else "MEDIUM")
                    anomalies.append({
                        "resource": lid,
                        "resource_type": "LINK",
                        "anomaly_type": "LINK_DEGRADATION" if link.loss_rate > 0.05 and link.utilization < 0.60 else "CONGESTION_ANOMALY",
                        "anomaly_score": composite_score,
                        "severity": severity,
                        "evidence": evidence,
                        "reason": f"Multi-metric anomaly on link {lid}: " + "; ".join(f"{k}={v}" for k, v in evidence.items()),
                    })

        # 2. Inspect Nodes
        for nid, node in snapshot.nodes.items():
            if node.status == "DOWN":
                anomalies.append({
                    "resource": nid,
                    "resource_type": "NODE",
                    "anomaly_type": "ROUTER_OFFLINE",
                    "anomaly_score": 1.0,
                    "severity": "CRITICAL",
                    "evidence": {"status": "DOWN", "health_score": 0.0},
                    "reason": f"Router node {nid} is offline/unreachable",
                })
            elif node.health_score < 0.50:
                anomalies.append({
                    "resource": nid,
                    "resource_type": "NODE",
                    "anomaly_type": "NODE_RESOURCE_PRESSURE",
                    "anomaly_score": 1.0 - node.health_score,
                    "severity": "HIGH",
                    "evidence": {
                        "health_score": node.health_score,
                        "cpu": f"{round(node.cpu_utilization * 100, 1)}%",
                        "memory": f"{round(node.memory_utilization * 100, 1)}%",
                    },
                    "reason": f"Severe resource pressure on node {nid}",
                })

        return anomalies
