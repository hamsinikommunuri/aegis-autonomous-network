"""
Tests for Anomaly Detection (Thresholds, Moving Baseline, Rate-of-Change, Multi-Metric Correlation)
"""
import pytest
from aegis.core.network.topology import Topology
from aegis.core.simulation.engine import SimulationEngine
from aegis.core.flows.flow import TrafficFlow
from aegis.core.packets.packet import TrafficClass
from aegis.telemetry.collectors.collector import TelemetryCollector
from aegis.intelligence.anomaly_detection.correlator import AnomalyDetector
from aegis.experiments.failure_injection.injector import FailureInjector


def test_hard_link_failure_detection():
    topo = Topology.create_enterprise_isp_topology()
    sim = SimulationEngine(topology=topo)
    telemetry = TelemetryCollector(sim)
    detector = AnomalyDetector()
    injector = FailureInjector(sim)

    # Initial baseline snapshot
    snapshot = telemetry.collect()
    anomalies = detector.analyze_snapshot(snapshot, telemetry.buffer)
    assert len(anomalies) == 0

    # Inject hard link failure
    injector.inject_link_failure("DR1-CR1")
    snapshot = telemetry.collect()
    anomalies = detector.analyze_snapshot(snapshot, telemetry.buffer)

    assert len(anomalies) >= 1
    found = any(a["resource"] == "DR1-CR1" and a["severity"] == "CRITICAL" for a in anomalies)
    assert found is True


def test_congestion_anomaly_detection():
    topo = Topology.create_enterprise_isp_topology()
    sim = SimulationEngine(topology=topo)
    # Add heavy flow to create utilization
    flow = TrafficFlow(
        id="f1", name="Heavy", source_id="HOST-A", dest_id="SVR-1",
        traffic_class=TrafficClass.NORMAL, demand_bps=80_000_000.0
    )
    sim.add_flow(flow)
    telemetry = TelemetryCollector(sim)
    detector = AnomalyDetector()

    # Step simulation
    for _ in range(5):
        sim.step()
        telemetry.collect()

    # Choke link to drive utilization up
    link = sim.topology.get_link_between("AS1", "DR1")
    assert link is not None
    link.current_utilization = 0.94
    link.current_queue_depth = 180

    snapshot = telemetry.collect()
    anomalies = detector.analyze_snapshot(snapshot, telemetry.buffer)
    assert len(anomalies) >= 1
    as1_anom = [a for a in anomalies if a["resource"] == link.id]
    assert len(as1_anom) > 0
    assert as1_anom[0]["anomaly_score"] >= 0.70
