from app.models import Reservation, ReservationState

def test_repository_save_and_get(temp_file_repo):
    # Should be empty initially
    assert len(temp_file_repo.get_all_state()) == 0

    res = Reservation(
        guest_name="Test Guest",
        portal="Airbnb",
        checkin="01/01/2026",
        checkout="02/01/2026",
        apartment="Test Apt",
        status="Confirmed"
    )
    
    state = ReservationState.from_reservation(res)
    
    # Save one
    temp_file_repo.save_states([state])
    
    states = temp_file_repo.get_all_state()
    assert len(states) == 1
    assert states[0].reservation_id == res.fingerprint
    
    # Test is_new
    assert temp_file_repo.is_new(res.fingerprint) is False
    assert temp_file_repo.is_new("some_other_id") is True

    # Save same state again (should overwrite/deduplicate in repo logic)
    temp_file_repo.save_states([state])
    states = temp_file_repo.get_all_state()
    assert len(states) == 1

    # Save a new state
    res2 = Reservation(
        guest_name="Another Guest",
        portal="Booking",
        checkin="01/01/2026",
        checkout="02/01/2026",
        apartment="Test Apt",
        status="Confirmed"
    )
    state2 = ReservationState.from_reservation(res2)
    temp_file_repo.save_states([state2])
    
    states = temp_file_repo.get_all_state()
    assert len(states) == 2
