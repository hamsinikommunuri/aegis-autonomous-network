import React from 'react';
import { 
  ShieldCheck, 
  Activity, 
  Play, 
  Pause, 
  RotateCcw, 
  FastForward, 
  Cpu, 
  Radio, 
  SlidersHorizontal,
  Flame,
  Award,
  Clock
} from 'lucide-react';

interface NocHeaderProps {
  isRunning: boolean;
  onTogglePlay: () => void;
  onStep: () => void;
  onReset: () => void;
  speed: number;
  onSpeedChange: (speed: number) => void;
  autonomousMode: boolean;
  onToggleAutonomous: () => void;
  activeTab: string;
  onTabChange: (tab: string) => void;
  simTimeMs: number;
  activeIncidentsCount: number;
  engineMode: 'BROWSER' | 'PYTHON';
}

export const NocHeader: React.FC<NocHeaderProps> = ({
  isRunning,
  onTogglePlay,
  onStep,
  onReset,
  speed,
  onSpeedChange,
  autonomousMode,
  onToggleAutonomous,
  activeTab,
  onTabChange,
  simTimeMs,
  activeIncidentsCount,
  engineMode,
}) => {
  const tabs = [
    { id: 'topology', label: 'Topology & Telemetry', icon: Activity },
    { id: 'incidents', label: 'Incident & Recovery', icon: ShieldCheck, badge: activeIncidentsCount },
    { id: 'experiments', label: 'Experiment Lab', icon: SlidersHorizontal },
    { id: 'benchmarks', label: 'Quantitative Benchmark', icon: Award },
    { id: 'timeline', label: 'Audit Timeline', icon: Clock },
  ];

  return (
    <header style={{
      background: 'linear-gradient(180deg, #0e131d 0%, #07090e 100%)',
      borderBottom: '1px solid #1e293b',
      padding: '12px 24px',
      display: 'flex',
      flexDirection: 'column',
      gap: '12px',
    }}>
      {/* Top row: Brand + Master Controls + System Status */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            background: 'linear-gradient(135deg, #0284c7 0%, #06b6d4 100%)',
            borderRadius: '8px',
            padding: '8px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 16px rgba(6, 182, 212, 0.35)',
          }}>
            <ShieldCheck size={26} color="#ffffff" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '18px', fontWeight: 800, letterSpacing: '0.05em', color: '#f8fafc' }}>
                AEGIS
              </span>
              <span style={{
                background: '#1e293b',
                color: '#38bdf8',
                fontSize: '11px',
                fontWeight: 700,
                padding: '2px 8px',
                borderRadius: '4px',
                fontFamily: 'monospace',
                border: '1px solid rgba(56, 189, 248, 0.3)',
              }}>
                v1.0-NOC
              </span>
              <span style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '5px',
                fontSize: '11px',
                padding: '2px 8px',
                borderRadius: '4px',
                background: engineMode === 'PYTHON' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(56, 189, 248, 0.15)',
                color: engineMode === 'PYTHON' ? '#34d399' : '#38bdf8',
                border: `1px solid ${engineMode === 'PYTHON' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(56, 189, 248, 0.3)'}`,
              }}>
                <Radio size={12} />
                {engineMode === 'PYTHON' ? 'Live Python Daemon' : 'In-Browser Simulation'}
              </span>
            </div>
            <p style={{ fontSize: '11px', color: '#64748b', marginTop: '1px' }}>
              Autonomous Network Intelligence & Closed-Loop Self-Healing Platform
            </p>
          </div>
        </div>

        {/* Master Simulation Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {/* Play/Pause Button */}
          <button
            onClick={onTogglePlay}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 14px',
              background: isRunning ? '#0284c7' : '#1e293b',
              color: '#ffffff',
              borderRadius: '6px',
              border: '1px solid #334155',
              cursor: 'pointer',
              fontSize: '12px',
              fontWeight: 600,
              transition: 'all 0.2s',
            }}
          >
            {isRunning ? <Pause size={14} /> : <Play size={14} />}
            {isRunning ? 'Pause' : 'Simulate'}
          </button>

          {/* Single Step Button */}
          <button
            onClick={onStep}
            disabled={isRunning}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              background: isRunning ? '#0f172a' : '#1e293b',
              color: isRunning ? '#475569' : '#e2e8f0',
              borderRadius: '6px',
              border: '1px solid #334155',
              cursor: isRunning ? 'not-allowed' : 'pointer',
              fontSize: '12px',
              fontWeight: 600,
            }}
            title="Advance 1 simulation interval (100ms)"
          >
            <FastForward size={14} />
            Step
          </button>

          {/* Speed Selector */}
          <div style={{ display: 'flex', alignItems: 'center', background: '#0f172a', borderRadius: '6px', border: '1px solid #334155', padding: '2px' }}>
            {[1, 2, 5].map((s) => (
              <button
                key={s}
                onClick={() => onSpeedChange(s)}
                style={{
                  padding: '4px 8px',
                  fontSize: '11px',
                  fontWeight: 600,
                  borderRadius: '4px',
                  border: 'none',
                  background: speed === s ? '#0284c7' : 'transparent',
                  color: speed === s ? '#ffffff' : '#94a3b8',
                  cursor: 'pointer',
                }}
              >
                {s}x
              </button>
            ))}
          </div>

          {/* Reset */}
          <button
            onClick={onReset}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              background: '#1e293b',
              color: '#e2e8f0',
              borderRadius: '6px',
              border: '1px solid #334155',
              cursor: 'pointer',
              fontSize: '12px',
              fontWeight: 600,
            }}
          >
            <RotateCcw size={14} />
            Reset
          </button>

          {/* Autonomous Self-Healing Toggle */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            marginLeft: '8px',
            padding: '4px 10px',
            borderRadius: '6px',
            background: autonomousMode ? 'rgba(16, 185, 129, 0.12)' : 'rgba(239, 68, 68, 0.12)',
            border: `1px solid ${autonomousMode ? 'rgba(16, 185, 129, 0.35)' : 'rgba(239, 68, 68, 0.35)'}`,
          }}>
            <Cpu size={14} color={autonomousMode ? '#10b981' : '#ef4444'} />
            <span style={{ fontSize: '11px', fontWeight: 700, color: autonomousMode ? '#34d399' : '#f87171' }}>
              {autonomousMode ? 'AEGIS SELF-HEALING: ACTIVE' : 'MANUAL ROUTING MODE'}
            </span>
            <input
              type="checkbox"
              checked={autonomousMode}
              onChange={onToggleAutonomous}
              style={{ cursor: 'pointer', accentColor: '#10b981' }}
            />
          </div>

          {/* Simulation Clock Readout */}
          <div style={{
            background: '#090d14',
            padding: '5px 12px',
            borderRadius: '6px',
            border: '1px solid #1e293b',
            fontFamily: 'monospace',
            fontSize: '12px',
            color: '#38bdf8',
          }}>
            T: {(simTimeMs / 1000).toFixed(1)}s
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div style={{ display: 'flex', gap: '8px', borderTop: '1px solid #151d2a', paddingTop: '8px', overflowX: 'auto' }}>
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 16px',
                borderRadius: '6px',
                fontSize: '13px',
                fontWeight: isActive ? 700 : 500,
                color: isActive ? '#38bdf8' : '#94a3b8',
                background: isActive ? '#131923' : 'transparent',
                border: isActive ? '1px solid #1e293b' : '1px solid transparent',
                cursor: 'pointer',
                transition: 'all 0.15s',
                whiteSpace: 'nowrap',
              }}
            >
              <Icon size={16} color={isActive ? '#38bdf8' : '#64748b'} />
              {tab.label}
              {tab.badge !== undefined && tab.badge > 0 && (
                <span style={{
                  background: '#ef4444',
                  color: '#ffffff',
                  fontSize: '10px',
                  fontWeight: 800,
                  padding: '1px 6px',
                  borderRadius: '10px',
                  marginLeft: '4px',
                }}>
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </header>
  );
};
