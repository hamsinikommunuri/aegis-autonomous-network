import React, { useState } from 'react';
import { BenchmarkReport } from '../types/network';
import { Award, Zap, Shield, ArrowDownRight, CheckCircle2 } from 'lucide-react';

interface BenchmarkArenaProps {
  onRunBenchmark: (scenarioType: string) => BenchmarkReport;
}

export const BenchmarkArena: React.FC<BenchmarkArenaProps> = ({ onRunBenchmark }) => {
  const [scenarioType, setScenarioType] = useState('LINK_FAILURE');
  const [report, setReport] = useState<BenchmarkReport>(() => onRunBenchmark('LINK_FAILURE'));
  const [isRunning, setIsRunning] = useState(false);

  const handleRun = () => {
    setIsRunning(true);
    setTimeout(() => {
      const res = onRunBenchmark(scenarioType);
      setReport(res);
      setIsRunning(false);
    }, 400);
  };

  const { baseline, reactive, predictive } = report.results;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Banner */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(2, 132, 199, 0.15) 0%, rgba(16, 185, 129, 0.1) 100%)',
        border: '1px solid #1e293b',
        borderRadius: '8px',
        padding: '18px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '12px',
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Award size={20} color="#38bdf8" />
            <h2 style={{ fontSize: '16px', fontWeight: 800, color: '#f8fafc' }}>
              AEGIS Quantitative Benchmark Arena
            </h2>
          </div>
          <p style={{ fontSize: '12px', color: '#94a3b8', marginTop: '4px' }}>
            Empirical evaluation comparing Static Conventional Routing vs Reactive Self-Healing vs Predictive AEGIS.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <select
            value={scenarioType}
            onChange={(e) => setScenarioType(e.target.value)}
            style={{
              padding: '6px 12px',
              background: '#090d14',
              color: '#f8fafc',
              border: '1px solid #334155',
              borderRadius: '6px',
              fontSize: '12px',
            }}
          >
            <option value="LINK_FAILURE">Failure Mode: Physical Link Cut</option>
            <option value="CONGESTION">Failure Mode: Progressive Congestion</option>
            <option value="ROUTER_FAILURE">Failure Mode: Core Router Crash</option>
          </select>

          <button
            onClick={handleRun}
            disabled={isRunning}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 16px',
              borderRadius: '6px',
              background: '#0284c7',
              color: '#ffffff',
              border: 'none',
              cursor: isRunning ? 'not-allowed' : 'pointer',
              fontSize: '12px',
              fontWeight: 700,
            }}
          >
            <Zap size={14} fill="#ffffff" />
            {isRunning ? 'Benchmarking...' : 'Execute Benchmark'}
          </button>
        </div>
      </div>

      {/* Summary Highlight Metrics */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '12px' }}>
        <div style={{ background: '#0d131f', border: '1px solid #1e293b', borderRadius: '8px', padding: '16px' }}>
          <span style={{ fontSize: '11px', color: '#64748b', textTransform: 'uppercase', fontWeight: 600 }}>
            Reactive Loss Reduction
          </span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', marginTop: '6px' }}>
            <span style={{ fontSize: '26px', fontWeight: 800, color: '#34d399', fontFamily: 'monospace' }}>
              -{report.summary.loss_reduction_pct}%
            </span>
            <ArrowDownRight size={16} color="#34d399" />
          </div>
          <p style={{ fontSize: '11px', color: '#64748b', marginTop: '4px' }}>
            Packet drop reduced vs static unmanaged routing
          </p>
        </div>

        <div style={{ background: '#0d131f', border: '1px solid #1e293b', borderRadius: '8px', padding: '16px' }}>
          <span style={{ fontSize: '11px', color: '#64748b', textTransform: 'uppercase', fontWeight: 600 }}>
            Predictive Loss Reduction
          </span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', marginTop: '6px' }}>
            <span style={{ fontSize: '26px', fontWeight: 800, color: '#38bdf8', fontFamily: 'monospace' }}>
              -{report.summary.predictive_loss_reduction_pct}%
            </span>
            <ArrowDownRight size={16} color="#38bdf8" />
          </div>
          <p style={{ fontSize: '11px', color: '#64748b', marginTop: '4px' }}>
            Preemptive proactive reroute before saturation
          </p>
        </div>

        <div style={{ background: '#0d131f', border: '1px solid #1e293b', borderRadius: '8px', padding: '16px' }}>
          <span style={{ fontSize: '11px', color: '#64748b', textTransform: 'uppercase', fontWeight: 600 }}>
            Mean Latency Improvement
          </span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', marginTop: '6px' }}>
            <span style={{ fontSize: '26px', fontWeight: 800, color: '#a855f7', fontFamily: 'monospace' }}>
              -{report.summary.latency_improvement_pct}%
            </span>
            <ArrowDownRight size={16} color="#a855f7" />
          </div>
          <p style={{ fontSize: '11px', color: '#64748b', marginTop: '4px' }}>
            Buffer bloat eliminated via QoS path selection
          </p>
        </div>

        <div style={{ background: '#0d131f', border: '1px solid #1e293b', borderRadius: '8px', padding: '16px' }}>
          <span style={{ fontSize: '11px', color: '#64748b', textTransform: 'uppercase', fontWeight: 600 }}>
            Mean Time To Recovery (MTTR)
          </span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', marginTop: '6px' }}>
            <span style={{ fontSize: '26px', fontWeight: 800, color: '#f59e0b', fontFamily: 'monospace' }}>
              {reactive.recovery_time_ms}
            </span>
            <span style={{ fontSize: '14px', color: '#94a3b8' }}>ms</span>
          </div>
          <p style={{ fontSize: '11px', color: '#64748b', marginTop: '4px' }}>
            Autonomous detect-to-mitigate cycle duration
          </p>
        </div>
      </div>

      {/* Head-to-Head Quantitative Comparison Table */}
      <div style={{
        background: '#0d131f',
        border: '1px solid #1e293b',
        borderRadius: '8px',
        padding: '18px',
      }}>
        <h3 style={{ fontSize: '14px', fontWeight: 800, color: '#f8fafc', marginBottom: '14px' }}>
          Head-to-Head Architectural Strategy Metrics
        </h3>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #1e293b', color: '#64748b' }}>
                <th style={{ padding: '10px 8px' }}>Strategy Architecture</th>
                <th style={{ padding: '10px 8px' }}>Packet Loss %</th>
                <th style={{ padding: '10px 8px' }}>Average Latency</th>
                <th style={{ padding: '10px 8px' }}>Throughput</th>
                <th style={{ padding: '10px 8px' }}>SLA Compliance %</th>
                <th style={{ padding: '10px 8px' }}>MTTR</th>
                <th style={{ padding: '10px 8px' }}>Rollbacks</th>
                <th style={{ padding: '10px 8px' }}>Affected Flows</th>
                <th style={{ padding: '10px 8px' }}>Success Rate</th>
                <th style={{ padding: '10px 8px' }}>Accuracy</th>
              </tr>
            </thead>
            <tbody>
              {/* Baseline */}
              <tr style={{ borderBottom: '1px solid #151d2a' }}>
                <td style={{ padding: '12px 8px', fontWeight: 700, color: '#ef4444' }}>
                  1. Baseline (Static Shortest Path)
                </td>
                <td style={{ padding: '12px 8px', color: '#ef4444', fontWeight: 700, fontFamily: 'monospace' }}>
                  {baseline.packet_loss_percent}%
                </td>
                <td style={{ padding: '12px 8px', fontFamily: 'monospace' }}>
                  {baseline.average_latency_ms} ms
                </td>
                <td style={{ padding: '12px 8px', fontFamily: 'monospace' }}>
                  {baseline.total_throughput_mbps} Mbps
                </td>
                <td style={{ padding: '12px 8px', color: '#ef4444', fontWeight: 700, fontFamily: 'monospace' }}>
                  {baseline.sla_availability_percent}%
                </td>
                <td style={{ padding: '12px 8px', color: '#64748b' }}>
                  N/A (Unrecovered)
                </td>
                <td style={{ padding: '12px 8px', fontFamily: 'monospace' }}>0</td>
                <td style={{ padding: '12px 8px', color: '#ef4444', fontFamily: 'monospace' }}>{baseline.affected_flows ?? 3}</td>
                <td style={{ padding: '12px 8px', color: '#64748b' }}>0%</td>
                <td style={{ padding: '12px 8px', color: '#64748b' }}>N/A</td>
              </tr>

              {/* Reactive */}
              <tr style={{ borderBottom: '1px solid #151d2a', background: 'rgba(56, 189, 248, 0.05)' }}>
                <td style={{ padding: '12px 8px', fontWeight: 700, color: '#38bdf8' }}>
                  2. Reactive AEGIS (Closed-Loop)
                </td>
                <td style={{ padding: '12px 8px', color: '#34d399', fontWeight: 700, fontFamily: 'monospace' }}>
                  {reactive.packet_loss_percent}%
                </td>
                <td style={{ padding: '12px 8px', fontFamily: 'monospace' }}>
                  {reactive.average_latency_ms} ms
                </td>
                <td style={{ padding: '12px 8px', fontFamily: 'monospace' }}>
                  {reactive.total_throughput_mbps} Mbps
                </td>
                <td style={{ padding: '12px 8px', color: '#34d399', fontWeight: 700, fontFamily: 'monospace' }}>
                  {reactive.sla_availability_percent}%
                </td>
                <td style={{ padding: '12px 8px', color: '#f59e0b', fontWeight: 700, fontFamily: 'monospace' }}>
                  {reactive.recovery_time_ms} ms
                </td>
                <td style={{ padding: '12px 8px', fontFamily: 'monospace' }}>
                  {reactive.rollbacks_count}
                </td>
                <td style={{ padding: '12px 8px', fontFamily: 'monospace' }}>{reactive.affected_flows ?? 1}</td>
                <td style={{ padding: '12px 8px', color: '#34d399', fontWeight: 700, fontFamily: 'monospace' }}>
                  {Math.round((reactive.recovery_success_rate ?? 1.0) * 100)}%
                </td>
                <td style={{ padding: '12px 8px', fontFamily: 'monospace' }}>
                  {Math.round((reactive.prediction_accuracy ?? 0.85) * 100)}%
                </td>
              </tr>

              {/* Predictive */}
              <tr style={{ borderBottom: '1px solid #151d2a', background: 'rgba(16, 185, 129, 0.05)' }}>
                <td style={{ padding: '12px 8px', fontWeight: 700, color: '#10b981' }}>
                  3. Predictive AEGIS (Trend Forecasting)
                </td>
                <td style={{ padding: '12px 8px', color: '#10b981', fontWeight: 800, fontFamily: 'monospace' }}>
                  {predictive.packet_loss_percent}%
                </td>
                <td style={{ padding: '12px 8px', fontFamily: 'monospace' }}>
                  {predictive.average_latency_ms} ms
                </td>
                <td style={{ padding: '12px 8px', fontFamily: 'monospace' }}>
                  {predictive.total_throughput_mbps} Mbps
                </td>
                <td style={{ padding: '12px 8px', color: '#10b981', fontWeight: 800, fontFamily: 'monospace' }}>
                  {predictive.sla_availability_percent}%
                </td>
                <td style={{ padding: '12px 8px', color: '#10b981', fontWeight: 700, fontFamily: 'monospace' }}>
                  {predictive.recovery_time_ms} ms (Preemptive)
                </td>
                <td style={{ padding: '12px 8px', fontFamily: 'monospace' }}>
                  {predictive.rollbacks_count}
                </td>
                <td style={{ padding: '12px 8px', fontFamily: 'monospace' }}>{predictive.affected_flows ?? 0}</td>
                <td style={{ padding: '12px 8px', color: '#10b981', fontWeight: 700, fontFamily: 'monospace' }}>
                  {Math.round((predictive.recovery_success_rate ?? 1.0) * 100)}%
                </td>
                <td style={{ padding: '12px 8px', color: '#10b981', fontWeight: 700, fontFamily: 'monospace' }}>
                  {Math.round((predictive.prediction_accuracy ?? 0.96) * 100)}%
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
