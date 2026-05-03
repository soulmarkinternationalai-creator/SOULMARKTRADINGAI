"""Global configuration settings for the AI Trading System."""
import os
from pydantic import BaseModel


class BinanceConfig(BaseModel):
    """Binance config — uses public WebSocket and REST API, no API keys required."""
    ws_url: str = "wss://data-stream.binance.vision/stream?streams="
    rest_url: str = "https://data-api.binance.vision/api/v3"


class TickDBConfig(BaseModel):
    """TickDB WebSocket config for forex/commodities."""
    ws_url: str = os.getenv("TICKDB_WS_URL", "wss://ws.tickdb.io/v1/stream")
    api_key: str = os.getenv("TICKDB_API_KEY", "")


class BiQuoteConfig(BaseModel):
    """BiQuote WebSocket config for stocks/indices."""
    ws_url: str = os.getenv("BIQUOTE_WS_URL", "wss://ws.biquote.io/v1/stream")
    api_key: str = os.getenv("BIQUOTE_API_KEY", "")


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
        # Crypto (Binance WebSocket - no API keys)
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT",
        # Forex (TickDB WebSocket)
        "EURUSD", "GBPUSD", "USDJPY", "XAUUSD",
        # Indices & Stocks (BiQuote WebSocket)
        "SPX500", "NAS100",
    ]
    timeframes: list[str] = ["1m", "5m", "15m", "1h", "4h", "1d"]
    primary_timeframe: str = "15m"
    buy_threshold: float = 5.0
    sell_threshold: float = -5.0


class SystemConfig(BaseModel):
    binance: BinanceConfig = BinanceConfig()
    tickdb: TickDBConfig = TickDBConfig()
    biquote: BiQuoteConfig = BiQuoteConfig()
    telegram: TelegramConfig = TelegramConfig()
    risk: RiskConfig = RiskConfig()
    trading: TradingConfig = TradingConfig()
    update_interval_seconds: int = 30
    data_history_bars: int = 500


settings = SystemConfig()
