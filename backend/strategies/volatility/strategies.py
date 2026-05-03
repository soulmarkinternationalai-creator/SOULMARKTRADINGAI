"""Volatility & Statistical strategy agents (6 strategies)."""
import numpy as np
from backend.strategies.base import StrategyAgent
from backend.models.signals import StrategySignal, SignalType, StrategyFamily


class VolatilityCompressionExpansion(StrategyAgent):
    def __init__(self):
        super().__init__("Volatility Compression/Expansion", StrategyFamily.VOLATILITY)

    def analyze(self, features: dict) -> StrategySignal:
        bb_upper = self._safe_val(features.get("bb_upper"))
        bb_lower = self._safe_val(features.get("bb_lower"))
        bb_middle = self._safe_val(features.get("bb_middle"))
        kc_upper = self._safe_val(features.get("kc_upper"))
        kc_lower = self._safe_val(features.get("kc_lower"))
        close = self._safe_val(features["df"]["close"])

        if bb_middle == 0 or kc_upper == 0:
            return self._no_signal()

        squeeze = bb_upper < kc_upper and bb_lower > kc_lower
        if not squeeze:
            bb_upper_prev = self._safe_val(features.get("bb_upper"), -2)
            kc_upper_prev = self._safe_val(features.get("kc_upper"), -2)
            bb_lower_prev = self._safe_val(features.get("bb_lower"), -2)
            kc_lower_prev = self._safe_val(features.get("kc_lower"), -2)

            was_squeeze = bb_upper_prev < kc_upper_prev and bb_lower_prev > kc_lower_prev
            if was_squeeze:
                if close > bb_middle:
                    return StrategySignal(
                        signal=SignalType.BUY, confidence=0.75, risk_reward=2.5,
                        strategy_name=self.name, strategy_family=self.family,
                        reasoning="Squeeze release - volatility expansion bullish"
                    )
                else:
                    return StrategySignal(
                        signal=SignalType.SELL, confidence=0.75, risk_reward=2.5,
                        strategy_name=self.name, strategy_family=self.family,
                        reasoning="Squeeze release - volatility expansion bearish"
                    )
        return self._no_signal()


class RangeExpansionModel(StrategyAgent):
    def __init__(self):
        super().__init__("Range Expansion Model", StrategyFamily.VOLATILITY)

    def analyze(self, features: dict) -> StrategySignal:
        df = features["df"]
        if len(df) < 10:
            return self._no_signal()

        ranges = (df["high"] - df["low"]).tail(10)
        avg_range = float(ranges.head(9).mean())
        current_range = float(ranges.iloc[-1])
        close = self._safe_val(features["df"]["close"])
        open_p = float(df["open"].iloc[-1]) if "open" in df.columns else self._safe_val(features["df"]["close"], -2)

        if avg_range > 0 and current_range > avg_range * 2:
            if close > open_p:
                return StrategySignal(
                    signal=SignalType.BUY, confidence=0.65, risk_reward=2.0,
                    strategy_name=self.name, strategy_family=self.family,
                    reasoning=f"Range expansion ({current_range/avg_range:.1f}x) bullish"
                )
            else:
                return StrategySignal(
                    signal=SignalType.SELL, confidence=0.65, risk_reward=2.0,
                    strategy_name=self.name, strategy_family=self.family,
                    reasoning=f"Range expansion ({current_range/avg_range:.1f}x) bearish"
                )
        return self._no_signal()


class StdDevBands(StrategyAgent):
    def __init__(self):
        super().__init__("Standard Deviation Bands", StrategyFamily.VOLATILITY)

    def analyze(self, features: dict) -> StrategySignal:
        z = self._safe_val(features.get("zscore"))
        if z > 2.5:
            return StrategySignal(
                signal=SignalType.SELL, confidence=0.7, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning=f"Price at {z:.1f} standard deviations above mean"
            )
        elif z < -2.5:
            return StrategySignal(
                signal=SignalType.BUY, confidence=0.7, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning=f"Price at {z:.1f} standard deviations below mean"
            )
        return self._no_signal()


class MeanVarianceBreakout(StrategyAgent):
    def __init__(self):
        super().__init__("Mean Variance Breakout", StrategyFamily.VOLATILITY)

    def analyze(self, features: dict) -> StrategySignal:
        df = features["df"]
        if len(df) < 50:
            return self._no_signal()

        close = df["close"].tail(50)
        returns = close.pct_change().dropna()
        mean_ret = float(returns.mean())
        var_ret = float(returns.var())
        last_ret = float(returns.iloc[-1])

        if var_ret > 0:
            z = (last_ret - mean_ret) / (var_ret ** 0.5)
            if z > 2:
                return StrategySignal(
                    signal=SignalType.BUY, confidence=0.65, risk_reward=2.0,
                    strategy_name=self.name, strategy_family=self.family,
                    reasoning=f"Returns breakout: z-score {z:.2f}"
                )
            elif z < -2:
                return StrategySignal(
                    signal=SignalType.SELL, confidence=0.65, risk_reward=2.0,
                    strategy_name=self.name, strategy_family=self.family,
                    reasoning=f"Returns breakdown: z-score {z:.2f}"
                )
        return self._no_signal()


class CorrelationDivergence(StrategyAgent):
    def __init__(self):
        super().__init__("Correlation Divergence", StrategyFamily.VOLATILITY)

    def analyze(self, features: dict) -> StrategySignal:
        df = features["df"]
        if len(df) < 30:
            return self._no_signal()

        close = df["close"].tail(30)
        vol = df["volume"].tail(30)

        if float(vol.std()) == 0:
            return self._no_signal()

        corr = float(close.corr(vol))

        price_up = float(close.iloc[-1]) > float(close.iloc[-5])
        vol_up = float(vol.iloc[-1]) > float(vol.tail(5).mean())

        if price_up and not vol_up and corr < -0.3:
            return StrategySignal(
                signal=SignalType.SELL, confidence=0.6, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="Price rising on declining volume (divergence)"
            )
        elif not price_up and vol_up and corr < -0.3:
            return StrategySignal(
                signal=SignalType.BUY, confidence=0.6, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="Price falling on rising volume (capitulation)"
            )
        return self._no_signal()


class PairImbalance(StrategyAgent):
    def __init__(self):
        super().__init__("Pair Imbalance", StrategyFamily.VOLATILITY)

    def analyze(self, features: dict) -> StrategySignal:
        df = features["df"]
        if len(df) < 20:
            return self._no_signal()

        close = float(df["close"].iloc[-1])
        sma_20 = self._safe_val(features.get("sma_20"))
        atr_val = self._safe_val(features.get("atr_14"))

        if sma_20 == 0 or atr_val == 0:
            return self._no_signal()

        imbalance = (close - sma_20) / atr_val

        if imbalance > 2.0:
            return StrategySignal(
                signal=SignalType.SELL, confidence=0.6, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning=f"Price imbalance: {imbalance:.1f} ATR above mean"
            )
        elif imbalance < -2.0:
            return StrategySignal(
                signal=SignalType.BUY, confidence=0.6, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning=f"Price imbalance: {abs(imbalance):.1f} ATR below mean"
            )
        return self._no_signal()


VOLATILITY_STRATEGIES = [
    VolatilityCompressionExpansion(), RangeExpansionModel(), StdDevBands(),
    MeanVarianceBreakout(), CorrelationDivergence(), PairImbalance()
]
