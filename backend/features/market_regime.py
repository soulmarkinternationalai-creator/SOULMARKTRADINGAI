"""Market regime detection - determines if market is trending, ranging, or volatile."""
import numpy as np
import pandas as pd

from backend.features.indicators import adx, atr, bollinger_bands, ema
from backend.models.signals import MarketRegime


def detect_regime(df: pd.DataFrame) -> MarketRegime:
    """Detect current market regime using multiple indicators."""
    close = df["close"]
    high = df["high"]
    low = df["low"]

    adx_val = adx(high, low, close, 14)
    current_adx = adx_val.iloc[-1] if not adx_val.empty else 0

    atr_val = atr(high, low, close, 14)
    atr_pct = (atr_val / close * 100)
    current_atr_pct = atr_pct.iloc[-1] if not atr_pct.empty else 0
    avg_atr_pct = atr_pct.rolling(50).mean().iloc[-1] if len(atr_pct) > 50 else current_atr_pct

    upper, middle, lower = bollinger_bands(close, 20, 2.0)
    bb_width = ((upper - lower) / middle * 100)
    current_bb_width = bb_width.iloc[-1] if not bb_width.empty else 0
    avg_bb_width = bb_width.rolling(50).mean().iloc[-1] if len(bb_width) > 50 else current_bb_width

    ema_20 = ema(close, 20)
    ema_50 = ema(close, 50)
    trend_aligned = (ema_20.iloc[-1] > ema_50.iloc[-1]) or (ema_20.iloc[-1] < ema_50.iloc[-1])
    ema_spread = abs(ema_20.iloc[-1] - ema_50.iloc[-1]) / close.iloc[-1] * 100

    if current_atr_pct > avg_atr_pct * 1.5 and current_bb_width > avg_bb_width * 1.3:
        return MarketRegime.VOLATILE

    if current_adx > 25 and ema_spread > 0.3:
        return MarketRegime.TRENDING

    if current_adx < 20:
        return MarketRegime.RANGING

    return MarketRegime.UNKNOWN


def detect_support_resistance(df: pd.DataFrame, lookback: int = 100) -> dict[str, list[float]]:
    """Detect support and resistance levels using pivot points and price clusters."""
    high = df["high"].tail(lookback)
    low = df["low"].tail(lookback)
    close = df["close"].tail(lookback)

    levels = []
    for i in range(2, len(high) - 2):
        if high.iloc[i] > high.iloc[i-1] and high.iloc[i] > high.iloc[i-2] and \
           high.iloc[i] > high.iloc[i+1] and high.iloc[i] > high.iloc[i+2]:
            levels.append(("resistance", float(high.iloc[i])))
        if low.iloc[i] < low.iloc[i-1] and low.iloc[i] < low.iloc[i-2] and \
           low.iloc[i] < low.iloc[i+1] and low.iloc[i] < low.iloc[i+2]:
            levels.append(("support", float(low.iloc[i])))

    current_price = float(close.iloc[-1])
    supports = sorted([l[1] for l in levels if l[0] == "support" and l[1] < current_price], reverse=True)[:5]
    resistances = sorted([l[1] for l in levels if l[0] == "resistance" and l[1] > current_price])[:5]

    return {"support": supports, "resistance": resistances}


def detect_session(hour_utc: int) -> str:
    """Detect active trading session based on UTC hour."""
    if 0 <= hour_utc < 8:
        return "ASIAN"
    elif 8 <= hour_utc < 13:
        return "LONDON"
    elif 13 <= hour_utc < 16:
        return "OVERLAP"
    elif 16 <= hour_utc < 21:
        return "NEW_YORK"
    else:
        return "OFF_HOURS"
