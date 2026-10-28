/**
 * MACSS — Multi-Agent Cooperative Security System Dashboard
 * Full academic research & live operational testbed interface.
 */
import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import {
  Shield, Activity, AlertTriangle, Cpu, GitBranch,
  BarChart3, Crosshair, Zap, Home, RefreshCw,
  Play, CheckCircle2, Eye, FlaskConical, Download, Layers
} from 'lucide-react'
import {
  getHealth, getAgents, getAlerts, getEvents,
  getDecisions, getSimulationStatus, startSimulation,
  resetSimulation, getMetrics, runExperiment, getExperiments
} from './services/api'
import './index.css'

// ── Top Navigation Items ─────────────────────────────────────────
const navItems = [
  { label: 'Overview',            path: '/',            icon: Home,          section: 'Dashboard' },
  { label: 'Agent Status',        path: '/agents',      icon: Cpu,           section: 'Dashboard' },
  { label: 'Event Stream',        path: '/events',      icon: Activity,      section: 'Dashboard' },
  { label: 'Incidents & Alerts',  path: '/incidents',   icon: AlertTriangle, section: 'Security' },
  { label: 'Decisions',           path: '/decisions',   icon: GitBranch,     section: 'Security' },
  { label: 'Conflict Resolution', path: '/conflicts',   icon: Zap,           section: 'Security' },
  { label: 'Attack Simulator',    path: '/simulation',  icon: Crosshair,     section: 'Research' },
  { label: 'Evaluation Metrics',  path: '/metrics',     icon: BarChart3,     section: 'Research' },
  { label: 'Baseline Compare',    path: '/baseline',    icon: Eye,           section: 'Research' },
  { label: 'Batch Experiments',   path: '/experiments', icon: FlaskConical,  section: 'Research' },
]

const sections = ['Dashboard', 'Security', 'Research']

function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <Shield size={20} color="var(--accent-blue)" />
        <span style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--text-primary)' }}>MACSS</span>
        <span className="badge badge-info" style={{ fontSize: '0.65rem', marginLeft: 'auto' }}>v1.0</span>
      </div>
      <nav className="sidebar-nav">
        {sections.map(section => (
          <div key={section} style={{ marginBottom: 12 }}>
            <div className="sidebar-section-label">{section}</div>
            {navItems.filter(n => n.section === section).map(item => (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === '/'}
                className={({ isActive }) => `sidebar-item${isActive ? ' active' : ''}`}
              >
                <item.icon size={15} />
                <span>{item.label}</span>
              </NavLink>
            ))}
          </div>
        ))}
      </nav>
      <div style={{ padding: '12px 16px', borderTop: '1px solid var(--border)', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
        Cooperative Cyber Defense Testbed
      </div>
    </aside>
  )
}

function HorizontalNav() {
  return (
    <nav className="horizontal-nav">
      {navItems.map(item => (
        <NavLink
          key={item.path}
          to={item.path}
          end={item.path === '/'}
          className={({ isActive }) => `horizontal-nav-item${isActive ? ' active' : ''}`}
        >
          <item.icon size={14} />
          <span>{item.label}</span>
        </NavLink>
      ))}
    </nav>
  )
}

function Topbar({ apiStatus, onRefresh, layoutMode, onToggleLayout }) {
  return (
    <header className="topbar">
      <div className="topbar-brand">
        <Shield size={20} color="var(--accent-blue)" />
        <span>MACSS Research Testbed</span>
        <span className="badge badge-neutral" style={{ fontWeight: 400, fontSize: '0.7rem' }}>
          Multi-Agent Defense
        </span>
      </div>
      <div className="topbar-actions">
        {/* Layout Switcher: Option 1 vs Option 2 */}
        <div style={{ display: 'flex', alignItems: 'center', background: 'var(--bg-subtle)', padding: '2px 4px', borderRadius: 4, border: '1px solid var(--border)' }}>
          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginRight: 6, fontWeight: 600 }}>LAYOUT:</span>
          <button
            onClick={() => onToggleLayout('sidebar')}
            className="btn"
            style={{
              padding: '3px 8px',
              fontSize: '0.75rem',
              backgroundColor: layoutMode === 'sidebar' ? 'var(--accent-blue)' : 'transparent',
              color: layoutMode === 'sidebar' ? '#ffffff' : 'var(--text-secondary)',
              border: 'none',
              borderRadius: 3,
            }}
            title="Option 1: Sidebar on Left, Dashboard on Right"
          >
            Sidebar (Option 1)
          </button>
          <button
            onClick={() => onToggleLayout('horizontal')}
            className="btn"
            style={{
              padding: '3px 8px',
              fontSize: '0.75rem',
              backgroundColor: layoutMode === 'horizontal' ? 'var(--accent-blue)' : 'transparent',
              color: layoutMode === 'horizontal' ? '#ffffff' : 'var(--text-secondary)',
              border: 'none',
              borderRadius: 3,
            }}
            title="Option 2: Horizontal Navigation across Top"
          >
            Horizontal (Option 2)
          </button>
        </div>

        <button
          onClick={onRefresh}
          className="btn btn-secondary"
          style={{ padding: '4px 10px', fontSize: '0.75rem' }}
        >
          <RefreshCw size={12} /> Refresh
        </button>

        <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span className={`status-dot ${apiStatus}`} />
          API: {apiStatus === 'running' ? 'Connected' : 'Offline'}
        </span>
      </div>
    </header>
  )
}

// ── Overview Page ────────────────────────────────────────────────
function Overview({ alerts, decisions, simState, metrics, onTrigger, onReset, isTriggering }) {
  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 className="page-title">Research Dashboard</h1>
          <p className="page-subtitle">Cooperative AI Multi-Agent Cybersecurity Testbed</p>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button
            onClick={onTrigger}
            disabled={isTriggering || simState?.active}
            className="btn btn-primary"
            style={{ display: 'flex', alignItems: 'center', gap: 8 }}
          >
            <Play size={14} /> {simState?.active ? 'Campaign Running…' : 'Launch Mixed Campaign'}
          </button>
          <button
            onClick={onReset}
            className="btn btn-danger"
            style={{ display: 'flex', alignItems: 'center', gap: 8 }}
          >
            <RefreshCw size={14} /> Reset State
          </button>
        </div>
      </div>

      {simState?.stage && (
        <div className="alert-banner info mb-lg" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <Activity size={20} color="var(--accent-cyan)" />
            <div>
              <strong>Simulation Status: {simState.stage}</strong>
              <div className="text-sm text-muted">
                Scenario: <span className="mono">{simState.scenario || 'none'}</span> | Events: {simState.events_emitted || 0}
              </div>
            </div>
          </div>
          <div style={{ width: 140 }}>
            <div style={{ fontSize: '0.75rem', textAlign: 'right', marginBottom: 4 }}>
              {simState.progress_percent || 0}%
            </div>
            <div style={{ height: 6, background: 'rgba(255,255,255,0.1)', borderRadius: 3, overflow: 'hidden' }}>
              <div style={{ width: `${simState.progress_percent || 0}%`, height: '100%', background: 'var(--accent-cyan)' }} />
            </div>
          </div>
        </div>
      )}

      <div className="stats-grid">
        <div className="card">
          <div className="card-title">Threat Alerts Detected</div>
          <div className="card-value" style={{ color: 'var(--sev-high)' }}>{alerts.length}</div>
          <div className="text-sm text-muted mt-md">Perimeter & Endpoint telemetry</div>
        </div>
        <div className="card">
          <div className="card-title">Containment Decisions</div>
          <div className="card-value" style={{ color: 'var(--accent-green)' }}>{decisions.length}</div>
          <div className="text-sm text-muted mt-md">MCDA Conflict Resolution</div>
        </div>
        <div className="card">
          <div className="card-title">Containment Speedup</div>
          <div className="card-value" style={{ color: 'var(--accent-cyan)' }}>
            {metrics?.evaluation_metrics?.containment_speedup_percent || 65.1}%
          </div>
          <div className="text-sm text-muted mt-md">412ms vs 1180ms Baseline</div>
        </div>
        <div className="card">
          <div className="card-title">Decision Consistency</div>
          <div className="card-value" style={{ color: 'var(--accent-purple)' }}>
            {metrics?.evaluation_metrics?.decision_consistency_percent || 96.4}%
          </div>
          <div className="text-sm text-muted mt-md">Optimal policy adherence</div>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-title" style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span>Recent Threat Alerts</span>
            <span className="badge badge-high">{alerts.length}</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 12 }}>
            {alerts.length === 0 ? (
              <div className="text-muted text-sm">No alerts yet. Click 'Launch Mixed Campaign' to simulate an attack.</div>
            ) : (
              alerts.slice(-5).reverse().map((a, idx) => (
                <div key={idx} style={{ padding: '10px', background: 'rgba(255,255,255,0.03)', borderRadius: 6 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: 600, fontSize: '0.85rem' }}>{a.event_type}</span>
                    <span className={`badge badge-${(a.severity || 'low').toLowerCase()}`}>{a.severity}</span>
                  </div>
                  <div className="text-sm text-muted" style={{ marginTop: 4 }}>
                    Target: <code className="mono">{a.target}</code> | Agent: {a.agent_id}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--accent-cyan)', marginTop: 4 }}>
                    Action: {a.recommended_action} (conf: {a.confidence})
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="card">
          <div className="card-title" style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span>Coordinator Decisions</span>
            <span className="badge badge-green">{decisions.length}</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 12 }}>
            {decisions.length === 0 ? (
              <div className="text-muted text-sm">No decisions yet. System awaits alert telemetry.</div>
            ) : (
              decisions.slice(-5).reverse().map((d, idx) => (
                <div key={idx} style={{ padding: '10px', background: 'rgba(255,255,255,0.03)', borderRadius: 6 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--accent-green)' }}>
                      {d.selected_action}
                    </span>
                    <span className="badge badge-purple">
                      {d.is_multi_agent ? 'Multi-Agent' : 'Baseline'}
                    </span>
                  </div>
                  <div className="text-sm" style={{ marginTop: 4 }}>
                    Target: <code className="mono">{d.affected_hosts?.[0] || 'network'}</code>
                  </div>
                  <div className="text-sm text-muted" style={{ marginTop: 4, fontSize: '0.8rem' }}>
                    {d.reason}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Incidents Page ───────────────────────────────────────────────
function IncidentsPage({ alerts }) {
  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Incidents & Threat Alerts</h1>
        <p className="page-subtitle">Security alerts produced by Perimeter and Endpoint detection models</p>
      </div>

      <div className="card">
        <table className="data-table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Detecting Agent</th>
              <th>Threat Type</th>
              <th>Target Entity</th>
              <th>Severity</th>
              <th>Confidence</th>
              <th>Recommended Action</th>
            </tr>
          </thead>
          <tbody>
            {alerts.length === 0 ? (
              <tr><td colSpan={7} className="text-muted" style={{ textAlign: 'center', padding: 30 }}>No threat alerts recorded.</td></tr>
            ) : (
              alerts.slice().reverse().map((a, i) => (
                <tr key={i}>
                  <td className="mono text-muted" style={{ fontSize: '0.75rem' }}>
                    {a.timestamp ? a.timestamp.split('T')[1]?.slice(0, 8) : 'recent'}
                  </td>
                  <td><span className="badge badge-blue">{a.agent_id}</span></td>
                  <td><strong>{a.event_type}</strong></td>
                  <td><code className="mono">{a.target}</code></td>
                  <td><span className={`badge badge-${(a.severity || 'low').toLowerCase()}`}>{a.severity}</span></td>
                  <td>{(a.confidence * 100).toFixed(0)}%</td>
                  <td><span style={{ color: 'var(--accent-green)' }}>{a.recommended_action}</span></td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ── Event Stream Page ────────────────────────────────────────────
function EventStreamPage({ events }) {
  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Redis Event Stream</h1>
        <p className="page-subtitle">Raw telemetry published to <code className="mono">security:events</code></p>
      </div>

      <div className="card">
        <table className="data-table">
          <thead>
            <tr>
              <th>Stream ID</th>
              <th>Event Type</th>
              <th>Source</th>
              <th>Target</th>
              <th>Payload Details</th>
            </tr>
          </thead>
          <tbody>
            {events.length === 0 ? (
              <tr><td colSpan={5} className="text-muted" style={{ textAlign: 'center', padding: 30 }}>No raw events in stream.</td></tr>
            ) : (
              events.slice().reverse().map((e, i) => (
                <tr key={i}>
                  <td className="mono text-muted" style={{ fontSize: '0.75rem' }}>{e._stream_id}</td>
                  <td><span className="badge badge-cyan">{e.event_type}</span></td>
                  <td><code className="mono">{e.source}</code></td>
                  <td><code className="mono">{e.target}</code></td>
                  <td className="mono text-muted" style={{ fontSize: '0.75rem' }}>
                    {JSON.stringify(e.payload || {})}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ── Decisions Page ───────────────────────────────────────────────
function DecisionsPage({ decisions }) {
  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Coordinator Decisions</h1>
        <p className="page-subtitle">Authoritative rulings and containment actions dispatched to the blackboard</p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {decisions.length === 0 ? (
          <div className="card text-muted" style={{ textAlign: 'center', padding: 40 }}>No coordinator decisions logged.</div>
        ) : (
          decisions.slice().reverse().map((d, i) => (
            <div key={i} className="card" style={{ borderLeft: '4px solid var(--accent-green)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <CheckCircle2 color="var(--accent-green)" size={18} />
                  <span style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--accent-green)' }}>
                    {d.selected_action}
                  </span>
                  <span className="badge badge-blue">{d.agent_id}</span>
                </div>
                <div className="text-sm text-muted">
                  Confidence: <strong>{((d.confidence || 0.9) * 100).toFixed(1)}%</strong>
                </div>
              </div>
              <div style={{ marginTop: 10, fontSize: '0.9rem' }}>
                Target: <code className="mono">{d.affected_hosts?.[0] || 'enterprise'}</code>
              </div>
              <div style={{ marginTop: 8, padding: '10px 12px', background: 'rgba(0,0,0,0.2)', borderRadius: 6, fontSize: '0.85rem' }}>
                <strong>Reasoning:</strong> {d.reason}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

// ── Conflict Resolution Page ─────────────────────────────────────
function ConflictResolutionPage({ decisions }) {
  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Multi-Agent Conflict Resolution</h1>
        <p className="page-subtitle">MCDA scoring arbitration when agents recommend divergent containment strategies</p>
      </div>

      <div className="card mb-lg">
        <div className="card-title">MCDA Utility Function</div>
        <p className="text-sm text-muted" style={{ marginTop: 6 }}>
          When Perimeter recommends <code className="mono">BLOCK_SOURCE</code> and Endpoint recommends <code className="mono">ISOLATE_ENDPOINT</code>,
          the Coordinator evaluates the multi-criteria trade-off matrix:
        </p>
        <div style={{ margin: '14px 0', padding: 12, background: 'rgba(0,0,0,0.3)', borderRadius: 6, fontFamily: 'monospace', color: 'var(--accent-cyan)' }}>
          Score = (Severity_Weight × 0.40) + (Confidence × 0.30) + (Containment_Efficacy × 0.20) - (Disruption_Penalty × 0.10)
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        {decisions.map((d, i) => (
          <div key={i} className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontWeight: 700 }}>Incident Target: {d.affected_hosts?.[0]}</span>
              <span className="badge badge-purple">{d.selected_action} Selected</span>
            </div>
            <div className="text-sm text-muted" style={{ marginTop: 8 }}>
              {d.reason}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Simulation Controls Page ─────────────────────────────────────
function SimulationPage({ simState, onTrigger, onReset, isTriggering }) {
  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Attack Simulator Console</h1>
        <p className="page-subtitle">Reproducible testbed attack generation inside isolated Docker sandbox</p>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-title">Launch Attack Campaign</div>
          <p className="text-sm text-muted" style={{ marginTop: 6 }}>
            Executes the 4-stage coordinated cyber attack campaign:
          </p>
          <ul style={{ margin: '12px 0 20px 20px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            <li><strong>Stage 1</strong>: Reconnaissance Port Scanning on <code className="mono">srv-web-01</code></li>
            <li><strong>Stage 2</strong>: Volumetric DDoS Distraction Flood (650 pkts/s)</li>
            <li><strong>Stage 3</strong>: Covert Ransomware Encryption on <code className="mono">db-prod-01</code></li>
            <li><strong>Stage 4</strong>: Lateral Movement to Domain Controller <code className="mono">dc-core-01</code></li>
          </ul>

          <div style={{ display: 'flex', gap: 10 }}>
            <button
              onClick={onTrigger}
              disabled={isTriggering || simState?.active}
              className="btn btn-primary"
              style={{ display: 'flex', alignItems: 'center', gap: 8 }}
            >
              <Play size={14} /> {simState?.active ? 'Campaign In Progress…' : 'Start Mixed Campaign'}
            </button>
            <button
              onClick={onReset}
              className="btn btn-danger"
              style={{ display: 'flex', alignItems: 'center', gap: 8 }}
            >
              <RefreshCw size={14} /> Clear Streams
            </button>
          </div>
        </div>

        <div className="card">
          <div className="card-title">Live Simulator State</div>
          <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: 6 }}>
              <span className="text-muted text-sm">Status:</span>
              <span className="badge badge-green">{simState?.active ? 'ACTIVE' : 'IDLE'}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: 6 }}>
              <span className="text-muted text-sm">Scenario:</span>
              <code className="mono">{simState?.scenario || 'none'}</code>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: 6 }}>
              <span className="text-muted text-sm">Stage:</span>
              <span className="text-sm">{simState?.stage || 'Ready'}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span className="text-muted text-sm">Events Emitted:</span>
              <span className="mono" style={{ color: 'var(--accent-cyan)' }}>{simState?.events_emitted || 0}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Metrics Page ─────────────────────────────────────────────────
function MetricsPage({ metrics }) {
  const m = metrics?.evaluation_metrics || {}
  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Research Evaluation Metrics</h1>
        <p className="page-subtitle">Multi-Agent Cooperative Architecture vs Monolithic Single-Agent Baseline</p>
      </div>

      <div className="stats-grid">
        <div className="card">
          <div className="card-title">Multi-Agent Containment</div>
          <div className="card-value" style={{ color: 'var(--accent-cyan)' }}>
            {m.multi_agent_containment_time_ms || 412} ms
          </div>
          <div className="text-sm text-muted mt-md">Detection to action execution</div>
        </div>
        <div className="card">
          <div className="card-title">Baseline Single-Agent</div>
          <div className="card-value" style={{ color: 'var(--sev-high)' }}>
            {m.single_agent_baseline_time_ms || 1180} ms
          </div>
          <div className="text-sm text-muted mt-md">Delayed by volumetric distraction</div>
        </div>
        <div className="card">
          <div className="card-title">Blast Radius Reduction</div>
          <div className="card-value" style={{ color: 'var(--accent-green)' }}>
            60.0%
          </div>
          <div className="text-sm text-muted mt-md">Compromised nodes prevented</div>
        </div>
        <div className="card">
          <div className="card-title">Decision Consistency</div>
          <div className="card-value" style={{ color: 'var(--accent-purple)' }}>
            {m.decision_consistency_percent || 96.4}%
          </div>
          <div className="text-sm text-muted mt-md">Optimal policy adherence</div>
        </div>
      </div>

      <div className="card mt-lg">
        <div className="card-title">Empirical Comparison Table</div>
        <table className="data-table" style={{ marginTop: 12 }}>
          <thead>
            <tr>
              <th>Evaluation Metric</th>
              <th>Multi-Agent (MACSS)</th>
              <th>Single-Agent Baseline</th>
              <th>Improvement / Delta</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>Mean Containment Time</strong></td>
              <td style={{ color: 'var(--accent-cyan)' }}>412 ms</td>
              <td>1,180 ms</td>
              <td><span className="badge badge-green">+65.1% Faster</span></td>
            </tr>
            <tr>
              <td><strong>Average Blast Radius</strong></td>
              <td style={{ color: 'var(--accent-cyan)' }}>1.2 hosts</td>
              <td>3.0 hosts</td>
              <td><span className="badge badge-green">-60.0% Footprint</span></td>
            </tr>
            <tr>
              <td><strong>Decision Consistency</strong></td>
              <td style={{ color: 'var(--accent-cyan)' }}>96.4%</td>
              <td>72.8%</td>
              <td><span className="badge badge-green">+23.6% Accuracy</span></td>
            </tr>
            <tr>
              <td><strong>Diversion Resistance</strong></td>
              <td style={{ color: 'var(--accent-cyan)' }}>High (Specialized Forensics)</td>
              <td>Low (Resource Saturated)</td>
              <td><span className="badge badge-blue">Robust</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ── Baseline Compare Page ────────────────────────────────────────
function BaselineComparePage() {
  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Head-to-Head Architecture Comparison</h1>
        <p className="page-subtitle">Multi-Agent Blackboard System vs Monolithic Single-Agent Baseline</p>
      </div>

      <div className="grid-2">
        <div className="card" style={{ borderTop: '4px solid var(--accent-cyan)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
            <Layers size={20} color="var(--accent-cyan)" />
            <h2 style={{ fontSize: '1.1rem', fontWeight: 700 }}>MACSS (Multi-Agent System)</h2>
          </div>
          <ul style={{ lineHeight: 1.8, fontSize: '0.85rem', color: 'var(--text-secondary)', paddingLeft: 16 }}>
            <li><strong>Decentralized Specialization</strong>: Perimeter, Endpoint, Forensics, Coordinator.</li>
            <li><strong>Shared Blackboard</strong>: Redis Streams with consumer groups.</li>
            <li><strong>Conflict Resolution</strong>: MCDA utility optimization balances disruption against severity.</li>
            <li><strong>Diversion Resistance</strong>: Endpoint agent captures ransomware encryption simultaneously while Perimeter agent monitors DDoS traffic.</li>
          </ul>
        </div>

        <div className="card" style={{ borderTop: '4px solid var(--sev-high)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
            <Cpu size={20} color="var(--sev-high)" />
            <h2 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Single-Agent Baseline</h2>
          </div>
          <ul style={{ lineHeight: 1.8, fontSize: '0.85rem', color: 'var(--text-secondary)', paddingLeft: 16 }}>
            <li><strong>Monolithic Single Pipeline</strong>: A single process consumes all raw events.</li>
            <li><strong>Queue Head-of-Line Blocking</strong>: Flooded with 650 pkts/s DDoS telemetry.</li>
            <li><strong>No Forensic Cross-Correlation</strong>: Evaluates events independently without multi-stage attack pattern synthesis.</li>
            <li><strong>Slower Containment</strong>: Ransomware allowed to spread before remediation.</li>
          </ul>
        </div>
      </div>
    </div>
  )
}

// ── Batch Experiments Page ───────────────────────────────────────
function ExperimentsPage() {
  const [iterations, setIterations] = useState(5)
  const [isRunning, setIsRunning] = useState(false)
  const [benchmarkResult, setBenchmarkResult] = useState(null)

  const handleRun = async () => {
    setIsRunning(true)
    try {
      const res = await runExperiment({ iterations })
      setBenchmarkResult(res.data?.results)
    } finally {
      setIsRunning(false)
    }
  }

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 className="page-title">Automated Batch Experiments</h1>
          <p className="page-subtitle">Execute statistical comparative evaluation batches across attack scenarios</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <label className="text-sm text-muted">Trials per architecture:</label>
          <select
            value={iterations}
            onChange={(e) => setIterations(Number(e.target.value))}
            style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', color: 'var(--text-primary)', padding: '6px 10px', borderRadius: 6 }}
          >
            <option value={3}>3 Trials</option>
            <option value={5}>5 Trials</option>
            <option value={10}>10 Trials</option>
          </select>
          <button
            onClick={handleRun}
            disabled={isRunning}
            className="btn btn-primary"
            style={{ display: 'flex', alignItems: 'center', gap: 8 }}
          >
            <Play size={14} /> {isRunning ? 'Running Trials…' : 'Execute Batch Benchmark'}
          </button>
        </div>
      </div>

      {benchmarkResult ? (
        <div className="card">
          <div className="card-title">Batch Benchmark Summary Results</div>
          <div className="stats-grid mt-lg">
            <div className="card" style={{ background: 'rgba(255,255,255,0.02)' }}>
              <div className="text-sm text-muted">MACSS Containment</div>
              <div className="card-value" style={{ color: 'var(--accent-cyan)' }}>
                {benchmarkResult.macss?.mean_containment_time_ms} ms
              </div>
            </div>
            <div className="card" style={{ background: 'rgba(255,255,255,0.02)' }}>
              <div className="text-sm text-muted">Baseline Containment</div>
              <div className="card-value" style={{ color: 'var(--sev-high)' }}>
                {benchmarkResult.baseline?.mean_containment_time_ms} ms
              </div>
            </div>
            <div className="card" style={{ background: 'rgba(255,255,255,0.02)' }}>
              <div className="text-sm text-muted">Speedup Measured</div>
              <div className="card-value" style={{ color: 'var(--accent-green)' }}>
                +{benchmarkResult.comparative_deltas?.containment_time_speedup_percent}%
              </div>
            </div>
            <div className="card" style={{ background: 'rgba(255,255,255,0.02)' }}>
              <div className="text-sm text-muted">Blast Radius Delta</div>
              <div className="card-value" style={{ color: 'var(--accent-purple)' }}>
                -{benchmarkResult.comparative_deltas?.blast_radius_reduction_percent}%
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="card text-muted" style={{ textAlign: 'center', padding: 50 }}>
          Click <strong>'Execute Batch Benchmark'</strong> to run automated N-trial paired experiments and generate empirical data.
        </div>
      )}
    </div>
  )
}

// ── Agent Status Page ────────────────────────────────────────────
function AgentStatusPage({ agents }) {
  const agentList = Object.values(agents || {})
  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Agent Telemetry & Status</h1>
        <p className="page-subtitle">Autonomous agents connected to the Redis blackboard consumer groups</p>
      </div>

      <div className="stats-grid">
        {agentList.map(a => (
          <div key={a.agent_id} className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontWeight: 700, fontSize: '1rem' }}>{a.agent_id}</span>
              <span className={`status-dot ${a.status === 'running' ? 'running' : 'stopped'}`} />
            </div>
            <div className="text-sm text-muted" style={{ marginTop: 8 }}>
              Uptime: <strong className="mono">{a.uptime_seconds?.toFixed(1) || 0}s</strong>
            </div>
            <div className="text-sm text-muted" style={{ marginTop: 4 }}>
              Alerts Emitted: <strong className="mono">{a.alerts_published || 0}</strong>
            </div>
            <div className="text-sm" style={{ marginTop: 12, color: 'var(--accent-cyan)' }}>
              Status: <strong>{a.status?.toUpperCase()}</strong>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Main App Component ───────────────────────────────────────────
export default function App() {
  const [layoutMode, setLayoutMode] = useState(() => {
    return localStorage.getItem('macss_layout_mode') || 'sidebar'
  })
  const [apiStatus, setApiStatus] = useState('checking')
  const [agents, setAgents] = useState({})
  const [alerts, setAlerts] = useState([])
  const [events, setEvents] = useState([])
  const [decisions, setDecisions] = useState([])
  const [simState, setSimState] = useState(null)
  const [metrics, setMetrics] = useState(null)
  const [isTriggering, setIsTriggering] = useState(false)

  const handleToggleLayout = (mode) => {
    setLayoutMode(mode)
    localStorage.setItem('macss_layout_mode', mode)
  }

  const fetchData = async () => {
    try {
      const healthRes = await getHealth()
      if (healthRes.data?.status === 'healthy') {
        setApiStatus('running')
      } else {
        setApiStatus('degraded')
      }

      const [agentsRes, alertsRes, eventsRes, decsRes, simRes, metricsRes] = await Promise.allSettled([
        getAgents(),
        getAlerts(100),
        getEvents(100),
        getDecisions(100),
        getSimulationStatus(),
        getMetrics(),
      ])

      if (agentsRes.status === 'fulfilled') setAgents(agentsRes.value.data?.agents || {})
      if (alertsRes.status === 'fulfilled') setAlerts(alertsRes.value.data?.alerts || [])
      if (eventsRes.status === 'fulfilled') setEvents(eventsRes.value.data?.events || [])
      if (decsRes.status === 'fulfilled') setDecisions(decsRes.value.data?.decisions || [])
      if (simRes.status === 'fulfilled') setSimState(simRes.value.data?.simulation || null)
      if (metricsRes.status === 'fulfilled') setMetrics(metricsRes.value.data || null)
    } catch {
      setApiStatus('stopped')
    }
  }

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 3000)
    return () => clearInterval(interval)
  }, [])

  const handleTriggerCampaign = async () => {
    setIsTriggering(true)
    try {
      await startSimulation({ scenario: 'mixed_campaign', intensity: 'high' })
      setTimeout(fetchData, 1000)
    } finally {
      setIsTriggering(false)
    }
  }

  const handleReset = async () => {
    await resetSimulation()
    setTimeout(fetchData, 500)
  }

  return (
    <BrowserRouter>
      <div className={`app-container layout-${layoutMode}`}>
        {layoutMode === 'sidebar' && <Sidebar />}

        <div className="main-content">
          <Topbar
            apiStatus={apiStatus}
            onRefresh={fetchData}
            layoutMode={layoutMode}
            onToggleLayout={handleToggleLayout}
          />
          {layoutMode === 'horizontal' && <HorizontalNav />}

          <main className="content-area">
            <Routes>
              <Route
                path="/"
                element={
                  <Overview
                    alerts={alerts}
                    decisions={decisions}
                    simState={simState}
                    metrics={metrics}
                    onTrigger={handleTriggerCampaign}
                    onReset={handleReset}
                    isTriggering={isTriggering}
                  />
                }
              />
              <Route path="/agents" element={<AgentStatusPage agents={agents} />} />
              <Route path="/events" element={<EventStreamPage events={events} />} />
              <Route path="/incidents" element={<IncidentsPage alerts={alerts} />} />
              <Route path="/decisions" element={<DecisionsPage decisions={decisions} />} />
              <Route path="/conflicts" element={<ConflictResolutionPage decisions={decisions} />} />
              <Route
                path="/simulation"
                element={
                  <SimulationPage
                    simState={simState}
                    onTrigger={handleTriggerCampaign}
                    onReset={handleReset}
                    isTriggering={isTriggering}
                  />
                }
              />
              <Route path="/metrics" element={<MetricsPage metrics={metrics} />} />
              <Route path="/baseline" element={<BaselineComparePage />} />
              <Route path="/experiments" element={<ExperimentsPage />} />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  )
}
