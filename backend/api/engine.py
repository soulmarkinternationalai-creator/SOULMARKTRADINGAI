"""Main trading engine - orchestrates all components."""
import asyncio
import logging
from datetime import datetime
from typing import Optional

from backend.data.market_data import market_data_provider
from backend.features.feature_engine import feature_engine
from backend.agents.meta_agent import meta_agent
from backend.agents.filter_agent import filter_agent
from backend.agents.risk_agent import risk_agent
from backend.agents.execution_agent import execution_agent
from backend.agents.feedback_agent import feedback_agent
from backend.agents.performance_agent import performance_agent
from backend.utils.telegram import telegram_bot
from backend.config.settings import settings
from backend.models.signals import SystemStatus, MarketRegime, TradingSession
from backend.features.market_regime import detect_session

logger = logging.getLogger(__name__)


class TradingEngine:
    """Main orchestrator for the AI trading system."""

    def __init__(self):
        self.is_running = False
        self.status = SystemStatus()
        self.current_signals: dict[str, dict] = {}
        self.signal_history: list[dict] = []
        self._task: Optional[asyncio.Task] = None
        self._start_time = datetime.utcnow()

    async def start(self):
        """Start the trading engine."""
        logger.info("Starting AI Trading Engine...")
        await market_data_provider.initialize()
        self.is_running = True
        self.status.status = "LIVE"
        self._start_time = datetime.utcnow()
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"Engine started with {meta_agent.get_strategy_count()} strategies")

    async def stop(self):
        """Stop the trading engine."""
        self.is_running = False
        self.status.status = "PAUSED"
        if self._task:
            self._task.cancel()
        logger.info("Engine stopped")

    async def _run_loop(self):
        """Main analysis loop."""
        while self.is_running:
            try:
                await self._run_analysis_cycle()
                await asyncio.sleep(settings.update_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Analysis cycle error: {e}")
                await asyncio.sleep(5)

    async def _run_analysis_cycle(self):
        """Run one analysis cycle for all symbols."""
        self.status.uptime_seconds = int((datetime.utcnow() - self._start_time).total_seconds())
        self.status.data_sources = market_data_provider.get_data_sources_status()

        now = datetime.utcnow()
        session_str = detect_session(now.hour)
        try:
            self.status.active_session = TradingSession(session_str)
        except ValueError:
            self.status.active_session = TradingSession.OFF_HOURS

        for symbol in settings.trading.symbols[:3]:
            try:
                await self._analyze_symbol(symbol)
            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {e}")

    async def _analyze_symbol(self, symbol: str):
        """Run full analysis pipeline for a symbol."""
        df = await market_data_provider.get_ohlcv(
            symbol, settings.trading.primary_timeframe, settings.data_history_bars
        )

        if df is None or len(df) < 50:
            return

        features = feature_engine.compute_all(df)
        self.status.market_regime = features.get("regime", MarketRegime.UNKNOWN)

        signals, meta_signal = meta_agent.analyze_all(features)
        meta_signal.symbol = symbol

        filter_result = filter_agent.apply_filters(meta_signal, features)
        risk_assessment = risk_agent.assess_risk(meta_signal)

        execution = execution_agent.prepare_execution(
            meta_signal, risk_assessment, filter_result, symbol
        )

        self.current_signals[symbol] = execution

        if execution.get("executable"):
            self.signal_history.append(execution)
            await telegram_bot.send_signal(execution)

    async def run_single_analysis(self, symbol: str) -> dict:
        """Run a single analysis for a specific symbol (for API calls)."""
        df = await market_data_provider.get_ohlcv(
            symbol, settings.trading.primary_timeframe, settings.data_history_bars
        )

        if df is None or len(df) < 50:
            return {"error": f"Insufficient data for {symbol}"}

        features = feature_engine.compute_all(df)
        self.status.market_regime = features.get("regime", MarketRegime.UNKNOWN)

        signals, meta_signal = meta_agent.analyze_all(features)
        meta_signal.symbol = symbol

        filter_result = filter_agent.apply_filters(meta_signal, features)
        risk_assessment = risk_agent.assess_risk(meta_signal)

        execution = execution_agent.prepare_execution(
            meta_signal, risk_assessment, filter_result, symbol
        )

        self.current_signals[symbol] = execution

        chart_data = {
            "timestamps": [t.isoformat() for t in df.index[-100:]],
            "open": df["open"].tail(100).tolist(),
            "high": df["high"].tail(100).tolist(),
            "low": df["low"].tail(100).tolist(),
            "close": df["close"].tail(100).tolist(),
            "volume": df["volume"].tail(100).tolist(),
            "ema_50": features["ema_50"].tail(100).tolist() if "ema_50" in features else [],
            "ema_200": features["ema_200"].tail(100).tolist() if "ema_200" in features else [],
            "rsi": features["rsi_14"].tail(100).tolist() if "rsi_14" in features else [],
            "vwap": features["vwap"].tail(100).tolist() if "vwap" in features else [],
            "bb_upper": features["bb_upper"].tail(100).tolist() if "bb_upper" in features else [],
            "bb_lower": features["bb_lower"].tail(100).tolist() if "bb_lower" in features else [],
            "support_levels": features.get("support_levels", []),
            "resistance_levels": features.get("resistance_levels", []),
        }

        return {
            "signal": execution,
            "chart_data": chart_data,
            "regime": str(features.get("regime", "UNKNOWN")),
            "session": features.get("session", "OFF_HOURS"),
        }

    def get_system_status(self) -> dict:
        return {
            "status": self.status.status,
            "balance": self.status.balance,
            "equity": self.status.equity,
            "market_regime": self.status.market_regime.value,
            "active_session": self.status.active_session.value,
            "data_sources": self.status.data_sources,
            "uptime_seconds": self.status.uptime_seconds,
            "total_strategies": meta_agent.get_strategy_count(),
            "active_strategies": meta_agent.get_active_count(),
        }

    def get_signal_history(self, limit: int = 50) -> list[dict]:
        return self.signal_history[-limit:]


trading_engine = TradingEngine()
