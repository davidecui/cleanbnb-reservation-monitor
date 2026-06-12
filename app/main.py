import sys
import logging
from dotenv import load_dotenv
from .config import get_settings
from .logging import setup_logging
from .clients.cleanbnb import CleanBnBClient
from .parsers.reservations import ReservationParser
from .models import ReservationState
from .notifiers.email_notifier import EmailNotifier
from .notifiers.telegram_notifier import TelegramNotifier
from .notifiers.composite_notifier import CompositeNotifier

logger = logging.getLogger(__name__)

def get_repository(settings):
    backend = settings.state_backend.lower()
    if backend == "firestore":
        from .state.firestore_repository import FirestoreReservationRepository
        logger.info("Using Firestore state backend.")
        return FirestoreReservationRepository(settings)
    else:
        from .state.file_repository import FileReservationRepository
        logger.info("Using File state backend.")
        return FileReservationRepository()

def main():
    # Load .env variables (useful for local mode)
    load_dotenv()
    
    settings = get_settings()
    setup_logging(settings.app_env)
    
    logger.info(f"Starting CleanBnB Reservation Monitor (Env: {settings.app_env})")
    
    try:
        # Initialize components
        client = CleanBnBClient(settings)
        parser = ReservationParser()
        repository = get_repository(settings)
        
        notifiers = []
        email_notifier = EmailNotifier(settings)
        if email_notifier.enabled:
            notifiers.append(email_notifier)
            
        telegram_notifier = TelegramNotifier(settings)
        if telegram_notifier.enabled:
            notifiers.append(telegram_notifier)
            
        if not notifiers:
            logger.warning("No notifiers are enabled. Notifications will not be sent.")
            
        composite_notifier = CompositeNotifier(notifiers)

        # 1. Login
        client.login()
        
        # 2. Fetch Reservations
        html_content = client.fetch_reservations_html()
        
        # 3. Parse Reservations
        reservations = parser.parse_reservations(html_content)
        logger.info(f"Parsed {len(reservations)} reservations from portal.")
        
        # 4. Compare with State
        new_reservations = []
        new_states = []
        
        # We fetch all states once to avoid multiple db roundtrips
        for res in reservations:
            if repository.is_new(res.fingerprint):
                new_reservations.append(res)
                new_states.append(ReservationState.from_reservation(res))
                
        logger.info(f"Found {len(new_reservations)} new, previously unseen reservations.")
        
        # 5. Notify & Persist
        if new_reservations:
            composite_notifier.notify(new_reservations)
            repository.save_states(new_states)
        else:
            logger.info("No new reservations to notify.")
            
        logger.info("Process completed successfully.")
        
    except Exception as e:
        logger.error(f"Critical operational failure: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
