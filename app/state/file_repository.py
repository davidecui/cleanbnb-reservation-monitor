import json
import logging
import os
import tempfile
from typing import List
from .base import ReservationRepository
from ..models import ReservationState

logger = logging.getLogger(__name__)

class FileReservationRepository(ReservationRepository):
    def __init__(self, file_path: str = "data/reservations_state.json"):
        self.file_path = file_path
        self._ensure_directory_exists()

    def _ensure_directory_exists(self):
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

    def get_all_state(self) -> List[ReservationState]:
        if not os.path.exists(self.file_path):
            return []
            
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return []
                data = json.loads(content)
                return [ReservationState(**item) for item in data]
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode state file {self.file_path}: {e}. Treating as empty.")
            return []
        except Exception as e:
            logger.error(f"Error reading state file {self.file_path}: {e}")
            raise

    def save_states(self, states: List[ReservationState]) -> None:
        if not states:
            return

        # First, read existing states to append and avoid overwriting existing data entirely
        existing_states = self.get_all_state()
        existing_dict = {s.reservation_id: s for s in existing_states}
        
        for state in states:
            existing_dict[state.reservation_id] = state
            
        merged_states = list(existing_dict.values())
        data = [state.model_dump() for state in merged_states]

        # Atomic write
        dir_name = os.path.dirname(self.file_path)
        fd, temp_path = tempfile.mkstemp(dir=dir_name, text=True)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(temp_path, self.file_path)
            logger.debug(f"Atomically saved {len(merged_states)} states to {self.file_path}")
        except Exception as e:
            logger.error(f"Error writing to state file {self.file_path}: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise
