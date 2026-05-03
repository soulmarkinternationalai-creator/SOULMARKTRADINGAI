import { useState } from 'react';

export default function RiskPanel({ risk, onToggleAutoTrade }) {
  const [autoTrade, setAutoTrade] = useState(false);

  if (!risk) return <div className="risk-panel-content"><h3>Risk & Execution</h3><p>Loading...</p></div>;

  const ddPct = risk.daily_drawdown_pct || 0;
  const maxDD = risk.max_daily_drawdown_pct || 5;
  const ddRatio = Math.min(ddPct / maxDD, 1);

  return (
    <div className="risk-panel-content">
      <h3>Risk & Execution</h3>

      <div className="risk-metrics">
        <div className="metric">
          <span className="label">Risk/Trade</span>
          <span className="value">{risk.risk_per_trade_pct}%</span>
        </div>
        <div className="metric">
          <span className="label">Balance</span>
          <span className="value">${risk.balance?.toLocaleString()}</span>
        </div>
        <div className="metric">
          <span className="label">Daily P&L</span>
          <span className={`value ${risk.daily_pnl >= 0 ? 'positive' : 'negative'}`}>
            ${risk.daily_pnl?.toFixed(2)}
          </span>
        </div>
        <div className="metric">
          <span className="label">Open Trades</span>
          <span className="value">{risk.open_trades}/{risk.max_open_trades}</span>
        </div>
      </div>

      <div className="drawdown-meter">
        <span className="label">Daily Drawdown: {ddPct.toFixed(1)}% / {maxDD}%</span>
        <div className="meter-bar">
          <div
            className={`meter-fill ${ddRatio > 0.8 ? 'danger' : ddRatio > 0.5 ? 'warning' : 'safe'}`}
            style={{ width: `${ddRatio * 100}%` }}
          ></div>
        </div>
      </div>

      <div className="trade-controls">
        <div className="auto-trade-toggle">
          <span>Auto Trading</span>
          <button
            className={`toggle-switch ${autoTrade ? 'on' : 'off'}`}
            onClick={() => {
              const newState = !autoTrade;
              setAutoTrade(newState);
              onToggleAutoTrade(newState);
            }}
          >
            {autoTrade ? 'ON' : 'OFF'}
          </button>
        </div>
      </div>
    </div>
  );
}
