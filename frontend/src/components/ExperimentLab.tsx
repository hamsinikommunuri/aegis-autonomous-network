import React, { useState } from 'react';
import { 
  Flame, 
  Play, 
  RotateCcw, 
  Sliders, 
  Scissors, 
  PowerOff, 
  Activity, 
  WifiOff, 
  TrendingUp, 
  ShieldAlert 
} from 'lucide-react';

interface ExperimentLabProps {
  onInjectLinkFailure: (linkId: string) => void;
  onInjectNodeFailure: (nodeId: string) => void;
  onInjectPacketLoss: (linkId: string, lossRate: number) => void;
  onInjectLatencySpike: (linkId: string, extraMs: number) => void;
  onInjectBandwidthReduction: (linkId: string, newBwBps: number) => void;
  onInjectTrafficSurge: (flowId: string, multiplier: number) => void;
  onInjectQueueSaturation?: (linkId: string, queueCapacity: number) => void;
  onInjectPacketCorruption?: (linkId: string, corruptionRate: number) => void;
  onRunScenario: (scenarioId: string) => void;
  onResetFailures: () => void;
  linkIds: string[];
  nodeIds: string[];
  flowIds: string[];
}

export const ExperimentLab: React.FC<ExperimentLabProps> = ({
  onInjectLinkFailure,
  onInjectNodeFailure,
  onInjectPacketLoss,
  onInjectLatencySpike,
  onInjectBandwidthReduction,
  onInjectTrafficSurge,
  onInjectQueueSaturation,
  onInjectPacketCorruption,
  onRunScenario,
  onResetFailures,
  linkIds,
  nodeIds,
  flowIds,
}) => {
  const [selectedLink, setSelectedLink] = useState(linkIds[0] || 'DR1-CR1');
  const [selectedNode, setSelectedNode] = useState('CR1');
  const [selectedFlow, setSelectedFlow] = useState(flowIds[0] || 'f-web-1');
  const [lossRate, setLossRate] = useState(15);
  const [latencySpike, setLatencySpike] = useState(80);
  const [chokeBwMbps, setChokeBwMbps] = useState(25);
  const [surgeMult, setSurgeMult] = useState(4);
  const [queueCapacity, setQueueCapacity] = useState(5);
  const [corruptionRate, setCorruptionRate] = useState(20);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const notify = (msg: string) => {
    setStatusMessage(msg);
    setTimeout(() => setStatusMessage(null), 4000);
  };

  const scenarios = [
    {
      id: 'SCENARIO_A',
      title: 'Scenario A — Progressive Link Congestion',
      desc: 'Chokes backbone link DR1-CR1 to 25 Mbps, steadily driving utilization above 90% and triggering predictive QoS rerouting.',
      tag: 'Congestion & Prediction',
    },
    {
      id: 'SCENARIO_B',
      title: 'Scenario B — Sudden Core Router Crash',
      desc: 'Powers off Core Router CR1 abruptly. Primary transit is severed, forcing instant autonomous topology reconvergence.',
      tag: 'Hardware Fault',
    },
    {
      id: 'SCENARIO_C',
      title: 'Scenario C — Optical Fiber Degradation (BER)',
      desc: 'Simulates dirty optical fiber with 15% packet loss and 60ms latency spike without queue saturation, validating RCA accuracy.',
      tag: 'Physical Layer Degradation',
    },
    {
      id: 'SCENARIO_D',
      title: 'Scenario D — Flash Crowd Traffic Surge',
      desc: 'Surges application workload by 400%, testing queue preemption, ingress traffic shaping, and dynamic load-balancing.',
      tag: 'Traffic Spike',
    },
    {
      id: 'SCENARIO_E',
      title: 'Scenario E — Cascading Multi-Link Failure',
      desc: 'Cuts primary link and chokes secondary link DR1-CR2, forcing AEGIS to route around the entire northern corridor.',
      tag: 'Cascading Fault',
    },
    {
      id: 'SCENARIO_F',
      title: 'Scenario F — Recovery Failure & Autonomous Rollback',
      desc: 'Initial reroute overburdens alternate path AS1-DR2, failing verification and proving autonomous rollback and Plan B retry.',
      tag: 'Rollback & Adaptation',
    },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Toast message */}
      {statusMessage && (
        <div style={{
          background: 'rgba(6, 182, 212, 0.2)',
          border: '1px solid #06b6d4',
          borderRadius: '6px',
          padding: '10px 16px',
          color: '#38bdf8',
          fontSize: '12px',
          fontWeight: 600,
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
        }}>
          <Activity size={16} />
          {statusMessage}
        </div>
      )}

      {/* Section 1: Pre-defined Realistic Scenarios */}
      <div style={{
        background: '#0d131f',
        border: '1px solid #1e293b',
        borderRadius: '8px',
        padding: '18px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
          <div>
            <h3 style={{ fontSize: '15px', fontWeight: 800, color: '#f8fafc' }}>
              One-Click Realistic Failure Scenarios
            </h3>
            <p style={{ fontSize: '12px', color: '#64748b', marginTop: '2px' }}>
              Curated experiments designed for professor viva demonstrations and self-healing verification.
            </p>
          </div>
          <button
            onClick={() => {
              onResetFailures();
              notify('All failures cleared. Network restored to nominal baseline.');
            }}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              borderRadius: '6px',
              background: '#1e293b',
              color: '#e2e8f0',
              border: '1px solid #334155',
              cursor: 'pointer',
              fontSize: '12px',
              fontWeight: 600,
            }}
          >
            <RotateCcw size={14} /> Clear All Failures
          </button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px' }}>
          {scenarios.map((sc) => (
            <div
              key={sc.id}
              style={{
                background: '#090d14',
                border: '1px solid #1a2333',
                borderRadius: '6px',
                padding: '14px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                  <span style={{
                    fontSize: '10px',
                    fontWeight: 800,
                    padding: '2px 6px',
                    borderRadius: '4px',
                    background: 'rgba(56, 189, 248, 0.15)',
                    color: '#38bdf8',
                    fontFamily: 'monospace',
                  }}>
                    {sc.tag}
                  </span>
                </div>
                <h4 style={{ fontSize: '13px', fontWeight: 700, color: '#f1f5f9' }}>{sc.title}</h4>
                <p style={{ fontSize: '11px', color: '#94a3b8', marginTop: '6px', lineHeight: '1.5' }}>
                  {sc.desc}
                </p>
              </div>

              <button
                onClick={() => {
                  onRunScenario(sc.id);
                  notify(`Loaded ${sc.title}`);
                }}
                style={{
                  marginTop: '12px',
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '6px',
                  padding: '8px 12px',
                  borderRadius: '6px',
                  background: '#0284c7',
                  color: '#ffffff',
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: '12px',
                  fontWeight: 700,
                }}
              >
                <Play size={12} fill="#ffffff" /> Launch Scenario
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Section 2: Controlled Failure Injection Controls */}
      <div style={{
        background: '#0d131f',
        border: '1px solid #1e293b',
        borderRadius: '8px',
        padding: '18px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
          <Flame size={18} color="#f97316" />
          <h3 style={{ fontSize: '15px', fontWeight: 800, color: '#f8fafc' }}>
            Interactive Fault Injector
          </h3>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '14px' }}>
          {/* Link Cut */}
          <div style={{ background: '#090d14', border: '1px solid #1a2333', borderRadius: '6px', padding: '12px' }}>
            <span style={{ fontSize: '12px', fontWeight: 700, color: '#f87171' }}>1. Cut Physical Link</span>
            <p style={{ fontSize: '11px', color: '#64748b', margin: '4px 0 8px 0' }}>Simulate fiber cut or port down</p>
            <select
              value={selectedLink}
              onChange={(e) => setSelectedLink(e.target.value)}
              style={{ width: '100%', padding: '6px', background: '#131d2e', color: '#f8fafc', border: '1px solid #334155', borderRadius: '4px', fontSize: '11px', marginBottom: '8px' }}
            >
              {linkIds.map((lid) => (
                <option key={lid} value={lid}>{lid}</option>
              ))}
            </select>
            <button
              onClick={() => {
                onInjectLinkFailure(selectedLink);
                notify(`Severed link ${selectedLink}`);
              }}
              style={{ width: '100%', padding: '6px', background: '#ef4444', color: '#fff', border: 'none', borderRadius: '4px', fontSize: '11px', fontWeight: 700, cursor: 'pointer' }}
            >
              Sever Link
            </button>
          </div>

          {/* Router Crash */}
          <div style={{ background: '#090d14', border: '1px solid #1a2333', borderRadius: '6px', padding: '12px' }}>
            <span style={{ fontSize: '12px', fontWeight: 700, color: '#f87171' }}>2. Crash Router Node</span>
            <p style={{ fontSize: '11px', color: '#64748b', margin: '4px 0 8px 0' }}>Immediate power-off or kernel crash</p>
            <select
              value={selectedNode}
              onChange={(e) => setSelectedNode(e.target.value)}
              style={{ width: '100%', padding: '6px', background: '#131d2e', color: '#f8fafc', border: '1px solid #334155', borderRadius: '4px', fontSize: '11px', marginBottom: '8px' }}
            >
              {['CR1', 'CR2', 'DR1', 'DR2', 'DR3', 'DR4', 'AS1', 'AS2'].map((nid) => (
                <option key={nid} value={nid}>{nid}</option>
              ))}
            </select>
            <button
              onClick={() => {
                onInjectNodeFailure(selectedNode);
                notify(`Crashed node ${selectedNode}`);
              }}
              style={{ width: '100%', padding: '6px', background: '#ef4444', color: '#fff', border: 'none', borderRadius: '4px', fontSize: '11px', fontWeight: 700, cursor: 'pointer' }}
            >
              Crash Node
            </button>
          </div>

          {/* Optical Packet Loss (BER) */}
          <div style={{ background: '#090d14', border: '1px solid #1a2333', borderRadius: '6px', padding: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '12px', fontWeight: 700, color: '#f59e0b' }}>3. Physical Loss (BER)</span>
              <span style={{ fontSize: '11px', color: '#f59e0b', fontFamily: 'monospace' }}>{lossRate}%</span>
            </div>
            <p style={{ fontSize: '11px', color: '#64748b', margin: '4px 0 8px 0' }}>Simulate dirty fiber dispersion</p>
            <input
              type="range"
              min="5"
              max="35"
              value={lossRate}
              onChange={(e) => setLossRate(Number(e.target.value))}
              style={{ width: '100%', marginBottom: '8px', accentColor: '#f59e0b' }}
            />
            <button
              onClick={() => {
                onInjectPacketLoss(selectedLink, lossRate / 100);
                notify(`Injected ${lossRate}% loss on ${selectedLink}`);
              }}
              style={{ width: '100%', padding: '6px', background: '#d97706', color: '#fff', border: 'none', borderRadius: '4px', fontSize: '11px', fontWeight: 700, cursor: 'pointer' }}
            >
              Apply Degradation
            </button>
          </div>

          {/* Traffic Surge */}
          <div style={{ background: '#090d14', border: '1px solid #1a2333', borderRadius: '6px', padding: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '12px', fontWeight: 700, color: '#38bdf8' }}>4. Traffic Volume Surge</span>
              <span style={{ fontSize: '11px', color: '#38bdf8', fontFamily: 'monospace' }}>{surgeMult}x</span>
            </div>
            <p style={{ fontSize: '11px', color: '#64748b', margin: '4px 0 8px 0' }}>Simulate application flash crowd</p>
            <input
              type="range"
              min="2"
              max="6"
              value={surgeMult}
              onChange={(e) => setSurgeMult(Number(e.target.value))}
              style={{ width: '100%', marginBottom: '8px', accentColor: '#38bdf8' }}
            />
            <button
              onClick={() => {
                onInjectTrafficSurge(selectedFlow, surgeMult);
                notify(`Surged flow ${selectedFlow} by ${surgeMult}x`);
              }}
              style={{ width: '100%', padding: '6px', background: '#0284c7', color: '#fff', border: 'none', borderRadius: '4px', fontSize: '11px', fontWeight: 700, cursor: 'pointer' }}
            >
              Inject Traffic Surge
            </button>
          </div>

          {/* Queue Saturation */}
          <div style={{ background: '#090d14', border: '1px solid #1a2333', borderRadius: '6px', padding: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '12px', fontWeight: 700, color: '#ec4899' }}>5. Queue Saturation</span>
              <span style={{ fontSize: '11px', color: '#ec4899', fontFamily: 'monospace' }}>{queueCapacity} pkts</span>
            </div>
            <p style={{ fontSize: '11px', color: '#64748b', margin: '4px 0 8px 0' }}>Simulate buffer bloat & tail-drop</p>
            <input
              type="range"
              min="1"
              max="20"
              value={queueCapacity}
              onChange={(e) => setQueueCapacity(Number(e.target.value))}
              style={{ width: '100%', marginBottom: '8px', accentColor: '#ec4899' }}
            />
            <button
              onClick={() => {
                if (onInjectQueueSaturation) {
                  onInjectQueueSaturation(selectedLink, queueCapacity);
                  notify(`Saturated queue on ${selectedLink} to ${queueCapacity} pkts`);
                }
              }}
              style={{ width: '100%', padding: '6px', background: '#db2777', color: '#fff', border: 'none', borderRadius: '4px', fontSize: '11px', fontWeight: 700, cursor: 'pointer' }}
            >
              Saturate Queue
            </button>
          </div>

          {/* Packet Corruption */}
          <div style={{ background: '#090d14', border: '1px solid #1a2333', borderRadius: '6px', padding: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '12px', fontWeight: 700, color: '#a855f7' }}>6. Packet Corruption</span>
              <span style={{ fontSize: '11px', color: '#a855f7', fontFamily: 'monospace' }}>{corruptionRate}%</span>
            </div>
            <p style={{ fontSize: '11px', color: '#64748b', margin: '4px 0 8px 0' }}>Simulate bit flip & CRC errors</p>
            <input
              type="range"
              min="5"
              max="50"
              value={corruptionRate}
              onChange={(e) => setCorruptionRate(Number(e.target.value))}
              style={{ width: '100%', marginBottom: '8px', accentColor: '#a855f7' }}
            />
            <button
              onClick={() => {
                if (onInjectPacketCorruption) {
                  onInjectPacketCorruption(selectedLink, corruptionRate / 100);
                  notify(`Injected ${corruptionRate}% corruption on ${selectedLink}`);
                }
              }}
              style={{ width: '100%', padding: '6px', background: '#9333ea', color: '#fff', border: 'none', borderRadius: '4px', fontSize: '11px', fontWeight: 700, cursor: 'pointer' }}
            >
              Inject Bit Corruption
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
