export default function AIDecisionPanel({ signal }) {
  if (!signal) {
    return (
      <div className="ai-decision">
        <h3>AI Decision Panel</h3>
        <div className="no-signal">Analyzing market...</div>
      </div>
    );
  }

  const signalType = signal.signal || 'NONE';
  const signalClass = signalType === 'BUY' ? 'buy' : signalType === 'SELL' ? 'sell' : 'none';

  const familyScores = signal.family_scores || {};
  const topStrategies = signal.top_strategies || [];

  return (
    <div className="ai-decision">
      <h3>AI Decision Panel</h3>

      <div className={`signal-box ${signalClass}`}>
        <div className="signal-header">
          <span className="signal-icon">{signalType === 'BUY' ? '🚀' : signalType === 'SELL' ? '📉' : '⏸️'}</span>
          <span className="signal-type">SIGNAL: {signalType}</span>
        </div>
        <div className="signal-details">
          <div className="detail-row">
            <span>Confidence</span>
            <span className="value">{((signal.confidence || 0) * 100).toFixed(0)}%</span>
          </div>
          <div className="detail-row">
            <span>Score</span>
            <span className="value">{signal.score?.toFixed(1) || '0.0'}</span>
          </div>
          <div className="detail-row">
            <span>Entry</span>
            <span className="value">{signal.entry_price?.toFixed(5)}</span>
          </div>
          <div className="detail-row">
            <span>Stop Loss</span>
            <span className="value stop">{signal.stop_loss?.toFixed(5)}</span>
          </div>
          <div className="detail-row">
            <span>Take Profit</span>
            <span className="value profit">{signal.take_profit?.toFixed(5)}</span>
          </div>
          <div className="detail-row">
            <span>R:R</span>
            <span className="value">1:{signal.risk_reward?.toFixed(1)}</span>
          </div>
        </div>
      </div>

      <div className="voting-breakdown">
        <h4>Strategy Voting Breakdown</h4>
        {Object.entries(familyScores).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1])).map(([family, score]) => (
          <div key={family} className="family-vote">
            <span className="family-name">{family.replace(/_/g, ' ')}</span>
            <div className="vote-bar-container">
              <div
                className={`vote-bar ${score > 0 ? 'positive' : 'negative'}`}
                style={{ width: `${Math.min(Math.abs(score) * 15, 100)}%` }}
              ></div>
            </div>
            <span className={`vote-score ${score > 0 ? 'positive' : 'negative'}`}>
              {score > 0 ? '+' : ''}{score.toFixed(1)}
            </span>
          </div>
        ))}
        <div className="total-score">
          Final Score: <strong>{signal.score?.toFixed(1)}</strong> → <strong>{signalType}</strong>
        </div>
      </div>

      <div className="top-contributors">
        <h4>Top Contributing Strategies</h4>
        {topStrategies.slice(0, 5).map((s, i) => (
          <div key={i} className="contributor">
            <span className="name">{s.name}</span>
            <span className={`confidence ${s.signal === 'BUY' ? 'positive' : s.signal === 'SELL' ? 'negative' : ''}`}>
              {s.confidence?.toFixed(2)}
            </span>
          </div>
        ))}
      </div>

      <div className="why-trade">
        <button className="why-button" onClick={() => {
          const reasons = topStrategies.slice(0, 3).map(s => `${s.name}: ${s.reasoning}`).join('\n');
          alert(`Why this trade?\n\n${reasons}\n\nRegime: ${signal.regime || 'N/A'}\nActive: ${signal.active_strategies} strategies\nAgreeing: ${signal.agreeing_strategies} strategies`);
        }}>
          🔥 Why this trade?
        </button>
      </div>
    </div>
  );
}
