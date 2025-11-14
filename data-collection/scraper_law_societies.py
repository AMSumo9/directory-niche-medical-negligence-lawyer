"""
Australian Law Society Directories Scraper
Scrapes medical negligence lawyer information from state law society directories
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AustralianLawSocietyScraper:
    """
    Scraper for Australian Law Society directories
    Handles multiple state-based law societies
    """

    def __init__(self, delay_seconds: float = 2.0):
        """
        Initialize scraper with rate limiting

        Args:
            delay_seconds: Delay between requests to be respectful
        """
        self.delay = delay_seconds
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

        # Law society search URLs (these may need updating as websites change)
        self.law_societies = {
            'NSW': {
                'name': 'Law Society of NSW',
                'search_url': 'https://www.lawsociety.com.au/find-a-lawyer',
                'state': 'New South Wales',
                'state_code': 'NSW'
            },
            'VIC': {
                'name': 'Law Institute of Victoria',
                'search_url': 'https://www.liv.asn.au/Referral/Find-a-Lawyer',
                'state': 'Victoria',
                'state_code': 'VIC'
            },
            'QLD': {
                'name': 'Queensland Law Society',
                'search_url': 'https://qls.com.au/for_the_public/find_a_solicitor',
                'state': 'Queensland',
                'state_code': 'QLD'
            },
            'WA': {
                'name': 'Law Society of Western Australia',
                'search_url': 'https://www.lawsocietywa.asn.au/find-a-lawyer/',
                'state': 'Western Australia',
                'state_code': 'WA'
            },
            'SA': {
                'name': 'Law Society of South Australia',
                'search_url': 'https://www.lawsocietysa.asn.au/find-a-lawyer',
                'state': 'South Australia',
                'state_code': 'SA'
            }
        }

    def search_lawyers(
        self,
        state_code: str,
        specialization: str = 'medical negligence',
        city: Optional[str] = None,
        max_results: int = 50
    ) -> List[Dict]:
        """
        Search for lawyers in a specific state

        Args:
            state_code: State code (NSW, VIC, QLD, etc.)
            specialization: Area of practice
            city: City to filter by
            max_results: Maximum number of results to return

        Returns:
            List of lawyer dictionaries
        """
        if state_code not in self.law_societies:
            logger.error(f"Unsupported state code: {state_code}")
            return []

        logger.info(f"Searching {state_code} for {specialization} lawyers...")

        # Note: Each law society has different search mechanisms
        # This is a template that needs customization per site
        # For production, you'd implement specific scrapers for each society

        lawyers = []

        # Example implementation (needs customization per site)
        if state_code == 'NSW':
            lawyers = self._scrape_nsw_law_society(specialization, city, max_results)
        elif state_code == 'VIC':
            lawyers = self._scrape_vic_law_institute(specialization, city, max_results)
        # Add other states as needed

        return lawyers

    def _scrape_nsw_law_society(
        self,
        specialization: str,
        city: Optional[str],
        max_results: int
    ) -> List[Dict]:
        """
        Scrape NSW Law Society directory

        Note: This is a template. Actual implementation depends on current website structure.
        You may need to use Selenium for JavaScript-heavy sites.
        """
        lawyers = []

        try:
            # This URL structure is illustrative - check actual site
            search_params = {
                'practiceArea': specialization,
                'location': city or '',
            }

            response = self.session.get(
                self.law_societies['NSW']['search_url'],
                params=search_params,
                timeout=10
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find lawyer listings (selector needs to match actual site)
            # This is a placeholder - inspect the actual HTML structure
            lawyer_cards = soup.find_all('div', class_='lawyer-result', limit=max_results)

            for card in lawyer_cards:
                lawyer_data = self._parse_lawyer_card_nsw(card)
                if lawyer_data:
                    lawyers.append(lawyer_data)

                time.sleep(self.delay)

        except Exception as e:
            logger.error(f"Error scraping NSW Law Society: {e}")

        return lawyers

    def _parse_lawyer_card_nsw(self, card) -> Optional[Dict]:
        """Parse individual lawyer card from NSW Law Society"""
        try:
            # These selectors are placeholders - update based on actual HTML
            firm_name = card.find('h3', class_='firm-name')
            address = card.find('div', class_='address')
            phone = card.find('a', class_='phone')
            email = card.find('a', class_='email')
            website = card.find('a', class_='website')

            if not firm_name:
                return None

            data = {
                'firm_name': firm_name.get_text(strip=True),
                'state': 'New South Wales',
                'state_code': 'NSW',
                'source': 'NSW Law Society',
                'source_url': self.law_societies['NSW']['search_url']
            }

            if address:
                addr_text = address.get_text(strip=True)
                # Parse city from address
                data['address'] = addr_text
                data['city'] = self._extract_city_from_address(addr_text, 'NSW')

            if phone:
                data['phone'] = self._clean_phone(phone.get_text(strip=True))

            if email:
                data['email'] = email.get_text(strip=True)

            if website:
                data['website'] = website.get('href', '').strip()

            return data

        except Exception as e:
            logger.error(f"Error parsing lawyer card: {e}")
            return None

    def _scrape_vic_law_institute(
        self,
        specialization: str,
        city: Optional[str],
        max_results: int
    ) -> List[Dict]:
        """
        Scrape VIC Law Institute directory
        Similar structure to NSW scraper
        """
        # Implement similar to NSW
        logger.warning("VIC scraper not yet implemented - needs customization")
        return []

    def _extract_city_from_address(self, address: str, state_code: str) -> str:
        """
        Extract city name from address string

        Common formats:
        - "123 Main St, Sydney NSW 2000"
        - "Level 5, 456 George St, Melbourne VIC 3000"
        """
        # Simple pattern matching - improve as needed
        major_cities = {
            'NSW': ['Sydney', 'Newcastle', 'Wollongong', 'Parramatta', 'Penrith'],
            'VIC': ['Melbourne', 'Geelong', 'Ballarat', 'Bendigo'],
            'QLD': ['Brisbane', 'Gold Coast', 'Townsville', 'Cairns', 'Toowoomba'],
            'WA': ['Perth', 'Fremantle', 'Mandurah'],
            'SA': ['Adelaide', 'Mount Gambier']
        }

        cities = major_cities.get(state_code, [])

        for city in cities:
            if city.lower() in address.lower():
                return city

        # Fallback: try to extract city before state code
        pattern = r',\s*([A-Za-z\s]+)\s+' + state_code
        match = re.search(pattern, address)
        if match:
            return match.group(1).strip()

        return 'Unknown'

    def _clean_phone(self, phone: str) -> str:
        """Clean and format phone number"""
        # Remove non-digits except + at start
        phone = re.sub(r'[^\d+]', '', phone)

        # Ensure Australian format +61
        if phone.startswith('0'):
            phone = '+61' + phone[1:]
        elif not phone.startswith('+'):
            phone = '+61' + phone

        return phone

    def save_results(self, lawyers: List[Dict], filename: str):
        """Save results to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(lawyers, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {len(lawyers)} lawyers to {filename}")


# ============================================================================
# ALTERNATIVE: Google Search Scraper for Medical Negligence Lawyers
# ============================================================================

class GoogleSearchScraper:
    """
    Scrape Google search results for medical negligence lawyers
    More reliable than individual law society scrapers
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def search_google_lawyers(
        self,
        city: str,
        state_code: str,
        query: str = "medical negligence lawyers"
    ) -> List[str]:
        """
        Search Google for lawyer websites

        Returns list of URLs to scrape

        Note: For production, consider using Google Custom Search API
        or SerpAPI to avoid being blocked
        """
        search_query = f"{query} {city} {state_code}"
        urls = []

        # This is a simplified version
        # For production, use Google Custom Search API or SerpAPI

        logger.info(f"Would search Google for: {search_query}")
        logger.info("Consider using Google Custom Search API or SerpAPI for reliable results")

        return urls


# ============================================================================
# Main execution example
# ============================================================================

if __name__ == "__main__":
    # Example usage
    scraper = AustralianLawSocietyScraper(delay_seconds=2.0)

    # Search NSW
    nsw_lawyers = scraper.search_lawyers(
        state_code='NSW',
        specialization='medical negligence',
        city='Sydney',
        max_results=20
    )

    print(f"Found {len(nsw_lawyers)} lawyers in NSW")

    # Save results
    if nsw_lawyers:
        scraper.save_results(nsw_lawyers, 'nsw_lawyers.json')

    # Note: The scrapers above are TEMPLATES
    # Each law society website has different structure
    # You'll need to inspect each site and customize the selectors
    #
    # Recommended approach:
    # 1. Use Selenium for JavaScript-heavy sites
    # 2. Or use the Google Places API (see google_places_scraper.py)
    # 3. Or manually compile a list and use the website scraper
