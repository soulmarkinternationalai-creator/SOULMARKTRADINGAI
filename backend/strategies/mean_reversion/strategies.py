"""Mean reversion strategy agents (10 strategies)."""
from backend.strategies.base import StrategyAgent
from backend.models.signals import StrategySignal, SignalType, StrategyFamily


class RSIOverboughtOversold(StrategyAgent):
    def __init__(self):
        super().__init__("RSI Overbought/Oversold", StrategyFamily.MEAN_REVERSION)

    def analyze(self, features: dict) -> StrategySignal:
        rsi = self._safe_val(features.get("rsi_14"))
        if rsi == 0:
            return self._no_signal()
        if rsi < 30:
            return StrategySignal(
                signal=SignalType.BUY, confidence=0.7 + (30 - rsi) / 100,
                risk_reward=2.0, strategy_name=self.name, strategy_family=self.family,
                reasoning=f"RSI oversold at {rsi:.1f}"
            )
        elif rsi > 70:
            return StrategySignal(
                signal=SignalType.SELL, confidence=0.7 + (rsi - 70) / 100,
                risk_reward=2.0, strategy_name=self.name, strategy_family=self.family,
                reasoning=f"RSI overbought at {rsi:.1f}"
            )
        return self._no_signal()


class BollingerBandsBounce(StrategyAgent):
    def __init__(self):
        super().__init__("Bollinger Bands Bounce", StrategyFamily.MEAN_REVERSION)

    def analyze(self, features: dict) -> StrategySignal:
        close = self._safe_val(features["df"]["close"])
        bb_lower = self._safe_val(features.get("bb_lower"))
        bb_upper = self._safe_val(features.get("bb_upper"))
        if bb_lower == 0 or bb_upper == 0:
            return self._no_signal()

        if close <= bb_lower:
            return StrategySignal(
                signal=SignalType.BUY, confidence=0.7, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="Price at lower Bollinger Band - bounce expected"
            )
        elif close >= bb_upper:
            return StrategySignal(
                signal=SignalType.SELL, confidence=0.7, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="Price at upper Bollinger Band - reversion expected"
            )
        return self._no_signal()


class RangeSRReversal(StrategyAgent):
    def __init__(self):
        super().__init__("Range S/R Reversal", StrategyFamily.MEAN_REVERSION)

    def analyze(self, features: dict) -> StrategySignal:
        close = self._safe_val(features["df"]["close"])
        supports = features.get("support_levels", [])
        resistances = features.get("resistance_levels", [])

        if supports:
            nearest_support = supports[0]
            if abs(close - nearest_support) / close < 0.003:
                return StrategySignal(
                    signal=SignalType.BUY, confidence=0.65, risk_reward=2.0,
                    strategy_name=self.name, strategy_family=self.family,
                    reasoning=f"Price near support level {nearest_support:.4f}"
                )
        if resistances:
            nearest_resistance = resistances[0]
            if abs(close - nearest_resistance) / close < 0.003:
                return StrategySignal(
                    signal=SignalType.SELL, confidence=0.65, risk_reward=2.0,
                    strategy_name=self.name, strategy_family=self.family,
                    reasoning=f"Price near resistance level {nearest_resistance:.4f}"
                )
        return self._no_signal()


class VWAPDeviation(StrategyAgent):
    def __init__(self):
        super().__init__("VWAP Deviation", StrategyFamily.MEAN_REVERSION)

    def analyze(self, features: dict) -> StrategySignal:
        close = self._safe_val(features["df"]["close"])
        vwap_val = self._safe_val(features.get("vwap"))
        if vwap_val == 0:
            return self._no_signal()

        deviation = (close - vwap_val) / vwap_val * 100
        if deviation < -1.0:
            return StrategySignal(
                signal=SignalType.BUY, confidence=min(0.5 + abs(deviation) * 0.15, 0.9),
                risk_reward=2.0, strategy_name=self.name, strategy_family=self.family,
                reasoning=f"Price {deviation:.2f}% below VWAP"
            )
        elif deviation > 1.0:
            return StrategySignal(
                signal=SignalType.SELL, confidence=min(0.5 + deviation * 0.15, 0.9),
                risk_reward=2.0, strategy_name=self.name, strategy_family=self.family,
                reasoning=f"Price {deviation:.2f}% above VWAP"
            )
        return self._no_signal()


class ZScoreReversion(StrategyAgent):
    def __init__(self):
        super().__init__("Z-Score Reversion", StrategyFamily.MEAN_REVERSION)

    def analyze(self, features: dict) -> StrategySignal:
        z = self._safe_val(features.get("zscore"))
        if z == 0:
            return self._no_signal()
        if z < -2.0:
            return StrategySignal(
                signal=SignalType.BUY, confidence=0.75, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning=f"Z-score extreme low: {z:.2f}"
            )
        elif z > 2.0:
            return StrategySignal(
                signal=SignalType.SELL, confidence=0.75, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning=f"Z-score extreme high: {z:.2f}"
            )
        return self._no_signal()


class KeltnerReversal(StrategyAgent):
    def __init__(self):
        super().__init__("Keltner Channel Reversal", StrategyFamily.MEAN_REVERSION)

    def analyze(self, features: dict) -> StrategySignal:
        close = self._safe_val(features["df"]["close"])
        kc_upper = self._safe_val(features.get("kc_upper"))
        kc_lower = self._safe_val(features.get("kc_lower"))
        if kc_upper == 0 or kc_lower == 0:
            return self._no_signal()

        if close <= kc_lower:
            return StrategySignal(
                signal=SignalType.BUY, confidence=0.65, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="Price at lower Keltner Channel"
            )
        elif close >= kc_upper:
            return StrategySignal(
                signal=SignalType.SELL, confidence=0.65, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="Price at upper Keltner Channel"
            )
        return self._no_signal()


class LiquiditySweepReversal(StrategyAgent):
    def __init__(self):
        super().__init__("Liquidity Sweep Reversal", StrategyFamily.MEAN_REVERSION)

    def analyze(self, features: dict) -> StrategySignal:
        df = features["df"]
        if len(df) < 20:
            return self._no_signal()

        recent_low = df["low"].tail(20).min()
        recent_high = df["high"].tail(20).max()
        close = float(df["close"].iloc[-1])
        low = float(df["low"].iloc[-1])
        high = float(df["high"].iloc[-1])
        prev_close = float(df["close"].iloc[-2])

        if low < recent_low and close > prev_close:
            return StrategySignal(
                signal=SignalType.BUY, confidence=0.7, risk_reward=2.5,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="Liquidity sweep below recent lows with bullish close"
            )
        elif high > recent_high and close < prev_close:
            return StrategySignal(
                signal=SignalType.SELL, confidence=0.7, risk_reward=2.5,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="Liquidity sweep above recent highs with bearish close"
            )
        return self._no_signal()


class FalseBreakoutTrap(StrategyAgent):
    def __init__(self):
        super().__init__("False Breakout Trap", StrategyFamily.MEAN_REVERSION)

    def analyze(self, features: dict) -> StrategySignal:
        df = features["df"]
        if len(df) < 20:
            return self._no_signal()

        bb_upper = self._safe_val(features.get("bb_upper"))
        bb_lower = self._safe_val(features.get("bb_lower"))
        close = float(df["close"].iloc[-1])
        prev_close = float(df["close"].iloc[-2])
        prev_high = float(df["high"].iloc[-2])
        prev_low = float(df["low"].iloc[-2])

        if prev_high > bb_upper and close < bb_upper and close < prev_close:
            return StrategySignal(
                signal=SignalType.SELL, confidence=0.7, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="False breakout above BB upper band"
            )
        elif prev_low < bb_lower and close > bb_lower and close > prev_close:
            return StrategySignal(
                signal=SignalType.BUY, confidence=0.7, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="False breakout below BB lower band"
            )
        return self._no_signal()


class PivotPointReversal(StrategyAgent):
    def __init__(self):
        super().__init__("Pivot Point Reversal", StrategyFamily.MEAN_REVERSION)

    def analyze(self, features: dict) -> StrategySignal:
        close = self._safe_val(features["df"]["close"])
        s1 = self._safe_val(features.get("S1"))
        r1 = self._safe_val(features.get("R1"))
        if s1 == 0 or r1 == 0:
            return self._no_signal()

        if abs(close - s1) / close < 0.002:
            return StrategySignal(
                signal=SignalType.BUY, confidence=0.6, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="Price near S1 pivot support"
            )
        elif abs(close - r1) / close < 0.002:
            return StrategySignal(
                signal=SignalType.SELL, confidence=0.6, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="Price near R1 pivot resistance"
            )
        return self._no_signal()


class SessionRangeMeanReversion(StrategyAgent):
    def __init__(self):
        super().__init__("Session Range Mean Reversion", StrategyFamily.MEAN_REVERSION)

    def analyze(self, features: dict) -> StrategySignal:
        df = features["df"]
        if len(df) < 30:
            return self._no_signal()

        session_high = float(df["high"].tail(20).max())
        session_low = float(df["low"].tail(20).min())
        session_mid = (session_high + session_low) / 2
        close = float(df["close"].iloc[-1])
        range_size = session_high - session_low

        if range_size == 0:
            return self._no_signal()

        position = (close - session_low) / range_size

        if position < 0.2:
            return StrategySignal(
                signal=SignalType.BUY, confidence=0.6, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="Price at bottom of session range"
            )
        elif position > 0.8:
            return StrategySignal(
                signal=SignalType.SELL, confidence=0.6, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="Price at top of session range"
            )
        return self._no_signal()


MEAN_REVERSION_STRATEGIES = [
    RSIOverboughtOversold(), BollingerBandsBounce(), RangeSRReversal(),
    VWAPDeviation(), ZScoreReversion(), KeltnerReversal(),
    LiquiditySweepReversal(), FalseBreakoutTrap(), PivotPointReversal(),
    SessionRangeMeanReversion()
]
