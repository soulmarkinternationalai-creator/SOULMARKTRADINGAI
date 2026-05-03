"""Feature engineering engine - precomputes all features for strategy agents."""
import pandas as pd
import numpy as np

from backend.features.indicators import (
    ema, sma, rsi, macd, atr, bollinger_bands, vwap, supertrend,
    adx, keltner_channels, donchian_channels, pivot_points, zscore, volume_sma
)
from backend.features.market_regime import detect_regime, detect_support_resistance, detect_session


class FeatureEngine:
    """Precomputes all technical features from raw OHLCV data."""

    def compute_all(self, df: pd.DataFrame) -> dict:
        """Compute all features and return as a dictionary."""
        close = df["close"]
        high = df["high"]
        low = df["low"]
        volume = df["volume"]

        features = {"df": df}

        # EMAs
        for period in [9, 20, 50, 100, 200]:
            features[f"ema_{period}"] = ema(close, period)

        # SMAs
        for period in [20, 50, 200]:
            features[f"sma_{period}"] = sma(close, period)

        # RSI
        features["rsi_14"] = rsi(close, 14)
        features["rsi_7"] = rsi(close, 7)

        # MACD
        macd_line, signal_line, histogram = macd(close)
        features["macd_line"] = macd_line
        features["macd_signal"] = signal_line
        features["macd_histogram"] = histogram

        # ATR
        features["atr_14"] = atr(high, low, close, 14)

        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = bollinger_bands(close)
        features["bb_upper"] = bb_upper
        features["bb_middle"] = bb_middle
        features["bb_lower"] = bb_lower

        # VWAP
        features["vwap"] = vwap(high, low, close, volume)

        # Supertrend
        features["supertrend"] = supertrend(high, low, close)

        # ADX
        features["adx"] = adx(high, low, close)

        # Keltner Channels
        kc_upper, kc_middle, kc_lower = keltner_channels(high, low, close)
        features["kc_upper"] = kc_upper
        features["kc_middle"] = kc_middle
        features["kc_lower"] = kc_lower

        # Donchian Channels
        dc_upper, dc_middle, dc_lower = donchian_channels(high, low)
        features["dc_upper"] = dc_upper
        features["dc_middle"] = dc_middle
        features["dc_lower"] = dc_lower

        # Pivot Points
        pivots = pivot_points(high, low, close)
        features.update(pivots)

        # Z-score
        features["zscore"] = zscore(close)

        # Volume SMA
        features["volume_sma_20"] = volume_sma(volume)

        # Market Regime
        features["regime"] = detect_regime(df)

        # Support/Resistance
        sr = detect_support_resistance(df)
        features["support_levels"] = sr["support"]
        features["resistance_levels"] = sr["resistance"]

        # Session
        if not df.index.empty:
            features["session"] = detect_session(df.index[-1].hour)
        else:
            features["session"] = "OFF_HOURS"

        # Derived
        features["trend_strength"] = self._compute_trend_strength(features)
        features["volatility_ratio"] = self._compute_volatility_ratio(features, close)

        return features

    def _compute_trend_strength(self, features: dict) -> float:
        ema_20 = features["ema_20"].iloc[-1]
        ema_50 = features["ema_50"].iloc[-1]
        ema_200 = features["ema_200"].iloc[-1]
        adx_val = features["adx"].iloc[-1] if not features["adx"].empty else 0

        alignment_score = 0
        if ema_20 > ema_50:
            alignment_score += 1
        if ema_50 > ema_200:
            alignment_score += 1
        if ema_20 > ema_200:
            alignment_score += 1

        adx_score = min(adx_val / 50, 1.0)
        return (alignment_score / 3 * 0.5) + (adx_score * 0.5)

    def _compute_volatility_ratio(self, features: dict, close: pd.Series) -> float:
        current_atr = features["atr_14"].iloc[-1] if not features["atr_14"].empty else 0
        avg_atr = features["atr_14"].rolling(50).mean().iloc[-1] if len(features["atr_14"]) > 50 else current_atr
        if avg_atr == 0:
            return 1.0
        return current_atr / avg_atr


feature_engine = FeatureEngine()
