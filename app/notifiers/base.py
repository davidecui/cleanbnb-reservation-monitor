from abc import ABC, abstractmethod
from typing import List
from ..models import Reservation

class Notifier(ABC):
    @abstractmethod
    def notify(self, new_reservations: List[Reservation]) -> None:
        """Sends a notification about the given list of new reservations."""
        pass
