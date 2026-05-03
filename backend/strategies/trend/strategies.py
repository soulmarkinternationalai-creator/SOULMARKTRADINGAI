"""Trend-following strategy agents (10 strategies)."""
from backend.strategies.base import StrategyAgent
from backend.models.signals import StrategySignal, SignalType, StrategyFamily


class EMACrossover(StrategyAgent):
    """EMA 50/200 crossover strategy."""
    def __init__(self):
        super().__init__("EMA 50/200 Crossover", StrategyFamily.TREND)

    def analyze(self, features: dict) -> StrategySignal:
        ema50 = self._safe_val(features.get("ema_50"))
        ema200 = self._safe_val(features.get("ema_200"))
        ema50_prev = self._safe_val(features.get("ema_50"), -2)
        ema200_prev = self._safe_val(features.get("ema_200"), -2)
        close = self._safe_val(features["df"]["close"])
        if ema50 == 0 or ema200 == 0:
            return self._no_signal()

        if ema50 > ema200 and ema50_prev <= ema200_prev:
            atr_val = self._safe_val(features.get("atr_14"))
            return StrategySignal(
                signal=SignalType.BUY, confidence=0.75, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                entry_price=close, stop_loss=close - 2 * atr_val, take_profit=close + 4 * atr_val,
                reasoning="Golden cross: EMA50 crossed above EMA200"
            )
        elif ema50 < ema200 and ema50_prev >= ema200_prev:
            atr_val = self._safe_val(features.get("atr_14"))
            return StrategySignal(
                signal=SignalType.SELL, confidence=0.75, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                entry_price=close, stop_loss=close + 2 * atr_val, take_profit=close - 4 * atr_val,
                reasoning="Death cross: EMA50 crossed below EMA200"
            )
        elif ema50 > ema200:
            return StrategySignal(
                signal=SignalType.BUY, confidence=0.4, risk_reward=1.5,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="Bullish EMA alignment"
            )
        elif ema50 < ema200:
            return StrategySignal(
                signal=SignalType.SELL, confidence=0.4, risk_reward=1.5,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="Bearish EMA alignment"
            )
        return self._no_signal()


class MultiTimeframeEMA(StrategyAgent):
    """Multi-timeframe EMA alignment strategy."""
    def __init__(self):
        super().__init__("Multi-TF EMA Alignment", StrategyFamily.TREND)

    def analyze(self, features: dict) -> StrategySignal:
        ema9 = self._safe_val(features.get("ema_9"))
        ema20 = self._safe_val(features.get("ema_20"))
        ema50 = self._safe_val(features.get("ema_50"))
        ema200 = self._safe_val(features.get("ema_200"))
        if any(v == 0 for v in [ema9, ema20, ema50, ema200]):
            return self._no_signal()

        if ema9 > ema20 > ema50 > ema200:
            return StrategySignal(
                signal=SignalType.BUY, confidence=0.85, risk_reward=2.5,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="Perfect bullish EMA alignment: 9 > 20 > 50 > 200"
            )
        elif ema9 < ema20 < ema50 < ema200:
            return StrategySignal(
                signal=SignalType.SELL, confidence=0.85, risk_reward=2.5,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="Perfect bearish EMA alignment: 9 < 20 < 50 < 200"
            )
        return self._no_signal()


class PullbackToEMA(StrategyAgent):
    """Pullback to EMA strategy - buy dips in uptrend."""
    def __init__(self):
        super().__init__("Pullback to EMA", StrategyFamily.TREND)

    def analyze(self, features: dict) -> StrategySignal:
        close = self._safe_val(features["df"]["close"])
        ema20 = self._safe_val(features.get("ema_20"))
        ema50 = self._safe_val(features.get("ema_50"))
        rsi = self._safe_val(features.get("rsi_14"))
        if ema20 == 0 or ema50 == 0:
            return self._no_signal()

        if ema20 > ema50 and abs(close - ema20) / close < 0.005 and rsi < 45:
            return StrategySignal(
                signal=SignalType.BUY, confidence=0.7, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="Price pulled back to EMA20 in uptrend"
            )
        elif ema20 < ema50 and abs(close - ema20) / close < 0.005 and rsi > 55:
            return StrategySignal(
                signal=SignalType.SELL, confidence=0.7, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="Price pulled back to EMA20 in downtrend"
            )
        return self._no_signal()


class TrendlineBreakout(StrategyAgent):
    """Trendline breakout detection."""
    def __init__(self):
        super().__init__("Trendline Breakout", StrategyFamily.TREND)

    def analyze(self, features: dict) -> StrategySignal:
        df = features["df"]
        close = df["close"]
        high = df["high"]
        low = df["low"]
        if len(close) < 20:
            return self._no_signal()

        recent_highs = high.tail(20)
        recent_lows = low.tail(20)
        slope_high = (recent_highs.iloc[-1] - recent_highs.iloc[0]) / 20
        slope_low = (recent_lows.iloc[-1] - recent_lows.iloc[0]) / 20
        current = float(close.iloc[-1])
        prev = float(close.iloc[-2])
        projected_high = float(recent_highs.iloc[-2]) + slope_high
        projected_low = float(recent_lows.iloc[-2]) + slope_low

        if prev < projected_high and current > projected_high:
            return StrategySignal(
                signal=SignalType.BUY, confidence=0.65, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="Bullish trendline breakout"
            )
        elif prev > projected_low and current < projected_low:
            return StrategySignal(
                signal=SignalType.SELL, confidence=0.65, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="Bearish trendline breakdown"
            )
        return self._no_signal()


class HigherHighLow(StrategyAgent):
    """Higher high / higher low structure."""
    def __init__(self):
        super().__init__("Higher High/Low Structure", StrategyFamily.TREND)

    def analyze(self, features: dict) -> StrategySignal:
        df = features["df"]
        if len(df) < 30:
            return self._no_signal()
        highs = df["high"].tail(30)
        lows = df["low"].tail(30)

        swing_highs, swing_lows = [], []
        for i in range(2, len(highs) - 2):
            if highs.iloc[i] > highs.iloc[i-1] and highs.iloc[i] > highs.iloc[i+1]:
                swing_highs.append(float(highs.iloc[i]))
            if lows.iloc[i] < lows.iloc[i-1] and lows.iloc[i] < lows.iloc[i+1]:
                swing_lows.append(float(lows.iloc[i]))

        if len(swing_highs) >= 2 and len(swing_lows) >= 2:
            if swing_highs[-1] > swing_highs[-2] and swing_lows[-1] > swing_lows[-2]:
                return StrategySignal(
                    signal=SignalType.BUY, confidence=0.7, risk_reward=2.0,
                    strategy_name=self.name, strategy_family=self.family,
                    reasoning="Higher highs and higher lows structure"
                )
            elif swing_highs[-1] < swing_highs[-2] and swing_lows[-1] < swing_lows[-2]:
                return StrategySignal(
                    signal=SignalType.SELL, confidence=0.7, risk_reward=2.0,
                    strategy_name=self.name, strategy_family=self.family,
                    reasoning="Lower highs and lower lows structure"
                )
        return self._no_signal()


class MovingAverageRibbon(StrategyAgent):
    """Moving average ribbon strategy."""
    def __init__(self):
        super().__init__("MA Ribbon", StrategyFamily.TREND)

    def analyze(self, features: dict) -> StrategySignal:
        ema9 = self._safe_val(features.get("ema_9"))
        ema20 = self._safe_val(features.get("ema_20"))
        ema50 = self._safe_val(features.get("ema_50"))
        ema100 = self._safe_val(features.get("ema_100"))
        if any(v == 0 for v in [ema9, ema20, ema50, ema100]):
            return self._no_signal()

        spread = (ema9 - ema100) / ema100 * 100
        if spread > 1.0:
            return StrategySignal(
                signal=SignalType.BUY, confidence=min(0.5 + spread * 0.1, 0.9), risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning=f"Bullish ribbon expansion: {spread:.2f}%"
            )
        elif spread < -1.0:
            return StrategySignal(
                signal=SignalType.SELL, confidence=min(0.5 + abs(spread) * 0.1, 0.9), risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning=f"Bearish ribbon expansion: {spread:.2f}%"
            )
        return self._no_signal()


class SupertrendContinuation(StrategyAgent):
    """Supertrend continuation strategy."""
    def __init__(self):
        super().__init__("Supertrend Continuation", StrategyFamily.TREND)

    def analyze(self, features: dict) -> StrategySignal:
        close = self._safe_val(features["df"]["close"])
        st = self._safe_val(features.get("supertrend"))
        if st == 0:
            return self._no_signal()

        if close > st:
            return StrategySignal(
                signal=SignalType.BUY, confidence=0.6, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="Price above Supertrend - bullish continuation"
            )
        elif close < st:
            return StrategySignal(
                signal=SignalType.SELL, confidence=0.6, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="Price below Supertrend - bearish continuation"
            )
        return self._no_signal()


class DonchianBreakout(StrategyAgent):
    """Donchian channel breakout."""
    def __init__(self):
        super().__init__("Donchian Breakout", StrategyFamily.TREND)

    def analyze(self, features: dict) -> StrategySignal:
        close = self._safe_val(features["df"]["close"])
        dc_upper = self._safe_val(features.get("dc_upper"))
        dc_lower = self._safe_val(features.get("dc_lower"))
        if dc_upper == 0 or dc_lower == 0:
            return self._no_signal()

        if close >= dc_upper:
            return StrategySignal(
                signal=SignalType.BUY, confidence=0.65, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="Donchian channel upper breakout"
            )
        elif close <= dc_lower:
            return StrategySignal(
                signal=SignalType.SELL, confidence=0.65, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="Donchian channel lower breakout"
            )
        return self._no_signal()


class TrendVolumeConfirmation(StrategyAgent):
    """Trend with volume confirmation."""
    def __init__(self):
        super().__init__("Trend + Volume", StrategyFamily.TREND)

    def analyze(self, features: dict) -> StrategySignal:
        close = self._safe_val(features["df"]["close"])
        ema50 = self._safe_val(features.get("ema_50"))
        vol = self._safe_val(features["df"]["volume"])
        vol_avg = self._safe_val(features.get("volume_sma_20"))
        if ema50 == 0 or vol_avg == 0:
            return self._no_signal()

        volume_spike = vol > vol_avg * 1.5
        if close > ema50 and volume_spike:
            return StrategySignal(
                signal=SignalType.BUY, confidence=0.7, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="Bullish trend confirmed by volume spike"
            )
        elif close < ema50 and volume_spike:
            return StrategySignal(
                signal=SignalType.SELL, confidence=0.7, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="Bearish trend confirmed by volume spike"
            )
        return self._no_signal()


class TrendADXFilter(StrategyAgent):
    """Trend with ADX filter."""
    def __init__(self):
        super().__init__("Trend + ADX Filter", StrategyFamily.TREND)

    def analyze(self, features: dict) -> StrategySignal:
        close = self._safe_val(features["df"]["close"])
        ema20 = self._safe_val(features.get("ema_20"))
        ema50 = self._safe_val(features.get("ema_50"))
        adx_val = self._safe_val(features.get("adx"))
        if ema20 == 0 or adx_val == 0:
            return self._no_signal()

        if adx_val > 25:
            if ema20 > ema50:
                return StrategySignal(
                    signal=SignalType.BUY, confidence=0.75, risk_reward=2.5,
                    strategy_name=self.name, strategy_family=self.family,
                    reasoning=f"Strong uptrend confirmed by ADX ({adx_val:.1f})"
                )
            elif ema20 < ema50:
                return StrategySignal(
                    signal=SignalType.SELL, confidence=0.75, risk_reward=2.5,
                    strategy_name=self.name, strategy_family=self.family,
                    reasoning=f"Strong downtrend confirmed by ADX ({adx_val:.1f})"
                )
        return self._no_signal()


TREND_STRATEGIES = [
    EMACrossover(), MultiTimeframeEMA(), PullbackToEMA(), TrendlineBreakout(),
    HigherHighLow(), MovingAverageRibbon(), SupertrendContinuation(),
    DonchianBreakout(), TrendVolumeConfirmation(), TrendADXFilter()
]
