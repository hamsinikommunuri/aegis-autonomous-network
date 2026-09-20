"""
AEGIS Incident Model and Lifecycle
Represents detected network incidents, anomaly evidence, diagnosis, mitigation state,
and verification outcomes.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import time


class IncidentSeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IncidentStatus(str, Enum):
    DETECTED = "DETECTED"
    INVESTIGATING = "INVESTIGATING"
    DIAGNOSED = "DIAGNOSED"
    PLANNING = "PLANNING"
    MITIGATING = "MITIGATING"
    VERIFYING = "VERIFYING"
    RESOLVED = "RESOLVED"
    ROLLBACK = "ROLLBACK"
    CLOSED = "CLOSED"


@dataclass
class Incident:
    id: str
    incident_type: str            # LINK_CONGESTION, LINK_FAILURE, ROUTER_FAILURE, PREDICTED_DEGRADATION
    affected_resource: str        # e.g., "DR1-CR1" or "CR1"
    severity: IncidentSeverity
    detected_time_ms: float
    status: IncidentStatus = IncidentStatus.DETECTED

    # Telemetry and anomaly evidence
    evidence: Dict[str, Any] = field(default_factory=dict)
    anomaly_score: float = 0.0

    # RCA findings
    diagnosis: Optional[str] = None
    diagnosis_confidence: float = 0.0
    diagnosis_explanation: Optional[str] = None

    # Prediction findings
    is_predictive: bool = False
    predicted_time_to_breach_ms: Optional[float] = None
    predicted_consequence: Optional[str] = None

    # Recovery tracking
    candidate_plans: List[Dict[str, Any]] = field(default_factory=list)
    selected_plan_id: Optional[str] = None
    applied_action: Optional[Dict[str, Any]] = None
    action_applied_time_ms: Optional[float] = None

    # Verification and rollback
    pre_recovery_metrics: Dict[str, float] = field(default_factory=dict)
    post_recovery_metrics: Dict[str, float] = field(default_factory=dict)
    verification_success: Optional[bool] = None
    verification_reason: Optional[str] = None
    rollback_performed: bool = False
    rollback_reason: Optional[str] = None
    resolved_time_ms: Optional[float] = None

    # Timeline event audit log
    timeline: List[Dict[str, Any]] = field(default_factory=list)

    def add_timeline_event(self, time_ms: float, event: str, details: Optional[str] = None) -> None:
        self.timeline.append({
            "time_ms": round(time_ms, 2),
            "event": event,
            "details": details or "",
        })

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "incident_type": self.incident_type,
            "affected_resource": self.affected_resource,
            "severity": self.severity.value,
            "detected_time_ms": round(self.detected_time_ms, 2),
            "status": self.status.value,
            "evidence": dict(self.evidence),
            "anomaly_score": round(self.anomaly_score, 3),
            "diagnosis": self.diagnosis,
            "diagnosis_confidence": round(self.diagnosis_confidence, 2),
            "diagnosis_explanation": self.diagnosis_explanation,
            "is_predictive": self.is_predictive,
            "predicted_time_to_breach_ms": round(self.predicted_time_to_breach_ms, 1) if self.predicted_time_to_breach_ms is not None else None,
            "predicted_consequence": self.predicted_consequence,
            "candidate_plans": list(self.candidate_plans),
            "selected_plan_id": self.selected_plan_id,
            "applied_action": self.applied_action,
            "action_applied_time_ms": round(self.action_applied_time_ms, 2) if self.action_applied_time_ms is not None else None,
            "verification_success": self.verification_success,
            "verification_reason": self.verification_reason,
            "rollback_performed": self.rollback_performed,
            "rollback_reason": self.rollback_reason,
            "resolved_time_ms": round(self.resolved_time_ms, 2) if self.resolved_time_ms is not None else None,
            "timeline": list(self.timeline),
        }
