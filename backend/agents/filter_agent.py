"""Filter agents - session, market regime, and news filters."""
from datetime import datetime
from backend.models.signals import MetaSignal, SignalType, MarketRegime


class FilterAgent:
    """Applies filters before execution to remove low-quality trades."""

    def __init__(self):
        self.session_filter_enabled = True
        self.regime_filter_enabled = True
        self.news_filter_enabled = True
        self.allowed_sessions = {"LONDON", "NEW_YORK", "OVERLAP"}
        self.blocked_news_times: list[tuple[datetime, datetime]] = []

    def apply_filters(self, signal: MetaSignal, features: dict) -> tuple[bool, list[str]]:
        """Apply all filters. Returns (should_trade, list of filter reasons)."""
        reasons = []

        if signal.signal == SignalType.NONE:
            return False, ["No signal generated"]

        if self.session_filter_enabled:
            passed, reason = self._session_filter(features)
            if not passed:
                reasons.append(reason)

        if self.regime_filter_enabled:
            passed, reason = self._regime_filter(signal, features)
            if not passed:
                reasons.append(reason)

        if self.news_filter_enabled:
            passed, reason = self._news_filter()
            if not passed:
                reasons.append(reason)

        confidence_ok, conf_reason = self._confidence_filter(signal)
        if not confidence_ok:
            reasons.append(conf_reason)

        return len(reasons) == 0, reasons

    def _session_filter(self, features: dict) -> tuple[bool, str]:
        session = features.get("session", "OFF_HOURS")
        if session in self.allowed_sessions:
            return True, ""
        return False, f"Session filter: {session} not in allowed sessions"

    def _regime_filter(self, signal: MetaSignal, features: dict) -> tuple[bool, str]:
        regime = features.get("regime", MarketRegime.UNKNOWN)

        family_scores = signal.family_scores

        if regime == MarketRegime.TRENDING:
            mr_score = abs(family_scores.get("MEAN_REVERSION", 0))
            trend_score = abs(family_scores.get("TREND", 0))
            if mr_score > trend_score and mr_score > 2:
                return False, "Regime filter: Mean reversion dominant in trending market"

        elif regime == MarketRegime.RANGING:
            breakout_score = abs(family_scores.get("BREAKOUT", 0))
            mr_score = abs(family_scores.get("MEAN_REVERSION", 0))
            if breakout_score > mr_score and breakout_score > 2:
                return False, "Regime filter: Breakout dominant in ranging market"

        return True, ""

    def _news_filter(self) -> tuple[bool, str]:
        now = datetime.utcnow()
        for start, end in self.blocked_news_times:
            if start <= now <= end:
                return False, "News filter: High-impact news event active"
        return True, ""

    def _confidence_filter(self, signal: MetaSignal) -> tuple[bool, str]:
        if signal.confidence < 0.3:
            return False, f"Confidence filter: {signal.confidence:.2f} below minimum 0.30"
        return True, ""

    def add_news_block(self, start: datetime, end: datetime):
        self.blocked_news_times.append((start, end))

    def set_allowed_sessions(self, sessions: set[str]):
        self.allowed_sessions = sessions


filter_agent = FilterAgent()
