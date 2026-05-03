# AI Trading System - Multi-Strategy Ensemble

A comprehensive AI-powered trading system with **56 independent strategy agents** across 7 families, a meta agent for weighted voting, risk management, and a full-featured real-time dashboard.

## Architecture

```
DATA LAYER (Binance + Simulated)
       ↓
FEATURE ENGINEERING (RSI, EMA, ATR, VWAP, Bollinger, etc.)
       ↓
STRATEGY AGENTS (56 strategies across 7 families)
       ↓
META AGENT (Weighted Voting & Scoring)
       ↓
FILTER AGENTS (Session, Regime, News)
       ↓
RISK AGENT (Position Sizing, Drawdown Limits)
       ↓
EXECUTION AGENT (Signal Output)
       ↓
FEEDBACK LOOP (Weight Updates, Performance Tracking)
```

## Strategy Families

| Family | Count | Description |
|--------|-------|-------------|
| Trend Following | 10 | EMA crossovers, pullbacks, Supertrend, ADX |
| Mean Reversion | 10 | RSI, Bollinger Bands, VWAP deviation, Z-score |
| Breakout | 10 | Session breakouts, consolidation, pattern breakouts |
| Momentum | 8 | MACD, volume spikes, divergence, impulse waves |
| Smart Money | 6 | Order blocks, FVG, liquidity sweeps, BOS |
| Volatility | 6 | Squeeze, range expansion, correlation divergence |
| AI-Driven | 6 | ML classifier, RL policy, pattern recognition |

## Dashboard Features

- **Mission Control Top Bar** — System status, balance, market regime, session, data sources
- **Market View** — Candlestick chart with EMA, support/resistance overlays
- **AI Decision Panel** — Signal box, voting breakdown, top contributors
- **Confidence Gauge** — Speedometer-style visualization
- **Strategy Heatmap** — Visual family contribution bars
- **Strategy Performance Table** — Sortable, filterable, with auto-disable
- **Risk & Execution Panel** — Drawdown meter, auto-trade toggle
- **Signal History** — Past signals with details
- **Equity Curve & Analytics** — Growth chart, win rate, profit factor
- **Notifications** — Trade alerts, system events

## Setup

### Backend
```bash
cd backend
pip install -r requirements.txt
```

### Frontend
```bash
cd frontend
npm install
npm run build
```

### Run
```bash
# Start backend (serves both API and built frontend)
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000

# Or for development (frontend with hot reload)
cd frontend && npm run dev  # Port 5173
uvicorn backend.api.main:app --port 8000  # API
```

### Environment Variables (Optional)
```
BINANCE_API_KEY=your_key
BINANCE_API_SECRET=your_secret
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

Without API keys, the system uses simulated market data.

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/status` | System status |
| `GET /api/analyze/{symbol}` | Run analysis for symbol |
| `GET /api/strategies` | List all strategies with performance |
| `GET /api/risk` | Risk summary |
| `GET /api/signals/history` | Signal history |
| `GET /api/analytics` | Trading analytics |
| `GET /api/analytics/equity-curve` | Equity curve data |
| `GET /api/market/{symbol}/chart` | Chart data with indicators |
| `POST /api/strategies/{name}/toggle` | Enable/disable strategy |
| `POST /api/execution/auto-trade` | Toggle auto-trading |
| `WS /ws` | WebSocket for live updates |

## Supported Symbols
BTCUSDT, ETHUSDT, EURUSD, GBPUSD, USDJPY, XAUUSD, SPX500, NAS100, BNBUSDT, SOLUSDT
