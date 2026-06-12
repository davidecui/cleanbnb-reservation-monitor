import hashlib
import json
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class Reservation(BaseModel):
    guest_name: str
    portal: str
    checkin: str
    checkout: str
    apartment: str
    status: str
    nights: Optional[int] = None
    guests_count: Optional[str] = None
    raw_data: Dict[str, Any] = Field(default_factory=dict)
    
    @property
    def fingerprint(self) -> str:
        """
        Creates a deterministic SHA-256 fingerprint from stable fields.
        Normalizes whitespace and casing before hashing.
        """
        # Create a tuple of normalized values
        stable_fields = [
            str(self.guest_name).strip().lower(),
            str(self.portal).strip().lower(),
            str(self.checkin).strip().lower(),
            str(self.checkout).strip().lower(),
            str(self.apartment).strip().lower(),
            str(self.status).strip().lower()
        ]
        
        # Serialize to a deterministic JSON array string
        raw_string = json.dumps(stable_fields, separators=(',', ':'))
        return hashlib.sha256(raw_string.encode('utf-8')).hexdigest()

class ReservationState(BaseModel):
    reservation_id: str
    first_seen_at: str
    guest_name: str
    portal: str
    checkin: str
    checkout: str
    apartment: str
    status: str
    raw_data: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_reservation(cls, reservation: Reservation) -> "ReservationState":
        return cls(
            reservation_id=reservation.fingerprint,
            first_seen_at=datetime.utcnow().isoformat() + "Z",
            guest_name=reservation.guest_name,
            portal=reservation.portal,
            checkin=reservation.checkin,
            checkout=reservation.checkout,
            apartment=reservation.apartment,
            status=reservation.status,
            raw_data=reservation.raw_data
        )
