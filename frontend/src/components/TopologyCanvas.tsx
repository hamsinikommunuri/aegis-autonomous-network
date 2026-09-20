import React, { useState } from 'react';
import { Node, Link, TrafficFlow } from '../types/network';
import { Server, Router, Monitor, Network, AlertTriangle, XCircle, CheckCircle, Info } from 'lucide-react';

interface TopologyCanvasProps {
  nodes: Record<string, Node>;
  links: Record<string, Link>;
  flows: Record<string, TrafficFlow>;
  selectedElement: { type: 'NODE' | 'LINK'; id: string } | null;
  onSelectElement: (elem: { type: 'NODE' | 'LINK'; id: string } | null) => void;
}

export const TopologyCanvas: React.FC<TopologyCanvasProps> = ({
  nodes,
  links,
  flows,
  selectedElement,
  onSelectElement,
}) => {
  const [hoveredLink, setHoveredLink] = useState<string | null>(null);

  // Group bidirectional links into single rendering pairs to avoid duplicate lines
  const renderedLinks: Array<{ id: string; src: string; dst: string; link: Link }> = [];
  const visitedPairs = new Set<string>();

  for (const lid in links) {
    const link = links[lid];
    const pairKey = [link.source, link.destination].sort().join('--');
    if (!visitedPairs.has(pairKey)) {
      visitedPairs.add(pairKey);
      renderedLinks.push({ id: lid, src: link.source, dst: link.destination, link });
    }
  }

  // Selected item data
  const selectedNode = selectedElement?.type === 'NODE' ? nodes[selectedElement.id] : null;
  const selectedLink = selectedElement?.type === 'LINK' ? links[selectedElement.id] : null;

  // Find flows traversing selected link
  const flowsOnSelectedLink = selectedLink
    ? Object.values(flows).filter((f) => {
        for (let i = 0; i < f.current_path.length - 1; i++) {
          if (
            (f.current_path[i] === selectedLink.source && f.current_path[i + 1] === selectedLink.destination) ||
            (f.current_path[i] === selectedLink.destination && f.current_path[i + 1] === selectedLink.source)
          ) {
            return true;
          }
        }
        return false;
      })
    : [];

  return (
    <div style={{
      position: 'relative',
      width: '100%',
      height: '520px',
      background: 'radial-gradient(circle at 50% 50%, #0d1424 0%, #06080d 100%)',
      borderRadius: '8px',
      border: '1px solid #1e293b',
      overflow: 'hidden',
    }}>
      {/* Background Grid Lines */}
      <svg style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', pointerEvents: 'none' }}>
        <defs>
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#151e2e" strokeWidth="1" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />
      </svg>

      {/* Main SVG Graph: Links, Flow Pulses, and Labels */}
      <svg viewBox="0 0 880 520" style={{ width: '100%', height: '100%' }}>
        {/* Render Links */}
        {renderedLinks.map(({ id, src, dst, link }) => {
          const u = nodes[src];
          const v = nodes[dst];
          if (!u || !v) return null;

          const isDown = link.status === 'DOWN';
          const isDegraded = link.status === 'DEGRADED' || link.loss_rate >= 0.05;
          const isCongested = link.current_utilization >= 0.85;
          const isSelected = selectedElement?.type === 'LINK' && selectedElement.id === id;

          let strokeColor = '#334155'; // idle
          if (isDown) strokeColor = '#ef4444';
          else if (isDegraded) strokeColor = '#f59e0b';
          else if (isCongested) strokeColor = '#f97316';
          else if (link.current_utilization > 0.40) strokeColor = '#06b6d4';
          else strokeColor = '#10b981';

          const strokeWidth = isSelected ? 4 : isCongested ? 3.5 : 2;
          const strokeDash = isDown ? '6,6' : isDegraded ? '4,4' : undefined;

          // Midpoint for badge label
          const midX = (u.x + v.x) / 2;
          const midY = (u.y + v.y) / 2;

          return (
            <g key={id} onClick={() => onSelectElement({ type: 'LINK', id })} style={{ cursor: 'pointer' }}>
              {/* Interactive Hitbox */}
              <line
                x1={u.x}
                y1={u.y}
                x2={v.x}
                y2={v.y}
                stroke="transparent"
                strokeWidth={16}
                onMouseEnter={() => setHoveredLink(id)}
                onMouseLeave={() => setHoveredLink(null)}
              />

              {/* Visible Physical Link Line */}
              <line
                x1={u.x}
                y1={u.y}
                x2={v.x}
                y2={v.y}
                stroke={strokeColor}
                strokeWidth={strokeWidth}
                strokeDasharray={strokeDash}
                style={{ transition: 'all 0.3s' }}
              />

              {/* Animated Packet Pulse along active links */}
              {!isDown && link.current_utilization > 0.05 && (
                <circle r={link.current_utilization > 0.7 ? 4 : 3} fill={isCongested ? '#f97316' : '#38bdf8'}>
                  <animateMotion
                    path={`M ${u.x} ${u.y} L ${v.x} ${v.y}`}
                    dur={`${Math.max(0.6, 2.5 - link.current_utilization * 1.8)}s`}
                    repeatCount="indefinite"
                  />
                </circle>
              )}

              {/* Link Utilization / Fault Badge */}
              <g transform={`translate(${midX}, ${midY})`}>
                <rect
                  x="-20"
                  y="-10"
                  width="40"
                  height="18"
                  rx="4"
                  fill="#090d14"
                  stroke={strokeColor}
                  strokeWidth="1"
                />
                <text
                  x="0"
                  y="2"
                  textAnchor="middle"
                  fill={strokeColor}
                  fontSize="9"
                  fontFamily="monospace"
                  fontWeight="700"
                >
                  {isDown ? 'FAIL' : `${Math.round(link.current_utilization * 100)}%`}
                </text>
              </g>
            </g>
          );
        })}

        {/* Render Nodes */}
        {Object.values(nodes).map((node) => {
          const isDown = node.status === 'DOWN';
          const isSelected = selectedElement?.type === 'NODE' && selectedElement.id === node.id;
          
          let borderColor = '#0284c7';
          if (isDown) borderColor = '#ef4444';
          else if (node.health_score < 0.6) borderColor = '#f59e0b';
          else if (node.node_type === 'SERVER') borderColor = '#a855f7';
          else if (node.node_type === 'HOST') borderColor = '#10b981';

          return (
            <g
              key={node.id}
              transform={`translate(${node.x}, ${node.y})`}
              onClick={(e) => {
                e.stopPropagation();
                onSelectElement({ type: 'NODE', id: node.id });
              }}
              style={{ cursor: 'pointer' }}
            >
              {/* Outer halo if selected */}
              {isSelected && (
                <circle r="26" fill="none" stroke="#38bdf8" strokeWidth="2" strokeDasharray="3,3" opacity="0.8" />
              )}

              {/* Node base circle */}
              <circle
                r="18"
                fill="#0e1726"
                stroke={borderColor}
                strokeWidth={isDown ? 2.5 : 2}
                className={isDown ? 'pulse-red' : undefined}
              />

              {/* Icon */}
              <g transform="translate(-8, -8)" pointerEvents="none">
                {node.node_type === 'HOST' && <Monitor size={16} color="#10b981" />}
                {node.node_type === 'SWITCH' && <Network size={16} color="#38bdf8" />}
                {node.node_type === 'ROUTER' && <Router size={16} color={isDown ? '#ef4444' : '#0284c7'} />}
                {node.node_type === 'SERVER' && <Server size={16} color="#c084fc" />}
              </g>

              {/* Node ID Label */}
              <text
                x="0"
                y="28"
                textAnchor="middle"
                fill="#f1f5f9"
                fontSize="11"
                fontWeight="700"
                fontFamily="monospace"
              >
                {node.id}
              </text>

              {/* Health Score Pill */}
              <text
                x="0"
                y="40"
                textAnchor="middle"
                fill="#64748b"
                fontSize="9"
                fontFamily="monospace"
              >
                {isDown ? 'OFFLINE' : `HLTH: ${Math.round(node.health_score * 100)}%`}
              </text>
            </g>
          );
        })}
      </svg>

      {/* Deep Inspection Drawer (Right side overlay when node or link selected) */}
      {selectedElement && (
        <div style={{
          position: 'absolute',
          top: '12px',
          right: '12px',
          width: '280px',
          background: 'rgba(15, 23, 42, 0.95)',
          backdropFilter: 'blur(8px)',
          border: '1px solid #334155',
          borderRadius: '8px',
          padding: '16px',
          color: '#f8fafc',
          boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
          fontSize: '12px',
          maxHeight: '90%',
          overflowY: 'auto',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #1e293b', paddingBottom: '8px', marginBottom: '12px' }}>
            <span style={{ fontWeight: 800, color: '#38bdf8', letterSpacing: '0.05em' }}>
              {selectedElement.type === 'NODE' ? `NODE: ${selectedNode?.id}` : `LINK: ${selectedLink?.id}`}
            </span>
            <button
              onClick={() => onSelectElement(null)}
              style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer' }}
            >
              ✕
            </button>
          </div>

          {selectedNode && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div><span style={{ color: '#64748b' }}>Role:</span> <strong style={{ color: '#e2e8f0' }}>{selectedNode.name}</strong></div>
              <div><span style={{ color: '#64748b' }}>Type:</span> <span style={{ color: '#38bdf8' }}>{selectedNode.node_type}</span></div>
              <div>
                <span style={{ color: '#64748b' }}>Operational Status:</span>{' '}
                <span style={{ color: selectedNode.status === 'UP' ? '#10b981' : '#ef4444', fontWeight: 700 }}>
                  {selectedNode.status}
                </span>
              </div>
              <div><span style={{ color: '#64748b' }}>Health Index:</span> <strong style={{ color: '#34d399' }}>{Math.round(selectedNode.health_score * 100)}%</strong></div>
              <div><span style={{ color: '#64748b' }}>Forwarding Capacity:</span> {selectedNode.processing_capacity_pps.toLocaleString()} pps</div>
              <div><span style={{ color: '#64748b' }}>Queue Depth:</span> {selectedNode.current_queue_depth} / {selectedNode.queue_capacity_packets} pkts</div>
              <div><span style={{ color: '#64748b' }}>CPU Utilization:</span> {Math.round(selectedNode.cpu_utilization * 100)}%</div>
              <div><span style={{ color: '#64748b' }}>Packets Forwarded:</span> {selectedNode.forwarded_packets.toLocaleString()}</div>
            </div>
          )}

          {selectedLink && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div><span style={{ color: '#64748b' }}>Endpoints:</span> {selectedLink.source} ↔ {selectedLink.destination}</div>
              <div><span style={{ color: '#64748b' }}>Bandwidth:</span> {(selectedLink.bandwidth_bps / 1e6).toFixed(0)} Mbps</div>
              <div>
                <span style={{ color: '#64748b' }}>Link Status:</span>{' '}
                <span style={{
                  color: selectedLink.status === 'UP' ? '#10b981' : selectedLink.status === 'DEGRADED' ? '#f59e0b' : '#ef4444',
                  fontWeight: 700
                }}>
                  {selectedLink.status}
                </span>
              </div>
              <div>
                <span style={{ color: '#64748b' }}>Current Utilization:</span>{' '}
                <strong style={{ color: selectedLink.current_utilization > 0.85 ? '#f97316' : '#38bdf8' }}>
                  {Math.round(selectedLink.current_utilization * 100)}%
                </strong>
              </div>
              <div><span style={{ color: '#64748b' }}>Current Latency:</span> {selectedLink.current_latency_ms.toFixed(1)} ms</div>
              <div><span style={{ color: '#64748b' }}>Physical Loss Rate:</span> {(selectedLink.loss_rate * 100).toFixed(1)}%</div>
              <div><span style={{ color: '#64748b' }}>Queue Buffer:</span> {selectedLink.current_queue_depth} / {selectedLink.queue_capacity_packets} pkts</div>

              <div style={{ borderTop: '1px solid #1e293b', paddingTop: '8px', marginTop: '4px' }}>
                <span style={{ color: '#64748b', fontWeight: 600 }}>Active Traversing Flows:</span>
                {flowsOnSelectedLink.length === 0 ? (
                  <p style={{ color: '#475569', fontSize: '11px', marginTop: '4px' }}>None</p>
                ) : (
                  <ul style={{ listStyle: 'none', marginTop: '6px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    {flowsOnSelectedLink.map((f) => (
                      <li key={f.id} style={{ background: '#090d14', padding: '4px 6px', borderRadius: '4px', fontSize: '11px' }}>
                        <span style={{ color: '#38bdf8', fontWeight: 600 }}>{f.name}</span>{' '}
                        <span style={{ color: '#64748b' }}>({(f.demand_bps / 1e6).toFixed(0)}M)</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
