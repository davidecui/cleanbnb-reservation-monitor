import pytest
import os
from tempfile import TemporaryDirectory
from app.state.file_repository import FileReservationRepository
from app.config import Settings

@pytest.fixture
def mock_html_reservations():
    return """
    <html>
        <body>
            <form action="/login" method="POST">
                <input type="hidden" name="csrf_token" value="abc123token" />
                <input type="text" name="user_login" />
                <input type="password" name="user_pass" />
            </form>
            <table>
                <tr>
                    <th>Guest / Ospite</th>
                    <th>Portal</th>
                    <th>Check-in</th>
                    <th>Check-out</th>
                    <th>Nights</th>
                    <th>Apartment</th>
                    <th>Country</th>
                    <th>Status</th>
                    <th>Guests count</th>
                </tr>
                <tr>
                    <td>Mario Rossi</td>
                    <td>Airbnb</td>
                    <td>15/05/2026</td>
                    <td>18/05/2026</td>
                    <td>3</td>
                    <td>Colosseum View</td>
                    <td>IT</td>
                    <td>Confirmed</td>
                    <td>2</td>
                </tr>
                <tr>
                    <td>Jane Doe</td>
                    <td>Booking</td>
                    <td>20/05/2026</td>
                    <td>25/05/2026</td>
                    <td>5</td>
                    <td>Vatican Suite</td>
                    <td>US</td>
                    <td>Pending</td>
                    <td>1</td>
                </tr>
            </table>
        </body>
    </html>
    """

@pytest.fixture
def temp_file_repo():
    with TemporaryDirectory() as tmpdir:
        repo_path = os.path.join(tmpdir, "state.json")
        yield FileReservationRepository(file_path=repo_path)

@pytest.fixture
def mock_settings():
    return Settings(
        app_env="local",
        cleanbnb_username="test_user",
        cleanbnb_password="test_password"
    )
