"""
Import Collected Lawyer Data into Supabase
Imports JSON data from collection pipeline into Supabase PostgreSQL database
"""

import json
import sys
import os
import re
from typing import List, Dict, Optional
from supabase import create_client, Client
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug"""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')


class SupabaseImporter:
    """Import lawyer data into Supabase"""

    def __init__(self, supabase_url: str, supabase_key: str):
        """
        Initialize Supabase client

        Args:
            supabase_url: Your Supabase project URL
            supabase_key: Your Supabase service role key (or anon key)
        """
        self.client: Client = create_client(supabase_url, supabase_key)
        self.stats = {
            'total': 0,
            'imported': 0,
            'updated': 0,
            'failed': 0,
            'errors': []
        }

    def import_lawyers(self, lawyers: List[Dict], update_existing: bool = False) -> Dict:
        """
        Import list of lawyers into Supabase

        Args:
            lawyers: List of lawyer dictionaries
            update_existing: If True, update existing records; if False, skip duplicates

        Returns:
            Statistics dictionary
        """
        self.stats['total'] = len(lawyers)

        logger.info(f"Starting import of {len(lawyers)} lawyers...")

        for i, lawyer_data in enumerate(lawyers, 1):
            try:
                logger.info(f"Processing {i}/{len(lawyers)}: {lawyer_data.get('firm_name', 'Unknown')}")

                # Check if lawyer exists (by google_place_id or slug)
                existing = self._find_existing_lawyer(lawyer_data)

                if existing and not update_existing:
                    logger.info("  Skipping - already exists")
                    continue

                if existing and update_existing:
                    # Update existing
                    self._update_lawyer(existing['id'], lawyer_data)
                    self.stats['updated'] += 1
                else:
                    # Insert new
                    self._insert_lawyer(lawyer_data)
                    self.stats['imported'] += 1

            except Exception as e:
                logger.error(f"  Error: {e}")
                self.stats['failed'] += 1
                self.stats['errors'].append({
                    'firm_name': lawyer_data.get('firm_name', 'Unknown'),
                    'error': str(e)
                })

        self._print_summary()
        return self.stats

    def _find_existing_lawyer(self, lawyer_data: Dict) -> Optional[Dict]:
        """Find existing lawyer by google_place_id or slug"""
        # Try by google_place_id first
        google_place_id = lawyer_data.get('google_place_id')
        if google_place_id:
            result = self.client.table('lawyers').select('*').eq('google_place_id', google_place_id).execute()
            if result.data:
                return result.data[0]

        # Try by slug
        slug = lawyer_data.get('slug') or self._generate_slug(lawyer_data)
        result = self.client.table('lawyers').select('*').eq('slug', slug).execute()
        if result.data:
            return result.data[0]

        return None

    def _generate_slug(self, lawyer_data: Dict) -> str:
        """Generate URL slug for lawyer"""
        firm_name = lawyer_data.get('firm_name', 'lawyer')
        city = lawyer_data.get('city', '')

        slug_base = f"{firm_name}-{city}" if city else firm_name
        return slugify(slug_base)

    def _insert_lawyer(self, lawyer_data: Dict):
        """Insert new lawyer"""
        # Prepare data for lawyers table
        lawyer_record = self._prepare_lawyer_record(lawyer_data)

        # Insert lawyer
        result = self.client.table('lawyers').insert(lawyer_record).execute()

        if not result.data:
            raise Exception("Failed to insert lawyer")

        lawyer_id = result.data[0]['id']
        logger.info(f"  ✓ Inserted lawyer with ID: {lawyer_id}")

        # Insert related data
        self._insert_related_data(lawyer_id, lawyer_data)

    def _update_lawyer(self, lawyer_id: str, lawyer_data: Dict):
        """Update existing lawyer"""
        lawyer_record = self._prepare_lawyer_record(lawyer_data)

        # Remove id from update data
        lawyer_record.pop('id', None)

        # Update lawyer
        result = self.client.table('lawyers').update(lawyer_record).eq('id', lawyer_id).execute()

        logger.info(f"  ✓ Updated lawyer with ID: {lawyer_id}")

        # Update related data
        # Note: This will add new related records but won't delete existing ones
        self._insert_related_data(lawyer_id, lawyer_data)

    def _prepare_lawyer_record(self, lawyer_data: Dict) -> Dict:
        """Prepare lawyer data for database insert/update"""
        # Generate slug if not present
        slug = lawyer_data.get('slug') or self._generate_slug(lawyer_data)

        record = {
            'firm_name': lawyer_data.get('firm_name', ''),
            'slug': slug,
            'state': lawyer_data.get('state', ''),
            'state_code': lawyer_data.get('state_code', ''),
            'city': lawyer_data.get('city', ''),
            'address': lawyer_data.get('address'),
            'phone': lawyer_data.get('phone'),
            'email': lawyer_data.get('email'),
            'website': lawyer_data.get('website'),
            'show_phone_link': lawyer_data.get('show_phone_link', True),
            'show_email_link': lawyer_data.get('show_email_link', True),
            'show_website_link': lawyer_data.get('show_website_link', True),
            'description': lawyer_data.get('description'),
            'short_description': lawyer_data.get('short_description'),
            'subscription_tier': lawyer_data.get('subscription_tier', 'free'),
            'is_featured': lawyer_data.get('is_featured', False),
            'featured_priority': lawyer_data.get('featured_priority', 0),
            'is_published': lawyer_data.get('is_published', False),

            # Enhanced fields
            'years_experience': lawyer_data.get('years_experience'),
            'founded_year': lawyer_data.get('founded_year'),
            'languages': lawyer_data.get('languages', []),
            'awards': lawyer_data.get('awards', []),
            'accreditations': lawyer_data.get('accreditations', []),
            'profile_image_url': lawyer_data.get('profile_image_url'),
            'office_images_urls': lawyer_data.get('office_images_urls', []),

            # Success metrics (no settlement amounts)
            'total_cases_handled': lawyer_data.get('total_cases_handled'),
            'success_rate': lawyer_data.get('success_rate'),

            # Client service features
            'free_consultation': lawyer_data.get('free_consultation'),
            'no_win_no_fee': lawyer_data.get('no_win_no_fee'),
            'home_visits_available': lawyer_data.get('home_visits_available'),
            'telehealth_available': lawyer_data.get('telehealth_available'),
            'accepts_legal_aid': lawyer_data.get('accepts_legal_aid'),

            # Responsiveness
            'average_response_time': lawyer_data.get('average_response_time'),
            'business_hours': lawyer_data.get('business_hours'),

            # SEO
            'meta_title': lawyer_data.get('meta_title'),
            'meta_description': lawyer_data.get('meta_description'),
            'service_areas': lawyer_data.get('service_areas', []),

            # Google data
            'google_place_id': lawyer_data.get('google_place_id'),
            'google_rating': lawyer_data.get('google_rating'),
            'google_review_count': lawyer_data.get('google_review_count'),

            # External data (JSONB)
            'external_data': lawyer_data.get('external_data'),

            # Verification
            'verification_status': lawyer_data.get('verification_status', 'unverified'),
        }

        return record

    def _insert_related_data(self, lawyer_id: str, lawyer_data: Dict):
        """Insert related data (specializations, team members, etc.)"""
        # Insert specializations
        specializations = lawyer_data.get('specializations', [])
        if specializations:
            self._insert_specializations(lawyer_id, specializations)

        # Insert service areas
        service_areas = lawyer_data.get('service_areas_detailed', [])
        if service_areas:
            self._insert_service_areas(lawyer_id, service_areas)

        # Insert team members
        team_members = lawyer_data.get('team_members', [])
        if team_members:
            self._insert_team_members(lawyer_id, team_members)

        # Insert case studies
        case_studies = lawyer_data.get('case_studies', [])
        if case_studies:
            self._insert_case_studies(lawyer_id, case_studies)

    def _insert_specializations(self, lawyer_id: str, specializations: List[str]):
        """Insert or link specializations"""
        for spec_name in specializations:
            try:
                # Get or create specialization
                spec_slug = slugify(spec_name)

                # Check if exists
                result = self.client.table('specializations').select('*').eq('slug', spec_slug).execute()

                if result.data:
                    spec_id = result.data[0]['id']
                else:
                    # Create new
                    result = self.client.table('specializations').insert({
                        'name': spec_name,
                        'slug': spec_slug
                    }).execute()
                    spec_id = result.data[0]['id']

                # Link to lawyer (ignore if already exists)
                try:
                    self.client.table('lawyer_specializations').insert({
                        'lawyer_id': lawyer_id,
                        'specialization_id': spec_id
                    }).execute()
                except:
                    pass  # Already exists

            except Exception as e:
                logger.warning(f"    Could not insert specialization '{spec_name}': {e}")

    def _insert_service_areas(self, lawyer_id: str, service_areas: List[Dict]):
        """Insert service areas"""
        for area in service_areas:
            try:
                self.client.table('lawyer_service_areas').insert({
                    'lawyer_id': lawyer_id,
                    'state': area.get('state', ''),
                    'state_code': area.get('state_code', ''),
                    'city': area.get('city', ''),
                    'postcode': area.get('postcode'),
                    'is_primary_location': area.get('is_primary_location', False)
                }).execute()
            except Exception as e:
                logger.warning(f"    Could not insert service area: {e}")

    def _insert_team_members(self, lawyer_id: str, team_members: List[Dict]):
        """Insert team members"""
        for i, member in enumerate(team_members):
            try:
                self.client.table('lawyer_team_members').insert({
                    'lawyer_id': lawyer_id,
                    'full_name': member.get('full_name', ''),
                    'role': member.get('role'),
                    'specialization': member.get('specialization'),
                    'photo_url': member.get('photo_url'),
                    'bio': member.get('bio'),
                    'years_experience': member.get('years_experience'),
                    'display_order': member.get('display_order', i)
                }).execute()
            except Exception as e:
                logger.warning(f"    Could not insert team member: {e}")

    def _insert_case_studies(self, lawyer_id: str, case_studies: List[Dict]):
        """Insert case studies"""
        for case in case_studies:
            try:
                slug = case.get('slug') or slugify(case.get('title', ''))

                self.client.table('case_studies').insert({
                    'lawyer_id': lawyer_id,
                    'title': case.get('title', ''),
                    'slug': slug,
                    'case_type': case.get('case_type'),
                    'year': case.get('year'),
                    'summary': case.get('summary', ''),
                    'outcome': case.get('outcome'),
                    'client_testimonial': case.get('client_testimonial'),
                    'is_published': case.get('is_published', False)
                }).execute()
            except Exception as e:
                logger.warning(f"    Could not insert case study: {e}")

    def _print_summary(self):
        """Print import summary"""
        print("\n" + "="*60)
        print("IMPORT SUMMARY")
        print("="*60)
        print(f"\nTotal processed: {self.stats['total']}")
        print(f"✓ Imported (new): {self.stats['imported']}")
        print(f"✓ Updated: {self.stats['updated']}")
        print(f"✗ Failed: {self.stats['failed']}")

        if self.stats['errors']:
            print("\nErrors:")
            for error in self.stats['errors'][:10]:  # Show first 10
                print(f"  - {error['firm_name']}: {error['error']}")

        print("\n" + "="*60 + "\n")


def main():
    """Main entry point"""
    # Get Supabase credentials from environment
    SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
    SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ERROR: Supabase credentials not set")
        print("\nRequired environment variables:")
        print("  SUPABASE_URL - Your Supabase project URL")
        print("  SUPABASE_SERVICE_ROLE_KEY - Your service role key")
        print("\nGet these from: https://app.supabase.com/project/_/settings/api")
        print("\nSet them:")
        print("  export SUPABASE_URL='https://xxxxx.supabase.co'")
        print("  export SUPABASE_SERVICE_ROLE_KEY='your-service-role-key'")
        sys.exit(1)

    # Get input file
    if len(sys.argv) < 2:
        print("Usage: python import_to_supabase.py <json_file>")
        print("\nExample:")
        print("  python import_to_supabase.py collected_data/03_final_20241114_120000.json")
        sys.exit(1)

    input_file = sys.argv[1]

    if not os.path.exists(input_file):
        print(f"ERROR: File not found: {input_file}")
        sys.exit(1)

    # Load data
    print(f"Loading data from: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        lawyers = json.load(f)

    print(f"Loaded {len(lawyers)} lawyers\n")

    # Confirm
    response = input("Proceed with import? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Import cancelled")
        sys.exit(0)

    # Import
    importer = SupabaseImporter(SUPABASE_URL, SUPABASE_KEY)
    stats = importer.import_lawyers(lawyers, update_existing=False)

    print("\n✅ Import complete!")


if __name__ == "__main__":
    main()
