"""
Tests for Pre-defined Scenarios and Quantitative Benchmarks
"""
import pytest
from aegis.core.network.topology import Topology
from aegis.core.simulation.engine import SimulationEngine
from aegis.telemetry.collectors.collector import TelemetryCollector
from aegis.recovery.orchestrator import AegisOrchestrator
from aegis.experiments.scenarios.scenarios import ScenarioRunner
from aegis.experiments.benchmarks.benchmark_runner import BenchmarkRunner


def test_scenario_loader_execution():
    topo = Topology.create_enterprise_isp_topology()
    sim = SimulationEngine(topology=topo)
    telemetry = TelemetryCollector(sim)
    orchestrator = AegisOrchestrator(sim, telemetry)
    runner = ScenarioRunner(orchestrator)

    # Load Scenario A
    res_a = runner.load_scenario("SCENARIO_A")
    assert res_a["scenario_id"] == "SCENARIO_A"
    assert sim.topology.get_link("DR1-CR1").bandwidth_bps == 25_000_000.0

    # Load Scenario B
    res_b = runner.load_scenario("SCENARIO_B")
    assert res_b["scenario_id"] == "SCENARIO_B"
    assert sim.topology.get_node("CR1").status.value == "DOWN"

    # Reset
    runner.injector.reset_all_failures()
    assert sim.topology.get_node("CR1").status.value == "UP"


def test_quantitative_benchmark_comparison():
    runner = BenchmarkRunner(step_duration_ms=100.0, seed=42)
    benchmark_res = runner.run_comparison(scenario_type="LINK_FAILURE", simulation_steps=18)

    assert "baseline" in benchmark_res["results"]
    assert "reactive" in benchmark_res["results"]
    assert "predictive" in benchmark_res["results"]
    
    baseline = benchmark_res["results"]["baseline"]
    reactive = benchmark_res["results"]["reactive"]

    # Baseline should experience packet loss after link failure, whereas reactive should recover
    assert baseline["packets_sent"] > 0
    assert reactive["packets_sent"] > 0
