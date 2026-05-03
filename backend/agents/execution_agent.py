"""Execution Agent - prepares final trade signal with entry, SL, TP."""
import logging
from datetime import datetime

from backend.models.signals import MetaSignal, SignalType

logger = logging.getLogger(__name__)


class ExecutionAgent:
    """Handles trade execution decisions and signal preparation."""

    def __init__(self):
        self.auto_trade = False
        self.pending_signals: list[dict] = []

    def prepare_execution(self, signal: MetaSignal, risk_assessment: dict,
                          filter_result: tuple[bool, list[str]], symbol: str) -> dict:
        """Prepare final execution signal."""
        should_trade, filter_reasons = filter_result

        execution = {
            "timestamp": datetime.utcnow().isoformat(),
            "symbol": symbol,
            "signal": signal.signal.value,
            "confidence": signal.confidence,
            "score": signal.total_score,
            "entry_price": signal.entry_price,
            "stop_loss": signal.stop_loss,
            "take_profit": signal.take_profit,
            "risk_reward": signal.risk_reward,
            "lot_size": risk_assessment.get("lot_size", 0),
            "risk_amount": risk_assessment.get("risk_amount", 0),
            "risk_percent": risk_assessment.get("risk_percent", 0),
            "filters_passed": should_trade,
            "filter_reasons": filter_reasons,
            "risk_approved": risk_assessment.get("approved", False),
            "risk_reason": risk_assessment.get("reason", ""),
            "auto_trade": self.auto_trade,
            "family_scores": signal.family_scores,
            "top_strategies": signal.top_strategies[:5],
            "active_strategies": signal.active_strategies,
            "agreeing_strategies": signal.agreeing_strategies,
            "executable": should_trade and risk_assessment.get("approved", False),
        }

        if execution["executable"]:
            self.pending_signals.append(execution)
            logger.info(f"Signal prepared: {signal.signal.value} {symbol} @ {signal.entry_price}")

        return execution

    def toggle_auto_trade(self, enabled: bool):
        self.auto_trade = enabled

    def get_pending_signals(self) -> list[dict]:
        return self.pending_signals.copy()

    def clear_pending(self):
        self.pending_signals.clear()

    def force_signal(self, signal_type: str, symbol: str, entry: float,
                     sl: float, tp: float) -> dict:
        """Force a manual signal."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "symbol": symbol,
            "signal": signal_type,
            "entry_price": entry,
            "stop_loss": sl,
            "take_profit": tp,
            "risk_reward": round(abs(tp - entry) / abs(sl - entry), 2) if abs(sl - entry) > 0 else 0,
            "manual": True,
            "executable": True,
        }


execution_agent = ExecutionAgent()
