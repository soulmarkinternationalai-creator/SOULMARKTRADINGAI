export default function SignalHistory({ signals }) {
  return (
    <div className="signal-history">
      <h3>Signal History</h3>
      {signals.length === 0 ? (
        <p className="empty">No signals yet</p>
      ) : (
        <div className="history-list">
          {signals.slice().reverse().slice(0, 20).map((s, i) => (
            <div key={i} className={`history-item ${s.signal?.toLowerCase()}`}>
              <div className="history-header">
                <span className={`signal-badge ${s.signal?.toLowerCase()}`}>{s.signal}</span>
                <span className="symbol">{s.symbol}</span>
                <span className="time">{new Date(s.timestamp).toLocaleTimeString()}</span>
              </div>
              <div className="history-details">
                <span>Entry: {s.entry_price?.toFixed(5)}</span>
                <span>Score: {s.score?.toFixed(1)}</span>
                <span>Conf: {((s.confidence || 0) * 100).toFixed(0)}%</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
