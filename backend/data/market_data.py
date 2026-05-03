"""Market data provider - fetches real data from Binance and generates simulated data for other sources."""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd

from backend.config.settings import settings

logger = logging.getLogger(__name__)

# Binance kline interval mapping
BINANCE_INTERVALS = {
    "1m": "1m", "5m": "5m", "15m": "15m",
    "1h": "1h", "4h": "4h", "1d": "1d"
}


class MarketDataProvider:
    """Fetches and manages market data from multiple sources."""

    def __init__(self):
        self._cache: dict[str, pd.DataFrame] = {}
        self._binance_client = None
        self._connected = False
        self._data_sources_status = {
            "Binance": "disconnected",
            "TickDB": "unavailable",
            "BiQuote": "unavailable"
        }

    async def initialize(self):
        """Initialize connections to data sources."""
        await self._connect_binance()

    async def _connect_binance(self):
        """Connect to Binance API."""
        try:
            from binance.client import Client
            api_key = settings.binance.api_key
            api_secret = settings.binance.api_secret
            if api_key and api_secret:
                self._binance_client = Client(api_key, api_secret, testnet=settings.binance.testnet)
                self._data_sources_status["Binance"] = "connected"
                self._connected = True
                logger.info("Connected to Binance API")
            else:
                logger.warning("Binance API keys not configured, using simulated data")
                self._data_sources_status["Binance"] = "no_keys"
        except Exception as e:
            logger.error(f"Failed to connect to Binance: {e}")
            self._data_sources_status["Binance"] = "error"

    def get_data_sources_status(self) -> dict[str, str]:
        return self._data_sources_status.copy()

    async def get_ohlcv(self, symbol: str, timeframe: str = "15m", limit: int = 500) -> pd.DataFrame:
        """Get OHLCV data for a symbol."""
        cache_key = f"{symbol}_{timeframe}"

        if self._binance_client and symbol.endswith("USDT"):
            try:
                return await self._fetch_binance_data(symbol, timeframe, limit)
            except Exception as e:
                logger.error(f"Binance fetch failed for {symbol}: {e}")

        # Fallback to simulated data
        return self._generate_simulated_data(symbol, timeframe, limit)

    async def _fetch_binance_data(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        """Fetch real data from Binance."""
        interval = BINANCE_INTERVALS.get(timeframe, "15m")
        klines = self._binance_client.get_klines(
            symbol=symbol, interval=interval, limit=limit
        )
        df = pd.DataFrame(klines, columns=[
            "timestamp", "open", "high", "low", "close", "volume",
            "close_time", "quote_volume", "trades", "taker_buy_base",
            "taker_buy_quote", "ignore"
        ])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = df[col].astype(float)
        df = df[["timestamp", "open", "high", "low", "close", "volume"]].copy()
        df.set_index("timestamp", inplace=True)
        self._cache[f"{symbol}_{timeframe}"] = df
        return df

    def _generate_simulated_data(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        """Generate realistic simulated market data."""
        rng = np.random.default_rng(hash((symbol, timeframe, datetime.utcnow().strftime('%Y%m%d%H%M'))) % 2**31)

        base_prices = {
            "BTCUSDT": 65000, "ETHUSDT": 3500, "BNBUSDT": 600, "SOLUSDT": 150,
            "EURUSD": 1.0850, "GBPUSD": 1.2650, "USDJPY": 155.50,
            "XAUUSD": 2350, "SPX500": 5200, "NAS100": 18500
        }
        base = base_prices.get(symbol, 100.0)
        volatility = base * 0.002

        tf_minutes = {"1m": 1, "5m": 5, "15m": 15, "1h": 60, "4h": 240, "1d": 1440}
        minutes = tf_minutes.get(timeframe, 15)

        now = datetime.utcnow()
        timestamps = [now - timedelta(minutes=minutes * (limit - i)) for i in range(limit)]

        prices = [base]
        for i in range(1, limit):
            change = rng.normal(0, volatility)
            trend = np.sin(i / 50) * volatility * 0.5
            prices.append(prices[-1] + change + trend)

        opens = prices
        highs = [p + abs(rng.normal(0, volatility * 0.5)) for p in prices]
        lows = [p - abs(rng.normal(0, volatility * 0.5)) for p in prices]
        closes = [p + rng.normal(0, volatility * 0.3) for p in prices]
        volumes = [abs(rng.normal(1000, 300)) for _ in prices]

        df = pd.DataFrame({
            "timestamp": timestamps,
            "open": opens, "high": highs, "low": lows,
            "close": closes, "volume": volumes
        })
        df.set_index("timestamp", inplace=True)
        self._cache[f"{symbol}_{timeframe}"] = df
        return df

    async def get_current_price(self, symbol: str) -> float:
        """Get current price for a symbol."""
        df = await self.get_ohlcv(symbol, "1m", 1)
        return float(df["close"].iloc[-1])

    async def get_order_book(self, symbol: str, limit: int = 20) -> dict:
        """Get order book data (simulated if no live connection)."""
        price = await self.get_current_price(symbol)
        spread = price * 0.0001
        bids = [{"price": price - spread * i, "qty": np.random.uniform(0.1, 10)}
                for i in range(1, limit + 1)]
        asks = [{"price": price + spread * i, "qty": np.random.uniform(0.1, 10)}
                for i in range(1, limit + 1)]
        return {"bids": bids, "asks": asks}


# Singleton
market_data_provider = MarketDataProvider()
