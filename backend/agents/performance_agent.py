"""Performance Tracking Agent - tracks strategy performance and auto-disables bad strategies."""
import logging
from datetime import datetime

from backend.models.signals import StrategyPerformance, StrategyFamily

logger = logging.getLogger(__name__)


class PerformanceAgent:
    """Tracks and manages strategy performance."""

    def __init__(self):
        self.performance: dict[str, StrategyPerformance] = {}
        self.min_trades_for_eval = 10
        self.min_win_rate = 0.35
        self.auto_disable_enabled = True

    def record_trade(self, strategy_name: str, family: StrategyFamily,
                     pnl: float, rr: float):
        """Record a trade result for a strategy."""
        if strategy_name not in self.performance:
            self.performance[strategy_name] = StrategyPerformance(
                strategy_name=strategy_name,
                strategy_family=family,
            )

        perf = self.performance[strategy_name]
        perf.total_trades += 1
        perf.total_profit += pnl

        if pnl > 0:
            perf.wins += 1
        else:
            perf.losses += 1

        perf.win_rate = perf.wins / perf.total_trades if perf.total_trades > 0 else 0
        perf.avg_rr = ((perf.avg_rr * (perf.total_trades - 1)) + rr) / perf.total_trades

        if pnl < 0:
            perf.max_drawdown = max(perf.max_drawdown, abs(pnl))

        if self.auto_disable_enabled:
            self._evaluate_strategy(strategy_name)

    def _evaluate_strategy(self, strategy_name: str):
        """Auto-disable strategies that perform poorly."""
        perf = self.performance.get(strategy_name)
        if not perf or perf.total_trades < self.min_trades_for_eval:
            return

        if perf.win_rate < self.min_win_rate and perf.total_profit < 0:
            perf.is_active = False
            logger.info(f"Auto-disabled strategy: {strategy_name} "
                       f"(win rate: {perf.win_rate:.1%}, profit: {perf.total_profit:.2f})")

    def get_all_performance(self) -> list[dict]:
        """Get performance data for all strategies."""
        return [
            {
                "strategy_name": p.strategy_name,
                "strategy_family": p.strategy_family.value,
                "win_rate": round(p.win_rate * 100, 1),
                "total_profit": round(p.total_profit, 2),
                "total_trades": p.total_trades,
                "wins": p.wins,
                "losses": p.losses,
                "avg_rr": round(p.avg_rr, 2),
                "max_drawdown": round(p.max_drawdown, 2),
                "is_active": p.is_active,
                "weight": p.weight,
            }
            for p in self.performance.values()
        ]

    def get_family_performance(self) -> dict[str, dict]:
        """Get aggregated performance by strategy family."""
        families: dict[str, dict] = {}
        for p in self.performance.values():
            family = p.strategy_family.value
            if family not in families:
                families[family] = {"trades": 0, "wins": 0, "profit": 0.0}
            families[family]["trades"] += p.total_trades
            families[family]["wins"] += p.wins
            families[family]["profit"] += p.total_profit

        for f in families.values():
            f["win_rate"] = round(f["wins"] / f["trades"] * 100, 1) if f["trades"] > 0 else 0

        return families

    def toggle_auto_disable(self, enabled: bool):
        self.auto_disable_enabled = enabled

    def manually_enable(self, strategy_name: str):
        if strategy_name in self.performance:
            self.performance[strategy_name].is_active = True


performance_agent = PerformanceAgent()
