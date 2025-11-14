"""
Lawyer Website Scraper
Extracts detailed information from lawyer firm websites
"""

import requests
from bs4 import BeautifulSoup
import re
import logging
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LawyerWebsiteScraper:
    """
    Scrape information from lawyer websites to enrich directory data
    """

    def __init__(self, delay_seconds: float = 1.0):
        self.delay = delay_seconds
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def scrape_website(self, url: str) -> Dict:
        """
        Scrape lawyer website for detailed information

        Returns dictionary with extracted data
        """
        logger.info(f"Scraping: {url}")

        data = {
            'website': url,
            'scraped_successfully': False,
            'error': None
        }

        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract various information
            data.update({
                'description': self._extract_description(soup, url),
                'short_description': self._extract_short_description(soup),
                'specializations': self._extract_specializations(soup),
                'team_members': self._extract_team_members(soup, url),
                'years_experience': self._extract_years_experience(soup),
                'awards': self._extract_awards(soup),
                'accreditations': self._extract_accreditations(soup),
                'case_studies': self._extract_case_studies(soup, url),
                'testimonials': self._extract_testimonials(soup),
                'features': self._extract_features(soup),
                'contact_info': self._extract_contact_info(soup),
                'social_media': self._extract_social_media(soup),
                'meta_title': self._extract_meta_title(soup),
                'meta_description': self._extract_meta_description(soup),
                'scraped_successfully': True
            })

        except requests.RequestException as e:
            logger.error(f"Error scraping {url}: {e}")
            data['error'] = str(e)

        time.sleep(self.delay)
        return data

    def _extract_description(self, soup: BeautifulSoup, base_url: str) -> str:
        """
        Extract main description/about text

        Look for:
        - About us page content
        - Homepage intro text
        - Main content areas
        """
        description_parts = []

        # Common patterns for about/intro content
        selectors = [
            ('div', {'class': re.compile(r'about|intro|overview', re.I)}),
            ('section', {'class': re.compile(r'about|intro|overview', re.I)}),
            ('div', {'id': re.compile(r'about|intro|overview', re.I)}),
            ('article', {}),
            ('main', {}),
        ]

        for tag, attrs in selectors:
            elements = soup.find_all(tag, attrs, limit=3)
            for elem in elements:
                text = elem.get_text(separator=' ', strip=True)
                # Filter out navigation, footer, etc.
                if len(text) > 100 and len(text) < 2000:
                    description_parts.append(text)

        # Try to find "About" page link and scrape it
        about_link = soup.find('a', href=re.compile(r'/about|/who-we-are|/our-firm', re.I))
        if about_link:
            about_url = urljoin(base_url, about_link.get('href', ''))
            about_text = self._scrape_about_page(about_url)
            if about_text:
                description_parts.insert(0, about_text)

        # Combine and clean
        full_description = ' '.join(description_parts)
        full_description = self._clean_text(full_description)

        # Limit length
        if len(full_description) > 1000:
            full_description = full_description[:1000].rsplit(' ', 1)[0] + '...'

        return full_description

    def _scrape_about_page(self, url: str) -> str:
        """Scrape the about page specifically"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove nav, footer, sidebar
            for element in soup(['nav', 'footer', 'aside', 'header']):
                element.decompose()

            main_content = soup.find('main') or soup.find('article') or soup.body
            if main_content:
                text = main_content.get_text(separator=' ', strip=True)
                return self._clean_text(text)[:1000]

        except Exception as e:
            logger.debug(f"Could not scrape about page {url}: {e}")

        return ''

    def _extract_short_description(self, soup: BeautifulSoup) -> str:
        """
        Extract short description (50-150 words)

        Look for:
        - Meta description
        - Hero/tagline text
        - First paragraph of main content
        """
        # Try meta description first
        meta_desc = soup.find('meta', {'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'][:200]

        # Look for hero/tagline sections
        hero = soup.find(['h1', 'h2'], class_=re.compile(r'hero|tagline|intro|lead', re.I))
        if hero:
            text = hero.get_text(strip=True)
            if 50 <= len(text) <= 200:
                return text

        # First significant paragraph
        paragraphs = soup.find_all('p', limit=5)
        for p in paragraphs:
            text = p.get_text(strip=True)
            if 50 <= len(text) <= 300:
                return text

        return ''

    def _extract_specializations(self, soup: BeautifulSoup) -> List[str]:
        """
        Extract practice areas/specializations

        Look for lists of practice areas
        """
        specializations = set()

        # Common medical negligence related terms
        keywords = [
            'medical negligence', 'medical malpractice', 'clinical negligence',
            'surgical error', 'misdiagnosis', 'birth injury', 'medication error',
            'hospital negligence', 'anesthesia error', 'emergency room error',
            'nursing home abuse', 'dental negligence', 'obstetric negligence'
        ]

        # Look for practice area sections
        practice_sections = soup.find_all(
            ['div', 'section', 'ul'],
            class_=re.compile(r'practice|specialization|area|service', re.I),
            limit=5
        )

        for section in practice_sections:
            text = section.get_text().lower()
            for keyword in keywords:
                if keyword in text:
                    # Capitalize properly
                    title = keyword.title()
                    specializations.add(title)

        # Also check page text generally
        page_text = soup.get_text().lower()
        for keyword in keywords:
            if keyword in page_text:
                specializations.add(keyword.title())

        return sorted(list(specializations))

    def _extract_team_members(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """
        Extract team member information

        Look for:
        - Team/staff sections
        - Individual profiles
        """
        team_members = []

        # Find team sections
        team_sections = soup.find_all(
            ['div', 'section'],
            class_=re.compile(r'team|staff|lawyer|attorney|partner', re.I),
            limit=10
        )

        for section in team_sections:
            # Look for individual member cards
            member_cards = section.find_all(
                ['div', 'article'],
                class_=re.compile(r'member|profile|bio', re.I),
                limit=10
            )

            for card in member_cards:
                member = {}

                # Name
                name_elem = card.find(['h2', 'h3', 'h4', 'h5'])
                if name_elem:
                    member['full_name'] = name_elem.get_text(strip=True)

                # Role/title
                role_elem = card.find(class_=re.compile(r'title|role|position', re.I))
                if role_elem:
                    member['role'] = role_elem.get_text(strip=True)

                # Bio
                bio_elem = card.find('p')
                if bio_elem:
                    member['bio'] = bio_elem.get_text(strip=True)[:500]

                # Photo
                img = card.find('img')
                if img and img.get('src'):
                    member['photo_url'] = urljoin(base_url, img['src'])

                if member.get('full_name'):
                    team_members.append(member)

        return team_members[:10]  # Limit to 10 members

    def _extract_years_experience(self, soup: BeautifulSoup) -> Optional[int]:
        """
        Extract years of experience

        Look for patterns like:
        - "25+ years"
        - "Since 1998"
        - "Established 1998"
        """
        text = soup.get_text()

        # Pattern: "X years" or "X+ years"
        years_match = re.search(r'(\d+)\+?\s*years\s*(of\s*)?experience', text, re.I)
        if years_match:
            return int(years_match.group(1))

        # Pattern: "Since YYYY" or "Established YYYY"
        since_match = re.search(r'(since|established|founded)\s*(\d{4})', text, re.I)
        if since_match:
            year = int(since_match.group(2))
            current_year = 2024  # Update as needed
            if 1950 <= year <= current_year:
                return current_year - year

        return None

    def _extract_awards(self, soup: BeautifulSoup) -> List[str]:
        """Extract awards and recognitions"""
        awards = []

        # Look for awards section
        awards_sections = soup.find_all(
            ['div', 'section', 'ul'],
            class_=re.compile(r'award|recognition|achievement', re.I),
            limit=3
        )

        for section in awards_sections:
            # Find list items or paragraphs
            items = section.find_all(['li', 'p', 'h3', 'h4'], limit=10)
            for item in items:
                text = item.get_text(strip=True)
                if len(text) > 10 and len(text) < 200:
                    awards.append(text)

        return awards[:10]

    def _extract_accreditations(self, soup: BeautifulSoup) -> List[str]:
        """Extract professional accreditations"""
        accreditations = []

        # Common legal accreditations in Australia
        keywords = [
            'accredited specialist',
            'law society',
            'lawyers alliance',
            'plaintiff lawyers',
            'admitted',
            'qualified',
            'certified'
        ]

        text = soup.get_text().lower()

        for keyword in keywords:
            if keyword in text:
                # Try to extract the full accreditation text
                pattern = rf'[^.]*{keyword}[^.]*\.'
                matches = re.findall(pattern, text, re.I)
                for match in matches[:3]:
                    clean = match.strip()
                    if len(clean) > 20 and len(clean) < 200:
                        accreditations.append(clean.capitalize())

        return accreditations[:5]

    def _extract_case_studies(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """
        Extract case studies/results

        Look for results, case studies, success stories
        """
        case_studies = []

        # Find case study sections
        case_sections = soup.find_all(
            ['div', 'section', 'article'],
            class_=re.compile(r'case|result|success|outcome', re.I),
            limit=5
        )

        for section in case_sections:
            case = {}

            # Title
            title_elem = section.find(['h2', 'h3', 'h4'])
            if title_elem:
                case['title'] = title_elem.get_text(strip=True)

            # Summary/outcome
            paragraphs = section.find_all('p', limit=3)
            if paragraphs:
                case['summary'] = ' '.join([p.get_text(strip=True) for p in paragraphs])[:500]

            # Look for year
            year_match = re.search(r'(20\d{2})', section.get_text())
            if year_match:
                case['year'] = int(year_match.group(1))

            if case.get('title') and case.get('summary'):
                case_studies.append(case)

        return case_studies[:5]

    def _extract_testimonials(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract client testimonials"""
        testimonials = []

        # Find testimonial sections
        testimonial_sections = soup.find_all(
            ['div', 'section', 'blockquote'],
            class_=re.compile(r'testimonial|review|feedback|client', re.I),
            limit=10
        )

        for section in testimonial_sections:
            testimonial = {}

            # Quote text
            quote = section.find(['blockquote', 'p', 'div'])
            if quote:
                text = quote.get_text(strip=True)
                if len(text) > 50:
                    testimonial['text'] = text[:500]

            # Author/client name
            author = section.find(class_=re.compile(r'author|client|name', re.I))
            if author:
                testimonial['client_name'] = author.get_text(strip=True)

            # Rating (if shown)
            stars = section.find_all(class_=re.compile(r'star|rating', re.I))
            if stars:
                testimonial['rating'] = len(stars)

            if testimonial.get('text'):
                testimonials.append(testimonial)

        return testimonials[:10]

    def _extract_features(self, soup: BeautifulSoup) -> Dict:
        """
        Extract service features

        Look for:
        - No win no fee
        - Free consultation
        - Home visits
        - etc.
        """
        text = soup.get_text().lower()

        features = {
            'no_win_no_fee': bool(re.search(r'no\s*win\s*no\s*fee|no\s*win,?\s*no\s*fee', text)),
            'free_consultation': bool(re.search(r'free\s*consultation|complimentary\s*consultation', text)),
            'home_visits': bool(re.search(r'home\s*visit|visit\s*you\s*at\s*home', text)),
            'telehealth': bool(re.search(r'telehealth|video\s*consultation|zoom\s*meeting', text)),
            '24_7_available': bool(re.search(r'24\s*/?\s*7|24\s*hour', text)),
        }

        return features

    def _extract_contact_info(self, soup: BeautifulSoup) -> Dict:
        """Extract additional contact information"""
        contact = {}

        # Email
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, soup.get_text())
        if emails:
            # Filter out common non-contact emails
            valid_emails = [e for e in emails if not any(x in e.lower() for x in ['example', 'test', 'noreply'])]
            if valid_emails:
                contact['email'] = valid_emails[0]

        return contact

    def _extract_social_media(self, soup: BeautifulSoup) -> Dict:
        """Extract social media links"""
        social = {}

        # Find all links
        links = soup.find_all('a', href=True)

        for link in links:
            href = link['href'].lower()

            if 'facebook.com' in href:
                social['facebook'] = link['href']
            elif 'linkedin.com' in href:
                social['linkedin'] = link['href']
            elif 'twitter.com' in href or 'x.com' in href:
                social['twitter'] = link['href']
            elif 'instagram.com' in href:
                social['instagram'] = link['href']

        return social

    def _extract_meta_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        title = soup.find('title')
        if title:
            return title.get_text(strip=True)

        og_title = soup.find('meta', property='og:title')
        if og_title:
            return og_title.get('content', '')

        return ''

    def _extract_meta_description(self, soup: BeautifulSoup) -> str:
        """Extract meta description"""
        meta_desc = soup.find('meta', {'name': 'description'})
        if meta_desc:
            return meta_desc.get('content', '')

        og_desc = soup.find('meta', property='og:description')
        if og_desc:
            return og_desc.get('content', '')

        return ''

    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters
        text = re.sub(r'[^\w\s.,;:!?\-\'\"()]', '', text)
        return text.strip()


# ============================================================================
# Batch processing
# ============================================================================

def enrich_lawyers_with_website_data(lawyers: List[Dict]) -> List[Dict]:
    """
    Enrich lawyer data by scraping their websites

    Args:
        lawyers: List of lawyer dictionaries (from Google Places or other source)

    Returns:
        Enriched list of lawyer dictionaries
    """
    scraper = LawyerWebsiteScraper(delay_seconds=2.0)
    enriched = []

    for i, lawyer in enumerate(lawyers, 1):
        logger.info(f"Processing {i}/{len(lawyers)}: {lawyer.get('firm_name', 'Unknown')}")

        website = lawyer.get('website')
        if not website:
            logger.warning(f"No website for {lawyer.get('firm_name')}, skipping scrape")
            enriched.append(lawyer)
            continue

        # Scrape website
        website_data = scraper.scrape_website(website)

        # Merge data
        if website_data.get('scraped_successfully'):
            # Update description if we found a better one
            if website_data.get('description') and len(website_data['description']) > 200:
                lawyer['description'] = website_data['description']

            if website_data.get('short_description'):
                lawyer['short_description'] = website_data['short_description']

            # Add specializations
            if website_data.get('specializations'):
                existing = lawyer.get('specializations', [])
                combined = list(set(existing + website_data['specializations']))
                lawyer['specializations'] = combined

            # Add team members
            if website_data.get('team_members'):
                lawyer['team_members'] = website_data['team_members']

            # Add other fields
            for field in ['years_experience', 'awards', 'accreditations', 'case_studies',
                         'meta_title', 'meta_description']:
                if website_data.get(field):
                    lawyer[field] = website_data[field]

            # Add features
            if website_data.get('features'):
                for key, value in website_data['features'].items():
                    if value:  # Only set True values
                        lawyer[key] = value

            # Add contact info if missing
            if website_data.get('contact_info', {}).get('email') and not lawyer.get('email'):
                lawyer['email'] = website_data['contact_info']['email']

        enriched.append(lawyer)

    return enriched


if __name__ == "__main__":
    import json

    # Example: Load lawyers from Google Places data and enrich
    try:
        with open('google_places_lawyers.json', 'r') as f:
            lawyers = json.load(f)

        print(f"Loaded {len(lawyers)} lawyers")
        print("Enriching with website data...")
        print("This will take a while...\n")

        enriched = enrich_lawyers_with_website_data(lawyers)

        # Save enriched data
        with open('lawyers_enriched.json', 'w', encoding='utf-8') as f:
            json.dump(enriched, f, indent=2, ensure_ascii=False)

        print(f"\nEnriched data saved to lawyers_enriched.json")

    except FileNotFoundError:
        print("No google_places_lawyers.json found")
        print("Run google_places_collector.py first to collect base data")
