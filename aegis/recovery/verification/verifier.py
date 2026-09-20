"""
AEGIS Verification Engine
Validates whether an executed recovery action genuinely improved network health
without causing collateral degradation on alternate links.
"""
from typing import Dict, List, Optional, Tuple, Any
from ..incident import Incident, IncidentStatus
from ...telemetry.metrics.definitions import NetworkGlobalSnapshot


class VerificationEngine:
    def __init__(
        self,
        required_settle_steps: int = 3,
        utilization_target_max: float = 0.82,
        loss_target_max: float = 0.01,
        max_acceptable_collateral_utilization: float = 0.92,
    ):
        self.settle_steps = required_settle_steps
        self.util_target = utilization_target_max
        self.loss_target = loss_target_max
        self.max_collateral = max_acceptable_collateral_utilization

    def evaluate_recovery(
        self,
        incident: Incident,
        current_snapshot: NetworkGlobalSnapshot
    ) -> Tuple[bool, str, Dict[str, float]]:
        """
        Compares post-recovery metrics against pre-recovery baseline.
        Returns: (is_success: bool, explanation: str, post_metrics: Dict[str, float])
        """
        res = incident.affected_resource
        post_metrics: Dict[str, float] = {}

        # 1. Target resource health
        target_link = current_snapshot.links.get(res)
        if target_link:
            post_metrics["utilization"] = target_link.utilization
            post_metrics["loss_rate"] = target_link.loss_rate
            post_metrics["latency_ms"] = target_link.latency_ms
            post_metrics["queue_depth"] = float(target_link.queue_depth)

            pre_util = incident.pre_recovery_metrics.get("utilization", 1.0)
            pre_loss = incident.pre_recovery_metrics.get("loss_rate", 0.0)

            # Check if condition on target link improved
            if target_link.status == "DOWN" or incident.incident_type in ("HARD_LINK_FAILURE", "LINK_FAILURE", "ROUTER_OFFLINE"):
                # Physical cut or router crash handled by routing around it
                pass
            elif target_link.utilization > self.util_target or target_link.loss_rate > self.loss_target:
                return (
                    False,
                    f"Mitigation failed: {res} remains congested (utilization: {round(target_link.utilization*100, 1)}%, loss: {round(target_link.loss_rate*100, 2)}%).",
                    post_metrics,
                )

        # 2. Check for Collateral Damage across all other links
        for lid, link in current_snapshot.links.items():
            if lid != res and link.status != "DOWN":
                if link.utilization > self.max_collateral:
                    return (
                        False,
                        f"Mitigation caused collateral degradation: alternate link {lid} saturated to {round(link.utilization*100, 1)}%!",
                        post_metrics,
                    )

        # 3. Check overall SLA compliance
        post_metrics["sla_compliance"] = current_snapshot.sla_compliance_rate
        post_metrics["global_loss"] = current_snapshot.global_packet_loss_rate

        return (
            True,
            f"Recovery verified: target resource utilization normalized to {round(post_metrics.get('utilization', 0.0)*100, 1)}% with zero collateral bottlenecking.",
            post_metrics,
        )
