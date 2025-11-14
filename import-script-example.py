"""
Data Import Script for Medical Negligence Lawyers Directory
This script helps import lawyer data from CSV/JSON into PostgreSQL database
"""

import csv
import json
import psycopg2
from psycopg2.extras import execute_values
import re
from datetime import datetime
from typing import List, Dict, Optional


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug"""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')


class LawyerImporter:
    def __init__(self, db_config: Dict[str, str]):
        """
        Initialize importer with database connection

        db_config example:
        {
            'host': 'localhost',
            'database': 'lawyers_db',
            'user': 'postgres',
            'password': 'your_password'
        }
        """
        self.conn = psycopg2.connect(**db_config)
        self.cur = self.conn.cursor()

    def __del__(self):
        """Close database connection"""
        if hasattr(self, 'cur'):
            self.cur.close()
        if hasattr(self, 'conn'):
            self.conn.close()

    def import_from_csv(self, csv_file_path: str) -> int:
        """
        Import lawyers from CSV file

        CSV Format:
        firm_name,state,state_code,city,address,phone,email,website,
        short_description,description,years_experience,founded_year,
        languages,free_consultation,no_win_no_fee,home_visits_available,
        specializations,service_areas

        Returns: Number of lawyers imported
        """
        imported_count = 0

        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)

            for row in reader:
                try:
                    lawyer_data = self._parse_csv_row(row)
                    lawyer_id = self._insert_lawyer(lawyer_data)

                    # Insert specializations
                    if 'specializations' in lawyer_data:
                        self._insert_lawyer_specializations(
                            lawyer_id,
                            lawyer_data['specializations']
                        )

                    # Insert service areas
                    if 'service_areas' in lawyer_data:
                        self._insert_service_areas(
                            lawyer_id,
                            lawyer_data['service_areas']
                        )

                    self.conn.commit()
                    imported_count += 1
                    print(f"✓ Imported: {lawyer_data['firm_name']}")

                except Exception as e:
                    self.conn.rollback()
                    print(f"✗ Error importing {row.get('firm_name', 'Unknown')}: {str(e)}")

        return imported_count

    def import_from_json(self, json_file_path: str) -> int:
        """
        Import lawyers from JSON file

        JSON should be array of lawyer objects matching data-collection-template.json

        Returns: Number of lawyers imported
        """
        imported_count = 0

        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

            # Handle both single object and array
            lawyers = data if isinstance(data, list) else [data]

            for lawyer_data in lawyers:
                try:
                    lawyer_id = self._insert_lawyer_from_json(lawyer_data)
                    self.conn.commit()
                    imported_count += 1
                    firm_name = lawyer_data.get('basic_information', {}).get('firm_name', 'Unknown')
                    print(f"✓ Imported: {firm_name}")

                except Exception as e:
                    self.conn.rollback()
                    firm_name = lawyer_data.get('basic_information', {}).get('firm_name', 'Unknown')
                    print(f"✗ Error importing {firm_name}: {str(e)}")

        return imported_count

    def _parse_csv_row(self, row: Dict[str, str]) -> Dict:
        """Parse CSV row into structured data"""
        # Generate slug if not provided
        slug = row.get('slug') or slugify(f"{row['firm_name']}-{row['city']}")

        # Parse array fields (pipe-separated)
        languages = row.get('languages', '').split('|') if row.get('languages') else []
        languages = [lang.strip() for lang in languages if lang.strip()]

        specializations = row.get('specializations', '').split('|') if row.get('specializations') else []
        specializations = [spec.strip() for spec in specializations if spec.strip()]

        service_areas = row.get('service_areas', '').split('|') if row.get('service_areas') else []
        service_areas = [area.strip() for area in service_areas if area.strip()]

        # Parse boolean fields
        def parse_bool(value: str) -> bool:
            if isinstance(value, bool):
                return value
            return value.lower() in ('true', '1', 'yes', 't') if value else False

        return {
            'firm_name': row['firm_name'],
            'slug': slug,
            'state': row['state'],
            'state_code': row['state_code'],
            'city': row['city'],
            'address': row.get('address'),
            'phone': row.get('phone'),
            'email': row.get('email'),
            'website': row.get('website'),
            'show_phone_link': parse_bool(row.get('show_phone_link', 'true')),
            'show_email_link': parse_bool(row.get('show_email_link', 'true')),
            'show_website_link': parse_bool(row.get('show_website_link', 'true')),
            'short_description': row.get('short_description'),
            'description': row.get('description'),
            'years_experience': int(row['years_experience']) if row.get('years_experience') else None,
            'founded_year': int(row['founded_year']) if row.get('founded_year') else None,
            'languages': languages,
            'free_consultation': parse_bool(row.get('free_consultation', 'false')),
            'no_win_no_fee': parse_bool(row.get('no_win_no_fee', 'false')),
            'home_visits_available': parse_bool(row.get('home_visits_available', 'false')),
            'specializations': specializations,
            'service_areas': service_areas,
        }

    def _insert_lawyer(self, data: Dict) -> str:
        """Insert lawyer into database and return ID"""
        query = """
            INSERT INTO lawyers (
                firm_name, slug, state, state_code, city, address,
                phone, email, website, show_phone_link, show_email_link,
                show_website_link, short_description, description,
                years_experience, founded_year, languages,
                free_consultation, no_win_no_fee, home_visits_available
            ) VALUES (
                %(firm_name)s, %(slug)s, %(state)s, %(state_code)s, %(city)s,
                %(address)s, %(phone)s, %(email)s, %(website)s,
                %(show_phone_link)s, %(show_email_link)s, %(show_website_link)s,
                %(short_description)s, %(description)s, %(years_experience)s,
                %(founded_year)s, %(languages)s, %(free_consultation)s,
                %(no_win_no_fee)s, %(home_visits_available)s
            )
            RETURNING id
        """

        self.cur.execute(query, data)
        lawyer_id = self.cur.fetchone()[0]
        return lawyer_id

    def _insert_lawyer_specializations(self, lawyer_id: str, specializations: List[str]):
        """Insert lawyer specializations"""
        for spec_name in specializations:
            # Get or create specialization
            self.cur.execute(
                "SELECT id FROM specializations WHERE name = %s",
                (spec_name,)
            )
            result = self.cur.fetchone()

            if result:
                spec_id = result[0]
            else:
                # Create new specialization
                spec_slug = slugify(spec_name)
                self.cur.execute(
                    """
                    INSERT INTO specializations (name, slug)
                    VALUES (%s, %s)
                    RETURNING id
                    """,
                    (spec_name, spec_slug)
                )
                spec_id = self.cur.fetchone()[0]

            # Link lawyer to specialization
            self.cur.execute(
                """
                INSERT INTO lawyer_specializations (lawyer_id, specialization_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                """,
                (lawyer_id, spec_id)
            )

    def _insert_service_areas(self, lawyer_id: str, service_areas: List[str]):
        """Insert service areas for lawyer"""
        # This is a simplified version - you may want to parse city/state from service_areas
        for i, area in enumerate(service_areas):
            # Try to parse "City, State" format
            parts = area.split(',')
            if len(parts) >= 2:
                city = parts[0].strip()
                state_code = parts[1].strip()
            else:
                # Just use the area as city
                city = area
                state_code = None

            if state_code:
                self.cur.execute(
                    """
                    INSERT INTO lawyer_service_areas
                    (lawyer_id, state_code, city, is_primary_location)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (lawyer_id, state_code, city, i == 0)
                )

    def _insert_lawyer_from_json(self, data: Dict) -> str:
        """Import lawyer from JSON template format"""
        basic = data.get('basic_information', {})
        contact_prefs = data.get('contact_preferences', {})
        descriptions = data.get('descriptions', {})
        firm_details = data.get('firm_details', {})
        client_service = data.get('client_service', {})

        # Generate slug
        slug = basic.get('slug') or slugify(f"{basic['firm_name']}-{basic['city']}")

        # Insert main lawyer record
        lawyer_data = {
            'firm_name': basic['firm_name'],
            'slug': slug,
            'state': basic['state'],
            'state_code': basic['state_code'],
            'city': basic['city'],
            'address': basic.get('address'),
            'phone': basic.get('phone'),
            'email': basic.get('email'),
            'website': basic.get('website'),
            'show_phone_link': contact_prefs.get('show_phone_link', False),
            'show_email_link': contact_prefs.get('show_email_link', False),
            'show_website_link': contact_prefs.get('show_website_link', False),
            'short_description': descriptions.get('short_description'),
            'description': descriptions.get('description'),
            'years_experience': firm_details.get('years_experience'),
            'founded_year': firm_details.get('founded_year'),
            'languages': firm_details.get('languages', []),
            'free_consultation': client_service.get('free_consultation', False),
            'no_win_no_fee': client_service.get('no_win_no_fee', False),
            'home_visits_available': client_service.get('home_visits_available', False),
        }

        lawyer_id = self._insert_lawyer(lawyer_data)

        # Insert specializations
        if 'specializations' in data:
            self._insert_lawyer_specializations(lawyer_id, data['specializations'])

        # Insert service areas
        if 'service_areas' in data:
            for area in data['service_areas']:
                self.cur.execute(
                    """
                    INSERT INTO lawyer_service_areas
                    (lawyer_id, state, state_code, city, postcode, is_primary_location)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        lawyer_id,
                        area['state'],
                        area['state_code'],
                        area['city'],
                        area.get('postcode'),
                        area.get('is_primary_location', False)
                    )
                )

        # Insert team members
        if 'team_members' in data:
            for member in data['team_members']:
                self.cur.execute(
                    """
                    INSERT INTO lawyer_team_members
                    (lawyer_id, full_name, role, specialization, years_experience, bio, display_order)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        lawyer_id,
                        member['full_name'],
                        member['role'],
                        member.get('specialization'),
                        member.get('years_experience'),
                        member.get('bio'),
                        member.get('display_order', 0)
                    )
                )

        # Insert qualifications
        if 'qualifications' in data:
            for qual in data['qualifications']:
                self.cur.execute(
                    """
                    INSERT INTO lawyer_qualifications
                    (lawyer_id, qualification_type, institution, qualification_name, year_obtained)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        lawyer_id,
                        qual['qualification_type'],
                        qual['institution'],
                        qual['qualification_name'],
                        qual.get('year_obtained')
                    )
                )

        # Insert case studies
        if 'case_studies' in data:
            for case in data['case_studies']:
                self.cur.execute(
                    """
                    INSERT INTO case_studies
                    (lawyer_id, title, slug, case_type, year, settlement_amount, summary, outcome)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        lawyer_id,
                        case['title'],
                        case['slug'],
                        case.get('case_type'),
                        case.get('year'),
                        case.get('settlement_amount'),
                        case['summary'],
                        case.get('outcome')
                    )
                )

        # Insert FAQs
        if 'faqs' in data:
            for faq in data['faqs']:
                self.cur.execute(
                    """
                    INSERT INTO lawyer_faqs
                    (lawyer_id, question, answer, display_order)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        lawyer_id,
                        faq['question'],
                        faq['answer'],
                        faq.get('display_order', 0)
                    )
                )

        return lawyer_id

    def calculate_profile_completeness(self, lawyer_id: str) -> int:
        """
        Calculate profile completeness score (0-100)

        Scoring:
        - Base info (20): name, address, phone, email, website
        - Enhanced info (30): description, experience, specializations, team, service features
        - Social proof (30): reviews, case studies, awards
        - Media (10): images
        - Verification (10): verified status
        """
        score = 0

        # Get lawyer data
        self.cur.execute("SELECT * FROM lawyers WHERE id = %s", (lawyer_id,))
        lawyer = self.cur.fetchone()

        if not lawyer:
            return 0

        # Base information (20 points)
        base_fields = ['firm_name', 'address', 'phone', 'email', 'website']
        # Note: Adjust indices based on your actual table structure
        # This is illustrative
        if all([lawyer[1], lawyer[5], lawyer[6], lawyer[7], lawyer[8]]):  # Example indices
            score += 20

        # Enhanced information (30 points)
        if lawyer[13]:  # description
            score += 5
        if lawyer[16]:  # years_experience
            score += 5

        # Check specializations count
        self.cur.execute(
            "SELECT COUNT(*) FROM lawyer_specializations WHERE lawyer_id = %s",
            (lawyer_id,)
        )
        spec_count = self.cur.fetchone()[0]
        if spec_count > 0:
            score += 5

        # Team members
        self.cur.execute(
            "SELECT COUNT(*) FROM lawyer_team_members WHERE lawyer_id = %s",
            (lawyer_id,)
        )
        team_count = self.cur.fetchone()[0]
        if team_count > 0:
            score += 5

        # Service features
        if lawyer[24] or lawyer[25]:  # free_consultation or no_win_no_fee
            score += 10

        # Social proof (30 points)
        # Reviews
        self.cur.execute(
            "SELECT COUNT(*) FROM lawyer_reviews WHERE lawyer_id = %s AND is_published = true",
            (lawyer_id,)
        )
        review_count = self.cur.fetchone()[0]
        if review_count >= 3:
            score += 15
        elif review_count > 0:
            score += 10

        # Case studies
        self.cur.execute(
            "SELECT COUNT(*) FROM case_studies WHERE lawyer_id = %s AND is_published = true",
            (lawyer_id,)
        )
        case_count = self.cur.fetchone()[0]
        if case_count > 0:
            score += 10

        # Awards (if exists in lawyer record)
        # score += 5 if has awards

        # Media (10 points)
        # Check for images
        # score += 10 if has images

        # Verification (10 points)
        # Check verification_status
        # score += 10 if verified

        # Update the lawyer record
        self.cur.execute(
            "UPDATE lawyers SET profile_completeness_score = %s WHERE id = %s",
            (score, lawyer_id)
        )

        return score


# Example usage
if __name__ == "__main__":
    # Database configuration
    db_config = {
        'host': 'localhost',
        'database': 'lawyers_directory',
        'user': 'postgres',
        'password': 'your_password'
    }

    # Create importer
    importer = LawyerImporter(db_config)

    # Import from CSV
    # count = importer.import_from_csv('lawyers_data.csv')
    # print(f"\nImported {count} lawyers from CSV")

    # Import from JSON
    # count = importer.import_from_json('lawyers_data.json')
    # print(f"\nImported {count} lawyers from JSON")

    print("Import script ready. Uncomment the import lines above to use.")
