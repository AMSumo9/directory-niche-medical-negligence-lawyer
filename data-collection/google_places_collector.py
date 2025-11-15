"""
Google Places API (New) Data Collector
Collects business information, ratings, and reviews for medical negligence lawyers
Uses the NEW Places API v1
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
    Collect lawyer data using NEW Google Places API v1
    """

    def __init__(self, api_key: str):
        """
        Initialize with Google Places API key

        Get API key from: https://console.cloud.google.com/
        Enable: Places API (New)
        """
        self.api_key = api_key
        self.base_url = 'https://places.googleapis.com/v1'
        self.geocoding_url = 'https://maps.googleapis.com/maps/api/geocode/json'

    def search_lawyers_in_city(
        self,
        city: str,
        state_code: str,
        query: str = 'medical negligence lawyer',
        radius: int = 50000  # 50km radius
    ) -> List[Dict]:
        """
        Search for lawyers in a specific city using NEW Places API

        Args:
            city: City name (e.g., 'Sydney')
            state_code: State code (e.g., 'NSW')
            query: Search query
            radius: Search radius in meters

        Returns:
            List of lawyer business data
        """
        # Get city coordinates using geocoding
        city_location = self._geocode_city(f"{city}, {state_code}, Australia")
        if not city_location:
            logger.error(f"Could not geocode {city}, {state_code}")
            return []

        lat, lng = city_location

        # Search for lawyers using new Places API
        lawyers = self._search_text(
            query=f"{query} {city} {state_code}",
            location={'latitude': lat, 'longitude': lng},
            radius=radius
        )

        # Format the data
        formatted_lawyers = []
        for place in lawyers:
            lawyer_data = self._format_lawyer_data(place, state_code, city)
            if lawyer_data:
                formatted_lawyers.append(lawyer_data)

        return formatted_lawyers

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
        Get lat/lng coordinates for a city using Geocoding API

        Returns: (lat, lng) tuple or None
        """
        params = {
            'address': address,
            'key': self.api_key
        }

        try:
            response = requests.get(self.geocoding_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data['status'] == 'OK' and data['results']:
                location = data['results'][0]['geometry']['location']
                return location['lat'], location['lng']

        except Exception as e:
            logger.error(f"Geocoding error for {address}: {e}")

        return None

    def _search_text(
        self,
        query: str,
        location: Dict[str, float],
        radius: int
    ) -> List[Dict]:
        """
        Perform text search using NEW Places API

        Returns list of place dictionaries
        """
        url = f"{self.base_url}/places:searchText"

        headers = {
            'Content-Type': 'application/json',
            'X-Goog-Api-Key': self.api_key,
            'X-Goog-FieldMask': ','.join([
                'places.id',
                'places.displayName',
                'places.formattedAddress',
                'places.nationalPhoneNumber',
                'places.internationalPhoneNumber',
                'places.websiteUri',
                'places.rating',
                'places.userRatingCount',
                'places.regularOpeningHours',
                'places.location',
                'places.types',
                'places.businessStatus',
                'places.googleMapsUri'
            ])
        }

        payload = {
            'textQuery': query,
            'locationBias': {
                'circle': {
                    'center': location,
                    'radius': radius
                }
            },
            'maxResultCount': 20,  # Max allowed by API
            'languageCode': 'en'
        }

        all_results = []

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            response.raise_for_status()
            data = response.json()

            if 'places' in data:
                all_results.extend(data['places'])

        except Exception as e:
            logger.error(f"Text search error: {e}")

        return all_results

    def _format_lawyer_data(self, place: Dict, state_code: str, city: str) -> Optional[Dict]:
        """
        Format place data into our lawyer schema
        """
        try:
            # Parse address
            address_full = place.get('formattedAddress', '')
            address_parts = self._parse_address(address_full)

            # Extract phone
            phone = (
                place.get('internationalPhoneNumber') or
                place.get('nationalPhoneNumber') or
                ''
            )

            # Get opening hours
            opening_hours = place.get('regularOpeningHours', {})
            business_hours = self._parse_business_hours(opening_hours)

            # Rating data
            rating = place.get('rating', 0.0)
            review_count = place.get('userRatingCount', 0)

            lawyer_data = {
                # Basic information
                'firm_name': place.get('displayName', {}).get('text', ''),
                'state': address_parts.get('state', ''),
                'state_code': state_code,
                'city': city,
                'address': address_full,
                'phone': self._clean_phone(phone),
                'website': place.get('websiteUri', ''),

                # Default contact preferences
                'show_phone_link': True,
                'show_email_link': False,
                'show_website_link': True,

                # Google data
                'google_place_id': place.get('id', ''),
                'google_rating': rating,
                'google_review_count': review_count,
                'google_maps_url': place.get('googleMapsUri', ''),

                # Business hours
                'business_hours': business_hours,

                # External data
                'external_data': {
                    'source': 'google_places_new_api',
                    'collected_at': datetime.now().isoformat(),
                    'business_status': place.get('businessStatus', ''),
                    'types': place.get('types', []),
                    'location': place.get('location', {})
                },

                # Defaults
                'is_published': False,
                'verification_status': 'unverified',
                'subscription_tier': 'free',
                'free_consultation': None,
                'no_win_no_fee': None,
            }

            return lawyer_data

        except Exception as e:
            logger.error(f"Error formatting lawyer data: {e}")
            return None

    def _parse_address(self, formatted_address: str) -> Dict:
        """
        Parse formatted address into components
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
                state_parts = state_postcode.split()
                if len(state_parts) >= 2:
                    components['state'] = state_parts[0]
                    components['postcode'] = state_parts[1]

            # Third to last is usually city
            if len(parts) >= 3:
                components['city'] = parts[-3].strip()

        return components

    def _parse_business_hours(self, hours_data: Dict) -> Optional[Dict]:
        """
        Parse Google Places opening hours into structured format
        """
        if not hours_data:
            return None

        weekday_descriptions = hours_data.get('weekdayDescriptions', [])
        if not weekday_descriptions:
            return None

        hours = {}
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

        for desc in weekday_descriptions:
            for day in days:
                if desc.lower().startswith(day):
                    hours_part = desc.split(':', 1)[1].strip() if ':' in desc else 'closed'
                    hours[day] = hours_part

        return hours if hours else None

    def _clean_phone(self, phone: str) -> str:
        """Clean phone number"""
        if not phone:
            return ''

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
        print("3. Enable 'Places API (New)' and 'Geocoding API'")
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
    print("Starting data collection from Google Places (NEW API)...")
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
