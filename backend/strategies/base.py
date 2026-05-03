"""Base strategy agent class."""
from abc import ABC, abstractmethod
from backend.models.signals import StrategySignal, SignalType, StrategyFamily


class StrategyAgent(ABC):
    """Base class for all strategy agents."""

    def __init__(self, name: str, family: StrategyFamily):
        self.name = name
        self.family = family
        self.is_active = True
        self.weight = 1.0

    @abstractmethod
    def analyze(self, features: dict) -> StrategySignal:
        """Analyze market data and return a signal."""
        pass

    def _no_signal(self) -> StrategySignal:
        return StrategySignal(
            signal=SignalType.NONE,
            confidence=0.0,
            risk_reward=0.0,
            strategy_name=self.name,
            strategy_family=self.family,
        )

    def _safe_val(self, series, offset: int = -1) -> float:
        try:
            if series is None or (hasattr(series, 'empty') and series.empty):
                return 0.0
            import numpy as np
            val = float(series.iloc[offset])
            if np.isnan(val):
                return 0.0
            return val
        except (IndexError, TypeError):
            return 0.0
