import logging
import requests
from typing import List
from .base import Notifier
from ..models import Reservation
from ..config import Settings

logger = logging.getLogger(__name__)

class TelegramNotifier(Notifier):
    def __init__(self, config: Settings):
        self.config = config
        self.enabled = bool(config.telegram_bot_token and config.telegram_chat_id)
        if not self.enabled:
            logger.warning("TelegramNotifier is disabled due to missing configuration.")

    def notify(self, new_reservations: List[Reservation]) -> None:
        if not self.enabled or not new_reservations:
            return

        message_lines = [f"🚨 *CleanBnB: {len(new_reservations)} New Reservation(s)!* 🚨\n"]
        for res in new_reservations:
            message_lines.append(f"👤 *Guest:* {res.guest_name}")
            message_lines.append(f"🌍 *Portal:* {res.portal}")
            message_lines.append(f"🏠 *Apt:* {res.apartment}")
            message_lines.append(f"📅 *Dates:* {res.checkin} ➡️ {res.checkout}")
            message_lines.append(f"📝 *Status:* {res.status}\n")

        message = "\n".join(message_lines)
        url = f"https://api.telegram.org/bot{self.config.telegram_bot_token}/sendMessage"
        payload = {
            "chat_id": self.config.telegram_chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }

        try:
            logger.info("Sending Telegram notification...")
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("Telegram notification sent successfully.")
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Telegram API response: {e.response.text}")
