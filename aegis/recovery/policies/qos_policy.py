"""
AEGIS QoS Protection Policy
Enforces priority rules during congestion and recovery:
CRITICAL (100) > REAL_TIME (80) > NORMAL (50) > BULK (10).
"""
from typing import List, Dict, Any
from ...core.packets.packet import TrafficClass
from ...core.flows.flow import TrafficFlow


class QoSPolicyEngine:
    @staticmethod
    def get_flow_sort_key_for_reroute(flow: TrafficFlow) -> int:
        """
        Returns integer sort priority where lower priority flows (BULK, NORMAL)
        are selected first for rerouting or throttling during congestion.
        """
        priority_map = {
            TrafficClass.BULK: 1,
            TrafficClass.NORMAL: 2,
            TrafficClass.REAL_TIME: 3,
            TrafficClass.CRITICAL: 4,
        }
        return priority_map.get(flow.traffic_class, 2)

    @staticmethod
    def can_throttle(flow: TrafficFlow) -> bool:
        """Only non-realtime, non-critical traffic can be throttled."""
        return flow.traffic_class in (TrafficClass.BULK, TrafficClass.NORMAL)

    @staticmethod
    def evaluate_sla_impact(flow: TrafficFlow, expected_latency_ms: float) -> bool:
        """Returns True if expected latency violates the flow SLA."""
        return expected_latency_ms > flow.latency_sla_ms
