import React from 'react';
import { NetworkGlobalSnapshot, TrafficFlow } from '../types/network';
import { Activity, Zap, CheckCircle2, AlertOctagon, Layers } from 'lucide-react';

interface LiveTelemetryPanelProps {
  snapshot: NetworkGlobalSnapshot | null;
  history: {
    timestamps: number[];
    throughput: number[];
    latency: number[];
    loss: number[];
    sla: number[];
  };
}

export const LiveTelemetryPanel: React.FC<LiveTelemetryPanelProps> = ({ snapshot, history }) => {
  if (!snapshot) return null;

  // Mini Sparkline SVG generator
  const renderSparkline = (data: number[], color: string, height: number = 36) => {
    if (!data || data.length < 2) return null;
    const min = Math.min(...data);
    const max = Math.max(...data, min + 0.001);
    const width = 160;

    const points = data
      .map((val, idx) => {
        const x = (idx / (data.length - 1)) * width;
        const y = height - ((val - min) / (max - min)) * (height - 6) - 3;
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(' ');

    return (
      <svg width={width} height={height} style={{ overflow: 'visible' }}>
        <polyline fill="none" stroke={color} strokeWidth="2" points={points} />
      </svg>
    );
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Top Metric Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
        {/* Throughput Card */}
        <div style={{
          background: '#0d131f',
          border: '1px solid #1e293b',
          borderRadius: '8px',
          padding: '14px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '11px', color: '#64748b', fontWeight: 600, textTransform: 'uppercase' }}>
              Global Throughput
            </span>
            <Activity size={16} color="#06b6d4" />
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', margin: '8px 0' }}>
            <span style={{ fontSize: '24px', fontWeight: 800, color: '#f8fafc', fontFamily: 'monospace' }}>
              {snapshot.total_throughput_mbps.toFixed(1)}
            </span>
            <span style={{ fontSize: '12px', color: '#94a3b8' }}>Mbps</span>
          </div>
          <div>{renderSparkline(history.throughput, '#06b6d4')}</div>
        </div>

        {/* Latency Card */}
        <div style={{
          background: '#0d131f',
          border: '1px solid #1e293b',
          borderRadius: '8px',
          padding: '14px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '11px', color: '#64748b', fontWeight: 600, textTransform: 'uppercase' }}>
              Average Latency
            </span>
            <Zap size={16} color="#3b82f6" />
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', margin: '8px 0' }}>
            <span style={{ fontSize: '24px', fontWeight: 800, color: '#f8fafc', fontFamily: 'monospace' }}>
              {snapshot.average_latency_ms.toFixed(1)}
            </span>
            <span style={{ fontSize: '12px', color: '#94a3b8' }}>ms</span>
          </div>
          <div>{renderSparkline(history.latency, '#3b82f6')}</div>
        </div>

        {/* Loss Rate Card */}
        <div style={{
          background: '#0d131f',
          border: '1px solid #1e293b',
          borderRadius: '8px',
          padding: '14px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '11px', color: '#64748b', fontWeight: 600, textTransform: 'uppercase' }}>
              Packet Loss Rate
            </span>
            <AlertOctagon size={16} color={snapshot.global_packet_loss_rate > 0.02 ? '#ef4444' : '#10b981'} />
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', margin: '8px 0' }}>
            <span style={{
              fontSize: '24px',
              fontWeight: 800,
              color: snapshot.global_packet_loss_rate > 0.02 ? '#f87171' : '#f8fafc',
              fontFamily: 'monospace'
            }}>
              {(snapshot.global_packet_loss_rate * 100).toFixed(2)}%
            </span>
            <span style={{ fontSize: '12px', color: '#94a3b8' }}>drop</span>
          </div>
          <div>{renderSparkline(history.loss, '#ef4444')}</div>
        </div>

        {/* SLA Compliance Card */}
        <div style={{
          background: '#0d131f',
          border: '1px solid #1e293b',
          borderRadius: '8px',
          padding: '14px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '11px', color: '#64748b', fontWeight: 600, textTransform: 'uppercase' }}>
              SLA Availability
            </span>
            <CheckCircle2 size={16} color="#10b981" />
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', margin: '8px 0' }}>
            <span style={{ fontSize: '24px', fontWeight: 800, color: '#34d399', fontFamily: 'monospace' }}>
              {(snapshot.sla_compliance_rate * 100).toFixed(1)}%
            </span>
            <span style={{ fontSize: '12px', color: '#94a3b8' }}>compliant</span>
          </div>
          <div>{renderSparkline(history.sla, '#10b981')}</div>
        </div>
      </div>

      {/* Active Traffic Flows Table */}
      <div style={{
        background: '#0d131f',
        border: '1px solid #1e293b',
        borderRadius: '8px',
        padding: '16px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Layers size={16} color="#38bdf8" />
            <h3 style={{ fontSize: '14px', fontWeight: 700, color: '#f8fafc' }}>
              Active Multi-Class QoS Traffic Flows
            </h3>
          </div>
          <span style={{ fontSize: '11px', color: '#64748b' }}>
            {Object.keys(snapshot.flows).length} End-to-End Flows Monitored
          </span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #1e293b', color: '#64748b' }}>
                <th style={{ padding: '8px' }}>Flow Name</th>
                <th style={{ padding: '8px' }}>QoS Class</th>
                <th style={{ padding: '8px' }}>Priority</th>
                <th style={{ padding: '8px' }}>Demand</th>
                <th style={{ padding: '8px' }}>Latency</th>
                <th style={{ padding: '8px' }}>Loss %</th>
                <th style={{ padding: '8px' }}>SLA Target</th>
                <th style={{ padding: '8px' }}>Active Forwarding Path</th>
                <th style={{ padding: '8px' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {Object.values(snapshot.flows).map((flow) => {
                let badgeBg = '#1e293b';
                let badgeColor = '#94a3b8';
                if (flow.traffic_class === 'CRITICAL') {
                  badgeBg = 'rgba(168, 85, 247, 0.2)';
                  badgeColor = '#c084fc';
                } else if (flow.traffic_class === 'REAL_TIME') {
                  badgeBg = 'rgba(6, 182, 212, 0.2)';
                  badgeColor = '#38bdf8';
                } else if (flow.traffic_class === 'NORMAL') {
                  badgeBg = 'rgba(59, 130, 246, 0.2)';
                  badgeColor = '#60a5fa';
                }

                return (
                  <tr key={flow.id} style={{ borderBottom: '1px solid #151d2a' }}>
                    <td style={{ padding: '8px', fontWeight: 600, color: '#f1f5f9' }}>{flow.name}</td>
                    <td style={{ padding: '8px' }}>
                      <span style={{
                        padding: '2px 8px',
                        borderRadius: '4px',
                        background: badgeBg,
                        color: badgeColor,
                        fontWeight: 700,
                        fontSize: '10px',
                      }}>
                        {flow.traffic_class}
                      </span>
                    </td>
                    <td style={{ padding: '8px', fontFamily: 'monospace', color: '#94a3b8' }}>
                      P-{flow.priority}
                    </td>
                    <td style={{ padding: '8px', fontFamily: 'monospace' }}>
                      {(flow.demand_bps / 1e6).toFixed(0)} Mbps
                    </td>
                    <td style={{ padding: '8px', fontFamily: 'monospace', color: flow.average_latency_ms > flow.latency_sla_ms ? '#ef4444' : '#f1f5f9' }}>
                      {flow.average_latency_ms.toFixed(1)} ms
                    </td>
                    <td style={{ padding: '8px', fontFamily: 'monospace', color: flow.loss_rate_percent > flow.loss_sla_percent ? '#ef4444' : '#10b981' }}>
                      {flow.loss_rate_percent.toFixed(2)}%
                    </td>
                    <td style={{ padding: '8px', color: '#64748b', fontSize: '11px' }}>
                      &lt;{flow.latency_sla_ms}ms / &lt;{flow.loss_sla_percent}%
                    </td>
                    <td style={{ padding: '8px', fontFamily: 'monospace', fontSize: '11px', color: '#38bdf8' }}>
                      {flow.current_path.join(' → ')}
                    </td>
                    <td style={{ padding: '8px' }}>
                      <span style={{
                        padding: '2px 6px',
                        borderRadius: '4px',
                        fontSize: '10px',
                        fontWeight: 700,
                        background: flow.sla_violated ? 'rgba(239, 68, 68, 0.2)' : 'rgba(16, 185, 129, 0.2)',
                        color: flow.sla_violated ? '#f87171' : '#34d399',
                      }}>
                        {flow.sla_violated ? 'SLA VIOLATED' : 'OK'}
                      </span>
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
