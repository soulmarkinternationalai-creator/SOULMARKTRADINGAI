"""Market data provider - live WebSocket streams from Binance (no API keys), TickDB, and BiQuote."""
import asyncio
import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd
import websockets

from backend.config.settings import settings

logger = logging.getLogger(__name__)

# Use data-stream.binance.vision (no geo-restrictions, no API keys needed)
BINANCE_WS_URL = "wss://data-stream.binance.vision/ws"
BINANCE_STREAM_URL = "wss://data-stream.binance.vision/stream?streams="
BINANCE_REST_URL = "https://data-api.binance.vision/api/v3"

TICKDB_WS_URL = "wss://ws.tickdb.io/v1/stream"
BIQUOTE_WS_URL = "wss://ws.biquote.io/v1/stream"

BINANCE_INTERVALS = {
    "1m": "1m", "5m": "5m", "15m": "15m",
    "1h": "1h", "4h": "4h", "1d": "1d"
}

# Symbol routing: which source provides each symbol
SYMBOL_SOURCE = {
    "BTCUSDT": "binance", "ETHUSDT": "binance", "BNBUSDT": "binance",
    "SOLUSDT": "binance", "ADAUSDT": "binance", "DOTUSDT": "binance",
    "XRPUSDT": "binance", "DOGEUSDT": "binance", "AVAXUSDT": "binance",
    "LINKUSDT": "binance",
    "EURUSD": "tickdb", "GBPUSD": "tickdb", "USDJPY": "tickdb",
    "AUDUSD": "tickdb", "USDCAD": "tickdb", "USDCHF": "tickdb",
    "NZDUSD": "tickdb", "EURJPY": "tickdb", "GBPJPY": "tickdb",
    "XAUUSD": "tickdb",
    "SPX500": "biquote", "NAS100": "biquote", "DJI30": "biquote",
    "FTSE100": "biquote", "DAX40": "biquote", "US30": "biquote",
    "AAPL": "biquote", "TSLA": "biquote", "MSFT": "biquote",
    "AMZN": "biquote", "GOOGL": "biquote", "META": "biquote",
}


class BinanceWebSocket:
    """Binance public WebSocket for live crypto kline data (no API keys required)."""

    def __init__(self):
        self._ws = None
        self._connected = False
        self._kline_buffers: dict[str, list[dict]] = defaultdict(list)
        self._latest_prices: dict[str, float] = {}
        self._task: Optional[asyncio.Task] = None

    async def connect(self, symbols: list[str], interval: str = "15m"):
        """Connect to Binance WebSocket streams for multiple symbols."""
        binance_symbols = [s.lower() for s in symbols if SYMBOL_SOURCE.get(s) == "binance"]
        if not binance_symbols:
            logger.info("No Binance symbols to stream")
            return False

        streams = [f"{sym}@kline_{interval}" for sym in binance_symbols]
        url = BINANCE_STREAM_URL + "/".join(streams)

        try:
            self._ws = await websockets.connect(url, ping_interval=20, ping_timeout=10)
            self._connected = True
            self._task = asyncio.create_task(self._listen())
            logger.info(f"Binance WebSocket connected: {len(binance_symbols)} streams")
            return True
        except Exception as e:
            logger.error(f"Binance WebSocket connection failed: {e}")
            self._connected = False
            return False

    async def _listen(self):
        """Listen for incoming kline data."""
        try:
            async for message in self._ws:
                try:
                    data = json.loads(message)
                    if "data" in data:
                        self._process_kline(data["data"])
                    elif "k" in data:
                        self._process_kline(data)
                except json.JSONDecodeError:
                    continue
        except websockets.ConnectionClosed:
            logger.warning("Binance WebSocket disconnected, reconnecting...")
            self._connected = False
            await asyncio.sleep(5)
            await self._reconnect()
        except Exception as e:
            logger.error(f"Binance WebSocket error: {e}")
            self._connected = False

    async def _reconnect(self):
        """Reconnect to Binance WebSocket."""
        symbols = list(set(
            s.upper() for s in self._kline_buffers.keys()
        ))
        if symbols:
            await self.connect(symbols)

    def _process_kline(self, data: dict):
        """Process a kline message and update buffers."""
        kline = data.get("k", data)
        symbol = kline.get("s", "").upper()
        if not symbol:
            return

        candle = {
            "timestamp": datetime.utcfromtimestamp(kline["t"] / 1000),
            "open": float(kline["o"]),
            "high": float(kline["h"]),
            "low": float(kline["l"]),
            "close": float(kline["c"]),
            "volume": float(kline["v"]),
            "is_closed": kline.get("x", False),
        }

        self._latest_prices[symbol] = candle["close"]

        buffer = self._kline_buffers[symbol]
        if buffer and not buffer[-1].get("is_closed") and buffer[-1]["timestamp"] == candle["timestamp"]:
            buffer[-1] = candle
        else:
            buffer.append(candle)

        # Keep buffer bounded
        if len(buffer) > 600:
            self._kline_buffers[symbol] = buffer[-500:]

    def get_ohlcv(self, symbol: str, limit: int = 500) -> Optional[pd.DataFrame]:
        """Get buffered OHLCV data as DataFrame."""
        buffer = self._kline_buffers.get(symbol, [])
        if not buffer:
            return None

        closed = [c for c in buffer if c.get("is_closed", True)]
        if len(closed) < 10:
            closed = buffer

        df = pd.DataFrame(closed[-limit:])
        df.set_index("timestamp", inplace=True)
        df = df[["open", "high", "low", "close", "volume"]].copy()
        return df

    def get_latest_price(self, symbol: str) -> Optional[float]:
        return self._latest_prices.get(symbol)

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def disconnect(self):
        if self._ws:
            await self._ws.close()
        if self._task:
            self._task.cancel()
        self._connected = False


class TickDBWebSocket:
    """TickDB WebSocket for live forex, commodities, and indices data."""

    def __init__(self):
        self._ws = None
        self._connected = False
        self._kline_buffers: dict[str, list[dict]] = defaultdict(list)
        self._latest_prices: dict[str, float] = {}
        self._task: Optional[asyncio.Task] = None
        self._url = TICKDB_WS_URL

    async def connect(self, symbols: list[str]):
        """Connect to TickDB WebSocket."""
        tickdb_symbols = [s for s in symbols if SYMBOL_SOURCE.get(s) == "tickdb"]
        if not tickdb_symbols:
            return False

        try:
            self._ws = await websockets.connect(self._url, ping_interval=20, ping_timeout=10)
            subscribe_msg = json.dumps({
                "action": "subscribe",
                "symbols": tickdb_symbols,
                "channels": ["kline_15m", "tick"]
            })
            await self._ws.send(subscribe_msg)
            self._connected = True
            self._task = asyncio.create_task(self._listen())
            logger.info(f"TickDB WebSocket connected: {len(tickdb_symbols)} symbols")
            return True
        except Exception as e:
            logger.warning(f"TickDB WebSocket connection failed: {e} — using simulated data")
            self._connected = False
            return False

    async def _listen(self):
        """Listen for TickDB messages."""
        try:
            async for message in self._ws:
                try:
                    data = json.loads(message)
                    self._process_message(data)
                except json.JSONDecodeError:
                    continue
        except websockets.ConnectionClosed:
            logger.warning("TickDB WebSocket disconnected")
            self._connected = False
        except Exception as e:
            logger.error(f"TickDB WebSocket error: {e}")
            self._connected = False

    def _process_message(self, data: dict):
        """Process TickDB kline/tick data."""
        msg_type = data.get("type", "")
        symbol = data.get("symbol", "").upper()
        if not symbol:
            return

        if msg_type == "kline":
            candle = {
                "timestamp": datetime.utcfromtimestamp(data.get("timestamp", 0) / 1000),
                "open": float(data.get("open", 0)),
                "high": float(data.get("high", 0)),
                "low": float(data.get("low", 0)),
                "close": float(data.get("close", 0)),
                "volume": float(data.get("volume", 0)),
                "is_closed": data.get("closed", True),
            }
            self._latest_prices[symbol] = candle["close"]
            buffer = self._kline_buffers[symbol]
            if buffer and not buffer[-1].get("is_closed") and buffer[-1]["timestamp"] == candle["timestamp"]:
                buffer[-1] = candle
            else:
                buffer.append(candle)
            if len(buffer) > 600:
                self._kline_buffers[symbol] = buffer[-500:]

        elif msg_type == "tick":
            price = float(data.get("price", data.get("bid", 0)))
            if price > 0:
                self._latest_prices[symbol] = price

    def get_ohlcv(self, symbol: str, limit: int = 500) -> Optional[pd.DataFrame]:
        buffer = self._kline_buffers.get(symbol, [])
        if not buffer:
            return None
        closed = [c for c in buffer if c.get("is_closed", True)]
        if len(closed) < 10:
            closed = buffer
        df = pd.DataFrame(closed[-limit:])
        df.set_index("timestamp", inplace=True)
        df = df[["open", "high", "low", "close", "volume"]].copy()
        return df

    def get_latest_price(self, symbol: str) -> Optional[float]:
        return self._latest_prices.get(symbol)

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def disconnect(self):
        if self._ws:
            await self._ws.close()
        if self._task:
            self._task.cancel()
        self._connected = False


class BiQuoteWebSocket:
    """BiQuote WebSocket for live stocks and index data."""

    def __init__(self):
        self._ws = None
        self._connected = False
        self._kline_buffers: dict[str, list[dict]] = defaultdict(list)
        self._latest_prices: dict[str, float] = {}
        self._task: Optional[asyncio.Task] = None
        self._url = BIQUOTE_WS_URL

    async def connect(self, symbols: list[str]):
        """Connect to BiQuote WebSocket."""
        bq_symbols = [s for s in symbols if SYMBOL_SOURCE.get(s) == "biquote"]
        if not bq_symbols:
            return False

        try:
            self._ws = await websockets.connect(self._url, ping_interval=20, ping_timeout=10)
            subscribe_msg = json.dumps({
                "action": "subscribe",
                "symbols": bq_symbols,
                "channels": ["ohlc_15m", "quote"]
            })
            await self._ws.send(subscribe_msg)
            self._connected = True
            self._task = asyncio.create_task(self._listen())
            logger.info(f"BiQuote WebSocket connected: {len(bq_symbols)} symbols")
            return True
        except Exception as e:
            logger.warning(f"BiQuote WebSocket connection failed: {e} — using simulated data")
            self._connected = False
            return False

    async def _listen(self):
        """Listen for BiQuote messages."""
        try:
            async for message in self._ws:
                try:
                    data = json.loads(message)
                    self._process_message(data)
                except json.JSONDecodeError:
                    continue
        except websockets.ConnectionClosed:
            logger.warning("BiQuote WebSocket disconnected")
            self._connected = False
        except Exception as e:
            logger.error(f"BiQuote WebSocket error: {e}")
            self._connected = False

    def _process_message(self, data: dict):
        """Process BiQuote OHLC/quote data."""
        msg_type = data.get("type", "")
        symbol = data.get("symbol", "").upper()
        if not symbol:
            return

        if msg_type in ("ohlc", "kline"):
            candle = {
                "timestamp": datetime.utcfromtimestamp(data.get("timestamp", 0) / 1000),
                "open": float(data.get("open", 0)),
                "high": float(data.get("high", 0)),
                "low": float(data.get("low", 0)),
                "close": float(data.get("close", 0)),
                "volume": float(data.get("volume", 0)),
                "is_closed": data.get("closed", True),
            }
            self._latest_prices[symbol] = candle["close"]
            buffer = self._kline_buffers[symbol]
            if buffer and not buffer[-1].get("is_closed") and buffer[-1]["timestamp"] == candle["timestamp"]:
                buffer[-1] = candle
            else:
                buffer.append(candle)
            if len(buffer) > 600:
                self._kline_buffers[symbol] = buffer[-500:]

        elif msg_type == "quote":
            price = float(data.get("price", data.get("last", 0)))
            if price > 0:
                self._latest_prices[symbol] = price

    def get_ohlcv(self, symbol: str, limit: int = 500) -> Optional[pd.DataFrame]:
        buffer = self._kline_buffers.get(symbol, [])
        if not buffer:
            return None
        closed = [c for c in buffer if c.get("is_closed", True)]
        if len(closed) < 10:
            closed = buffer
        df = pd.DataFrame(closed[-limit:])
        df.set_index("timestamp", inplace=True)
        df = df[["open", "high", "low", "close", "volume"]].copy()
        return df

    def get_latest_price(self, symbol: str) -> Optional[float]:
        return self._latest_prices.get(symbol)

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def disconnect(self):
        if self._ws:
            await self._ws.close()
        if self._task:
            self._task.cancel()
        self._connected = False


class MarketDataProvider:
    """Unified market data provider using WebSocket streams from Binance, TickDB, and BiQuote."""

    def __init__(self):
        self._cache: dict[str, pd.DataFrame] = {}
        self._binance_ws = BinanceWebSocket()
        self._tickdb_ws = TickDBWebSocket()
        self._biquote_ws = BiQuoteWebSocket()

    async def initialize(self):
        """Initialize all WebSocket connections."""
        symbols = settings.trading.symbols

        # Binance: public WebSocket, no API keys needed
        binance_ok = await self._binance_ws.connect(symbols, settings.trading.primary_timeframe)
        if binance_ok:
            logger.info("Binance public WebSocket streaming live crypto data (no API keys)")
        else:
            logger.warning("Binance WebSocket failed — crypto symbols will use simulated data")

        # TickDB: forex/commodities WebSocket
        tickdb_ok = await self._tickdb_ws.connect(symbols)
        if not tickdb_ok:
            logger.warning("TickDB WebSocket not available — forex/commodity symbols will use simulated data")

        # BiQuote: stocks/indices WebSocket
        biquote_ok = await self._biquote_ws.connect(symbols)
        if not biquote_ok:
            logger.warning("BiQuote WebSocket not available — stock/index symbols will use simulated data")

        # Seed initial historical data for Binance symbols using REST API (no keys)
        await self._seed_binance_history(symbols)

    async def _seed_binance_history(self, symbols: list[str]):
        """Fetch initial historical klines from Binance REST API (public, no keys)."""
        import aiohttp
        binance_symbols = [s for s in symbols if SYMBOL_SOURCE.get(s) == "binance"]
        interval = BINANCE_INTERVALS.get(settings.trading.primary_timeframe, "15m")

        async with aiohttp.ClientSession() as session:
            for symbol in binance_symbols:
                try:
                    url = f"https://data-api.binance.vision/api/v3/klines?symbol={symbol}&interval={interval}&limit=500"
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        if resp.status == 200:
                            klines = await resp.json()
                            for k in klines:
                                candle = {
                                    "timestamp": datetime.utcfromtimestamp(k[0] / 1000),
                                    "open": float(k[1]),
                                    "high": float(k[2]),
                                    "low": float(k[3]),
                                    "close": float(k[4]),
                                    "volume": float(k[5]),
                                    "is_closed": True,
                                }
                                self._binance_ws._kline_buffers[symbol].append(candle)
                            self._binance_ws._latest_prices[symbol] = float(klines[-1][4])
                            logger.info(f"Seeded {len(klines)} historical candles for {symbol}")
                except Exception as e:
                    logger.warning(f"Failed to seed history for {symbol}: {e}")

    def get_data_sources_status(self) -> dict[str, str]:
        return {
            "Binance": "connected" if self._binance_ws.is_connected else "streaming" if self._binance_ws._kline_buffers else "disconnected",
            "TickDB": "connected" if self._tickdb_ws.is_connected else "simulated",
            "BiQuote": "connected" if self._biquote_ws.is_connected else "simulated",
        }

    async def get_ohlcv(self, symbol: str, timeframe: str = "15m", limit: int = 500) -> pd.DataFrame:
        """Get OHLCV data — tries live WebSocket first, falls back to simulated."""
        source = SYMBOL_SOURCE.get(symbol, "unknown")

        # Try WebSocket sources first
        df = None
        if source == "binance":
            df = self._binance_ws.get_ohlcv(symbol, limit)
        elif source == "tickdb":
            df = self._tickdb_ws.get_ohlcv(symbol, limit)
        elif source == "biquote":
            df = self._biquote_ws.get_ohlcv(symbol, limit)

        if df is not None and len(df) >= 50:
            self._cache[f"{symbol}_{timeframe}"] = df
            return df

        # Check cache
        cache_key = f"{symbol}_{timeframe}"
        if cache_key in self._cache and len(self._cache[cache_key]) >= 50:
            return self._cache[cache_key]

        # Fallback: for Binance symbols, try REST API fetch
        if source == "binance":
            try:
                df = await self._fetch_binance_rest(symbol, timeframe, limit)
                if df is not None and len(df) >= 50:
                    self._cache[cache_key] = df
                    return df
            except Exception as e:
                logger.warning(f"Binance REST fallback failed for {symbol}: {e}")

        # Final fallback: simulated data
        return self._generate_simulated_data(symbol, timeframe, limit)

    async def _fetch_binance_rest(self, symbol: str, timeframe: str, limit: int) -> Optional[pd.DataFrame]:
        """Fetch data from Binance public REST API (no API keys needed)."""
        import aiohttp
        interval = BINANCE_INTERVALS.get(timeframe, "15m")
        url = f"https://data-api.binance.vision/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    return None
                klines = await resp.json()

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
        return df

    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get the latest price from any connected source."""
        source = SYMBOL_SOURCE.get(symbol, "unknown")
        if source == "binance":
            return self._binance_ws.get_latest_price(symbol)
        elif source == "tickdb":
            return self._tickdb_ws.get_latest_price(symbol)
        elif source == "biquote":
            return self._biquote_ws.get_latest_price(symbol)
        return None

    def _generate_simulated_data(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        """Generate realistic simulated market data as fallback."""
        rng = np.random.default_rng(hash((symbol, timeframe, datetime.utcnow().strftime('%Y%m%d%H%M'))) % 2**31)

        base_prices = {
            "BTCUSDT": 65000, "ETHUSDT": 3500, "BNBUSDT": 600, "SOLUSDT": 150,
            "ADAUSDT": 0.45, "DOTUSDT": 7.50, "XRPUSDT": 0.55,
            "DOGEUSDT": 0.08, "AVAXUSDT": 35.0, "LINKUSDT": 15.0,
            "EURUSD": 1.0850, "GBPUSD": 1.2650, "USDJPY": 155.50,
            "AUDUSD": 0.6550, "USDCAD": 1.3650, "USDCHF": 0.8850,
            "NZDUSD": 0.6100, "EURJPY": 168.50, "GBPJPY": 196.50,
            "XAUUSD": 2350, "SPX500": 5200, "NAS100": 18500,
            "DJI30": 39500, "FTSE100": 8200, "DAX40": 18300,
            "US30": 39500, "AAPL": 175, "TSLA": 180,
            "MSFT": 420, "AMZN": 180, "GOOGL": 155, "META": 500,
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
        return df

    async def disconnect(self):
        """Disconnect all WebSocket connections."""
        await self._binance_ws.disconnect()
        await self._tickdb_ws.disconnect()
        await self._biquote_ws.disconnect()


market_data_provider = MarketDataProvider()
