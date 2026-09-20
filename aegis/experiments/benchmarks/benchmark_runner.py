"""
AEGIS Quantitative Benchmark Runner
Executes head-to-head comparison between:
1. Baseline (Static Shortest Path, no self-healing)
2. Reactive AEGIS (Anomaly detection -> RCA -> Mitigation -> Verification)
3. Predictive AEGIS (Trend analysis -> Proactive preventive reroute)
"""
from typing import Dict, List, Any
import copy
from ...core.network.topology import Topology
from ...core.network.link import LinkStatus
from ...core.simulation.engine import SimulationEngine
from ...core.flows.flow import TrafficFlow
from ...core.packets.packet import TrafficClass
from ...telemetry.collectors.collector import TelemetryCollector
from ...recovery.orchestrator import AegisOrchestrator
from ..failure_injection.injector import FailureInjector


class BenchmarkRunner:
    def __init__(self, step_duration_ms: float = 100.0, seed: int = 42):
        self.step_duration_ms = step_duration_ms
        self.seed = seed

    def run_comparison(self, scenario_type: str = "LINK_FAILURE", simulation_steps: int = 40) -> Dict[str, Any]:
        """
        Runs 3 identical simulation trials under the same workload and injected failure:
        Trial 1: Baseline Static (No recovery)
        Trial 2: Reactive AEGIS
        Trial 3: Predictive AEGIS
        """
        baseline_res = self._run_single_trial(mode="BASELINE", scenario_type=scenario_type, total_steps=simulation_steps)
        reactive_res = self._run_single_trial(mode="REACTIVE", scenario_type=scenario_type, total_steps=simulation_steps)
        predictive_res = self._run_single_trial(mode="PREDICTIVE", scenario_type=scenario_type, total_steps=simulation_steps)

        return {
            "scenario": scenario_type,
            "total_steps": simulation_steps,
            "simulation_duration_sec": (simulation_steps * self.step_duration_ms) / 1000.0,
            "results": {
                "baseline": baseline_res,
                "reactive": reactive_res,
                "predictive": predictive_res,
            },
            "summary": {
                "loss_reduction_pct": round(((baseline_res["packet_loss_rate"] - reactive_res["packet_loss_rate"]) / max(0.001, baseline_res["packet_loss_rate"])) * 100, 1),
                "latency_improvement_pct": round(((baseline_res["average_latency_ms"] - reactive_res["average_latency_ms"]) / max(0.001, baseline_res["average_latency_ms"])) * 100, 1),
                "predictive_loss_reduction_pct": round(((baseline_res["packet_loss_rate"] - predictive_res["packet_loss_rate"]) / max(0.001, baseline_res["packet_loss_rate"])) * 100, 1),
            }
        }

    def _run_single_trial(self, mode: str, scenario_type: str, total_steps: int) -> Dict[str, Any]:
        topo = Topology.create_enterprise_isp_topology()
        sim = SimulationEngine(topology=topo, step_duration_ms=self.step_duration_ms, seed=self.seed)

        # Standard test workload: 3 flows (CRITICAL, NORMAL, BULK)
        f_crit = TrafficFlow(id="f_crit", name="VoIP/Control", source_id="HOST-A", dest_id="SVR-1", traffic_class=TrafficClass.CRITICAL, demand_bps=15_000_000.0, latency_sla_ms=35.0)
        f_norm = TrafficFlow(id="f_norm", name="Web Apps", source_id="HOST-A", dest_id="SVR-1", traffic_class=TrafficClass.NORMAL, demand_bps=30_000_000.0, latency_sla_ms=50.0)
        f_bulk = TrafficFlow(id="f_bulk", name="DB Backup", source_id="HOST-B", dest_id="SVR-2", traffic_class=TrafficClass.BULK, demand_bps=45_000_000.0, latency_sla_ms=100.0)

        sim.add_flow(f_crit)
        sim.add_flow(f_norm)
        sim.add_flow(f_bulk)

        telemetry = TelemetryCollector(sim)
        orchestrator = AegisOrchestrator(sim, telemetry, autonomous_mode=(mode != "BASELINE"))
        injector = FailureInjector(sim)

        # In PREDICTIVE mode, we configure proactive early sensitivity
        if mode == "PREDICTIVE":
            orchestrator.predictor.min_trend_slope = 0.015

        failure_injected_step = 10
        recovery_time_steps = 0
        failure_active = False

        for step in range(total_steps):
            # Inject failure at step 10
            if step == failure_injected_step:
                failure_active = True
                if scenario_type == "LINK_FAILURE":
                    injector.inject_link_failure("DR1-CR1")
                elif scenario_type == "CONGESTION":
                    injector.inject_bandwidth_reduction("DR1-CR1", 20_000_000.0)
                elif scenario_type == "ROUTER_FAILURE":
                    injector.inject_node_failure("CR1")

            sim.step()

            # Measure recovery time in steps
            if failure_active and mode != "BASELINE":
                if len(orchestrator.memory.history) > 0:
                    if recovery_time_steps == 0:
                        recovery_time_steps = step - failure_injected_step

        # Final telemetry snapshot
        latest = telemetry.get_latest_snapshot()
        total_sent = latest.total_packets_sent if latest else 1
        total_recv = latest.total_packets_received if latest else 0
        total_drop = latest.total_packets_dropped if latest else 0

        loss_rate = (total_drop / max(1, total_recv + total_drop))
        sla_rate = latest.sla_compliance_rate if latest else 0.0
        avg_lat = latest.average_latency_ms if latest else 0.0
        throughput_mbps = (latest.total_throughput_bps / 1e6) if latest else 0.0

        recovery_time_ms = (recovery_time_steps * self.step_duration_ms) if recovery_time_steps > 0 else (0.0 if mode != "BASELINE" else -1.0)

        return {
            "mode": mode,
            "packets_sent": total_sent,
            "packets_received": total_recv,
            "packets_dropped": total_drop,
            "packet_loss_rate": round(loss_rate, 4),
            "packet_loss_percent": round(loss_rate * 100.0, 2),
            "average_latency_ms": round(avg_lat, 2),
            "total_throughput_mbps": round(throughput_mbps, 2),
            "sla_availability_percent": round(sla_rate * 100.0, 1),
            "recovery_time_ms": round(recovery_time_ms, 1),
            "incidents_handled": len(orchestrator.memory.history),
            "rollbacks_count": sum(1 for inc in orchestrator.memory.history if inc.get("rollback_performed")),
        }
