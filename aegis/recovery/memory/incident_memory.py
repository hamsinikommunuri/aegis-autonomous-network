"""
AEGIS Incident Memory and Knowledge Base
Maintains persistent records of resolved and rolled back incidents to evaluate strategy efficacy
and support historical inspection.
"""
from typing import Dict, List, Optional, Any
from ..incident import Incident


class IncidentMemory:
    def __init__(self):
        self.history: List[Dict[str, Any]] = []

    def record_resolved_incident(self, incident: Incident) -> None:
        record = incident.to_dict()
        self.history.append(record)

    def get_all_incidents(self) -> List[Dict[str, Any]]:
        return list(self.history)

    def get_incident_by_id(self, incident_id: str) -> Optional[Dict[str, Any]]:
        for inc in self.history:
            if inc["id"] == incident_id:
                return inc
        return None

    def get_efficacy_stats(self) -> Dict[str, Any]:
        """Calculates recovery success rate, rollback rate, and mean recovery time."""
        total = len(self.history)
        if total == 0:
            return {
                "total_incidents": 0,
                "recovery_success_rate": 1.0,
                "rollback_rate": 0.0,
                "mean_recovery_time_ms": 0.0,
            }

        successful = sum(1 for inc in self.history if inc.get("verification_success") is True)
        rollbacks = sum(1 for inc in self.history if inc.get("rollback_performed") is True)
        
        recovery_durations = [
            (inc["resolved_time_ms"] - inc["detected_time_ms"])
            for inc in self.history
            if inc.get("resolved_time_ms") and inc.get("detected_time_ms")
        ]
        mean_time = (sum(recovery_durations) / len(recovery_durations)) if recovery_durations else 0.0

        return {
            "total_incidents": total,
            "successful_recoveries": successful,
            "recovery_success_rate": round(successful / total, 4),
            "rollbacks_count": rollbacks,
            "rollback_rate": round(rollbacks / total, 4),
            "mean_recovery_time_ms": round(mean_time, 2),
        }
