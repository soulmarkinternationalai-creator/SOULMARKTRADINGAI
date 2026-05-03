"""AI-driven strategy agents (6 strategies)."""
import numpy as np
from backend.strategies.base import StrategyAgent
from backend.models.signals import StrategySignal, SignalType, StrategyFamily


class MLClassifier(StrategyAgent):
    """ML classifier using feature-based logistic-style scoring."""
    def __init__(self):
        super().__init__("ML Classifier", StrategyFamily.AI_DRIVEN)
        self._weights = None

    def analyze(self, features: dict) -> StrategySignal:
        rsi = self._safe_val(features.get("rsi_14"))
        trend = features.get("trend_strength", 0.5)
        vol_ratio = features.get("volatility_ratio", 1.0)
        z = self._safe_val(features.get("zscore"))
        macd_h = self._safe_val(features.get("macd_histogram"))

        score = (
            (rsi - 50) / 50 * 0.25 +
            (trend - 0.5) * 0.3 +
            (1 if macd_h > 0 else -1) * 0.2 +
            (-z * 0.15) +
            (vol_ratio - 1) * 0.1
        )

        prob = 1 / (1 + np.exp(-score * 3))

        if prob > 0.65:
            return StrategySignal(
                signal=SignalType.BUY, confidence=prob, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning=f"ML buy probability: {prob:.2f}"
            )
        elif prob < 0.35:
            return StrategySignal(
                signal=SignalType.SELL, confidence=1 - prob, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning=f"ML sell probability: {1 - prob:.2f}"
            )
        return self._no_signal()


class RLPolicy(StrategyAgent):
    """Reinforcement learning policy using Q-value approximation."""
    def __init__(self):
        super().__init__("RL Policy Agent", StrategyFamily.AI_DRIVEN)
        self._q_table = {}

    def analyze(self, features: dict) -> StrategySignal:
        rsi = self._safe_val(features.get("rsi_14"))
        trend = features.get("trend_strength", 0.5)
        regime = str(features.get("regime", "UNKNOWN"))

        rsi_state = "low" if rsi < 40 else "high" if rsi > 60 else "mid"
        trend_state = "up" if trend > 0.6 else "down" if trend < 0.4 else "flat"

        state = f"{rsi_state}_{trend_state}_{regime}"

        q_buy = self._q_table.get(f"{state}_BUY", 0)
        q_sell = self._q_table.get(f"{state}_SELL", 0)
        q_none = self._q_table.get(f"{state}_NONE", 0)

        if q_buy == q_sell == q_none == 0:
            if rsi_state == "low" and trend_state == "up":
                q_buy = 0.7
            elif rsi_state == "high" and trend_state == "down":
                q_sell = 0.7
            elif trend_state == "up":
                q_buy = 0.5
            elif trend_state == "down":
                q_sell = 0.5

        if q_buy > q_sell and q_buy > q_none and q_buy > 0.3:
            return StrategySignal(
                signal=SignalType.BUY, confidence=min(q_buy, 0.9), risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning=f"RL policy: Q(buy)={q_buy:.2f}"
            )
        elif q_sell > q_buy and q_sell > q_none and q_sell > 0.3:
            return StrategySignal(
                signal=SignalType.SELL, confidence=min(q_sell, 0.9), risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning=f"RL policy: Q(sell)={q_sell:.2f}"
            )
        return self._no_signal()

    def update(self, state: str, action: str, reward: float, lr: float = 0.1):
        key = f"{state}_{action}"
        old_q = self._q_table.get(key, 0)
        self._q_table[key] = old_q + lr * (reward - old_q)


class PatternRecognition(StrategyAgent):
    """Candlestick pattern recognition."""
    def __init__(self):
        super().__init__("Pattern Recognition", StrategyFamily.AI_DRIVEN)

    def analyze(self, features: dict) -> StrategySignal:
        df = features["df"]
        if len(df) < 5 or "open" not in df.columns:
            return self._no_signal()

        c = [float(df["close"].iloc[i]) for i in range(-3, 0)]
        o = [float(df["open"].iloc[i]) for i in range(-3, 0)]
        h = [float(df["high"].iloc[i]) for i in range(-3, 0)]
        l = [float(df["low"].iloc[i]) for i in range(-3, 0)]

        body_2 = abs(c[-1] - o[-1])
        upper_wick = h[-1] - max(c[-1], o[-1])
        lower_wick = min(c[-1], o[-1]) - l[-1]

        if body_2 > 0 and lower_wick > body_2 * 2 and upper_wick < body_2 * 0.5:
            return StrategySignal(
                signal=SignalType.BUY, confidence=0.7, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="Hammer/pin bar pattern detected"
            )
        elif body_2 > 0 and upper_wick > body_2 * 2 and lower_wick < body_2 * 0.5:
            return StrategySignal(
                signal=SignalType.SELL, confidence=0.7, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="Shooting star pattern detected"
            )

        if c[-3] < o[-3] and c[-2] < o[-2] and c[-1] > o[-1] and c[-1] > o[-2]:
            return StrategySignal(
                signal=SignalType.BUY, confidence=0.65, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="Bullish engulfing pattern"
            )
        elif c[-3] > o[-3] and c[-2] > o[-2] and c[-1] < o[-1] and c[-1] < o[-2]:
            return StrategySignal(
                signal=SignalType.SELL, confidence=0.65, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning="Bearish engulfing pattern"
            )
        return self._no_signal()


class SentimentTrading(StrategyAgent):
    """Sentiment-based trading using price action as proxy."""
    def __init__(self):
        super().__init__("Sentiment Analysis", StrategyFamily.AI_DRIVEN)

    def analyze(self, features: dict) -> StrategySignal:
        df = features["df"]
        if len(df) < 20:
            return self._no_signal()

        close = df["close"].tail(20)
        returns = close.pct_change().dropna()
        positive = (returns > 0).sum()
        negative = (returns < 0).sum()
        total = len(returns)

        if total == 0:
            return self._no_signal()

        sentiment = (positive - negative) / total
        vol_trend = float(df["volume"].tail(5).mean()) / float(df["volume"].tail(20).mean()) if float(df["volume"].tail(20).mean()) > 0 else 1

        if sentiment > 0.3 and vol_trend > 1.2:
            return StrategySignal(
                signal=SignalType.BUY, confidence=0.6, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning=f"Bullish sentiment ({sentiment:.2f}) with rising volume"
            )
        elif sentiment < -0.3 and vol_trend > 1.2:
            return StrategySignal(
                signal=SignalType.SELL, confidence=0.6, risk_reward=2.0,
                strategy_name=self.name, strategy_family=self.family,
                reasoning=f"Bearish sentiment ({sentiment:.2f}) with rising volume"
            )
        return self._no_signal()


class RegimeSwitching(StrategyAgent):
    """Regime-switching model."""
    def __init__(self):
        super().__init__("Regime Switching Model", StrategyFamily.AI_DRIVEN)

    def analyze(self, features: dict) -> StrategySignal:
        regime = str(features.get("regime", "UNKNOWN"))
        trend = features.get("trend_strength", 0.5)
        rsi = self._safe_val(features.get("rsi_14"))

        if regime == "TRENDING":
            if trend > 0.6:
                return StrategySignal(
                    signal=SignalType.BUY, confidence=0.7, risk_reward=2.0,
                    strategy_name=self.name, strategy_family=self.family,
                    reasoning="Trending regime - following uptrend"
                )
            elif trend < 0.4:
                return StrategySignal(
                    signal=SignalType.SELL, confidence=0.7, risk_reward=2.0,
                    strategy_name=self.name, strategy_family=self.family,
                    reasoning="Trending regime - following downtrend"
                )
        elif regime == "RANGING":
            if rsi < 30:
                return StrategySignal(
                    signal=SignalType.BUY, confidence=0.65, risk_reward=1.5,
                    strategy_name=self.name, strategy_family=self.family,
                    reasoning="Ranging regime - RSI oversold reversion"
                )
            elif rsi > 70:
                return StrategySignal(
                    signal=SignalType.SELL, confidence=0.65, risk_reward=1.5,
                    strategy_name=self.name, strategy_family=self.family,
                    reasoning="Ranging regime - RSI overbought reversion"
                )
        return self._no_signal()


class EnsemblePredictor(StrategyAgent):
    """Ensemble predictor combining multiple signal types."""
    def __init__(self):
        super().__init__("Ensemble Predictor", StrategyFamily.AI_DRIVEN)

    def analyze(self, features: dict) -> StrategySignal:
        rsi = self._safe_val(features.get("rsi_14"))
        macd_h = self._safe_val(features.get("macd_histogram"))
        trend = features.get("trend_strength", 0.5)
        z = self._safe_val(features.get("zscore"))
        vol_ratio = features.get("volatility_ratio", 1.0)

        votes = {"BUY": 0, "SELL": 0}

        if rsi < 40: votes["BUY"] += 1
        elif rsi > 60: votes["SELL"] += 1

        if macd_h > 0: votes["BUY"] += 1
        elif macd_h < 0: votes["SELL"] += 1

        if trend > 0.6: votes["BUY"] += 1
        elif trend < 0.4: votes["SELL"] += 1

        if z < -1: votes["BUY"] += 1
        elif z > 1: votes["SELL"] += 1

        if vol_ratio > 1.3:
            close = self._safe_val(features["df"]["close"])
            prev = self._safe_val(features["df"]["close"], -2)
            if close > prev: votes["BUY"] += 1
            else: votes["SELL"] += 1

        max_votes = max(votes["BUY"], votes["SELL"])
        if max_votes >= 3:
            if votes["BUY"] > votes["SELL"]:
                return StrategySignal(
                    signal=SignalType.BUY, confidence=0.5 + max_votes * 0.1,
                    risk_reward=2.0, strategy_name=self.name, strategy_family=self.family,
                    reasoning=f"Ensemble: {votes['BUY']}/5 indicators bullish"
                )
            else:
                return StrategySignal(
                    signal=SignalType.SELL, confidence=0.5 + max_votes * 0.1,
                    risk_reward=2.0, strategy_name=self.name, strategy_family=self.family,
                    reasoning=f"Ensemble: {votes['SELL']}/5 indicators bearish"
                )
        return self._no_signal()


AI_DRIVEN_STRATEGIES = [
    MLClassifier(), RLPolicy(), PatternRecognition(),
    SentimentTrading(), RegimeSwitching(), EnsemblePredictor()
]
