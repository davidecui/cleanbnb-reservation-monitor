import pytest
import responses
from app.clients.cleanbnb import CleanBnBClient
from app.config import Settings
from urllib.parse import urlparse, parse_qs

@pytest.fixture
def mock_settings():
    return Settings(
        app_env="local",
        cleanbnb_username="myuser",
        cleanbnb_password="mypassword",
        cleanbnb_property_id="wrong_property_id" # This should NOT be used for the apt query string
    )

@responses.activate
def test_login_payload_extraction(mock_settings):
    client = CleanBnBClient(mock_settings)
    
    html_form = """
    <form action="/cleanbnb/login/" class="login-form" method="post">
        <input name="csrf_token" type="hidden" value="secret123"/>
        <input name="property_id" type="text" value="cleanbnb"/>
        <input name="username" type="text"/>
        <input name="password" type="password"/>
        <button name="login_form" type="submit">Log in</button>
    </form>
    """
    
    responses.add(responses.GET, CleanBnBClient.LOGIN_URL, body=html_form, status=200)
    
    def request_callback(request):
        import urllib.parse
        payload = dict(urllib.parse.parse_qsl(request.body))
        
        assert payload.get("csrf_token") == "secret123"
        assert payload.get("property_id") == "cleanbnb"
        assert payload.get("username") == "myuser"
        assert payload.get("password") == "mypassword"
        assert payload.get("login_form") == "Log in"
        
        return (200, {}, "Success")
        
    responses.add_callback(
        responses.POST,
        "https://proprietari.cleanbnb.net/cleanbnb/login/",
        callback=request_callback,
    )
    
    client.login()
    assert len(responses.calls) == 2

@responses.activate
def test_fetch_reservations_apt_is_empty(mock_settings):
    """
    Ensure that the 'apt' parameter is always sent empty to fetch all reservations,
    even if cleanbnb_property_id is set in the configuration.
    """
    client = CleanBnBClient(mock_settings)
    
    def request_callback(request):
        parsed = urlparse(request.url)
        query = parse_qs(parsed.query)
        
        # 'apt' should be explicitly an empty string, NOT 'wrong_property_id'
        assert query.get('apt') == [''] or 'apt' not in query or query.get('apt', [''])[0] == ''
        assert 'from' in query
        assert 'to' in query
        assert query.get('type') == ['stay']
        
        return (200, {}, "<table></table>")

    # Add a mock matching any query parameters on RESERVATIONS_URL
    import re
    url_pattern = re.compile(rf"{CleanBnBClient.RESERVATIONS_URL}\?.*")
    
    responses.add_callback(
        responses.GET,
        url_pattern,
        callback=request_callback,
    )
    
    html = client.fetch_reservations_html()
    assert "<table>" in html
    assert len(responses.calls) == 1
