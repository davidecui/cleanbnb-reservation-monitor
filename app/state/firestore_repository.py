import logging
from typing import List
from google.cloud import firestore
from .base import ReservationRepository
from ..models import ReservationState
from ..config import Settings

logger = logging.getLogger(__name__)

class FirestoreReservationRepository(ReservationRepository):
    COLLECTION_NAME = "reservations"

    def __init__(self, config: Settings):
        # Initializes using default credentials (Workload Identity or injected from local auth)
        kwargs = {}
        if config.gcp_project:
            kwargs['project'] = config.gcp_project
        self.db = firestore.Client(**kwargs)

    def get_all_state(self) -> List[ReservationState]:
        try:
            docs = self.db.collection(self.COLLECTION_NAME).stream()
            states = []
            for doc in docs:
                try:
                    data = doc.to_dict()
                    states.append(ReservationState(**data))
                except Exception as e:
                    logger.warning(f"Failed to parse document {doc.id}: {e}")
            return states
        except Exception as e:
            logger.error(f"Error fetching state from Firestore: {e}")
            raise

    def save_states(self, states: List[ReservationState]) -> None:
        if not states:
            return
            
        try:
            # Using batched writes for atomicity/efficiency
            batch = self.db.batch()
            collection_ref = self.db.collection(self.COLLECTION_NAME)
            
            for state in states:
                doc_ref = collection_ref.document(state.reservation_id)
                batch.set(doc_ref, state.model_dump())
                
            batch.commit()
            logger.info(f"Saved {len(states)} new reservation states to Firestore.")
        except Exception as e:
            logger.error(f"Error saving state to Firestore: {e}")
            raise
