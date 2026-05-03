import { useState } from 'react';

export default function TopBar({ status }) {
  if (!status) return <div className="top-bar loading">Loading system...</div>;

  const isLive = status.status === 'LIVE';
  const regimeColors = {
    TRENDING: '#3b82f6',
    RANGING: '#f59e0b',
    VOLATILE: '#ef4444',
    UNKNOWN: '#6b7280',
  };

  const sourceIcons = {
    connected: '●',
    streaming: '●',
    disconnected: '○',
    simulated: '◐',
    no_keys: '◐',
    unavailable: '○',
    error: '✕',
  };

  const sourceColors = {
    connected: '#22c55e',
    streaming: '#22c55e',
    disconnected: '#ef4444',
    simulated: '#f59e0b',
    no_keys: '#f59e0b',
    unavailable: '#6b7280',
    error: '#ef4444',
  };

  return (
    <div className="top-bar">
      <div className="top-bar-section">
        <div className="system-status">
          <span className={`status-dot ${isLive ? 'live' : 'paused'}`}></span>
          <span className="status-text">{status.status}</span>
        </div>
      </div>

      <div className="top-bar-section">
        <div className="balance-info">
          <span className="label">Balance</span>
          <span className="value">${status.balance?.toLocaleString()}</span>
        </div>
        <div className="equity-mini">
          <span className="label">Equity</span>
          <span className="value">${status.equity?.toLocaleString()}</span>
        </div>
      </div>

      <div className="top-bar-section">
        <div className="regime-badge" style={{ backgroundColor: regimeColors[status.market_regime] || '#6b7280' }}>
          {status.market_regime}
        </div>
      </div>

      <div className="top-bar-section">
        <span className="session-label">Session: <strong>{status.active_session}</strong></span>
      </div>

      <div className="top-bar-section">
        <div className="data-sources">
          {Object.entries(status.data_sources || {}).map(([name, stat]) => (
            <span key={name} className="source" title={`${name}: ${stat}`}>
              <span style={{ color: sourceColors[stat] || '#6b7280' }}>{sourceIcons[stat] || '○'}</span>
              {name}
            </span>
          ))}
        </div>
      </div>

      <div className="top-bar-section">
        <span className="strategies-count">
          {status.active_strategies}/{status.total_strategies} strategies
        </span>
      </div>
    </div>
  );
}
