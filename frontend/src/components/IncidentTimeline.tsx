import React from 'react';
import { TimelineEvent, Incident } from '../types/network';
import { Clock, ShieldAlert, Cpu, CheckCircle2, RotateCcw, Activity } from 'lucide-react';

interface IncidentTimelineProps {
  activeIncidents: Record<string, Incident>;
  incidentHistory: Incident[];
}

export const IncidentTimeline: React.FC<IncidentTimelineProps> = ({
  activeIncidents,
  incidentHistory,
}) => {
  // Aggregate all timeline events from active and resolved incidents
  const allEvents: Array<TimelineEvent & { incidentId: string }> = [];

  for (const inc of Object.values(activeIncidents)) {
    for (const ev of inc.timeline) {
      allEvents.push({ ...ev, incidentId: inc.id });
    }
  }

  for (const inc of incidentHistory) {
    for (const ev of inc.timeline) {
      allEvents.push({ ...ev, incidentId: inc.id });
    }
  }

  // Sort descending by time
  allEvents.sort((a, b) => b.time_ms - a.time_ms);

  const getEventIcon = (ev: string) => {
    if (ev.includes('ANOMALY') || ev.includes('WARNING')) return <ShieldAlert size={14} color="#ef4444" />;
    if (ev.includes('ROOT_CAUSE') || ev.includes('DIAGNOSED')) return <Activity size={14} color="#f59e0b" />;
    if (ev.includes('PLAN') || ev.includes('MITIGATION')) return <Cpu size={14} color="#38bdf8" />;
    if (ev.includes('VERIFIED') || ev.includes('RESOLVED')) return <CheckCircle2 size={14} color="#10b981" />;
    if (ev.includes('ROLLBACK') || ev.includes('FAILED')) return <RotateCcw size={14} color="#f87171" />;
    return <Clock size={14} color="#94a3b8" />;
  };

  return (
    <div style={{
      background: '#0d131f',
      border: '1px solid #1e293b',
      borderRadius: '8px',
      padding: '18px',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Clock size={18} color="#38bdf8" />
          <h3 style={{ fontSize: '15px', fontWeight: 800, color: '#f8fafc' }}>
            Closed-Loop Autonomous Incident & Actuation Audit Timeline
          </h3>
        </div>
        <span style={{ fontSize: '11px', color: '#64748b' }}>
          {allEvents.length} Recorded Architectural Events
        </span>
      </div>

      {allEvents.length === 0 ? (
        <p style={{ fontSize: '12px', color: '#64748b', textAlign: 'center', padding: '24px' }}>
          No lifecycle events recorded yet. Inject a failure to observe real-time incident timeline generation.
        </p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '500px', overflowY: 'auto' }}>
          {allEvents.map((item, idx) => (
            <div
              key={idx}
              style={{
                background: '#090d14',
                border: '1px solid #1a2333',
                borderRadius: '6px',
                padding: '10px 14px',
                display: 'flex',
                alignItems: 'flex-start',
                gap: '12px',
                fontSize: '12px',
              }}
            >
              <div style={{ marginTop: '2px' }}>{getEventIcon(item.event)}</div>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{
                      fontWeight: 800,
                      color: '#38bdf8',
                      fontFamily: 'monospace',
                      fontSize: '11px',
                    }}>
                      {item.event}
                    </span>
                    <span style={{ color: '#64748b', fontSize: '10px' }}>({item.incidentId})</span>
                  </div>
                  <span style={{ fontFamily: 'monospace', fontSize: '11px', color: '#64748b' }}>
                    T: {(item.time_ms / 1000).toFixed(2)}s
                  </span>
                </div>
                <p style={{ color: '#cbd5e1', fontSize: '11px', marginTop: '3px' }}>
                  {item.details}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
