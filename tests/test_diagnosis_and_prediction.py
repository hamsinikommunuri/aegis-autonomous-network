"""
Tests for Root Cause Analysis (RCA) and Predictive Degradation Engine
"""
import pytest
from aegis.core.network.topology import Topology
from aegis.core.simulation.engine import SimulationEngine
from aegis.telemetry.collectors.collector import TelemetryCollector
from aegis.intelligence.anomaly_detection.correlator import AnomalyDetector
from aegis.intelligence.diagnosis.rca_engine import RootCauseAnalyzer
from aegis.intelligence.prediction.predictor import DegradationPredictor
from aegis.experiments.failure_injection.injector import FailureInjector


def test_rca_hardware_router_failure():
    topo = Topology.create_enterprise_isp_topology()
    sim = SimulationEngine(topology=topo)
    telemetry = TelemetryCollector(sim)
    rca = RootCauseAnalyzer(topo)
    injector = FailureInjector(sim)

    # Crash core router
    injector.inject_node_failure("CR1")
    snapshot = telemetry.collect()

    detector = AnomalyDetector()
    anomalies = detector.analyze_snapshot(snapshot, telemetry.buffer)
    node_anom = [a for a in anomalies if a["resource"] == "CR1"][0]

    diagnosis = rca.diagnose(node_anom, snapshot)
    assert diagnosis["confidence"] >= 0.90
    assert "ROUTER" in diagnosis["root_cause"]
    assert len(diagnosis["evidence"]) >= 2


def test_rca_physical_optical_degradation():
    topo = Topology.create_enterprise_isp_topology()
    sim = SimulationEngine(topology=topo)
    telemetry = TelemetryCollector(sim)
    rca = RootCauseAnalyzer(topo)
    injector = FailureInjector(sim)

    # Degrade link with 12% loss but low load
    injector.inject_packet_loss("DR1-CR1", loss_rate=0.12)
    snapshot = telemetry.collect()

    anomaly = {
        "resource": "DR1-CR1",
        "resource_type": "LINK",
        "anomaly_type": "LINK_DEGRADATION",
        "anomaly_score": 0.85,
    }
    diag = rca.diagnose(anomaly, snapshot)
    assert diag["confidence"] >= 0.85
    assert "PHYSICAL" in diag["root_cause"] or "BIT_ERROR" in diag["root_cause"] or "OPTICAL" in diag["root_cause"]


def test_predictive_degradation_forecast():
    topo = Topology.create_enterprise_isp_topology()
    sim = SimulationEngine(topology=topo)
    telemetry = TelemetryCollector(sim)
    predictor = DegradationPredictor(lookback_window=5, min_trend_slope=0.03)

    # Simulate rising utilization trend: 60%, 65%, 70%, 75%, 80%
    target_link = "DR1-CR1"
    link = topo.get_link(target_link)
    link.current_utilization = 0.80
    snapshot = telemetry.collect()
    
    time_ms = 0.0
    for u in [0.60, 0.65, 0.70, 0.75, 0.80]:
        time_ms += 100.0
        telemetry.buffer.append_point(time_ms, {f"link:{target_link}:utilization": u})

    preds = predictor.predict_degradations(snapshot, telemetry.buffer)
    
    assert len(preds) >= 1
    p = preds[0]
    assert p["resource"] == target_link
    assert p["risk_level"] in ("HIGH", "CRITICAL")
    assert p["estimated_steps_to_crossing"] > 0
    assert "recommended_preventive_action" in p
