"""Telegram bot integration for signal delivery."""
import logging
import httpx

from backend.config.settings import settings

logger = logging.getLogger(__name__)


class TelegramBot:
    """Sends trading signals to Telegram."""

    def __init__(self):
        self.bot_token = settings.telegram.bot_token
        self.chat_id = settings.telegram.chat_id
        self.enabled = bool(self.bot_token and self.chat_id)

    async def send_signal(self, execution: dict):
        """Send a trading signal to Telegram."""
        if not self.enabled:
            logger.debug("Telegram not configured, skipping signal")
            return

        signal = execution.get("signal", "NONE")
        symbol = execution.get("symbol", "???")
        emoji = "🟢" if signal == "BUY" else "🔴" if signal == "SELL" else "⚪"

        message = (
            f"{emoji} <b>{signal} Signal - {symbol}</b>\n\n"
            f"📊 <b>Confidence:</b> {execution.get('confidence', 0):.0%}\n"
            f"📈 <b>Score:</b> {execution.get('score', 0):.1f}\n\n"
            f"💰 <b>Entry:</b> {execution.get('entry_price', 0):.5f}\n"
            f"🛑 <b>Stop Loss:</b> {execution.get('stop_loss', 0):.5f}\n"
            f"🎯 <b>Take Profit:</b> {execution.get('take_profit', 0):.5f}\n"
            f"📐 <b>R:R:</b> 1:{execution.get('risk_reward', 0):.1f}\n\n"
            f"📏 <b>Lot Size:</b> {execution.get('lot_size', 0):.4f}\n"
            f"⚠️ <b>Risk:</b> {execution.get('risk_percent', 0):.1f}%\n\n"
            f"<b>Top Strategies:</b>\n"
        )

        for strat in execution.get("top_strategies", [])[:5]:
            message += f"  • {strat['name']} ({strat['confidence']:.2f})\n"

        family_scores = execution.get("family_scores", {})
        if family_scores:
            message += "\n<b>Family Scores:</b>\n"
            for family, score in sorted(family_scores.items(), key=lambda x: abs(x[1]), reverse=True):
                bar = "█" * int(abs(score) * 2)
                prefix = "+" if score > 0 else ""
                message += f"  {family}: {prefix}{score:.1f} {bar}\n"

        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
                    json={
                        "chat_id": self.chat_id,
                        "text": message,
                        "parse_mode": "HTML",
                    },
                    timeout=10,
                )
                logger.info(f"Telegram signal sent: {signal} {symbol}")
        except Exception as e:
            logger.error(f"Failed to send Telegram signal: {e}")

    async def send_alert(self, text: str):
        """Send a general alert to Telegram."""
        if not self.enabled:
            return
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
                    json={"chat_id": self.chat_id, "text": text, "parse_mode": "HTML"},
                    timeout=10,
                )
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")


telegram_bot = TelegramBot()
