"""Breakout strategy agents (10 strategies)."""
from backend.strategies.base import StrategyAgent
from backend.models.signals import StrategySignal, SignalType, StrategyFamily


class LondonBreakout(StrategyAgent):
    def __init__(self):
        super().__init__("London Breakout", StrategyFamily.BREAKOUT)

    def analyze(self, features: dict) -> StrategySignal:
        session = features.get("session", "OFF_HOURS")
        if session != "LONDON":
            return self._no_signal()

        df = features["df"]
        if len(df) < 30:
            return self._no_signal()

        asian_range_high = float(df["high"].tail(30).head(12).max())
        asian_range_low = float(df["low"].tail(30).head(12).min())
        close = float(df["close"].iloc[-1])

        if close > asian_range_high:
            return StrategySignal(
                signal=SignalType.BUY, confidence=0.75, risk_reward=2.5,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="London breakout above Asian range"
            )
        elif close < asian_range_low:
            return StrategySignal(
                signal=SignalType.SELL, confidence=0.75, risk_reward=2.5,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="London breakout below Asian range"
            )
        return self._no_signal()


class NewYorkBreakout(StrategyAgent):
    def __init__(self):
        super().__init__("New York Breakout", StrategyFamily.BREAKOUT)

    def analyze(self, features: dict) -> StrategySignal:
        session = features.get("session", "OFF_HOURS")
        if session not in ("NEW_YORK", "OVERLAP"):
            return self._no_signal()

        df = features["df"]
        if len(df) < 30:
            return self._no_signal()

        pre_ny_high = float(df["high"].tail(30).head(18).max())
        pre_ny_low = float(df["low"].tail(30).head(18).min())
        close = float(df["close"].iloc[-1])

        if close > pre_ny_high:
            return StrategySignal(
                signal=SignalType.BUY, confidence=0.7, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="NY session breakout above pre-NY range"
            )
        elif close < pre_ny_low:
            return StrategySignal(
                signal=SignalType.SELL, confidence=0.7, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="NY session breakout below pre-NY range"
            )
        return self._no_signal()


class AsianRangeBreakout(StrategyAgent):
    def __init__(self):
        super().__init__("Asian Range Breakout", StrategyFamily.BREAKOUT)

    def analyze(self, features: dict) -> StrategySignal:
        df = features["df"]
        if len(df) < 30:
            return self._no_signal()

        asian_high = float(df["high"].tail(30).head(8).max())
        asian_low = float(df["low"].tail(30).head(8).min())
        close = float(df["close"].iloc[-1])
        atr_val = self._safe_val(features.get("atr_14"))

        if close > asian_high and atr_val > 0:
            return StrategySignal(
                signal=SignalType.BUY, confidence=0.65, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                entry_price=close, stop_loss=asian_low, take_profit=close + 2 * (close - asian_low),
                reasoning="Breakout above Asian session range"
            )
        elif close < asian_low:
            return StrategySignal(
                signal=SignalType.SELL, confidence=0.65, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                entry_price=close, stop_loss=asian_high, take_profit=close - 2 * (asian_high - close),
                reasoning="Breakout below Asian session range"
            )
        return self._no_signal()


class HighLowBreakout(StrategyAgent):
    def __init__(self):
        super().__init__("High/Low Breakout", StrategyFamily.BREAKOUT)

    def analyze(self, features: dict) -> StrategySignal:
        df = features["df"]
        if len(df) < 50:
            return self._no_signal()

        period_high = float(df["high"].tail(50).max())
        period_low = float(df["low"].tail(50).min())
        close = float(df["close"].iloc[-1])
        prev_close = float(df["close"].iloc[-2])

        if close > period_high and prev_close <= period_high:
            return StrategySignal(
                signal=SignalType.BUY, confidence=0.7, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="Breakout above 50-period high"
            )
        elif close < period_low and prev_close >= period_low:
            return StrategySignal(
                signal=SignalType.SELL, confidence=0.7, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="Breakout below 50-period low"
            )
        return self._no_signal()


class VolatilityExpansion(StrategyAgent):
    def __init__(self):
        super().__init__("Volatility Expansion (ATR)", StrategyFamily.BREAKOUT)

    def analyze(self, features: dict) -> StrategySignal:
        atr_val = self._safe_val(features.get("atr_14"))
        close = self._safe_val(features["df"]["close"])
        prev_close = self._safe_val(features["df"]["close"], -2)
        vol_ratio = features.get("volatility_ratio", 1.0)

        if vol_ratio > 1.5:
            if close > prev_close:
                return StrategySignal(
                    signal=SignalType.BUY, confidence=0.65, risk_reward=2.0,
                    strategy_name=self.name, strategy_family=self.family,
                    reasoning=f"Volatility expansion (ratio: {vol_ratio:.2f}) with bullish move"
                )
            else:
                return StrategySignal(
                    signal=SignalType.SELL, confidence=0.65, risk_reward=2.0,
                    strategy_name=self.name, strategy_family=self.family,
                    reasoning=f"Volatility expansion (ratio: {vol_ratio:.2f}) with bearish move"
                )
        return self._no_signal()


class ConsolidationBreakout(StrategyAgent):
    def __init__(self):
        super().__init__("Consolidation Breakout", StrategyFamily.BREAKOUT)

    def analyze(self, features: dict) -> StrategySignal:
        df = features["df"]
        if len(df) < 20:
            return self._no_signal()

        recent = df.tail(20)
        range_high = float(recent["high"].max())
        range_low = float(recent["low"].min())
        range_pct = (range_high - range_low) / range_low * 100
        close = float(df["close"].iloc[-1])

        if range_pct < 1.0:
            if close > range_high:
                return StrategySignal(
                    signal=SignalType.BUY, confidence=0.7, risk_reward=2.5,
                    strategy_name=self.name, strategy_family=self.family,
                    reasoning="Breakout from tight consolidation"
                )
            elif close < range_low:
                return StrategySignal(
                    signal=SignalType.SELL, confidence=0.7, risk_reward=2.5,
                    strategy_name=self.name, strategy_family=self.family,
                    reasoning="Breakdown from tight consolidation"
                )
        return self._no_signal()


class TriangleBreakout(StrategyAgent):
    def __init__(self):
        super().__init__("Triangle Breakout", StrategyFamily.BREAKOUT)

    def analyze(self, features: dict) -> StrategySignal:
        df = features["df"]
        if len(df) < 30:
            return self._no_signal()

        highs = df["high"].tail(30)
        lows = df["low"].tail(30)

        high_slope = (float(highs.iloc[-1]) - float(highs.iloc[0])) / 30
        low_slope = (float(lows.iloc[-1]) - float(lows.iloc[0])) / 30

        converging = high_slope < 0 and low_slope > 0
        close = float(df["close"].iloc[-1])

        if converging:
            projected_high = float(highs.iloc[-2]) + high_slope
            projected_low = float(lows.iloc[-2]) + low_slope

            if close > projected_high:
                return StrategySignal(
                    signal=SignalType.BUY, confidence=0.7, risk_reward=2.5,
                    strategy_name=self.name, strategy_family=self.family,
                    reasoning="Triangle pattern breakout to upside"
                )
            elif close < projected_low:
                return StrategySignal(
                    signal=SignalType.SELL, confidence=0.7, risk_reward=2.5,
                    strategy_name=self.name, strategy_family=self.family,
                    reasoning="Triangle pattern breakout to downside"
                )
        return self._no_signal()


class FlagPennantBreakout(StrategyAgent):
    def __init__(self):
        super().__init__("Flag/Pennant Breakout", StrategyFamily.BREAKOUT)

    def analyze(self, features: dict) -> StrategySignal:
        df = features["df"]
        if len(df) < 40:
            return self._no_signal()

        impulse = df.tail(40).head(10)
        flag = df.tail(20)
        impulse_move = float(impulse["close"].iloc[-1]) - float(impulse["close"].iloc[0])
        flag_range = float(flag["high"].max()) - float(flag["low"].min())
        close = float(df["close"].iloc[-1])

        if abs(impulse_move) > flag_range * 2:
            if impulse_move > 0 and close > float(flag["high"].max()):
                return StrategySignal(
                    signal=SignalType.BUY, confidence=0.7, risk_reward=2.5,
                    strategy_name=self.name, strategy_family=self.family,
                    reasoning="Bull flag breakout"
                )
            elif impulse_move < 0 and close < float(flag["low"].min()):
                return StrategySignal(
                    signal=SignalType.SELL, confidence=0.7, risk_reward=2.5,
                    strategy_name=self.name, strategy_family=self.family,
                    reasoning="Bear flag breakout"
                )
        return self._no_signal()


class NewsBreakout(StrategyAgent):
    def __init__(self):
        super().__init__("News Breakout", StrategyFamily.BREAKOUT)

    def analyze(self, features: dict) -> StrategySignal:
        df = features["df"]
        if len(df) < 5:
            return self._no_signal()

        vol = float(df["volume"].iloc[-1])
        vol_avg = self._safe_val(features.get("volume_sma_20"))
        close = float(df["close"].iloc[-1])
        prev_close = float(df["close"].iloc[-2])
        atr_val = self._safe_val(features.get("atr_14"))

        if vol_avg > 0 and vol > vol_avg * 3 and atr_val > 0:
            move = abs(close - prev_close) / atr_val
            if move > 1.5:
                if close > prev_close:
                    return StrategySignal(
                        signal=SignalType.BUY, confidence=0.6, risk_reward=1.5,
                        strategy_name=self.name, strategy_family=self.family,
                        reasoning="High-volume news breakout to upside"
                    )
                else:
                    return StrategySignal(
                        signal=SignalType.SELL, confidence=0.6, risk_reward=1.5,
                        strategy_name=self.name, strategy_family=self.family,
                        reasoning="High-volume news breakout to downside"
                    )
        return self._no_signal()


class OrderBlockBreakout(StrategyAgent):
    def __init__(self):
        super().__init__("Order Block Breakout", StrategyFamily.BREAKOUT)

    def analyze(self, features: dict) -> StrategySignal:
        df = features["df"]
        if len(df) < 30:
            return self._no_signal()

        close = float(df["close"].iloc[-1])
        vol_avg = self._safe_val(features.get("volume_sma_20"))

        for i in range(-20, -2):
            candle_body = abs(float(df["close"].iloc[i]) - float(df["open"].iloc[i])) if "open" in df.columns else 0
            candle_vol = float(df["volume"].iloc[i])

            if vol_avg > 0 and candle_vol > vol_avg * 2 and candle_body > 0:
                ob_high = max(float(df["open"].iloc[i]), float(df["close"].iloc[i]))
                ob_low = min(float(df["open"].iloc[i]), float(df["close"].iloc[i]))

                if close > ob_high and float(df["close"].iloc[i-1]) < ob_high:
                    return StrategySignal(
                        signal=SignalType.BUY, confidence=0.65, risk_reward=2.0,
                        strategy_name=self.name, strategy_family=self.family,
                        reasoning="Breakout above institutional order block"
                    )
                elif close < ob_low and float(df["close"].iloc[i-1]) > ob_low:
                    return StrategySignal(
                        signal=SignalType.SELL, confidence=0.65, risk_reward=2.0,
                        strategy_name=self.name, strategy_family=self.family,
                        reasoning="Breakdown below institutional order block"
                    )
        return self._no_signal()


BREAKOUT_STRATEGIES = [
    LondonBreakout(), NewYorkBreakout(), AsianRangeBreakout(),
    HighLowBreakout(), VolatilityExpansion(), ConsolidationBreakout(),
    TriangleBreakout(), FlagPennantBreakout(), NewsBreakout(), OrderBlockBreakout()
]
