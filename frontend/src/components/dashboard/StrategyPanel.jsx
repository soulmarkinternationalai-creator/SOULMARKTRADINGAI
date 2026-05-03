import { useState } from 'react';

const FAMILY_COLORS = {
  TREND: '#3b82f6',
  MEAN_REVERSION: '#8b5cf6',
  BREAKOUT: '#f59e0b',
  MOMENTUM: '#ef4444',
  SMART_MONEY: '#6366f1',
  VOLATILITY: '#1f2937',
  AI_DRIVEN: '#f97316',
};

export default function StrategyPanel({ strategies, onToggle }) {
  const [filter, setFilter] = useState('ALL');
  const [sortBy, setSortBy] = useState('name');

  const families = ['ALL', ...new Set(strategies.map(s => s.family))];

  const filtered = strategies
    .filter(s => filter === 'ALL' || s.family === filter)
    .sort((a, b) => {
      if (sortBy === 'win_rate') return b.win_rate - a.win_rate;
      if (sortBy === 'profit') return b.total_profit - a.total_profit;
      if (sortBy === 'trades') return b.total_trades - a.total_trades;
      return a.name.localeCompare(b.name);
    });

  return (
    <div className="strategy-panel">
      <h3>Strategy Performance ({strategies.length} strategies)</h3>

      <div className="strategy-controls">
        <div className="filter-buttons">
          {families.map(f => (
            <button key={f} className={filter === f ? 'active' : ''} onClick={() => setFilter(f)}
              style={f !== 'ALL' ? { borderColor: FAMILY_COLORS[f] } : {}}>
              {f.replace(/_/g, ' ')}
            </button>
          ))}
        </div>
        <div className="sort-controls">
          <span>Sort:</span>
          <select value={sortBy} onChange={e => setSortBy(e.target.value)}>
            <option value="name">Name</option>
            <option value="win_rate">Win Rate</option>
            <option value="profit">Profit</option>
            <option value="trades">Trades</option>
          </select>
        </div>
      </div>

      <div className="strategy-table">
        <div className="table-header">
          <span>Strategy</span>
          <span>Family</span>
          <span>Win Rate</span>
          <span>Profit</span>
          <span>Trades</span>
          <span>Weight</span>
          <span>Status</span>
        </div>
        {filtered.map(s => (
          <div key={s.name} className={`table-row ${!s.is_active ? 'disabled' : ''}`}>
            <span className="strategy-name">{s.name}</span>
            <span className="family-tag" style={{ color: FAMILY_COLORS[s.family] }}>
              {s.family.replace(/_/g, ' ')}
            </span>
            <span className={`win-rate ${s.win_rate >= 50 ? 'good' : s.win_rate >= 40 ? 'ok' : 'bad'}`}>
              {s.win_rate}%
            </span>
            <span className={`profit ${s.total_profit >= 0 ? 'positive' : 'negative'}`}>
              {s.total_profit >= 0 ? '+' : ''}{s.total_profit.toFixed(2)}
            </span>
            <span>{s.total_trades}</span>
            <span>{s.weight}</span>
            <span>
              <button
                className={`toggle-btn ${s.is_active ? 'active' : 'inactive'}`}
                onClick={() => onToggle(s.name, !s.is_active)}
              >
                {s.is_active ? 'Active' : 'Disabled'}
              </button>
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
