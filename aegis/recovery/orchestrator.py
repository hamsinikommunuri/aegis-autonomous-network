"""
AEGIS Autonomous Lifecycle Orchestrator
Executes the closed-loop autonomous control loop:
OBSERVE -> DETECT -> DIAGNOSE -> PREDICT -> PLAN -> ACT -> VERIFY -> ROLLBACK / ADAPT -> LEARN
"""
from typing import Dict, List, Optional, Any
import uuid
from .incident import Incident, IncidentStatus, IncidentSeverity
from .planner.planner import RecoveryPlanner
from .actuator.network_actuator import NetworkActuator
from .verification.verifier import VerificationEngine
from .rollback.rollback_manager import RollbackManager
from .memory.incident_memory import IncidentMemory
from ..telemetry.collectors.collector import TelemetryCollector
from ..intelligence.anomaly_detection.correlator import AnomalyDetector
from ..intelligence.diagnosis.rca_engine import RootCauseAnalyzer
from ..intelligence.prediction.predictor import DegradationPredictor
from ..core.simulation.engine import SimulationEngine


class AegisOrchestrator:
    def __init__(
        self,
        simulation: SimulationEngine,
        telemetry: TelemetryCollector,
        autonomous_mode: bool = True,
    ):
        self.sim = simulation
        self.telemetry = telemetry
        self.autonomous_mode = autonomous_mode

        # Intelligence components
        self.anomaly_detector = AnomalyDetector()
        self.rca_engine = RootCauseAnalyzer(simulation.topology)
        self.predictor = DegradationPredictor()

        # Recovery components
        self.planner = RecoveryPlanner(simulation)
        self.actuator = NetworkActuator(simulation)
        self.verifier = VerificationEngine(required_settle_steps=3)
        self.rollback_mgr = RollbackManager(self.actuator)
        self.memory = IncidentMemory()

        # Active state
        self.active_incidents: Dict[str, Incident] = {}
        self.incident_counter = 0

        # Verification tracking: incident_id -> (remaining_steps, action_record)
        self.pending_verifications: Dict[str, Tuple[int, Dict[str, Any]]] = {}

        # Connect step callback
        self.sim.on_step_complete = self._on_simulation_step

    def _on_simulation_step(self, step_data: Dict[str, Any]) -> None:
        """Called immediately after each discrete simulation tick."""
        self.process_cycle()

    def process_cycle(self) -> Dict[str, Any]:
        """
        Executes one complete closed-loop cycle.
        """
        current_time = self.sim.current_time_ms

        # 1. OBSERVE: Collect current telemetry snapshot
        snapshot = self.telemetry.collect()

        # 2. DETECT: Run anomaly detection
        detected_anomalies = self.anomaly_detector.analyze_snapshot(snapshot, self.telemetry.buffer)

        for anomaly in detected_anomalies:
            res = anomaly["resource"]
            # Check if an active incident already tracks this resource
            existing = self._find_active_incident_for_resource(res)
            if not existing:
                self.incident_counter += 1
                inc_id = f"INC-{self.incident_counter:03d}"
                sev = IncidentSeverity(anomaly.get("severity", "HIGH"))
                incident = Incident(
                    id=inc_id,
                    incident_type=anomaly.get("anomaly_type", "ANOMALY"),
                    affected_resource=res,
                    severity=sev,
                    detected_time_ms=current_time,
                    status=IncidentStatus.DETECTED,
                    evidence=anomaly.get("evidence", {}),
                    anomaly_score=anomaly.get("anomaly_score", 0.7),
                )
                incident.add_timeline_event(current_time, "ANOMALY_DETECTED", anomaly.get("reason"))
                self.active_incidents[inc_id] = incident

                # 3. DIAGNOSE: Perform root cause analysis
                diag = self.rca_engine.diagnose(anomaly, snapshot)
                incident.status = IncidentStatus.DIAGNOSED
                incident.diagnosis = diag["root_cause"]
                incident.diagnosis_confidence = diag["confidence"]
                incident.diagnosis_explanation = diag["explanation"]
                incident.add_timeline_event(
                    current_time,
                    "ROOT_CAUSE_IDENTIFIED",
                    f"{diag['root_cause']} (Confidence: {int(diag['confidence']*100)}%)"
                )

        # 4. PREDICT: Run predictive degradation analysis
        predictions = self.predictor.predict_degradations(snapshot, self.telemetry.buffer)
        for pred in predictions:
            res = pred["resource"]
            existing = self._find_active_incident_for_resource(res)
            if not existing:
                self.incident_counter += 1
                inc_id = f"PRED-{self.incident_counter:03d}"
                incident = Incident(
                    id=inc_id,
                    incident_type="PREDICTED_DEGRADATION",
                    affected_resource=res,
                    severity=IncidentSeverity(pred.get("risk_level", "HIGH")),
                    detected_time_ms=current_time,
                    status=IncidentStatus.DIAGNOSED,
                    is_predictive=True,
                    predicted_time_to_breach_ms=pred.get("estimated_time_to_crossing_ms"),
                    predicted_consequence=pred.get("expected_consequence"),
                    diagnosis="PREDICTED_SATURATION_TREND",
                    diagnosis_confidence=0.85,
                    diagnosis_explanation=pred.get("reason"),
                    evidence={"slope": pred.get("slope_per_interval"), "current_util": pred.get("current_utilization")},
                )
                incident.add_timeline_event(current_time, "PREDICTIVE_WARNING", pred.get("reason"))
                self.active_incidents[inc_id] = incident

        # 5. PLAN & ACT: For active incidents requiring action
        if self.autonomous_mode:
            for inc_id, incident in list(self.active_incidents.items()):
                if incident.status in (IncidentStatus.DIAGNOSED, IncidentStatus.DETECTED, IncidentStatus.ROLLBACK):
                    # Capture pre-recovery snapshot
                    link = snapshot.links.get(incident.affected_resource)
                    if link:
                        incident.pre_recovery_metrics = {
                            "utilization": link.utilization,
                            "loss_rate": link.loss_rate,
                            "latency_ms": link.latency_ms,
                        }

                    # PLAN: Generate and rank recovery plans
                    incident.status = IncidentStatus.PLANNING
                    candidates = self.planner.generate_and_rank_plans(incident)
                    
                    # Pick top untried candidate plan
                    chosen_plan = None
                    for cand in candidates:
                        if cand.get("id") not in incident.failed_plan_ids and cand.get("status") != "FAILED":
                            chosen_plan = cand
                            break

                    if chosen_plan:
                        incident.selected_plan_id = chosen_plan["id"]
                        incident.add_timeline_event(
                            current_time,
                            "RECOVERY_PLAN_SELECTED",
                            f"{chosen_plan['id']}: {chosen_plan['title']} (Score: {chosen_plan['score']})"
                        )

                        # ACT: Execute action through actuator
                        incident.status = IncidentStatus.MITIGATING
                        action_record = self.actuator.execute_plan(chosen_plan)
                        incident.applied_action = action_record
                        incident.action_applied_time_ms = current_time
                        incident.add_timeline_event(
                            current_time,
                            "MITIGATION_EXECUTED",
                            "; ".join(action_record.get("actions_applied", []))
                        )

                        # Start verification countdown
                        incident.status = IncidentStatus.VERIFYING
                        self.pending_verifications[inc_id] = (self.verifier.settle_steps, action_record)
                    else:
                        incident.status = IncidentStatus.CLOSED
                        incident.add_timeline_event(
                            current_time,
                            "ALL_PLANS_EXHAUSTED",
                            "All candidate recovery plans were attempted and rolled back."
                        )

        # 6. VERIFY / ROLLBACK: Handle pending verifications
        for inc_id, (steps_left, action_record) in list(self.pending_verifications.items()):
            if steps_left > 1:
                self.pending_verifications[inc_id] = (steps_left - 1, action_record)
            else:
                # Verification interval reached; evaluate outcome!
                del self.pending_verifications[inc_id]
                incident = self.active_incidents.get(inc_id)
                if not incident:
                    continue

                is_success, reason, post_metrics = self.verifier.evaluate_recovery(incident, snapshot)
                incident.post_recovery_metrics = post_metrics
                incident.verification_success = is_success
                incident.verification_reason = reason

                if is_success:
                    # 7. RESOLVE
                    incident.status = IncidentStatus.RESOLVED
                    incident.resolved_time_ms = current_time
                    incident.add_timeline_event(current_time, "RECOVERY_VERIFIED", reason)
                    self.memory.record_resolved_incident(incident)
                    del self.active_incidents[inc_id]
                else:
                    # 8. ROLLBACK & ADAPT
                    incident.add_timeline_event(current_time, "VERIFICATION_FAILED", reason)
                    self.rollback_mgr.perform_rollback(incident, action_record, reason)
                    # Incident status is now ROLLBACK; next process_cycle will try next candidate!

        snapshot.active_incidents_count = len(self.active_incidents)
        return {
            "time_ms": current_time,
            "active_incidents": {k: v.to_dict() for k, v in self.active_incidents.items()},
            "resolved_count": len(self.memory.history),
        }

    def _find_active_incident_for_resource(self, resource: str) -> Optional[Incident]:
        for inc in self.active_incidents.values():
            if inc.affected_resource == resource and inc.status != IncidentStatus.RESOLVED:
                return inc
        return None
