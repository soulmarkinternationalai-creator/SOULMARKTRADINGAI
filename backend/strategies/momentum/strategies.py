"""Momentum strategy agents (8 strategies)."""
from backend.strategies.base import StrategyAgent
from backend.models.signals import StrategySignal, SignalType, StrategyFamily


class RSIMomentum(StrategyAgent):
    def __init__(self):
        super().__init__("RSI Momentum Continuation", StrategyFamily.MOMENTUM)

    def analyze(self, features: dict) -> StrategySignal:
        rsi = self._safe_val(features.get("rsi_14"))
        rsi_prev = self._safe_val(features.get("rsi_14"), -2)
        close = self._safe_val(features["df"]["close"])
        prev_close = self._safe_val(features["df"]["close"], -2)

        if 50 < rsi < 70 and rsi > rsi_prev and close > prev_close:
            return StrategySignal(
                signal=SignalType.BUY, confidence=0.65, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning=f"RSI bullish momentum at {rsi:.1f}"
            )
        elif 30 < rsi < 50 and rsi < rsi_prev and close < prev_close:
            return StrategySignal(
                signal=SignalType.SELL, confidence=0.65, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning=f"RSI bearish momentum at {rsi:.1f}"
            )
        return self._no_signal()


class MACDAcceleration(StrategyAgent):
    def __init__(self):
        super().__init__("MACD Acceleration", StrategyFamily.MOMENTUM)

    def analyze(self, features: dict) -> StrategySignal:
        hist = self._safe_val(features.get("macd_histogram"))
        hist_prev = self._safe_val(features.get("macd_histogram"), -2)
        macd_line = self._safe_val(features.get("macd_line"))
        signal_line = self._safe_val(features.get("macd_signal"))

        if hist > 0 and hist > hist_prev and macd_line > signal_line:
            return StrategySignal(
                signal=SignalType.BUY, confidence=0.7, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="MACD histogram accelerating bullish"
            )
        elif hist < 0 and hist < hist_prev and macd_line < signal_line:
            return StrategySignal(
                signal=SignalType.SELL, confidence=0.7, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="MACD histogram accelerating bearish"
            )
        return self._no_signal()


class StrongCandleMomentum(StrategyAgent):
    def __init__(self):
        super().__init__("Strong Candle Momentum", StrategyFamily.MOMENTUM)

    def analyze(self, features: dict) -> StrategySignal:
        df = features["df"]
        if len(df) < 5:
            return self._no_signal()

        close = float(df["close"].iloc[-1])
        open_p = float(df["open"].iloc[-1]) if "open" in df.columns else float(df["close"].iloc[-2])
        high = float(df["high"].iloc[-1])
        low = float(df["low"].iloc[-1])
        atr_val = self._safe_val(features.get("atr_14"))

        body = abs(close - open_p)
        total_range = high - low if high != low else 0.001

        if atr_val > 0 and body > atr_val * 1.5 and body / total_range > 0.7:
            if close > open_p:
                return StrategySignal(
                    signal=SignalType.BUY, confidence=0.7, risk_reward=2.0,
                    strategy_name=self.name, strategy_family=self.family,
                    reasoning="Strong bullish candle (body > 1.5x ATR)"
                )
            else:
                return StrategySignal(
                    signal=SignalType.SELL, confidence=0.7, risk_reward=2.0,
                    strategy_name=self.name, strategy_family=self.family,
                    reasoning="Strong bearish candle (body > 1.5x ATR)"
                )
        return self._no_signal()


class VolumeSpikeBreakout(StrategyAgent):
    def __init__(self):
        super().__init__("Volume Spike Breakout", StrategyFamily.MOMENTUM)

    def analyze(self, features: dict) -> StrategySignal:
        vol = self._safe_val(features["df"]["volume"])
        vol_avg = self._safe_val(features.get("volume_sma_20"))
        close = self._safe_val(features["df"]["close"])
        prev_close = self._safe_val(features["df"]["close"], -2)

        if vol_avg > 0 and vol > vol_avg * 2.5:
            if close > prev_close:
                return StrategySignal(
                    signal=SignalType.BUY, confidence=0.7, risk_reward=2.0,
                    strategy_name=self.name, strategy_family=self.family,
                    reasoning=f"Volume spike ({vol/vol_avg:.1f}x avg) with bullish move"
                )
            else:
                return StrategySignal(
                    signal=SignalType.SELL, confidence=0.7, risk_reward=2.0,
                    strategy_name=self.name, strategy_family=self.family,
                    reasoning=f"Volume spike ({vol/vol_avg:.1f}x avg) with bearish move"
                )
        return self._no_signal()


class MultiCandleMomentum(StrategyAgent):
    def __init__(self):
        super().__init__("Multi-Candle Momentum Burst", StrategyFamily.MOMENTUM)

    def analyze(self, features: dict) -> StrategySignal:
        df = features["df"]
        if len(df) < 5:
            return self._no_signal()

        bullish_count = sum(1 for i in range(-3, 0) if float(df["close"].iloc[i]) > float(df["open"].iloc[i]) if "open" in df.columns)
        bearish_count = sum(1 for i in range(-3, 0) if float(df["close"].iloc[i]) < float(df["open"].iloc[i]) if "open" in df.columns)

        if bullish_count == 3:
            return StrategySignal(
                signal=SignalType.BUY, confidence=0.65, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="3 consecutive bullish candles"
            )
        elif bearish_count == 3:
            return StrategySignal(
                signal=SignalType.SELL, confidence=0.65, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="3 consecutive bearish candles"
            )
        return self._no_signal()


class MomentumDivergence(StrategyAgent):
    def __init__(self):
        super().__init__("Momentum Divergence", StrategyFamily.MOMENTUM)

    def analyze(self, features: dict) -> StrategySignal:
        df = features["df"]
        rsi = features.get("rsi_14")
        if rsi is None or len(df) < 20:
            return self._no_signal()

        price_low1 = float(df["low"].tail(20).head(10).min())
        price_low2 = float(df["low"].tail(10).min())
        rsi_at_low1 = float(rsi.tail(20).head(10).min())
        rsi_at_low2 = float(rsi.tail(10).min())

        if price_low2 < price_low1 and rsi_at_low2 > rsi_at_low1:
            return StrategySignal(
                signal=SignalType.BUY, confidence=0.75, risk_reward=2.5,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="Bullish RSI divergence"
            )

        price_high1 = float(df["high"].tail(20).head(10).max())
        price_high2 = float(df["high"].tail(10).max())
        rsi_at_high1 = float(rsi.tail(20).head(10).max())
        rsi_at_high2 = float(rsi.tail(10).max())

        if price_high2 > price_high1 and rsi_at_high2 < rsi_at_high1:
            return StrategySignal(
                signal=SignalType.SELL, confidence=0.75, risk_reward=2.5,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="Bearish RSI divergence"
            )
        return self._no_signal()


class ImpulseWaveDetection(StrategyAgent):
    def __init__(self):
        super().__init__("Impulse Wave Detection", StrategyFamily.MOMENTUM)

    def analyze(self, features: dict) -> StrategySignal:
        df = features["df"]
        if len(df) < 10:
            return self._no_signal()

        atr_val = self._safe_val(features.get("atr_14"))
        close = float(df["close"].iloc[-1])
        close_5_ago = float(df["close"].iloc[-5])

        if atr_val > 0:
            move = abs(close - close_5_ago) / atr_val
            if move > 3:
                if close > close_5_ago:
                    return StrategySignal(
                        signal=SignalType.BUY, confidence=0.7, risk_reward=2.0,
                        strategy_name=self.name, strategy_family=self.family,
                        reasoning=f"Bullish impulse wave ({move:.1f}x ATR in 5 bars)"
                    )
                else:
                    return StrategySignal(
                        signal=SignalType.SELL, confidence=0.7, risk_reward=2.0,
                        strategy_name=self.name, strategy_family=self.family,
                        reasoning=f"Bearish impulse wave ({move:.1f}x ATR in 5 bars)"
                    )
        return self._no_signal()


class BreakMomentumConfirmation(StrategyAgent):
    def __init__(self):
        super().__init__("Break + Momentum Confirmation", StrategyFamily.MOMENTUM)

    def analyze(self, features: dict) -> StrategySignal:
        df = features["df"]
        if len(df) < 20:
            return self._no_signal()

        close = float(df["close"].iloc[-1])
        high_20 = float(df["high"].tail(20).head(19).max())
        low_20 = float(df["low"].tail(20).head(19).min())
        rsi = self._safe_val(features.get("rsi_14"))
        vol = self._safe_val(features["df"]["volume"])
        vol_avg = self._safe_val(features.get("volume_sma_20"))

        vol_confirm = vol_avg > 0 and vol > vol_avg * 1.5

        if close > high_20 and rsi > 50 and vol_confirm:
            return StrategySignal(
                signal=SignalType.BUY, confidence=0.75, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="Breakout with RSI + volume momentum confirmation"
            )
        elif close < low_20 and rsi < 50 and vol_confirm:
            return StrategySignal(
                signal=SignalType.SELL, confidence=0.75, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="Breakdown with RSI + volume momentum confirmation"
            )
        return self._no_signal()


MOMENTUM_STRATEGIES = [
    RSIMomentum(), MACDAcceleration(), StrongCandleMomentum(),
    VolumeSpikeBreakout(), MultiCandleMomentum(), MomentumDivergence(),
    ImpulseWaveDetection(), BreakMomentumConfirmation()
]
