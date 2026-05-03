"""Feedback & Learning Loop - stores trade results, updates strategy weights and ML models."""
import logging
from datetime import datetime

from backend.agents.meta_agent import meta_agent
from backend.agents.performance_agent import performance_agent
from backend.models.signals import MetaSignal, StrategyFamily

logger = logging.getLogger(__name__)


class FeedbackAgent:
    """Manages the feedback loop for continuous improvement."""

    def __init__(self):
        self.trade_history: list[dict] = []
        self.weight_update_interval = 20
        self.learning_rate = 0.05

    def record_trade_result(self, execution: dict, outcome: str, pnl: float):
        """Record trade result and update strategy weights."""
        trade = {
            "timestamp": datetime.utcnow().isoformat(),
            "symbol": execution.get("symbol", ""),
            "signal": execution.get("signal", ""),
            "entry_price": execution.get("entry_price", 0),
            "stop_loss": execution.get("stop_loss", 0),
            "take_profit": execution.get("take_profit", 0),
            "outcome": outcome,
            "pnl": pnl,
            "confidence": execution.get("confidence", 0),
            "score": execution.get("score", 0),
            "top_strategies": execution.get("top_strategies", []),
        }
        self.trade_history.append(trade)

        for strat in execution.get("top_strategies", []):
            name = strat.get("name", "")
            family_str = strat.get("family", "TREND")
            try:
                family = StrategyFamily(family_str)
            except ValueError:
                family = StrategyFamily.TREND
            performance_agent.record_trade(name, family, pnl, execution.get("risk_reward", 0))

        self._update_weights(execution, outcome, pnl)

        if len(self.trade_history) % self.weight_update_interval == 0:
            self._recalibrate_weights()

    def _update_weights(self, execution: dict, outcome: str, pnl: float):
        """Incremental weight update based on trade result."""
        for strat in execution.get("top_strategies", []):
            name = strat.get("name", "")
            current_weight = meta_agent.strategy_weights.get(name, 1.0)

            if outcome == "WIN":
                new_weight = current_weight + self.learning_rate * strat.get("confidence", 0)
            else:
                new_weight = current_weight - self.learning_rate * strat.get("confidence", 0)

            meta_agent.update_strategy_weight(name, new_weight)

    def _recalibrate_weights(self):
        """Periodic recalibration of all strategy weights based on performance."""
        all_perf = performance_agent.get_all_performance()
        for perf in all_perf:
            name = perf["strategy_name"]
            if perf["total_trades"] < 5:
                continue

            score = (perf["win_rate"] / 100 * 0.4 +
                    min(perf["total_profit"] / 1000, 1) * 0.3 +
                    min(perf["avg_rr"] / 3, 1) * 0.3)

            new_weight = 0.5 + score * 2
            meta_agent.update_strategy_weight(name, new_weight)

        # Sync active status
        for perf in all_perf:
            meta_agent.toggle_strategy(perf["strategy_name"], perf["is_active"])

        logger.info(f"Recalibrated weights for {len(all_perf)} strategies")

    def get_trade_history(self, limit: int = 50) -> list[dict]:
        return self.trade_history[-limit:]

    def get_equity_curve(self) -> list[dict]:
        """Generate equity curve from trade history."""
        curve = []
        equity = 10000.0
        for trade in self.trade_history:
            equity += trade.get("pnl", 0)
            curve.append({
                "timestamp": trade["timestamp"],
                "equity": round(equity, 2),
                "pnl": trade.get("pnl", 0),
            })
        return curve

    def get_analytics(self) -> dict:
        """Get comprehensive analytics."""
        if not self.trade_history:
            return {
                "total_trades": 0, "wins": 0, "losses": 0,
                "win_rate": 0, "total_pnl": 0, "avg_pnl": 0,
                "max_win": 0, "max_loss": 0, "profit_factor": 0,
            }

        wins = [t for t in self.trade_history if t.get("pnl", 0) > 0]
        losses = [t for t in self.trade_history if t.get("pnl", 0) <= 0]
        pnls = [t.get("pnl", 0) for t in self.trade_history]

        total_wins = sum(t.get("pnl", 0) for t in wins)
        total_losses = abs(sum(t.get("pnl", 0) for t in losses))

        return {
            "total_trades": len(self.trade_history),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": round(len(wins) / len(self.trade_history) * 100, 1),
            "total_pnl": round(sum(pnls), 2),
            "avg_pnl": round(sum(pnls) / len(pnls), 2),
            "max_win": round(max(pnls), 2) if pnls else 0,
            "max_loss": round(min(pnls), 2) if pnls else 0,
            "profit_factor": round(total_wins / total_losses, 2) if total_losses > 0 else 0,
        }


feedback_agent = FeedbackAgent()
