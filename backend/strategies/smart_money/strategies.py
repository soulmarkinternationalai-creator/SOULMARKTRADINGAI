"""Smart Money / Liquidity strategy agents (6 strategies)."""
from backend.strategies.base import StrategyAgent
from backend.models.signals import StrategySignal, SignalType, StrategyFamily


class OrderBlocks(StrategyAgent):
    def __init__(self):
        super().__init__("Order Blocks", StrategyFamily.SMART_MONEY)

    def analyze(self, features: dict) -> StrategySignal:
        df = features["df"]
        if len(df) < 30 or "open" not in df.columns:
            return self._no_signal()

        close = float(df["close"].iloc[-1])
        vol_avg = self._safe_val(features.get("volume_sma_20"))

        for i in range(-25, -3):
            candle_close = float(df["close"].iloc[i])
            candle_open = float(df["open"].iloc[i])
            candle_vol = float(df["volume"].iloc[i])
            next_close = float(df["close"].iloc[i + 1])

            if vol_avg > 0 and candle_vol > vol_avg * 1.5:
                ob_high = max(candle_open, candle_close)
                ob_low = min(candle_open, candle_close)

                if candle_close < candle_open and next_close > candle_open:
                    if ob_low <= close <= ob_high:
                        return StrategySignal(
                            signal=SignalType.BUY, confidence=0.7, risk_reward=2.5,
                            strategy_name=self.name, strategy_family=self.family,
                            reasoning="Price at bullish order block zone"
                        )
                elif candle_close > candle_open and next_close < candle_open:
                    if ob_low <= close <= ob_high:
                        return StrategySignal(
                            signal=SignalType.SELL, confidence=0.7, risk_reward=2.5,
                            strategy_name=self.name, strategy_family=self.family,
                            reasoning="Price at bearish order block zone"
                        )
        return self._no_signal()


class FairValueGaps(StrategyAgent):
    def __init__(self):
        super().__init__("Fair Value Gaps (FVG)", StrategyFamily.SMART_MONEY)

    def analyze(self, features: dict) -> StrategySignal:
        df = features["df"]
        if len(df) < 20:
            return self._no_signal()

        close = float(df["close"].iloc[-1])

        for i in range(-15, -2):
            high_prev = float(df["high"].iloc[i - 1])
            low_next = float(df["low"].iloc[i + 1])
            high_next = float(df["high"].iloc[i + 1])
            low_prev = float(df["low"].iloc[i - 1])

            if low_next > high_prev:
                fvg_top = low_next
                fvg_bottom = high_prev
                if fvg_bottom <= close <= fvg_top:
                    return StrategySignal(
                        signal=SignalType.BUY, confidence=0.7, risk_reward=2.5,
                        strategy_name=self.name, strategy_family=self.family,
                        reasoning="Price filling bullish FVG"
                    )
            elif high_next < low_prev:
                fvg_top = low_prev
                fvg_bottom = high_next
                if fvg_bottom <= close <= fvg_top:
                    return StrategySignal(
                        signal=SignalType.SELL, confidence=0.7, risk_reward=2.5,
                        strategy_name=self.name, strategy_family=self.family,
                        reasoning="Price filling bearish FVG"
                    )
        return self._no_signal()


class LiquiditySweeps(StrategyAgent):
    def __init__(self):
        super().__init__("Liquidity Sweeps", StrategyFamily.SMART_MONEY)

    def analyze(self, features: dict) -> StrategySignal:
        df = features["df"]
        if len(df) < 30:
            return self._no_signal()

        lookback = df.tail(30)
        equal_lows = []
        equal_highs = []

        for i in range(len(lookback) - 5):
            for j in range(i + 2, min(i + 10, len(lookback))):
                if abs(float(lookback["low"].iloc[i]) - float(lookback["low"].iloc[j])) / float(lookback["low"].iloc[i]) < 0.001:
                    equal_lows.append(float(lookback["low"].iloc[i]))
                if abs(float(lookback["high"].iloc[i]) - float(lookback["high"].iloc[j])) / float(lookback["high"].iloc[i]) < 0.001:
                    equal_highs.append(float(lookback["high"].iloc[i]))

        close = float(df["close"].iloc[-1])
        low = float(df["low"].iloc[-1])
        high = float(df["high"].iloc[-1])
        prev_close = float(df["close"].iloc[-2])

        for eq_low in equal_lows:
            if low < eq_low and close > eq_low and close > prev_close:
                return StrategySignal(
                    signal=SignalType.BUY, confidence=0.75, risk_reward=3.0,
                    strategy_name=self.name, strategy_family=self.family,
                    reasoning="Liquidity sweep below equal lows with reversal"
                )

        for eq_high in equal_highs:
            if high > eq_high and close < eq_high and close < prev_close:
                return StrategySignal(
                    signal=SignalType.SELL, confidence=0.75, risk_reward=3.0,
                    strategy_name=self.name, strategy_family=self.family,
                    reasoning="Liquidity sweep above equal highs with reversal"
                )
        return self._no_signal()


class StopHuntReversals(StrategyAgent):
    def __init__(self):
        super().__init__("Stop Hunt Reversals", StrategyFamily.SMART_MONEY)

    def analyze(self, features: dict) -> StrategySignal:
        df = features["df"]
        if len(df) < 20:
            return self._no_signal()

        recent_low = float(df["low"].tail(20).head(18).min())
        recent_high = float(df["high"].tail(20).head(18).max())
        close = float(df["close"].iloc[-1])
        low = float(df["low"].iloc[-1])
        high = float(df["high"].iloc[-1])
        prev_close = float(df["close"].iloc[-2])

        if low < recent_low and close > recent_low and close > prev_close:
            vol = self._safe_val(features["df"]["volume"])
            vol_avg = self._safe_val(features.get("volume_sma_20"))
            if vol_avg > 0 and vol > vol_avg * 1.3:
                return StrategySignal(
                    signal=SignalType.BUY, confidence=0.75, risk_reward=3.0,
                    strategy_name=self.name, strategy_family=self.family,
                    reasoning="Stop hunt below support with bullish reversal"
                )

        if high > recent_high and close < recent_high and close < prev_close:
            vol = self._safe_val(features["df"]["volume"])
            vol_avg = self._safe_val(features.get("volume_sma_20"))
            if vol_avg > 0 and vol > vol_avg * 1.3:
                return StrategySignal(
                    signal=SignalType.SELL, confidence=0.75, risk_reward=3.0,
                    strategy_name=self.name, strategy_family=self.family,
                    reasoning="Stop hunt above resistance with bearish reversal"
                )
        return self._no_signal()


class InstitutionalFootprint(StrategyAgent):
    def __init__(self):
        super().__init__("Institutional Footprint Zones", StrategyFamily.SMART_MONEY)

    def analyze(self, features: dict) -> StrategySignal:
        df = features["df"]
        if len(df) < 30 or "open" not in df.columns:
            return self._no_signal()

        close = float(df["close"].iloc[-1])
        vol_avg = self._safe_val(features.get("volume_sma_20"))

        institutional_zones = []
        for i in range(-25, -3):
            vol = float(df["volume"].iloc[i])
            if vol_avg > 0 and vol > vol_avg * 2:
                zone_high = max(float(df["open"].iloc[i]), float(df["close"].iloc[i]))
                zone_low = min(float(df["open"].iloc[i]), float(df["close"].iloc[i]))
                bullish = float(df["close"].iloc[i]) > float(df["open"].iloc[i])
                institutional_zones.append((zone_low, zone_high, bullish))

        for zone_low, zone_high, bullish in institutional_zones:
            if zone_low <= close <= zone_high:
                if bullish:
                    return StrategySignal(
                        signal=SignalType.BUY, confidence=0.7, risk_reward=2.5,
                        strategy_name=self.name, strategy_family=self.family,
                        reasoning="Price at bullish institutional footprint zone"
                    )
                else:
                    return StrategySignal(
                        signal=SignalType.SELL, confidence=0.7, risk_reward=2.5,
                        strategy_name=self.name, strategy_family=self.family,
                        reasoning="Price at bearish institutional footprint zone"
                    )
        return self._no_signal()


class BreakOfStructure(StrategyAgent):
    def __init__(self):
        super().__init__("Break of Structure (BOS)", StrategyFamily.SMART_MONEY)

    def analyze(self, features: dict) -> StrategySignal:
        df = features["df"]
        if len(df) < 30:
            return self._no_signal()

        highs = df["high"].tail(30)
        lows = df["low"].tail(30)
        close = float(df["close"].iloc[-1])

        swing_highs, swing_lows = [], []
        for i in range(2, len(highs) - 2):
            if float(highs.iloc[i]) > float(highs.iloc[i-1]) and float(highs.iloc[i]) > float(highs.iloc[i+1]):
                swing_highs.append(float(highs.iloc[i]))
            if float(lows.iloc[i]) < float(lows.iloc[i-1]) and float(lows.iloc[i]) < float(lows.iloc[i+1]):
                swing_lows.append(float(lows.iloc[i]))

        if len(swing_highs) >= 2 and close > swing_highs[-1]:
            return StrategySignal(
                signal=SignalType.BUY, confidence=0.75, risk_reward=2.5,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="Bullish Break of Structure - new swing high"
            )
        elif len(swing_lows) >= 2 and close < swing_lows[-1]:
            return StrategySignal(
                signal=SignalType.SELL, confidence=0.75, risk_reward=2.5,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="Bearish Break of Structure - new swing low"
            )
        return self._no_signal()


SMART_MONEY_STRATEGIES = [
    OrderBlocks(), FairValueGaps(), LiquiditySweeps(),
    StopHuntReversals(), InstitutionalFootprint(), BreakOfStructure()
]
