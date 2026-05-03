import { useEffect, useRef } from 'react';

const SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'SPX500', 'NAS100', 'BNBUSDT', 'SOLUSDT'];
const TIMEFRAMES = ['1m', '5m', '15m', '1h', '4h', '1d'];

export default function MarketView({ chartData, symbol, timeframe, onSymbolChange, onTimeframeChange }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    if (!chartData || !canvasRef.current) return;
    drawChart(canvasRef.current, chartData);
  }, [chartData]);

  function drawChart(canvas, data) {
    const ctx = canvas.getContext('2d');
    const { width, height } = canvas.getBoundingClientRect();
    canvas.width = width * 2;
    canvas.height = height * 2;
    ctx.scale(2, 2);

    ctx.fillStyle = '#0f1923';
    ctx.fillRect(0, 0, width, height);

    if (!data?.close?.length) return;

    const closes = data.close;
    const highs = data.high;
    const lows = data.low;
    const opens = data.open;
    const ema50 = data.ema_50 || [];
    const ema200 = data.ema_200 || [];

    const allPrices = [...highs, ...lows].filter(v => v != null);
    const minPrice = Math.min(...allPrices);
    const maxPrice = Math.max(...allPrices);
    const priceRange = maxPrice - minPrice || 1;

    const padding = { top: 30, bottom: 50, left: 10, right: 60 };
    const chartW = width - padding.left - padding.right;
    const chartH = height - padding.top - padding.bottom;
    const barW = Math.max(chartW / closes.length - 1, 2);

    const toX = (i) => padding.left + (i / closes.length) * chartW;
    const toY = (price) => padding.top + chartH - ((price - minPrice) / priceRange) * chartH;

    // Grid lines
    ctx.strokeStyle = '#1a2332';
    ctx.lineWidth = 0.5;
    for (let i = 0; i < 5; i++) {
      const y = padding.top + (i / 4) * chartH;
      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(width - padding.right, y);
      ctx.stroke();

      const price = maxPrice - (i / 4) * priceRange;
      ctx.fillStyle = '#4a5568';
      ctx.font = '10px monospace';
      ctx.textAlign = 'right';
      ctx.fillText(price.toFixed(2), width - 5, y + 3);
    }

    // Candlesticks
    for (let i = 0; i < closes.length; i++) {
      const x = toX(i);
      const o = opens[i], c = closes[i], h = highs[i], l = lows[i];
      const bullish = c >= o;

      ctx.strokeStyle = bullish ? '#22c55e' : '#ef4444';
      ctx.fillStyle = bullish ? '#22c55e' : '#ef4444';

      // Wick
      ctx.beginPath();
      ctx.moveTo(x + barW / 2, toY(h));
      ctx.lineTo(x + barW / 2, toY(l));
      ctx.lineWidth = 1;
      ctx.stroke();

      // Body
      const bodyTop = toY(Math.max(o, c));
      const bodyBottom = toY(Math.min(o, c));
      const bodyH = Math.max(bodyBottom - bodyTop, 1);
      if (bullish) {
        ctx.fillRect(x, bodyTop, barW, bodyH);
      } else {
        ctx.fillRect(x, bodyTop, barW, bodyH);
      }
    }

    // EMA 50
    if (ema50.length) {
      ctx.strokeStyle = '#3b82f6';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      let started = false;
      for (let i = 0; i < ema50.length; i++) {
        if (ema50[i] == null) continue;
        const x = toX(i) + barW / 2;
        const y = toY(ema50[i]);
        if (!started) { ctx.moveTo(x, y); started = true; }
        else ctx.lineTo(x, y);
      }
      ctx.stroke();
    }

    // EMA 200
    if (ema200.length) {
      ctx.strokeStyle = '#f59e0b';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      let started = false;
      for (let i = 0; i < ema200.length; i++) {
        if (ema200[i] == null) continue;
        const x = toX(i) + barW / 2;
        const y = toY(ema200[i]);
        if (!started) { ctx.moveTo(x, y); started = true; }
        else ctx.lineTo(x, y);
      }
      ctx.stroke();
    }

    // S/R levels
    const supports = data.support_levels || [];
    const resistances = data.resistance_levels || [];

    supports.forEach(level => {
      if (level < minPrice || level > maxPrice) return;
      ctx.strokeStyle = 'rgba(34, 197, 94, 0.4)';
      ctx.setLineDash([5, 5]);
      ctx.beginPath();
      ctx.moveTo(padding.left, toY(level));
      ctx.lineTo(width - padding.right, toY(level));
      ctx.stroke();
      ctx.setLineDash([]);
    });

    resistances.forEach(level => {
      if (level < minPrice || level > maxPrice) return;
      ctx.strokeStyle = 'rgba(239, 68, 68, 0.4)';
      ctx.setLineDash([5, 5]);
      ctx.beginPath();
      ctx.moveTo(padding.left, toY(level));
      ctx.lineTo(width - padding.right, toY(level));
      ctx.stroke();
      ctx.setLineDash([]);
    });

    // Legend
    ctx.font = '11px sans-serif';
    ctx.fillStyle = '#3b82f6';
    ctx.fillText('EMA 50', padding.left + 5, padding.top + 15);
    ctx.fillStyle = '#f59e0b';
    ctx.fillText('EMA 200', padding.left + 65, padding.top + 15);
    ctx.fillStyle = '#22c55e';
    ctx.fillText('Support', padding.left + 135, padding.top + 15);
    ctx.fillStyle = '#ef4444';
    ctx.fillText('Resistance', padding.left + 195, padding.top + 15);

    // Current price
    const lastClose = closes[closes.length - 1];
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 12px monospace';
    ctx.textAlign = 'left';
    ctx.fillText(`${symbol}: ${lastClose?.toFixed(2)}`, padding.left + 5, height - 10);
  }

  return (
    <div className="market-view">
      <div className="market-controls">
        <select value={symbol} onChange={e => onSymbolChange(e.target.value)}>
          {SYMBOLS.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
        <div className="timeframe-buttons">
          {TIMEFRAMES.map(tf => (
            <button key={tf} className={tf === timeframe ? 'active' : ''} onClick={() => onTimeframeChange(tf)}>
              {tf}
            </button>
          ))}
        </div>
      </div>
      <canvas ref={canvasRef} className="chart-canvas"></canvas>
    </div>
  );
}
