"""Risk Agent - protects capital with dynamic lot sizing, drawdown limits, and SL/TP optimization."""
from backend.models.signals import MetaSignal, SignalType
from backend.config.settings import settings


class RiskAgent:
    """Manages risk for all trades."""

    def __init__(self):
        self.balance = 10000.0
        self.equity = 10000.0
        self.daily_pnl = 0.0
        self.open_trades = 0
        self.max_risk_per_trade = settings.risk.max_risk_per_trade
        self.max_daily_drawdown = settings.risk.max_daily_drawdown
        self.max_open_trades = settings.risk.max_open_trades

    def assess_risk(self, signal: MetaSignal) -> dict:
        """Assess risk and calculate position sizing."""
        if signal.signal == SignalType.NONE:
            return {"approved": False, "reason": "No signal"}

        if self.open_trades >= self.max_open_trades:
            return {"approved": False, "reason": f"Max open trades ({self.max_open_trades}) reached"}

        daily_dd = abs(min(self.daily_pnl, 0)) / self.balance if self.balance > 0 else 0
        if daily_dd >= self.max_daily_drawdown:
            return {"approved": False, "reason": f"Daily drawdown limit ({self.max_daily_drawdown*100}%) reached"}

        risk_amount = self.balance * self.max_risk_per_trade
        sl_distance = abs(signal.entry_price - signal.stop_loss)

        if sl_distance == 0:
            return {"approved": False, "reason": "Invalid stop loss (zero distance)"}

        lot_size = risk_amount / sl_distance
        lot_size = round(lot_size, 4)

        potential_loss = lot_size * sl_distance
        potential_profit = lot_size * abs(signal.take_profit - signal.entry_price)

        return {
            "approved": True,
            "lot_size": lot_size,
            "risk_amount": round(risk_amount, 2),
            "risk_percent": round(self.max_risk_per_trade * 100, 2),
            "potential_loss": round(potential_loss, 2),
            "potential_profit": round(potential_profit, 2),
            "sl_distance": round(sl_distance, 5),
            "daily_drawdown_used": round(daily_dd * 100, 2),
            "daily_drawdown_remaining": round((self.max_daily_drawdown - daily_dd) * 100, 2),
            "open_trades": self.open_trades,
            "max_open_trades": self.max_open_trades,
        }

    def update_balance(self, pnl: float):
        self.balance += pnl
        self.equity = self.balance
        self.daily_pnl += pnl

    def reset_daily(self):
        self.daily_pnl = 0.0

    def record_trade_open(self):
        self.open_trades += 1

    def record_trade_close(self):
        self.open_trades = max(0, self.open_trades - 1)

    def get_risk_summary(self) -> dict:
        daily_dd = abs(min(self.daily_pnl, 0)) / self.balance if self.balance > 0 else 0
        return {
            "balance": round(self.balance, 2),
            "equity": round(self.equity, 2),
            "daily_pnl": round(self.daily_pnl, 2),
            "daily_drawdown_pct": round(daily_dd * 100, 2),
            "max_daily_drawdown_pct": round(self.max_daily_drawdown * 100, 2),
            "risk_per_trade_pct": round(self.max_risk_per_trade * 100, 2),
            "open_trades": self.open_trades,
            "max_open_trades": self.max_open_trades,
        }


risk_agent = RiskAgent()
