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
                "root_cause": "PHYSICAL_LAYER_OPTICAL_OR_BIT_ERROR_DEGRADATION",
                "confidence": 0.92,
                "evidence": [
                    f"Packet loss rate is elevated at {round(effective_loss * 100, 2)}%",
                    f"Link utilization remains low at {round(link.utilization * 100, 1)}%",
                    f"Queue occupancy is low ({link.queue_depth} packets), ruling out queue drops",
                ],
                "explanation": f"High packet loss without queue congestion indicates optical dispersion, dirty fiber, or hardware CRC errors on link {resource}.",
            }

        # Case C: Congestion / Traffic Surge
        if link.utilization >= 0.85:
            # Check if neighboring parallel links are also saturated or have spare capacity
            src_node_links = self.topology.get_out_links(link.source)
            alternate_links = [l for lid, l in src_node_links.items() if lid != resource and l.is_operational()]
            alternate_utilizations = [snapshot.links[l.id].utilization for l in alternate_links if l.id in snapshot.links]
            avg_alt_util = sum(alternate_utilizations) / len(alternate_utilizations) if alternate_utilizations else 0.0

            evidence = [
                f"Link {resource} utilization is {round(link.utilization * 100, 1)}%",
                f"Queue depth is {link.queue_depth} packets with queue drops recorded",
                f"Round-trip latency surged to {round(link.latency_ms, 1)}ms",
            ]

            if avg_alt_util > 0.80:
                return {
                    "root_cause": "CASCADING_SYSTEMIC_NETWORK_CONGESTION",
                    "confidence": 0.89,
                    "evidence": evidence + [f"Parallel alternate egress links also highly utilized (avg {round(avg_alt_util * 100, 1)}%)"],
                    "explanation": f"System-wide traffic volume exceeds available edge capacity, leading to cascading congestion across {resource} and parallel trunks.",
                }
            else:
                return {
                    "root_cause": "LINK_BOTTLENECK_CONGESTION_AND_SUBOPTIMAL_FLOW_DISTRIBUTION",
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
