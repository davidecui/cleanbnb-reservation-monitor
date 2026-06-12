from typing import List, Dict, Any
from bs4 import BeautifulSoup
import logging
from ..models import Reservation

logger = logging.getLogger(__name__)

class ReservationParser:
    def parse_reservations(self, html_content: str) -> List[Reservation]:
        """
        Parses the HTML reservations table and returns a list of Reservation objects.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Heuristic to find the correct table: look for one containing rows with expected headers
        table = None
        tables = soup.find_all('table')
        for t in tables:
            headers = [th.get_text(strip=True).lower() for th in t.find_all('th')]
            if any("guest" in h or "ospite" in h for h in headers) and \
               any("check-in" in h or "checkin" in h for h in headers):
                table = t
                break
                
        if not table:
            # If no th headers, just take the first table that has many td's, or fail loudly.
            if not tables:
                logger.error("No tables found in reservations page.")
                raise ValueError("Reservations table not found in HTML.")
            table = tables[0]

        reservations = []
        rows = table.find_all('tr')
        
        # Some tables have headers in the first row. We try to map columns dynamically or fallback to positional mapping
        header_row = rows[0]
        header_cells = [th.get_text(strip=True).lower() for th in header_row.find_all(['th', 'td'])]
        
        has_headers = any("guest" in h or "ospite" in h or "check" in h for h in header_cells)
        start_idx = 1 if has_headers else 0
        
        # Map known headers to field names, fallback positions if headers aren't clear
        # Positional fallback (from prompt): guest name, portal, check-in, check-out, nights, apartment, country, status, guests count
        for row in rows[start_idx:]:
            cells = row.find_all('td')
            if not cells or len(cells) < 6:
                continue
                
            cell_texts = [td.get_text(strip=True) for td in cells]
            
            # Simple positional fallback implementation, robustness can be improved if header mapping is reliable
            guest_name = cell_texts[0]
            portal = cell_texts[1]
            checkin = cell_texts[2]
            checkout = cell_texts[3]
            
            # If length is enough, extract others
            nights = None
            try:
                nights = int(cell_texts[4]) if len(cell_texts) > 4 and cell_texts[4].isdigit() else None
            except ValueError:
                pass
                
            apartment = cell_texts[5] if len(cell_texts) > 5 else ""
            status = cell_texts[7] if len(cell_texts) > 7 else ""
            guests_count = cell_texts[8] if len(cell_texts) > 8 else None

            reservation = Reservation(
                guest_name=guest_name,
                portal=portal,
                checkin=checkin,
                checkout=checkout,
                apartment=apartment,
                status=status,
                nights=nights,
                guests_count=guests_count,
                raw_data={"cells": cell_texts}
            )
            reservations.append(reservation)
            
        return reservations
