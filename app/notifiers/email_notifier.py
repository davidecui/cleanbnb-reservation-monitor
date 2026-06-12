import logging
import smtplib
from email.message import EmailMessage
from typing import List
from .base import Notifier
from ..models import Reservation
from ..config import Settings

logger = logging.getLogger(__name__)

class EmailNotifier(Notifier):
    def __init__(self, config: Settings):
        self.config = config
        self.enabled = bool(
            config.smtp_host and 
            config.smtp_port and 
            config.smtp_username and 
            config.smtp_password and 
            config.smtp_from and 
            config.smtp_to
        )
        if not self.enabled:
            logger.warning("EmailNotifier is disabled due to missing SMTP configuration.")

    def notify(self, new_reservations: List[Reservation]) -> None:
        if not self.enabled or not new_reservations:
            return

        subject = f"CleanBnB: {len(new_reservations)} New Reservation(s) Found!"
        
        body_lines = ["New reservations detected on CleanBnB portal:\n"]
        for idx, res in enumerate(new_reservations, 1):
            body_lines.append(f"{idx}. Guest: {res.guest_name}")
            body_lines.append(f"   Portal: {res.portal}")
            body_lines.append(f"   Apartment: {res.apartment}")
            body_lines.append(f"   Dates: {res.checkin} to {res.checkout}")
            body_lines.append(f"   Status: {res.status}")
            body_lines.append("")
            
        body = "\n".join(body_lines)

        msg = EmailMessage()
        msg.set_content(body)
        msg['Subject'] = subject
        msg['From'] = self.config.smtp_from
        msg['To'] = self.config.smtp_to

        try:
            logger.info("Sending email notification...")
            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
                server.starttls()
                server.login(self.config.smtp_username, self.config.smtp_password)
                server.send_message(msg)
            logger.info("Email notification sent successfully.")
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
