import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';

export default function EquityCurve({ data, analytics }) {
  return (
    <div className="equity-curve">
      <h3>Equity Curve & Analytics</h3>

      {analytics && (
        <div className="analytics-cards">
          <div className="card">
            <span className="label">Total Trades</span>
            <span className="value">{analytics.total_trades}</span>
          </div>
          <div className="card">
            <span className="label">Win Rate</span>
            <span className={`value ${analytics.win_rate >= 50 ? 'positive' : 'negative'}`}>
              {analytics.win_rate}%
            </span>
          </div>
          <div className="card">
            <span className="label">Total P&L</span>
            <span className={`value ${analytics.total_pnl >= 0 ? 'positive' : 'negative'}`}>
              ${analytics.total_pnl?.toFixed(2)}
            </span>
          </div>
          <div className="card">
            <span className="label">Profit Factor</span>
            <span className="value">{analytics.profit_factor?.toFixed(2)}</span>
          </div>
          <div className="card">
            <span className="label">Avg P&L</span>
            <span className={`value ${analytics.avg_pnl >= 0 ? 'positive' : 'negative'}`}>
              ${analytics.avg_pnl?.toFixed(2)}
            </span>
          </div>
          <div className="card">
            <span className="label">Max Win</span>
            <span className="value positive">${analytics.max_win?.toFixed(2)}</span>
          </div>
          <div className="card">
            <span className="label">Max Loss</span>
            <span className="value negative">${analytics.max_loss?.toFixed(2)}</span>
          </div>
          <div className="card">
            <span className="label">W/L</span>
            <span className="value">{analytics.wins}/{analytics.losses}</span>
          </div>
        </div>
      )}

      {data.length > 0 ? (
        <div className="chart-container">
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1a2332" />
              <XAxis dataKey="timestamp" tick={{ fontSize: 10, fill: '#6b7280' }} />
              <YAxis tick={{ fontSize: 10, fill: '#6b7280' }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1a2332', border: '1px solid #2d3748', borderRadius: '8px' }}
                labelStyle={{ color: '#9ca3af' }}
              />
              <Area type="monotone" dataKey="equity" stroke="#3b82f6" fill="rgba(59, 130, 246, 0.1)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <div className="no-data">
          <p>No trade data yet. Equity curve will appear after trades are recorded.</p>
          <div className="placeholder-chart">
            <svg viewBox="0 0 400 150" className="placeholder-svg">
              <polyline
                fill="none"
                stroke="#3b82f6"
                strokeWidth="2"
                points="0,100 50,90 100,95 150,70 200,60 250,50 300,45 350,30 400,20"
              />
              <text x="200" y="130" textAnchor="middle" fill="#6b7280" fontSize="12">
                Sample equity curve
              </text>
            </svg>
          </div>
        </div>
      )}
    </div>
  );
}
