const FAMILIES = ['TREND', 'BREAKOUT', 'MOMENTUM', 'MEAN_REVERSION', 'SMART_MONEY', 'VOLATILITY', 'AI_DRIVEN'];

const FAMILY_LABELS = {
  TREND: 'Trend',
  BREAKOUT: 'Breakout',
  MOMENTUM: 'Momentum',
  MEAN_REVERSION: 'Mean Rev.',
  SMART_MONEY: 'Smart Money',
  VOLATILITY: 'Volatility',
  AI_DRIVEN: 'AI Driven',
};

export default function StrategyHeatmap({ signal }) {
  const familyScores = signal?.family_scores || {};

  const maxScore = Math.max(...Object.values(familyScores).map(Math.abs), 1);

  return (
    <div className="strategy-heatmap">
      <h3>Strategy Heatmap</h3>
      <div className="heatmap-bars">
        {FAMILIES.map(family => {
          const score = familyScores[family] || 0;
          const pct = Math.abs(score) / maxScore * 100;
          const blocks = Math.round(pct / 10);

          return (
            <div key={family} className="heatmap-row">
              <span className="family-label">{FAMILY_LABELS[family]}</span>
              <div className="bar-visual">
                {Array.from({ length: 10 }, (_, i) => (
                  <span
                    key={i}
                    className={`block ${i < blocks ? (score > 0 ? 'positive' : 'negative') : 'empty'}`}
                  >
                    █
                  </span>
                ))}
              </div>
              <span className={`score ${score > 0 ? 'positive' : score < 0 ? 'negative' : ''}`}>
                {score > 0 ? '+' : ''}{score.toFixed(1)}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
