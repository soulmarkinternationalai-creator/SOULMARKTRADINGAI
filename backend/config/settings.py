"""Global configuration settings for the AI Trading System."""
import os
from typing import Optional
from pydantic import BaseModel


class BinanceConfig(BaseModel):
    api_key: str = os.getenv("BINANCE_API_KEY", "")
    api_secret: str = os.getenv("BINANCE_API_SECRET", "")
    testnet: bool = True


class TelegramConfig(BaseModel):
    bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")


class RiskConfig(BaseModel):
    max_risk_per_trade: float = 0.02
    max_daily_drawdown: float = 0.05
    max_open_trades: int = 5
    default_rr_ratio: float = 2.0


class TradingConfig(BaseModel):
    symbols: list[str] = [
        "BTCUSDT", "ETHUSDT", "EURUSD", "GBPUSD", "USDJPY",
        "XAUUSD", "SPX500", "NAS100", "BNBUSDT", "SOLUSDT"
    ]
    timeframes: list[str] = ["1m", "5m", "15m", "1h", "4h", "1d"]
    primary_timeframe: str = "15m"
    buy_threshold: float = 5.0
    sell_threshold: float = -5.0


class SystemConfig(BaseModel):
    binance: BinanceConfig = BinanceConfig()
    telegram: TelegramConfig = TelegramConfig()
    risk: RiskConfig = RiskConfig()
    trading: TradingConfig = TradingConfig()
    update_interval_seconds: int = 30
    data_history_bars: int = 500


settings = SystemConfig()
