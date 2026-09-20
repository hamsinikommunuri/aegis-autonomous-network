"""
AEGIS Rollback Manager
Coordinates the reversion of ineffective mitigations and triggers retry with secondary plans.
"""
from typing import Dict, List, Optional, Any
from ..incident import Incident, IncidentStatus
from ..actuator.network_actuator import NetworkActuator


class RollbackManager:
    def __init__(self, actuator: NetworkActuator):
        self.actuator = actuator
        self.rollback_records: List[Dict[str, Any]] = []

    def perform_rollback(
        self,
        incident: Incident,
        action_record: Dict[str, Any],
        failure_reason: str
    ) -> bool:
        """
        Rolls back the executed plan using the captured snapshot,
        updates incident state, and marks the failed candidate plan.
        """
        snapshot = action_record.get("snapshot")
        if not snapshot:
            return False

        # 1. Revert simulation state via actuator
        self.actuator.rollback_snapshot(snapshot)

        # 2. Record rollback event
        incident.status = IncidentStatus.ROLLBACK
        incident.rollback_performed = True
        incident.rollback_reason = failure_reason
        incident.add_timeline_event(
            self.actuator.sim.current_time_ms,
            "ROLLBACK_EXECUTED",
            f"Rolled back plan {incident.selected_plan_id}: {failure_reason}"
        )

        record = {
            "incident_id": incident.id,
            "failed_plan_id": incident.selected_plan_id,
            "failure_reason": failure_reason,
            "timestamp_ms": self.actuator.sim.current_time_ms,
        }
        self.rollback_records.append(record)

        # Mark candidate plan as FAILED in candidate list
        for cand in incident.candidate_plans:
            if cand.get("id") == incident.selected_plan_id:
                cand["status"] = "FAILED"
                cand["failure_reason"] = failure_reason

        return True
