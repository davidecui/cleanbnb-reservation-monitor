from app.parsers.reservations import ReservationParser

def test_parse_reservations(mock_html_reservations):
    parser = ReservationParser()
    reservations = parser.parse_reservations(mock_html_reservations)
    
    assert len(reservations) == 2
    
    res1 = reservations[0]
    assert res1.guest_name == "Mario Rossi"
    assert res1.portal == "Airbnb"
    assert res1.checkin == "15/05/2026"
    assert res1.checkout == "18/05/2026"
    assert res1.nights == 3
    assert res1.apartment == "Colosseum View"
    assert res1.status == "Confirmed"
    assert res1.guests_count == "2"

    res2 = reservations[1]
    assert res2.guest_name == "Jane Doe"
    assert res2.portal == "Booking"
    assert res2.checkin == "20/05/2026"
    assert res2.checkout == "25/05/2026"
    assert res2.nights == 5
    assert res2.apartment == "Vatican Suite"
    assert res2.status == "Pending"
    assert res2.guests_count == "1"

def test_parse_empty_table():
    html = """
    <table>
        <tr><th>Guest</th><th>Check-in</th></tr>
    </table>
    """
    parser = ReservationParser()
    reservations = parser.parse_reservations(html)
    assert len(reservations) == 0
