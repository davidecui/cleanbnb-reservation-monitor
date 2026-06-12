import logging
from typing import List
from .base import Notifier
from ..models import Reservation

logger = logging.getLogger(__name__)

class CompositeNotifier(Notifier):
    def __init__(self, notifiers: List[Notifier]):
        self.notifiers = notifiers

    def notify(self, new_reservations: List[Reservation]) -> None:
        if not new_reservations:
            return
            
        for notifier in self.notifiers:
            try:
                notifier.notify(new_reservations)
            except Exception as e:
                logger.error(f"Notifier {notifier.__class__.__name__} failed: {e}")
