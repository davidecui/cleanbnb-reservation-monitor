import logging
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential
from ..config import Settings

logger = logging.getLogger(__name__)

class CleanBnBClient:
    LOGIN_URL = "https://proprietari.cleanbnb.net/cleanbnb/login/"
    PROPERTY_URL = "https://proprietari.cleanbnb.net/cleanbnb/property"
    RESERVATIONS_URL = "https://proprietari.cleanbnb.net/cleanbnb/reservations"

    def __init__(self, config: Settings):
        self.config = config
        self.session = requests.Session()
        # Set a common user-agent to avoid simple bot blocking
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def login(self):
        """
        Executes the login flow.
        1. GET the login page.
        2. Parse all hidden input fields (anti-CSRF, tokens).
        3. POST credentials + hidden fields.
        4. Validate successful login.
        """
        logger.info("Starting login flow to CleanBnB portal...")
        
        # 1. GET login page
        response = self.session.get(self.LOGIN_URL, timeout=15)
        response.raise_for_status()
        
        # 2. Extract hidden fields
        soup = BeautifulSoup(response.text, 'html.parser')
        form = soup.find('form')
        if not form:
            logger.error("Login form not found on the login page.")
            raise ValueError("Login form not found.")

        payload = {}
        for tag in form.find_all(['input', 'button']):
            input_name = tag.get('name')
            input_type = tag.get('type', 'text')
            input_value = tag.get('value', '')
            
            if not input_name:
                continue
                
            if input_type == 'hidden':
                payload[input_name] = input_value
            elif input_type == 'password':
                payload[input_name] = self.config.cleanbnb_password
            elif tag.name == 'button' and input_type == 'submit':
                payload[input_name] = input_value or tag.get_text(strip=True)
            elif input_type == 'submit':
                payload[input_name] = input_value
            elif input_type == 'text':
                if 'user' in input_name.lower() and 'property' not in input_name.lower():
                    payload[input_name] = self.config.cleanbnb_username
                else:
                    payload[input_name] = input_value

        # Fallback if names were not identified correctly
        if not any('user' in k.lower() for k in payload.keys()):
            # Fallback to general known inputs if any
            payload['username'] = self.config.cleanbnb_username
            payload['password'] = self.config.cleanbnb_password

        # 3. POST login
        post_url = form.get('action') or self.LOGIN_URL
        if not post_url.startswith('http'):
            from urllib.parse import urljoin
            post_url = urljoin(self.LOGIN_URL, post_url)

        logger.info("Submitting login credentials...")
        login_resp = self.session.post(post_url, data=payload, timeout=15, allow_redirects=True)
        login_resp.raise_for_status()

        # 4. Confirm login success
        # Typically the URL changes, or the content contains properties/logout link.
        if "/login" in login_resp.url and "error" in login_resp.text.lower():
            logger.error("Login failed: Redirected back to login or error shown.")
            raise Exception("CleanBnB login failed. Please check credentials.")
            
        logger.info("Login successful.")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def fetch_reservations_html(self) -> str:
        """
        Fetches the reservations page for the configured date window.
        """
        logger.info("Fetching reservations page...")
        
        now = datetime.now()
        date_from = (now - timedelta(days=self.config.reservation_lookback_days)).strftime("%d/%m/%Y")
        date_to = (now + timedelta(days=self.config.reservation_lookahead_days)).strftime("%d/%m/%Y")
        
        params = {
            "from": date_from,
            "to": date_to,
            "type": "stay",
            "apt": ""
        }
        
        response = self.session.get(self.RESERVATIONS_URL, params=params, timeout=20)
        response.raise_for_status()
        
        if "login" in response.url:
            logger.warning("Session expired or redirected to login, re-authenticating...")
            self.login()
            response = self.session.get(self.RESERVATIONS_URL, params=params, timeout=20)
            response.raise_for_status()
            
        return response.text
