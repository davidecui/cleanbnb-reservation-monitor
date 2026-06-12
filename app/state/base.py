from abc import ABC, abstractmethod
from typing import List
from ..models import ReservationState

class ReservationRepository(ABC):
    @abstractmethod
    def get_all_state(self) -> List[ReservationState]:
        """Returns all previously stored reservation states."""
        pass

    @abstractmethod
    def save_states(self, states: List[ReservationState]) -> None:
        """Saves a list of new reservation states."""
        pass

    def is_new(self, reservation_id: str) -> bool:
        """
        Helper to check if a reservation is new.
        Subclasses can optimize this if needed.
        """
        all_states = self.get_all_state()
        existing_ids = {s.reservation_id for s in all_states}
        return reservation_id not in existing_ids
