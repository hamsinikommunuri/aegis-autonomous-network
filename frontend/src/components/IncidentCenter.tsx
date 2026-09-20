import React from 'react';
import { Incident, IncidentStatus } from '../types/network';
import { 
  AlertTriangle, 
  CheckCircle, 
  RotateCcw, 
  ArrowRight, 
  ShieldAlert, 
  HelpCircle,
  Clock,
  Activity
} from 'lucide-react';

interface IncidentCenterProps {
  activeIncidents: Record<string, Incident>;
  incidentHistory: Incident[];
  onSelectIncident?: (incident: Incident) => void;
}

export const IncidentCenter: React.FC<IncidentCenterProps> = ({
  activeIncidents,
  incidentHistory,
}) => {
  const activeList = Object.values(activeIncidents);

  const stages: IncidentStatus[] = [
    'DETECTED',
    'DIAGNOSED',
    'PLANNING',
    'MITIGATING',
    'VERIFYING',
    'RESOLVED',
  ];

  const getStageIndex = (status: IncidentStatus): number => {
    if (status === 'ROLLBACK') return 4; // Between verify and adapt
    const idx = stages.indexOf(status);
    return idx >= 0 ? idx : 0;
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Active Incidents Overview */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ShieldAlert size={18} color="#ef4444" />
            <h2 style={{ fontSize: '16px', fontWeight: 800, color: '#f8fafc' }}>
              Active Incidents & Autonomous Response ({activeList.length})
            </h2>
          </div>
          {activeList.length === 0 && (
            <span style={{ fontSize: '12px', color: '#34d399', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <CheckCircle size={14} /> Nominal Operation — No active disruptions
            </span>
          )}
        </div>

        {activeList.length === 0 ? (
          <div style={{
            background: '#0d131f',
            border: '1px dashed #1e293b',
            borderRadius: '8px',
            padding: '36px',
            textAlign: 'center',
            color: '#64748b',
          }}>
            <p style={{ fontSize: '14px', fontWeight: 600, color: '#94a3b8' }}>
              Network telemetry is within nominal baseline bounds.
            </p>
            <p style={{ fontSize: '12px', marginTop: '4px' }}>
              To test self-healing, inject a fault or run a scenario from the <strong>Experiment Lab</strong> tab.
            </p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {activeList.map((inc) => {
              const currentStageIdx = getStageIndex(inc.status);
              const isRollback = inc.status === 'ROLLBACK' || inc.rollback_performed;

              return (
                <div
                  key={inc.id}
                  style={{
                    background: '#0d131f',
                    border: '1px solid #1e293b',
                    borderRadius: '8px',
                    padding: '20px',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                  }}
                >
                  {/* Header */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '10px' }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{
                          background: inc.severity === 'CRITICAL' ? '#ef4444' : inc.severity === 'HIGH' ? '#f97316' : '#eab308',
                          color: '#ffffff',
                          fontWeight: 800,
                          fontSize: '11px',
                          padding: '2px 8px',
                          borderRadius: '4px',
                          fontFamily: 'monospace',
                        }}>
                          {inc.severity}
                        </span>
                        <h3 style={{ fontSize: '15px', fontWeight: 800, color: '#f8fafc' }}>
                          Incident #{inc.id} — {inc.incident_type}
                        </h3>
                        <span style={{ fontSize: '12px', color: '#64748b', fontFamily: 'monospace' }}>
                          Resource: <strong style={{ color: '#38bdf8' }}>{inc.affected_resource}</strong>
                        </span>
                      </div>
                      <p style={{ fontSize: '11px', color: '#64748b', marginTop: '4px' }}>
                        Detected at T: {(inc.detected_time_ms / 1000).toFixed(1)}s | Anomaly Score: {inc.anomaly_score.toFixed(2)}
                      </p>
                    </div>

                    {isRollback && (
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        background: 'rgba(239, 68, 68, 0.15)',
                        border: '1px solid #ef4444',
                        padding: '4px 10px',
                        borderRadius: '6px',
                        color: '#f87171',
                        fontSize: '11px',
                        fontWeight: 700,
                      }}>
                        <RotateCcw size={14} />
                        ROLLBACK EXECUTED: ADAPTING STRATEGY
                      </div>
                    )}
                  </div>

                  {/* Visual Autonomous Self-Healing Lifecycle Progress Bar */}
                  <div style={{ margin: '20px 0 16px 0' }}>
                    <div style={{ fontSize: '11px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', marginBottom: '8px' }}>
                      Closed-Loop Self-Healing Lifecycle
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', overflowX: 'auto' }}>
                      {stages.map((stage, idx) => {
                        const isDone = idx < currentStageIdx;
                        const isCurrent = idx === currentStageIdx;
                        let pillBg = '#131d2e';
                        let pillText = '#475569';
                        let pillBorder = '#1e293b';

                        if (isDone) {
                          pillBg = 'rgba(16, 185, 129, 0.15)';
                          pillText = '#34d399';
                          pillBorder = 'rgba(16, 185, 129, 0.4)';
                        } else if (isCurrent) {
                          pillBg = 'rgba(6, 182, 212, 0.2)';
                          pillText = '#38bdf8';
                          pillBorder = '#06b6d4';
                        }

                        return (
                          <React.Fragment key={stage}>
                            <div style={{
                              padding: '6px 12px',
                              borderRadius: '6px',
                              fontSize: '11px',
                              fontWeight: 700,
                              fontFamily: 'monospace',
                              background: pillBg,
                              color: pillText,
                              border: `1px solid ${pillBorder}`,
                              whiteSpace: 'nowrap',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '6px',
                            }}>
                              {isDone ? <CheckCircle size={12} /> : <span>{idx + 1}.</span>}
                              {stage}
                            </div>
                            {idx < stages.length - 1 && (
                              <ArrowRight size={14} color="#334155" style={{ flexShrink: 0 }} />
                            )}
                          </React.Fragment>
                        );
                      })}
                    </div>
                  </div>

                  {/* Root-Cause Diagnosis Card */}
                  <div style={{
                    background: '#090d14',
                    border: '1px solid #1a2333',
                    borderRadius: '6px',
                    padding: '14px',
                    marginTop: '12px',
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                      <span style={{ fontSize: '12px', fontWeight: 700, color: '#38bdf8' }}>
                        Root-Cause Analysis (RCA Engine)
                      </span>
                      <span style={{
                        fontSize: '11px',
                        fontFamily: 'monospace',
                        color: '#34d399',
                        background: 'rgba(16, 185, 129, 0.1)',
                        padding: '2px 8px',
                        borderRadius: '4px',
                      }}>
                        Confidence: {Math.round(inc.diagnosis_confidence * 100)}%
                      </span>
                    </div>
                    <p style={{ fontSize: '13px', fontWeight: 600, color: '#f1f5f9' }}>
                      {inc.diagnosis || 'Investigating probable causes...'}
                    </p>
                    <p style={{ fontSize: '11px', color: '#94a3b8', marginTop: '4px' }}>
                      {inc.diagnosis_explanation}
                    </p>

                    {/* Evidence List */}
                    {inc.evidence && Object.keys(inc.evidence).length > 0 && (
                      <div style={{ marginTop: '10px', display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                        {Object.entries(inc.evidence).map(([k, v]) => (
                          <div key={k} style={{
                            background: '#131b28',
                            border: '1px solid #1e293b',
                            padding: '3px 8px',
                            borderRadius: '4px',
                            fontSize: '10px',
                            fontFamily: 'monospace',
                            color: '#e2e8f0',
                          }}>
                            <span style={{ color: '#64748b' }}>{k}:</span> {String(v)}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Historical Resolved Incidents Memory */}
      <div style={{
        background: '#0d131f',
        border: '1px solid #1e293b',
        borderRadius: '8px',
        padding: '16px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Clock size={16} color="#38bdf8" />
            <h3 style={{ fontSize: '14px', fontWeight: 700, color: '#f8fafc' }}>
              Incident Memory & Resolved Disruption Log ({incidentHistory.length})
            </h3>
          </div>
        </div>

        {incidentHistory.length === 0 ? (
          <p style={{ fontSize: '12px', color: '#64748b' }}>No resolved incidents in persistent store yet.</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {incidentHistory.map((inc) => (
              <div
                key={inc.id}
                style={{
                  background: '#090d14',
                  border: '1px solid #151d2a',
                  borderRadius: '6px',
                  padding: '10px 14px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  fontSize: '12px',
                }}
              >
                <div>
                  <span style={{ fontWeight: 700, color: '#38bdf8', fontFamily: 'monospace' }}>#{inc.id}</span>
                  <span style={{ color: '#64748b', margin: '0 8px' }}>|</span>
                  <span style={{ color: '#f1f5f9', fontWeight: 600 }}>{inc.diagnosis || inc.incident_type}</span>
                  <span style={{ color: '#64748b', margin: '0 8px' }}>|</span>
                  <span style={{ color: '#94a3b8' }}>Resource: {inc.affected_resource}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{
                    padding: '2px 8px',
                    borderRadius: '4px',
                    fontSize: '10px',
                    fontWeight: 700,
                    background: 'rgba(16, 185, 129, 0.15)',
                    color: '#34d399',
                  }}>
                    RESOLVED ({((inc.resolved_time_ms! - inc.detected_time_ms) / 1000).toFixed(1)}s)
                  </span>
                  {inc.rollback_performed && (
                    <span style={{
                      padding: '2px 6px',
                      borderRadius: '4px',
                      fontSize: '10px',
                      fontWeight: 700,
                      background: 'rgba(239, 68, 68, 0.15)',
                      color: '#f87171',
                    }}>
                      ROLLED BACK
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
