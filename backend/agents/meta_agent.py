"""Meta Agent - THE BRAIN. Collects all signals, weights them, resolves conflicts, makes final decision."""
import logging
from datetime import datetime

from backend.models.signals import (
    StrategySignal, MetaSignal, SignalType, StrategyFamily, MarketRegime
)
from backend.strategies.base import StrategyAgent
from backend.strategies.trend.strategies import TREND_STRATEGIES
from backend.strategies.mean_reversion.strategies import MEAN_REVERSION_STRATEGIES
from backend.strategies.breakout.strategies import BREAKOUT_STRATEGIES
from backend.strategies.momentum.strategies import MOMENTUM_STRATEGIES
from backend.strategies.smart_money.strategies import SMART_MONEY_STRATEGIES
from backend.strategies.volatility.strategies import VOLATILITY_STRATEGIES
from backend.strategies.ai_driven.strategies import AI_DRIVEN_STRATEGIES
from backend.config.settings import settings

logger = logging.getLogger(__name__)

# Regime-dependent family weights
REGIME_WEIGHTS = {
    MarketRegime.TRENDING: {
        StrategyFamily.TREND: 2.0,
        StrategyFamily.MEAN_REVERSION: 0.5,
        StrategyFamily.BREAKOUT: 1.5,
        StrategyFamily.MOMENTUM: 1.5,
        StrategyFamily.SMART_MONEY: 1.2,
        StrategyFamily.VOLATILITY: 0.8,
        StrategyFamily.AI_DRIVEN: 1.0,
    },
    MarketRegime.RANGING: {
        StrategyFamily.TREND: 0.5,
        StrategyFamily.MEAN_REVERSION: 2.0,
        StrategyFamily.BREAKOUT: 0.5,
        StrategyFamily.MOMENTUM: 0.8,
        StrategyFamily.SMART_MONEY: 1.5,
        StrategyFamily.VOLATILITY: 1.2,
        StrategyFamily.AI_DRIVEN: 1.0,
    },
    MarketRegime.VOLATILE: {
        StrategyFamily.TREND: 0.8,
        StrategyFamily.MEAN_REVERSION: 0.5,
        StrategyFamily.BREAKOUT: 2.0,
        StrategyFamily.MOMENTUM: 1.5,
        StrategyFamily.SMART_MONEY: 1.0,
        StrategyFamily.VOLATILITY: 2.0,
        StrategyFamily.AI_DRIVEN: 1.2,
    },
    MarketRegime.UNKNOWN: {
        StrategyFamily.TREND: 1.0,
        StrategyFamily.MEAN_REVERSION: 1.0,
        StrategyFamily.BREAKOUT: 1.0,
        StrategyFamily.MOMENTUM: 1.0,
        StrategyFamily.SMART_MONEY: 1.0,
        StrategyFamily.VOLATILITY: 1.0,
        StrategyFamily.AI_DRIVEN: 1.0,
    },
}


class MetaAgent:
    """Aggregates signals from 50+ strategies into a single trading decision."""

    def __init__(self):
        self.all_strategies: list[StrategyAgent] = (
            TREND_STRATEGIES + MEAN_REVERSION_STRATEGIES +
            BREAKOUT_STRATEGIES + MOMENTUM_STRATEGIES +
            SMART_MONEY_STRATEGIES + VOLATILITY_STRATEGIES +
            AI_DRIVEN_STRATEGIES
        )
        self.strategy_weights: dict[str, float] = {
            s.name: 1.0 for s in self.all_strategies
        }

    def analyze_all(self, features: dict) -> tuple[list[StrategySignal], MetaSignal]:
        """Run all strategies and produce a meta signal."""
        regime = features.get("regime", MarketRegime.UNKNOWN)
        regime_weights = REGIME_WEIGHTS.get(regime, REGIME_WEIGHTS[MarketRegime.UNKNOWN])

        signals: list[StrategySignal] = []
        for strategy in self.all_strategies:
            if not strategy.is_active:
                continue
            try:
                signal = strategy.analyze(features)
                signals.append(signal)
            except Exception as e:
                logger.warning(f"Strategy {strategy.name} failed: {e}")

        score = 0.0
        family_scores: dict[str, float] = {}
        top_strategies = []

        for sig in signals:
            if sig.signal == SignalType.NONE:
                continue

            family_weight = regime_weights.get(sig.strategy_family, 1.0)
            strategy_weight = self.strategy_weights.get(sig.strategy_name, 1.0)
            weighted_confidence = sig.confidence * family_weight * strategy_weight

            if sig.signal == SignalType.BUY:
                score += weighted_confidence
            elif sig.signal == SignalType.SELL:
                score -= weighted_confidence

            family_name = sig.strategy_family.value
            if family_name not in family_scores:
                family_scores[family_name] = 0.0
            if sig.signal == SignalType.BUY:
                family_scores[family_name] += weighted_confidence
            elif sig.signal == SignalType.SELL:
                family_scores[family_name] -= weighted_confidence

            top_strategies.append({
                "name": sig.strategy_name,
                "family": sig.strategy_family.value,
                "signal": sig.signal.value,
                "confidence": round(weighted_confidence, 2),
                "reasoning": sig.reasoning
            })

        top_strategies.sort(key=lambda x: abs(x["confidence"]), reverse=True)

        # Decision
        buy_threshold = settings.trading.buy_threshold
        sell_threshold = settings.trading.sell_threshold

        if score > buy_threshold:
            final_signal = SignalType.BUY
        elif score < sell_threshold:
            final_signal = SignalType.SELL
        else:
            final_signal = SignalType.NONE

        close = float(features["df"]["close"].iloc[-1])
        atr_val = float(features.get("atr_14", features["df"]["close"]).iloc[-1]) if "atr_14" in features else close * 0.01

        if final_signal == SignalType.BUY:
            entry = close
            sl = close - 2 * atr_val
            tp = close + 4 * atr_val
        elif final_signal == SignalType.SELL:
            entry = close
            sl = close + 2 * atr_val
            tp = close - 4 * atr_val
        else:
            entry = close
            sl = close
            tp = close

        rr = abs(tp - entry) / abs(sl - entry) if abs(sl - entry) > 0 else 0

        active_count = sum(1 for s in signals if s.signal != SignalType.NONE)
        agreeing = sum(1 for s in signals
                      if (s.signal == SignalType.BUY and score > 0) or
                         (s.signal == SignalType.SELL and score < 0))

        overall_confidence = min(abs(score) / 10, 1.0)

        meta_signal = MetaSignal(
            signal=final_signal,
            total_score=round(score, 2),
            confidence=round(overall_confidence, 2),
            entry_price=round(entry, 5),
            stop_loss=round(sl, 5),
            take_profit=round(tp, 5),
            risk_reward=round(rr, 2),
            family_scores={k: round(v, 2) for k, v in family_scores.items()},
            top_strategies=top_strategies[:10],
            active_strategies=active_count,
            agreeing_strategies=agreeing,
            timestamp=datetime.utcnow()
        )

        return signals, meta_signal

    def update_strategy_weight(self, strategy_name: str, weight: float):
        self.strategy_weights[strategy_name] = max(0.1, min(3.0, weight))

    def toggle_strategy(self, strategy_name: str, active: bool):
        for s in self.all_strategies:
            if s.name == strategy_name:
                s.is_active = active
                break

    def get_strategy_count(self) -> int:
        return len(self.all_strategies)

    def get_active_count(self) -> int:
        return sum(1 for s in self.all_strategies if s.is_active)


meta_agent = MetaAgent()
