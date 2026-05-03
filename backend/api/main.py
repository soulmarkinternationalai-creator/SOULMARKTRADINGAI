"""FastAPI application - REST API for the AI Trading System dashboard."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.api.engine import trading_engine
from backend.agents.meta_agent import meta_agent
from backend.agents.risk_agent import risk_agent
from backend.agents.execution_agent import execution_agent
from backend.agents.performance_agent import performance_agent
from backend.agents.feedback_agent import feedback_agent
from backend.agents.filter_agent import filter_agent
from backend.config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AI Trading System...")
    await trading_engine.start()
    yield
    await trading_engine.stop()


app = FastAPI(
    title="AI Trading System",
    description="Multi-strategy AI ensemble trading system with 50+ strategies",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── System ──────────────────────────────────────────────────
@app.get("/api/status")
async def get_status():
    return trading_engine.get_system_status()


@app.post("/api/system/{action}")
async def system_control(action: str):
    if action == "start":
        await trading_engine.start()
    elif action == "stop":
        await trading_engine.stop()
    elif action == "pause":
        trading_engine.is_running = False
        trading_engine.status.status = "PAUSED"
    return {"status": trading_engine.status.status}


# ── Analysis ────────────────────────────────────────────────
@app.get("/api/analyze/{symbol}")
async def analyze_symbol(symbol: str):
    result = await trading_engine.run_single_analysis(symbol)
    return result


@app.get("/api/signals")
async def get_current_signals():
    return trading_engine.current_signals


@app.get("/api/signals/history")
async def get_signal_history(limit: int = 50):
    return trading_engine.get_signal_history(limit)


# ── Strategies ──────────────────────────────────────────────
@app.get("/api/strategies")
async def get_strategies():
    strategies = []
    for s in meta_agent.all_strategies:
        perf = performance_agent.performance.get(s.name)
        strategies.append({
            "name": s.name,
            "family": s.family.value,
            "is_active": s.is_active,
            "weight": round(meta_agent.strategy_weights.get(s.name, 1.0), 2),
            "win_rate": round(perf.win_rate * 100, 1) if perf else 0,
            "total_profit": round(perf.total_profit, 2) if perf else 0,
            "total_trades": perf.total_trades if perf else 0,
        })
    return strategies


@app.post("/api/strategies/{name}/toggle")
async def toggle_strategy(name: str, active: bool = True):
    meta_agent.toggle_strategy(name, active)
    return {"name": name, "active": active}


@app.post("/api/strategies/{name}/weight")
async def set_strategy_weight(name: str, weight: float = 1.0):
    meta_agent.update_strategy_weight(name, weight)
    return {"name": name, "weight": weight}


# ── Performance ─────────────────────────────────────────────
@app.get("/api/performance")
async def get_performance():
    return performance_agent.get_all_performance()


@app.get("/api/performance/families")
async def get_family_performance():
    return performance_agent.get_family_performance()


# ── Risk ────────────────────────────────────────────────────
@app.get("/api/risk")
async def get_risk():
    return risk_agent.get_risk_summary()


@app.post("/api/risk/update")
async def update_risk_settings(max_risk: float = 0.02, max_drawdown: float = 0.05, max_trades: int = 5):
    risk_agent.max_risk_per_trade = max_risk
    risk_agent.max_daily_drawdown = max_drawdown
    risk_agent.max_open_trades = max_trades
    return risk_agent.get_risk_summary()


# ── Execution ───────────────────────────────────────────────
@app.post("/api/execution/auto-trade")
async def toggle_auto_trade(enabled: bool = False):
    execution_agent.toggle_auto_trade(enabled)
    return {"auto_trade": enabled}


@app.post("/api/execution/force")
async def force_signal(signal_type: str, symbol: str, entry: float, sl: float, tp: float):
    result = execution_agent.force_signal(signal_type, symbol, entry, sl, tp)
    return result


# ── Analytics ───────────────────────────────────────────────
@app.get("/api/analytics")
async def get_analytics():
    return feedback_agent.get_analytics()


@app.get("/api/analytics/equity-curve")
async def get_equity_curve():
    return feedback_agent.get_equity_curve()


@app.get("/api/analytics/trade-history")
async def get_trade_history(limit: int = 50):
    return feedback_agent.get_trade_history(limit)


# ── Market Data ─────────────────────────────────────────────
@app.get("/api/market/{symbol}/chart")
async def get_chart_data(symbol: str, timeframe: str = "15m"):
    from backend.data.market_data import market_data_provider
    from backend.features.feature_engine import feature_engine

    df = await market_data_provider.get_ohlcv(symbol, timeframe, 200)
    if df is None or len(df) < 10:
        return {"error": "No data"}

    features = feature_engine.compute_all(df)

    return {
        "timestamps": [t.isoformat() for t in df.index],
        "open": df["open"].tolist(),
        "high": df["high"].tolist(),
        "low": df["low"].tolist(),
        "close": df["close"].tolist(),
        "volume": df["volume"].tolist(),
        "ema_50": [float(v) if not (v != v) else None for v in features["ema_50"].tolist()],
        "ema_200": [float(v) if not (v != v) else None for v in features["ema_200"].tolist()],
        "rsi": [float(v) if not (v != v) else None for v in features["rsi_14"].tolist()],
        "vwap": [float(v) if not (v != v) else None for v in features["vwap"].tolist()],
        "bb_upper": [float(v) if not (v != v) else None for v in features["bb_upper"].tolist()],
        "bb_lower": [float(v) if not (v != v) else None for v in features["bb_lower"].tolist()],
        "support_levels": features.get("support_levels", []),
        "resistance_levels": features.get("resistance_levels", []),
        "regime": str(features.get("regime", "UNKNOWN")),
    }


@app.get("/api/symbols")
async def get_symbols():
    return settings.trading.symbols


# ── WebSocket for live updates ──────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = {
                "status": trading_engine.get_system_status(),
                "signals": trading_engine.current_signals,
                "risk": risk_agent.get_risk_summary(),
            }
            await websocket.send_json(data)
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        pass


import asyncio

# Serve frontend static files
import os
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))
