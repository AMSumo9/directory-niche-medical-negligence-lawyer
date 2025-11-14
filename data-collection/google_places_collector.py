"""
Google Places API Data Collector
Collects business information, ratings, and reviews for medical negligence lawyers
"""

import requests
import json
import time
from typing import List, Dict, Optional
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GooglePlacesCollector:
    """
    Collect lawyer data using Google Places API
    More reliable than web scraping
    """

    def __init__(self, api_key: str):
        """
        Initialize with Google Places API key

        Get API key from: https://console.cloud.google.com/
        Enable: Places API, Maps JavaScript API
        """
        self.api_key = api_key
        self.base_url = 'https://maps.googleapis.com/maps/api/place'

    def search_lawyers_in_city(
        self,
        city: str,
        state_code: str,
        query: str = 'medical negligence lawyer',
        radius: int = 50000  # 50km radius
    ) -> List[Dict]:
        """
        Search for lawyers in a specific city using Places API

        Args:
            city: City name (e.g., 'Sydney')
            state_code: State code (e.g., 'NSW')
            query: Search query
            radius: Search radius in meters

        Returns:
            List of lawyer business data
        """
        # First, get city coordinates
        city_location = self._geocode_city(f"{city}, {state_code}, Australia")
        if not city_location:
            logger.error(f"Could not geocode {city}, {state_code}")
            return []

        lat, lng = city_location

        # Search for lawyers near this location
        lawyers = self._text_search(
            query=f"{query} in {city} {state_code}",
            location=f"{lat},{lng}",
            radius=radius
        )

        # Enrich each lawyer with detailed information
        enriched_lawyers = []
        for lawyer in lawyers:
            place_id = lawyer.get('place_id')
            if place_id:
                details = self._get_place_details(place_id)
                if details:
                    # Merge search result with details
                    enriched_lawyer = self._merge_lawyer_data(lawyer, details, state_code)
                    enriched_lawyers.append(enriched_lawyer)

                # Rate limiting
                time.sleep(0.5)

        return enriched_lawyers

    def search_lawyers_bulk(self, cities_states: List[tuple]) -> List[Dict]:
        """
        Search for lawyers in multiple cities

        Args:
            cities_states: List of (city, state_code) tuples
                          e.g., [('Sydney', 'NSW'), ('Melbourne', 'VIC')]

        Returns:
            Combined list of all lawyers found
        """
        all_lawyers = []

        for city, state_code in cities_states:
            logger.info(f"Searching for lawyers in {city}, {state_code}...")

            lawyers = self.search_lawyers_in_city(city, state_code)
            all_lawyers.extend(lawyers)

            logger.info(f"Found {len(lawyers)} lawyers in {city}")

            # Rate limiting between cities
            time.sleep(2.0)

        return all_lawyers

    def _geocode_city(self, address: str) -> Optional[tuple]:
        """
        Get lat/lng coordinates for a city

        Returns: (lat, lng) tuple or None
        """
        url = f"https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            'address': address,
            'key': self.api_key
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data['status'] == 'OK' and data['results']:
                location = data['results'][0]['geometry']['location']
                return location['lat'], location['lng']

        except Exception as e:
            logger.error(f"Geocoding error for {address}: {e}")

        return None

    def _text_search(
        self,
        query: str,
        location: str,
        radius: int
    ) -> List[Dict]:
        """
        Perform text search using Places API

        Returns list of basic place information
        """
        url = f"{self.base_url}/textsearch/json"
        params = {
            'query': query,
            'location': location,
            'radius': radius,
            'key': self.api_key,
            'type': 'lawyer'  # Filter to lawyer businesses
        }

        all_results = []

        try:
            while True:
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()

                if data['status'] in ['OK', 'ZERO_RESULTS']:
                    all_results.extend(data.get('results', []))

                    # Check for next page
                    next_page_token = data.get('next_page_token')
                    if next_page_token:
                        # Wait a bit before fetching next page
                        time.sleep(2.0)
                        params = {
                            'pagetoken': next_page_token,
                            'key': self.api_key
                        }
                    else:
                        break
                else:
                    logger.error(f"Places API error: {data['status']}")
                    break

        except Exception as e:
            logger.error(f"Text search error: {e}")

        return all_results

    def _get_place_details(self, place_id: str) -> Optional[Dict]:
        """
        Get detailed information about a place

        Returns detailed place data including reviews, hours, etc.
        """
        url = f"{self.base_url}/details/json"
        params = {
            'place_id': place_id,
            'key': self.api_key,
            'fields': ','.join([
                'name',
                'formatted_address',
                'formatted_phone_number',
                'international_phone_number',
                'website',
                'rating',
                'user_ratings_total',
                'reviews',
                'opening_hours',
                'geometry',
                'types',
                'business_status',
                'url'  # Google Maps URL
            ])
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data['status'] == 'OK':
                return data['result']
            else:
                logger.error(f"Place details error: {data['status']}")

        except Exception as e:
            logger.error(f"Error getting place details for {place_id}: {e}")

        return None

    def _merge_lawyer_data(
        self,
        search_result: Dict,
        details: Dict,
        state_code: str
    ) -> Dict:
        """
        Merge search result with detailed data into our schema format
        """
        # Parse address
        address_components = self._parse_address(
            details.get('formatted_address', '')
        )

        # Extract phone
        phone = (
            details.get('international_phone_number') or
            details.get('formatted_phone_number') or
            ''
        )

        # Get reviews data (but don't copy review text - just stats)
        reviews = details.get('reviews', [])
        review_count = details.get('user_ratings_total', 0)
        rating = details.get('rating', 0.0)

        # Parse business hours
        hours = details.get('opening_hours', {})
        business_hours = self._parse_business_hours(hours)

        lawyer_data = {
            # Basic information
            'firm_name': details.get('name', search_result.get('name', '')),
            'state': address_components.get('state', ''),
            'state_code': state_code,
            'city': address_components.get('city', ''),
            'address': details.get('formatted_address', ''),
            'phone': self._clean_phone(phone),
            'website': details.get('website', ''),

            # Default contact preferences
            'show_phone_link': True,
            'show_email_link': False,  # Usually not in Google Places
            'show_website_link': True,

            # Google data (for reference, not public display without verification)
            'google_place_id': search_result.get('place_id', ''),
            'google_rating': rating,
            'google_review_count': review_count,
            'google_maps_url': details.get('url', ''),

            # Business hours
            'business_hours': business_hours,

            # External data (store for later reference)
            'external_data': {
                'source': 'google_places',
                'collected_at': datetime.now().isoformat(),
                'business_status': details.get('business_status', ''),
                'types': details.get('types', []),
                'geometry': details.get('geometry', {}),
                'reviews_sample': [
                    {
                        'rating': review.get('rating'),
                        'time': review.get('time'),
                        'author_name': review.get('author_name'),
                        # NOTE: We store review text for reference only
                        # Lawyer must approve before displaying publicly
                        'text': review.get('text', '')[:200] + '...'  # Truncate
                    }
                    for review in reviews[:5]  # Store up to 5 reviews
                ]
            },

            # Set default values
            'is_published': False,  # Don't publish until verified
            'verification_status': 'unverified',
            'subscription_tier': 'free',

            # Flags to set after verification
            'free_consultation': None,  # Unknown until verified
            'no_win_no_fee': None,  # Unknown until verified
        }

        return lawyer_data

    def _parse_address(self, formatted_address: str) -> Dict:
        """
        Parse formatted address into components

        Example: "Level 15/123 George St, Sydney NSW 2000, Australia"
        """
        components = {
            'street': '',
            'city': '',
            'state': '',
            'postcode': '',
            'country': ''
        }

        if not formatted_address:
            return components

        parts = [p.strip() for p in formatted_address.split(',')]

        if len(parts) >= 2:
            # Last part is usually country
            components['country'] = parts[-1]

            # Second to last usually has state and postcode
            if len(parts) >= 2:
                state_postcode = parts[-2].strip()
                # Pattern: "NSW 2000" or "VIC 3000"
                state_parts = state_postcode.split()
                if len(state_parts) >= 2:
                    components['state'] = state_parts[0]
                    components['postcode'] = state_parts[1]
                elif len(state_parts) == 1:
                    components['state'] = state_parts[0]

            # Third to last is usually city
            if len(parts) >= 3:
                components['city'] = parts[-3].strip()

            # Everything before is street
            if len(parts) >= 4:
                components['street'] = ', '.join(parts[:-3])

        return components

    def _parse_business_hours(self, hours_data: Dict) -> Optional[Dict]:
        """
        Parse Google Places opening hours into structured format
        """
        if not hours_data:
            return None

        weekday_text = hours_data.get('weekday_text', [])
        if not weekday_text:
            return None

        # Parse weekday_text which looks like:
        # ["Monday: 9:00 AM – 5:00 PM", "Tuesday: 9:00 AM – 5:00 PM", ...]

        hours = {}
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

        for text in weekday_text:
            for day in days:
                if text.lower().startswith(day):
                    # Extract hours part
                    hours_part = text.split(':', 1)[1].strip()

                    if 'closed' in hours_part.lower():
                        hours[day] = 'closed'
                    else:
                        # Try to parse "9:00 AM – 5:00 PM" format
                        hours[day] = hours_part

        return hours if hours else None

    def _clean_phone(self, phone: str) -> str:
        """Clean phone number"""
        if not phone:
            return ''

        # Remove formatting but keep the + if international
        import re
        cleaned = re.sub(r'[^\d+]', '', phone)

        # Ensure Australian format
        if cleaned.startswith('0'):
            cleaned = '+61' + cleaned[1:]
        elif not cleaned.startswith('+'):
            cleaned = '+61' + cleaned

        return cleaned

    def save_results(self, lawyers: List[Dict], filename: str):
        """Save results to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(lawyers, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {len(lawyers)} lawyers to {filename}")


# ============================================================================
# Main execution
# ============================================================================

if __name__ == "__main__":
    import os

    # Get API key from environment variable
    API_KEY = os.environ.get('GOOGLE_PLACES_API_KEY', '')

    if not API_KEY:
        print("ERROR: Please set GOOGLE_PLACES_API_KEY environment variable")
        print("\nTo get an API key:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project")
        print("3. Enable 'Places API' and 'Geocoding API'")
        print("4. Create credentials (API key)")
        print("5. Set environment variable: export GOOGLE_PLACES_API_KEY='your-key'")
        exit(1)

    # Initialize collector
    collector = GooglePlacesCollector(API_KEY)

    # Define cities to search
    australian_cities = [
        ('Sydney', 'NSW'),
        ('Melbourne', 'VIC'),
        ('Brisbane', 'QLD'),
        ('Perth', 'WA'),
        ('Adelaide', 'SA'),
        ('Gold Coast', 'QLD'),
        ('Newcastle', 'NSW'),
        ('Canberra', 'ACT'),
        ('Wollongong', 'NSW'),
        ('Geelong', 'VIC'),
    ]

    # Collect data
    print("Starting data collection from Google Places...")
    print(f"Searching {len(australian_cities)} cities")
    print("This may take a while due to API rate limiting...\n")

    all_lawyers = collector.search_lawyers_bulk(australian_cities)

    print(f"\n{'='*60}")
    print(f"Collection complete!")
    print(f"Total lawyers found: {len(all_lawyers)}")
    print(f"{'='*60}\n")

    # Save results
    output_file = 'google_places_lawyers.json'
    collector.save_results(all_lawyers, output_file)

    print(f"Data saved to: {output_file}")
    print("\nNext steps:")
    print("1. Review the collected data")
    print("2. Use website_scraper.py to enrich with website data")
    print("3. Use description_generator.py to create descriptions")
    print("4. Import into database using the import script")
