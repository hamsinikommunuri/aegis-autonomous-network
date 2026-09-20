import React from 'react';
import { Incident, CandidatePlan } from '../types/network';
import { Compass, CheckCircle2, ShieldCheck, AlertCircle, Award } from 'lucide-react';

interface RecoveryPlannerPanelProps {
  activeIncidents: Record<string, Incident>;
}

export const RecoveryPlannerPanel: React.FC<RecoveryPlannerPanelProps> = ({ activeIncidents }) => {
  const activeList = Object.values(activeIncidents);
  const selectedIncident = activeList[0]; // Primary active incident

  if (!selectedIncident || !selectedIncident.candidate_plans || selectedIncident.candidate_plans.length === 0) {
    return (
      <div style={{
        background: '#0d131f',
        border: '1px solid #1e293b',
        borderRadius: '8px',
        padding: '32px',
        textAlign: 'center',
        color: '#64748b',
      }}>
        <Compass size={32} color="#334155" style={{ margin: '0 auto 12px auto' }} />
        <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#94a3b8' }}>
          Recovery Planning Center Standby
        </h3>
        <p style={{ fontSize: '12px', marginTop: '6px' }}>
          When an anomaly or failure is diagnosed, AEGIS generates and evaluates multiple candidate recovery strategies.
        </p>
      </div>
    );
  }

  const plans = selectedIncident.candidate_plans;
  const chosenPlan = plans.find((p) => p.id === selectedIncident.selected_plan_id) || plans[0];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* "Why did AEGIS choose this plan?" Explanatory Banner */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(2, 132, 199, 0.15) 0%, rgba(6, 182, 212, 0.1) 100%)',
        border: '1px solid rgba(6, 182, 212, 0.3)',
        borderRadius: '8px',
        padding: '16px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
          <Award size={18} color="#38bdf8" />
          <h3 style={{ fontSize: '14px', fontWeight: 800, color: '#f8fafc' }}>
            Autonomous Strategy Selection: Why AEGIS Selected {chosenPlan.id}
          </h3>
        </div>
        <p style={{ fontSize: '12px', color: '#e2e8f0', lineHeight: '1.6' }}>
          {chosenPlan.explanation}
        </p>
        <div style={{ display: 'flex', gap: '16px', marginTop: '12px', flexWrap: 'wrap', fontSize: '11px' }}>
          <span style={{ color: '#38bdf8' }}>
            Overall Score: <strong>{chosenPlan.score} / 100</strong>
          </span>
          <span style={{ color: '#34d399' }}>
            Predicted Loss Reduction: <strong>{chosenPlan.predicted_loss_reduction_pct}%</strong>
          </span>
          <span style={{ color: '#f59e0b' }}>
            Risk Score: <strong>{chosenPlan.risk_score} / 100</strong>
          </span>
          <span style={{ color: chosenPlan.qos_priority_preserved ? '#34d399' : '#f87171' }}>
            QoS Preservation: <strong>{chosenPlan.qos_priority_preserved ? 'VERIFIED (Critical traffic protected)' : 'RE-ROUTED'}</strong>
          </span>
        </div>
      </div>

      {/* Candidate Recovery Plans Comparison Table */}
      <div style={{
        background: '#0d131f',
        border: '1px solid #1e293b',
        borderRadius: '8px',
        padding: '16px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
          <h3 style={{ fontSize: '14px', fontWeight: 700, color: '#f8fafc' }}>
            Evaluated Candidate Recovery Strategies ({plans.length})
          </h3>
          <span style={{ fontSize: '11px', color: '#64748b' }}>
            Scored by Multi-Objective Loss, Latency, Risk & QoS Policy
          </span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #1e293b', color: '#64748b' }}>
                <th style={{ padding: '8px' }}>Candidate</th>
                <th style={{ padding: '8px' }}>Strategy Description</th>
                <th style={{ padding: '8px' }}>Pred. Loss Δ</th>
                <th style={{ padding: '8px' }}>Pred. Latency Δ</th>
                <th style={{ padding: '8px' }}>Risk Index</th>
                <th style={{ padding: '8px' }}>QoS Safety</th>
                <th style={{ padding: '8px' }}>Score</th>
                <th style={{ padding: '8px' }}>Decision</th>
              </tr>
            </thead>
            <tbody>
              {plans.map((plan) => {
                const isSelected = plan.id === selectedIncident.selected_plan_id;
                const isFailed = plan.status === 'FAILED';

                return (
                  <tr
                    key={plan.id}
                    style={{
                      borderBottom: '1px solid #151d2a',
                      background: isSelected ? 'rgba(6, 182, 212, 0.08)' : 'transparent',
                    }}
                  >
                    <td style={{ padding: '10px 8px', fontWeight: 700, color: '#38bdf8', fontFamily: 'monospace' }}>
                      {plan.id}
                    </td>
                    <td style={{ padding: '10px 8px' }}>
                      <div style={{ fontWeight: 600, color: '#f1f5f9' }}>{plan.title}</div>
                      <div style={{ fontSize: '11px', color: '#64748b', marginTop: '2px' }}>{plan.description}</div>
                    </td>
                    <td style={{ padding: '10px 8px', color: '#34d399', fontWeight: 600 }}>
                      -{plan.predicted_loss_reduction_pct}%
                    </td>
                    <td style={{ padding: '10px 8px', color: plan.predicted_latency_impact_pct < 0 ? '#34d399' : '#f59e0b' }}>
                      {plan.predicted_latency_impact_pct > 0 ? `+${plan.predicted_latency_impact_pct}%` : `${plan.predicted_latency_impact_pct}%`}
                    </td>
                    <td style={{ padding: '10px 8px' }}>
                      <span style={{
                        padding: '2px 6px',
                        borderRadius: '4px',
                        fontSize: '10px',
                        fontWeight: 700,
                        background: plan.risk_score < 25 ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                        color: plan.risk_score < 25 ? '#34d399' : '#f59e0b',
                      }}>
                        {plan.risk_score}/100
                      </span>
                    </td>
                    <td style={{ padding: '10px 8px' }}>
                      <span style={{
                        color: plan.qos_priority_preserved ? '#34d399' : '#94a3b8',
                        fontSize: '11px',
                        fontWeight: 600,
                      }}>
                        {plan.qos_priority_preserved ? 'Protected' : 'Standard'}
                      </span>
                    </td>
                    <td style={{ padding: '10px 8px', fontWeight: 800, color: '#f8fafc', fontFamily: 'monospace' }}>
                      {plan.score}
                    </td>
                    <td style={{ padding: '10px 8px' }}>
                      {isSelected ? (
                        <span style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '4px',
                          padding: '3px 8px',
                          borderRadius: '4px',
                          fontSize: '11px',
                          fontWeight: 800,
                          background: '#0284c7',
                          color: '#ffffff',
                        }}>
                          <CheckCircle2 size={12} /> SELECTED
                        </span>
                      ) : isFailed ? (
                        <span style={{
                          padding: '3px 8px',
                          borderRadius: '4px',
                          fontSize: '10px',
                          fontWeight: 700,
                          background: 'rgba(239, 68, 68, 0.2)',
                          color: '#f87171',
                        }}>
                          FAILED / ROLLED BACK
                        </span>
                      ) : (
                        <span style={{ color: '#64748b', fontSize: '11px' }}>Alternative</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
