"""
AEGIS Telemetry Collector
Continuously aggregates link, node, and flow metrics into point-in-time snapshots
and time-series buffers.
"""
from typing import Dict, List, Optional, Any
from ..metrics.definitions import (
    LinkMetricSnapshot,
    NodeMetricSnapshot,
    FlowMetricSnapshot,
    NetworkGlobalSnapshot,
)
from ..time_series.buffer import TimeSeriesBuffer
from ...core.simulation.engine import SimulationEngine


class TelemetryCollector:
    def __init__(self, simulation: SimulationEngine, buffer_size: int = 300):
        self.sim = simulation
        self.buffer = TimeSeriesBuffer(max_points=buffer_size)
        self.snapshots: List[NetworkGlobalSnapshot] = []
        self.max_snapshots = 100

    def collect(self) -> NetworkGlobalSnapshot:
        """Takes a full snapshot of current network state and updates time-series buffer."""
        step_duration_sec = self.sim.step_duration_ms / 1000.0

        # 1. Collect Links
        link_snapshots: Dict[str, LinkMetricSnapshot] = {}
        total_throughput_bps = 0.0

        for lid, link in self.sim.topology.links.items():
            bytes_sent = self.sim.step_bytes_per_link.get(lid, 0)
            throughput = (bytes_sent * 8.0) / step_duration_sec
            total_throughput_bps += throughput

            link_snapshots[lid] = LinkMetricSnapshot(
                link_id=lid,
                source=link.source,
                destination=link.destination,
                status=link.status.value,
                bandwidth_bps=link.bandwidth_bps,
                utilization=link.current_utilization,
                latency_ms=link.current_latency_ms,
                loss_rate=link.recent_loss_rate,
                queue_depth=link.current_queue_depth,
                queue_bytes=link.current_queue_bytes,
                bytes_transmitted=link.bytes_transmitted,
                packets_transmitted=link.packets_transmitted,
                packets_dropped=link.packets_dropped,
            )

            # Record per-link metric in time-series
            self.buffer.append_point(
                self.sim.current_time_ms,
                {
                    f"link:{lid}:utilization": link.current_utilization,
                    f"link:{lid}:latency": link.current_latency_ms,
                    f"link:{lid}:loss": link.recent_loss_rate,
                    f"link:{lid}:queue": link.current_queue_depth,
                }
            )

        # 2. Collect Nodes
        node_snapshots: Dict[str, NodeMetricSnapshot] = {}
        for nid, node in self.sim.topology.nodes.items():
            node.update_health()
            node_snapshots[nid] = NodeMetricSnapshot(
                node_id=nid,
                status=node.status.value,
                cpu_utilization=node.cpu_utilization,
                memory_utilization=node.memory_utilization,
                queue_depth=node.current_queue_depth,
                health_score=node.health_score,
                forwarded_packets=node.forwarded_packets,
                dropped_packets=node.dropped_packets,
            )

        # 3. Collect Flows
        flow_snapshots: Dict[str, FlowMetricSnapshot] = {}
        total_pkts_sent = 0
        total_pkts_recv = 0
        total_pkts_drop = 0
        latencies: List[float] = []
        jitters: List[float] = []
        sla_compliant_count = 0

        for fid, flow in self.sim.flows.items():
            total_pkts_sent += flow.packets_sent
            total_pkts_recv += flow.packets_received
            total_pkts_drop += flow.packets_dropped
            if flow.average_latency_ms > 0:
                latencies.append(flow.average_latency_ms)
            if flow.jitter_ms > 0:
                jitters.append(flow.jitter_ms)
            if not flow.sla_violated:
                sla_compliant_count += 1

            flow_snapshots[fid] = FlowMetricSnapshot(
                flow_id=fid,
                traffic_class=flow.traffic_class.value,
                demand_bps=flow.demand_bps,
                packets_sent=flow.packets_sent,
                packets_received=flow.packets_received,
                packets_dropped=flow.packets_dropped,
                loss_percent=flow.loss_rate_percent,
                avg_latency_ms=flow.average_latency_ms,
                jitter_ms=flow.jitter_ms,
                sla_violated=flow.sla_violated,
                current_path=list(flow.current_path),
            )

        total_flow_pkts = total_pkts_recv + total_pkts_drop
        global_loss = (total_pkts_drop / total_flow_pkts) if total_flow_pkts > 0 else 0.0
        avg_lat = (sum(latencies) / len(latencies)) if latencies else 0.0
        avg_jit = (sum(jitters) / len(jitters)) if jitters else 0.0
        sla_rate = (sla_compliant_count / max(1, len(self.sim.flows))) if self.sim.flows else 1.0

        snapshot = NetworkGlobalSnapshot(
            timestamp_ms=self.sim.current_time_ms,
            tick=self.sim.tick_count,
            total_throughput_bps=total_throughput_bps,
            total_packets_sent=total_pkts_sent,
            total_packets_received=total_pkts_recv,
            total_packets_dropped=total_pkts_drop,
            global_packet_loss_rate=global_loss,
            average_latency_ms=avg_lat,
            average_jitter_ms=avg_jit,
            sla_compliance_rate=sla_rate,
            links=link_snapshots,
            nodes=node_snapshots,
            flows=flow_snapshots,
        )

        self.snapshots.append(snapshot)
        if len(self.snapshots) > self.max_snapshots:
            self.snapshots.pop(0)

        # Global time series points
        self.buffer.append_point(
            self.sim.current_time_ms,
            {
                "global:throughput_mbps": total_throughput_bps / 1_000_000.0,
                "global:packet_loss_rate": global_loss,
                "global:average_latency_ms": avg_lat,
                "global:average_jitter_ms": avg_jit,
                "global:sla_compliance_rate": sla_rate,
            }
        )

        return snapshot

    def get_latest_snapshot(self) -> Optional[NetworkGlobalSnapshot]:
        return self.snapshots[-1] if self.snapshots else None
