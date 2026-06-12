from app.models import Reservation

def test_fingerprint_generation():
    res1 = Reservation(
        guest_name="  Mario Rossi  ",
        portal="AIRBNB",
        checkin="15/05/2026",
        checkout="18/05/2026",
        apartment="Colosseum",
        status="Confirmed",
        nights=3,
        guests_count="2"
    )
    
    # Same stable fields, different casing/spacing, different transient fields (nights)
    res2 = Reservation(
        guest_name="mario rossi",
        portal="airbnb",
        checkin="15/05/2026",
        checkout="18/05/2026",
        apartment="colosseum",
        status="confirmed",
        nights=4, # Different transient field
        guests_count="3" # Different transient field
    )
    
    assert res1.fingerprint == res2.fingerprint

def test_fingerprint_difference():
    res1 = Reservation(
        guest_name="Mario Rossi",
        portal="Airbnb",
        checkin="15/05/2026",
        checkout="18/05/2026",
        apartment="Colosseum",
        status="Confirmed"
    )
    
    # Different status
    res2 = Reservation(
        guest_name="Mario Rossi",
        portal="Airbnb",
        checkin="15/05/2026",
        checkout="18/05/2026",
        apartment="Colosseum",
        status="Cancelled"
    )
    
    assert res1.fingerprint != res2.fingerprint
