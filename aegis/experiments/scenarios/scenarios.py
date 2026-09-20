"""
AEGIS Pre-defined Realistic Failure and Self-Healing Scenarios
Executable scenarios demonstrating congestion, router crash, progressive optical degradation,
surges, cascading failures, and verification failure with rollback.
"""
from typing import Dict, List, Any, Callable
from ..failure_injection.injector import FailureInjector
from ...recovery.orchestrator import AegisOrchestrator


class ScenarioRunner:
    def __init__(self, orchestrator: AegisOrchestrator):
        self.orchestrator = orchestrator
        self.sim = orchestrator.sim
        self.injector = FailureInjector(self.sim)

    def load_scenario(self, scenario_id: str) -> Dict[str, Any]:
        """Loads and prepares a specified scenario."""
        self.injector.reset_all_failures()
        
        scenarios_map: Dict[str, Callable[[], Dict[str, Any]]] = {
            "SCENARIO_A": self._setup_scenario_a,
            "SCENARIO_B": self._setup_scenario_b,
            "SCENARIO_C": self._setup_scenario_c,
            "SCENARIO_D": self._setup_scenario_d,
            "SCENARIO_E": self._setup_scenario_e,
            "SCENARIO_F": self._setup_scenario_f,
        }

        handler = scenarios_map.get(scenario_id.upper())
        if handler:
            return handler()
        else:
            raise ValueError(f"Unknown scenario ID: {scenario_id}")

    def _setup_scenario_a(self) -> Dict[str, Any]:
        """Scenario A — Progressive Link Congestion on Primary Backbone."""
        target_link = "DR1-CR1"
        # Choke backbone link bandwidth to trigger saturation under existing flows
        self.injector.inject_bandwidth_reduction(target_link, new_bandwidth_bps=25_000_000.0)
        return {
            "scenario_id": "SCENARIO_A",
            "title": "Progressive Backbone Congestion",
            "description": f"Chokes link {target_link} to 25 Mbps under high load, driving utilization above 90% and triggering predictive warning followed by QoS flow offload.",
            "expected_lifecycle": "DETECT -> DIAGNOSE -> REROUTE_BULK -> VERIFY_RECOVERY",
        }

    def _setup_scenario_b(self) -> Dict[str, Any]:
        """Scenario B — Sudden Core Router Hardware Failure."""
        target_node = "CR1"
        self.injector.inject_node_failure(target_node)
        return {
            "scenario_id": "SCENARIO_B",
            "title": "Sudden Core Router Hardware Failure",
            "description": f"Core Router {target_node} goes abruptly offline, dropping heartbeats and severing primary backbone transit, triggering immediate topology reconvergence.",
            "expected_lifecycle": "DETECT -> DIAGNOSE (ROUTER_FAILURE) -> ISOLATE & RECONVERGE -> VERIFY",
        }

    def _setup_scenario_c(self) -> Dict[str, Any]:
        """Scenario C — Progressive Optical Link Degradation (Physical BER)."""
        target_link = "DR1-CR1"
        self.injector.inject_packet_loss(target_link, loss_rate=0.15)
        self.injector.inject_latency_spike(target_link, extra_delay_ms=65.0)
        return {
            "scenario_id": "SCENARIO_C",
            "title": "Progressive Physical Fiber Degradation",
            "description": f"Link {target_link} experiences 15% bit error rate and optical dispersion latency spike without high utilization, testing RCA differentiation between congestion and hardware faults.",
            "expected_lifecycle": "DETECT -> DIAGNOSE (PHYSICAL_DEGRADATION) -> DIVERT_PATH -> VERIFY",
        }

    def _setup_scenario_d(self) -> Dict[str, Any]:
        """Scenario D — Flash Crowd Traffic Surge."""
        # Find any active normal or bulk flow
        target_flow_id = list(self.sim.flows.keys())[0] if self.sim.flows else "flow-1"
        self.injector.inject_traffic_surge(target_flow_id, multiplier=5.0)
        return {
            "scenario_id": "SCENARIO_D",
            "title": "Flash Crowd Application Traffic Surge",
            "description": f"Flow {target_flow_id} surges by 500%, instantly filling queue buffers and triggering autonomous rate-limiting and dynamic multi-path rebalancing.",
            "expected_lifecycle": "DETECT -> PREDICT -> SHAPE / REBALANCE -> VERIFY",
        }

    def _setup_scenario_e(self) -> Dict[str, Any]:
        """Scenario E — Cascading Network Failure."""
        # Fail primary link DR1-CR1 and choke DR1-CR2
        self.injector.inject_link_failure("DR1-CR1")
        self.injector.inject_bandwidth_reduction("DR1-CR2", new_bandwidth_bps=20_000_000.0)
        return {
            "scenario_id": "SCENARIO_E",
            "title": "Cascading Multi-Link Congestion Failure",
            "description": "Primary link cut forces transit onto secondary path which is simultaneously constrained, forcing AEGIS to route traffic around the entire northern corridor via southern distribution.",
            "expected_lifecycle": "DETECT -> RE-ROUTE -> CASCADE_DETECT -> GLOBAL_RECONVERGE -> VERIFY",
        }

    def _setup_scenario_f(self) -> Dict[str, Any]:
        """
        Scenario F — Ineffective First Strategy & Autonomous Rollback.
        We deliberately degrade secondary link AS1-DR2, so that if Plan A offloads to DR2,
        it triggers collateral congestion and fails verification, proving automated rollback and Plan B retry!
        """
        # Constrain primary link
        self.injector.inject_bandwidth_reduction("DR1-CR1", new_bandwidth_bps=25_000_000.0)
        # Constrain alternate path link so offloading there will cause collateral degradation
        self.injector.inject_bandwidth_reduction("AS1-DR2", new_bandwidth_bps=10_000_000.0)
        return {
            "scenario_id": "SCENARIO_F",
            "title": "Mitigation Failure & Autonomous Rollback",
            "description": "Initial reroute overburdens alternate path AS1-DR2, violating collateral safety threshold. AEGIS automatically aborts, rolls back previous configuration, and deploys alternate Plan B.",
            "expected_lifecycle": "DETECT -> PLAN_A -> MITIGATE -> VERIFY_FAIL -> ROLLBACK -> PLAN_B -> VERIFY_SUCCESS",
        }
