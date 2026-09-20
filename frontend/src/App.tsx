import React, { useState, useEffect, useRef } from 'react';
import { InBrowserEngine } from './simulation/inBrowserEngine';
import { NetworkGlobalSnapshot } from './types/network';
import { NocHeader } from './components/NocHeader';
import { TopologyCanvas } from './components/TopologyCanvas';
import { LiveTelemetryPanel } from './components/LiveTelemetryPanel';
import { IncidentCenter } from './components/IncidentCenter';
import { RecoveryPlannerPanel } from './components/RecoveryPlannerPanel';
import { ExperimentLab } from './components/ExperimentLab';
import { BenchmarkArena } from './components/BenchmarkArena';
import { IncidentTimeline } from './components/IncidentTimeline';

export const App: React.FC = () => {
  // Initialize in-browser simulation engine
  const engineRef = useRef<InBrowserEngine>(new InBrowserEngine());
  const engine = engineRef.current;

  const [engineMode, setEngineMode] = useState<'BROWSER' | 'PYTHON'>('BROWSER');
  const [isRunning, setIsRunning] = useState<boolean>(true);
  const [speed, setSpeed] = useState<number>(1);
  const [autonomousMode, setAutonomousMode] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<string>('topology');
  const [snapshot, setSnapshot] = useState<NetworkGlobalSnapshot>(() => engine.step());
  const [selectedElement, setSelectedElement] = useState<{ type: 'NODE' | 'LINK'; id: string } | null>(null);

  // Try WebSocket connection to Python backend
  useEffect(() => {
    let ws: WebSocket | null = null;
    try {
      ws = new WebSocket('ws://localhost:8000/ws/stream');
      ws.onopen = () => {
        setEngineMode('PYTHON');
      };
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.snapshot && data.snapshot.links) {
            setSnapshot(data.snapshot);
          }
        } catch (e) {
          // ignore
        }
      };
      ws.onerror = () => {
        setEngineMode('BROWSER');
      };
      ws.onclose = () => {
        setEngineMode('BROWSER');
      };
    } catch (err) {
      setEngineMode('BROWSER');
    }

    return () => {
      if (ws) ws.close();
    };
  }, []);

  // Main Simulation Loop (runs when in BROWSER mode and isRunning is true)
  useEffect(() => {
    if (engineMode !== 'BROWSER' || !isRunning) return;

    const intervalMs = Math.max(25, 100 / speed);
    const interval = setInterval(() => {
      engine.autonomousMode = autonomousMode;
      const nextSnap = engine.step();
      setSnapshot({ ...nextSnap });
    }, intervalMs);

    return () => clearInterval(interval);
  }, [engineMode, isRunning, speed, autonomousMode]);

  // Single step manually
  const handleStep = () => {
    if (engineMode === 'BROWSER') {
      engine.autonomousMode = autonomousMode;
      const nextSnap = engine.step();
      setSnapshot({ ...nextSnap });
    }
  };

  // Reset simulation
  const handleReset = () => {
    if (engineMode === 'BROWSER') {
      engine.reset();
      const nextSnap = engine.step();
      setSnapshot({ ...nextSnap });
    }
  };

  // Toggle Autonomous Self-Healing
  const handleToggleAutonomous = () => {
    const next = !autonomousMode;
    setAutonomousMode(next);
    engine.autonomousMode = next;
  };

  const linkIds = Object.keys(snapshot.links || {});
  const nodeIds = Object.keys(snapshot.nodes || {});
  const flowIds = Object.keys(snapshot.flows || {});

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: '#07090e' }}>
      {/* Top NOC Header */}
      <NocHeader
        isRunning={isRunning}
        onTogglePlay={() => setIsRunning(!isRunning)}
        onStep={handleStep}
        onReset={handleReset}
        speed={speed}
        onSpeedChange={setSpeed}
        autonomousMode={autonomousMode}
        onToggleAutonomous={handleToggleAutonomous}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        simTimeMs={snapshot.timestamp_ms}
        activeIncidentsCount={snapshot.active_incidents_count}
        engineMode={engineMode}
      />

      {/* Main Workspace Body */}
      <main style={{ flex: 1, padding: '20px', maxWidth: '1440px', width: '100%', margin: '0 auto' }}>
        {activeTab === 'topology' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* Interactive Network Topology Map */}
            <TopologyCanvas
              nodes={snapshot.nodes}
              links={snapshot.links}
              flows={snapshot.flows}
              selectedElement={selectedElement}
              onSelectElement={setSelectedElement}
            />

            {/* Real-time Telemetry Dashboard */}
            <LiveTelemetryPanel
              snapshot={snapshot}
              history={engine.history}
            />
          </div>
        )}

        {activeTab === 'incidents' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            {/* Active Incident Lifecycle & RCA */}
            <IncidentCenter
              activeIncidents={engine.activeIncidents}
              incidentHistory={engine.incidentHistory}
            />

            {/* Recovery Planner & Candidate Evaluator */}
            <RecoveryPlannerPanel
              activeIncidents={engine.activeIncidents}
            />
          </div>
        )}

        {activeTab === 'experiments' && (
          <ExperimentLab
            linkIds={linkIds}
            nodeIds={nodeIds}
            flowIds={flowIds}
            onInjectLinkFailure={(id) => engine.injectLinkFailure(id)}
            onInjectNodeFailure={(id) => engine.injectNodeFailure(id)}
            onInjectPacketLoss={(id, rate) => engine.injectPacketLoss(id, rate)}
            onInjectLatencySpike={(id, ms) => engine.injectLatencySpike(id, ms)}
            onInjectBandwidthReduction={(id, bw) => engine.injectBandwidthReduction(id, bw)}
            onInjectTrafficSurge={(id, mult) => engine.injectTrafficSurge(id, mult)}
            onRunScenario={(scId) => engine.runScenario(scId)}
            onResetFailures={() => engine.clearAllFailures()}
          />
        )}

        {activeTab === 'benchmarks' && (
          <BenchmarkArena
            onRunBenchmark={(type) => engine.runBenchmark(type)}
          />
        )}

        {activeTab === 'timeline' && (
          <IncidentTimeline
            activeIncidents={engine.activeIncidents}
            incidentHistory={engine.incidentHistory}
          />
        )}
      </main>

      {/* Footer */}
      <footer style={{
        borderTop: '1px solid #151d2a',
        padding: '12px 24px',
        fontSize: '11px',
        color: '#64748b',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        background: '#090d14',
      }}>
        <span>
          AEGIS System — Closed-Loop Autonomous Network Management & Self-Healing Architecture
        </span>
        <span style={{ fontFamily: 'monospace' }}>
          Sim Clock: {(snapshot.timestamp_ms / 1000).toFixed(1)}s | Tick #{snapshot.tick} | Packets Delivered: {snapshot.total_packets_received.toLocaleString()}
        </span>
      </footer>
    </div>
  );
};

export default App;
