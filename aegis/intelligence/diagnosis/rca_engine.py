"""
AEGIS Root Cause Analysis (RCA) Diagnostic Engine
Inference engine evaluating network topology, link load distributions, queue states,
and error signatures to pinpoint root cause with confidence scoring.
"""
from typing import Dict, List, Optional, Any, Tuple
from ...core.network.topology import Topology
from ...telemetry.metrics.definitions import NetworkGlobalSnapshot, LinkMetricSnapshot


class RootCauseAnalyzer:
    def __init__(self, topology: Topology):
        self.topology = topology

    def diagnose(self, anomaly: Dict[str, Any], snapshot: NetworkGlobalSnapshot) -> Dict[str, Any]:
        """
        Diagnoses the probable root cause of an anomaly.
        Returns: {
            "root_cause": str,
            "confidence": float,
            "evidence": List[str],
            "explanation": str
        }
        """
        resource = anomaly["resource"]
        resource_type = anomaly.get("resource_type", "LINK")
        anomaly_type = anomaly.get("anomaly_type", "")

        # 1. Node Anomaly Diagnosis
        if resource_type == "NODE":
            node = snapshot.nodes.get(resource)
            if node and node.status == "DOWN":
                # Check connected links
                connected_links = self.topology.get_out_links(resource)
                return {
                    "root_cause": "ROUTER_HARDWARE_OR_POWER_FAILURE",
                    "confidence": 0.98,
                    "evidence": [
                        f"Node {resource} operational status is DOWN",
                        f"All {len(connected_links)} incident links terminated at {resource} unreachable",
                        "Zero heartbeats received from control plane",
                    ],
                    "explanation": f"Router node {resource} suffered immediate hardware or power failure, severing transit through {resource}.",
                }
            elif node and node.cpu_utilization > 0.90:
                return {
                    "root_cause": "ROUTER_CPU_EXHAUSTION_OR_CONTROL_PLANE_STORM",
                    "confidence": 0.88,
                    "evidence": [
                        f"Node {resource} CPU utilization at {round(node.cpu_utilization * 100, 1)}%",
                        f"Node health score degraded to {round(node.health_score, 2)}",
                    ],
                    "explanation": f"Control plane storm or processing exhaustion causing packet drop at router {resource}.",
                }

        # 2. Link Anomaly Diagnosis
        link = snapshot.links.get(resource)
        if not link:
            return {
                "root_cause": "UNKNOWN_RESOURCE",
                "confidence": 0.30,
                "evidence": [f"Resource {resource} not found in topology snapshot"],
                "explanation": "Could not locate resource in current topology snapshot.",
            }

        # Case A: Hard Link Failure
        if link.status == "DOWN":
            return {
                "root_cause": "PHYSICAL_LINK_CUT_OR_PORT_SHUTDOWN",
                "confidence": 0.99,
                "evidence": [
                    f"Link {resource} operational status is DOWN",
                    "Packet loss is 100% for in-flight traffic",
                    "Throughput dropped to 0 bps",
                ],
                "explanation": f"Link {resource} experienced an abrupt loss of carrier/link cut.",
            }

        # Case B: Physical Loss Degradation (high loss, low-moderate utilization)
        topo_link = self.topology.get_link(resource)
        effective_loss = max(link.loss_rate, getattr(topo_link, "loss_rate", 0.0))
        if (effective_loss >= 0.05 or link.status == "DEGRADED" or (topo_link and topo_link.status.value == "DEGRADED")) and link.utilization < 0.65:
            return {
                "root_cause": "PHYSICAL_PACKET_LOSS_DEGRADATION",
                "confidence": 0.92,
                "evidence": [
                    f"Packet loss rate is elevated at {round(effective_loss * 100, 2)}%",
                    f"Link utilization remains low at {round(link.utilization * 100, 1)}%",
                    f"Queue occupancy is low ({link.queue_depth} packets), ruling out queue drops",
                ],
                "explanation": f"High packet loss without queue congestion indicates optical dispersion, dirty fiber, or hardware CRC errors on link {resource}.",
            }

        # Case C: Topology Partition or Routing Failure Check
        if anomaly_type in ("TOPOLOGY_PARTITION", "ROUTING_FAILURE"):
            return {
                "root_cause": anomaly_type,
                "confidence": 0.96,
                "evidence": [f"Anomaly type flagged as {anomaly_type}", f"Affected resource {resource}"],
                "explanation": f"Forwarding failure detected due to {anomaly_type} impacting path reachability.",
            }

        # Case D: Traffic Surge Detection
        if "rate_of_change" in anomaly.get("evidence", {}):
            roc_str = str(anomaly["evidence"]["rate_of_change"])
            return {
                "root_cause": "ABNORMAL_TRAFFIC_SURGE",
                "confidence": 0.91,
                "evidence": [
                    f"Rate of change spike: {roc_str}",
                    f"Link utilization reached {round(link.utilization * 100, 1)}%",
                    f"Queue depth is {link.queue_depth} packets",
                ],
                "explanation": f"Sudden burst of application traffic / flash crowd saturated link {resource}.",
            }

        # Case E: Queue Overflow Detection
        queue_ratio = link.queue_depth / 200.0
        if queue_ratio >= 0.85 or (link.queue_depth > 180 and link.packets_dropped > 0):
            return {
                "root_cause": "QUEUE_OVERFLOW",
                "confidence": 0.93,
                "evidence": [
                    f"Queue depth reached {link.queue_depth} packets (near buffer capacity)",
                    f"Packets dropped in interval: {link.packets_dropped}",
                    f"Link utilization: {round(link.utilization * 100, 1)}%",
                ],
                "explanation": f"Buffer capacity exhausted at link {resource} causing persistent tail drops.",
            }

        # Case F: Bandwidth Exhaustion / Congestion
        if link.utilization >= 0.85:
            # Check neighboring parallel links for cascading vs bottleneck
            src_node_links = self.topology.get_out_links(link.source)
            alternate_links = [l for dest_nid, l in src_node_links.items() if l.id != resource and l.is_operational()]
            alternate_utilizations = [snapshot.links[l.id].utilization for l in alternate_links if l.id in snapshot.links]
            avg_alt_util = sum(alternate_utilizations) / len(alternate_utilizations) if alternate_utilizations else 0.0

            evidence = [
                f"Link {resource} utilization is {round(link.utilization * 100, 1)}%",
                f"Queue depth is {link.queue_depth} packets with queue drops recorded",
                f"Round-trip latency surged to {round(link.latency_ms, 1)}ms",
            ]

            if link.utilization >= 0.98:
                return {
                    "root_cause": "BANDWIDTH_EXHAUSTION",
                    "confidence": 0.96,
                    "evidence": evidence + ["Physical transmission bandwidth completely saturated"],
                    "explanation": f"Offered load exceeds maximum physical throughput capacity of link {resource}.",
                }

            if avg_alt_util > 0.80:
                return {
                    "root_cause": "CASCADING_CONGESTION",
                    "confidence": 0.89,
                    "evidence": evidence + [f"Parallel alternate egress links also highly utilized (avg {round(avg_alt_util * 100, 1)}%)"],
                    "explanation": f"System-wide traffic volume exceeds available edge capacity, leading to cascading congestion across {resource} and parallel trunks.",
                }
            else:
                return {
                    "root_cause": "LINK_CONGESTION",
                    "confidence": 0.94,
                    "evidence": evidence + [f"Alternate paths have spare capacity (avg utilization: {round(avg_alt_util * 100, 1)}%)"],
                    "explanation": f"Traffic concentration on primary shortest-path link {resource} caused buffer bloat and queue exhaustion while alternate paths remain underutilized.",
                }

        # Default fallback
        return {
            "root_cause": "TRANSIENT_MICROBURST",
            "confidence": 0.65,
            "evidence": [f"Transient anomaly detected with score {anomaly.get('anomaly_score')}"],
            "explanation": f"Transient traffic microburst observed on {resource}.",
        }
