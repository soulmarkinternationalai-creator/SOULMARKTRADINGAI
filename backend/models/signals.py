"""Data models for trading signals and market data."""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel


class SignalType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    NONE = "NONE"


class MarketRegime(str, Enum):
    TRENDING = "TRENDING"
    RANGING = "RANGING"
    VOLATILE = "VOLATILE"
    UNKNOWN = "UNKNOWN"


class TradingSession(str, Enum):
    ASIAN = "ASIAN"
    LONDON = "LONDON"
    NEW_YORK = "NEW_YORK"
    OVERLAP = "OVERLAP"
    OFF_HOURS = "OFF_HOURS"


class StrategyFamily(str, Enum):
    TREND = "TREND"
    MEAN_REVERSION = "MEAN_REVERSION"
    BREAKOUT = "BREAKOUT"
    MOMENTUM = "MOMENTUM"
    SMART_MONEY = "SMART_MONEY"
    VOLATILITY = "VOLATILITY"
    AI_DRIVEN = "AI_DRIVEN"


class StrategySignal(BaseModel):
    signal: SignalType
    confidence: float  # 0-1
    risk_reward: float
    strategy_name: str
    strategy_family: StrategyFamily
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    reasoning: str = ""
    timestamp: datetime = datetime.utcnow()


class MetaSignal(BaseModel):
    signal: SignalType
    total_score: float
    confidence: float
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_reward: float
    family_scores: dict[str, float]
    top_strategies: list[dict]
    active_strategies: int
    agreeing_strategies: int
    timestamp: datetime = datetime.utcnow()
    symbol: str = ""


class TradeResult(BaseModel):
    signal: MetaSignal
    outcome: str  # "WIN" / "LOSS"
    pnl: float
    entry_time: datetime
    exit_time: datetime
    strategy_contributions: dict[str, float]


class MarketData(BaseModel):
    symbol: str
    timeframe: str
    open: list[float]
    high: list[float]
    low: list[float]
    close: list[float]
    volume: list[float]
    timestamps: list[datetime]


class SystemStatus(BaseModel):
    status: str = "PAUSED"  # LIVE / PAUSED
    balance: float = 10000.0
    equity: float = 10000.0
    market_regime: MarketRegime = MarketRegime.UNKNOWN
    active_session: TradingSession = TradingSession.OFF_HOURS
    data_sources: dict[str, str] = {
        "Binance": "disconnected",
        "TickDB": "unavailable",
        "BiQuote": "unavailable"
    }
    uptime_seconds: int = 0


class StrategyPerformance(BaseModel):
    strategy_name: str
    strategy_family: StrategyFamily
    win_rate: float = 0.0
    total_profit: float = 0.0
    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    avg_rr: float = 0.0
    max_drawdown: float = 0.0
    is_active: bool = True
    weight: float = 1.0
