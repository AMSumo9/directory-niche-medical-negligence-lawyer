"""
Main Data Collection Pipeline
Orchestrates the complete data collection process for medical negligence lawyers
"""

import json
import os
import sys
from typing import List, Dict
import logging
from datetime import datetime

# Import our collection modules
from google_places_collector import GooglePlacesCollector
from website_scraper import enrich_lawyers_with_website_data
from description_generator import generate_descriptions_for_all

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataCollectionPipeline:
    """
    Main pipeline for collecting lawyer data
    """

    def __init__(self, google_api_key: str, output_dir: str = './collected_data'):
        self.google_api_key = google_api_key
        self.output_dir = output_dir
        self.ensure_output_dir()

        # Initialize collectors
        self.places_collector = GooglePlacesCollector(google_api_key)

    def ensure_output_dir(self):
        """Create output directory if it doesn't exist"""
        os.makedirs(self.output_dir, exist_ok=True)

    def run_full_collection(
        self,
        cities_states: List[tuple],
        skip_google: bool = False,
        skip_websites: bool = False,
        skip_descriptions: bool = False
    ) -> List[Dict]:
        """
        Run the complete data collection pipeline

        Args:
            cities_states: List of (city, state_code) tuples to search
            skip_google: Skip Google Places collection (use existing data)
            skip_websites: Skip website scraping
            skip_descriptions: Skip description generation

        Returns:
            List of fully enriched lawyer dictionaries
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Step 1: Collect from Google Places
        if not skip_google:
            logger.info("="*60)
            logger.info("STEP 1: Collecting data from Google Places API")
            logger.info("="*60)

            lawyers = self.places_collector.search_lawyers_bulk(cities_states)

            logger.info(f"Collected {len(lawyers)} lawyers from Google Places")

            # Save intermediate result
            google_file = os.path.join(self.output_dir, f'01_google_places_{timestamp}.json')
            self.save_json(lawyers, google_file)
            logger.info(f"Saved to: {google_file}\n")
        else:
            # Load existing Google Places data
            logger.info("Skipping Google Places collection, loading existing data...")
            lawyers = self.load_latest_file('01_google_places_*.json')

        # Step 2: Enrich with website data
        if not skip_websites and lawyers:
            logger.info("="*60)
            logger.info("STEP 2: Enriching with website data")
            logger.info("="*60)

            lawyers = enrich_lawyers_with_website_data(lawyers)

            logger.info(f"Enriched {len(lawyers)} lawyer profiles")

            # Save intermediate result
            enriched_file = os.path.join(self.output_dir, f'02_enriched_{timestamp}.json')
            self.save_json(lawyers, enriched_file)
            logger.info(f"Saved to: {enriched_file}\n")
        elif skip_websites and not skip_google:
            # Just loaded Google data, so enriched = google
            pass
        else:
            # Load existing enriched data
            logger.info("Skipping website scraping, loading existing data...")
            lawyers = self.load_latest_file('02_enriched_*.json')

        # Step 3: Generate descriptions
        if not skip_descriptions and lawyers:
            logger.info("="*60)
            logger.info("STEP 3: Generating descriptions")
            logger.info("="*60)

            lawyers = generate_descriptions_for_all(lawyers)

            logger.info(f"Generated descriptions for {len(lawyers)} lawyers")

            # Save final result
            final_file = os.path.join(self.output_dir, f'03_final_{timestamp}.json')
            self.save_json(lawyers, final_file)
            logger.info(f"Saved to: {final_file}\n")
        else:
            # Load existing final data
            logger.info("Skipping description generation, loading existing data...")
            lawyers = self.load_latest_file('03_final_*.json')

        # Step 4: Generate summary report
        self.generate_report(lawyers, timestamp)

        return lawyers

    def save_json(self, data: List[Dict], filename: str):
        """Save data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_latest_file(self, pattern: str) -> List[Dict]:
        """Load the most recent file matching pattern"""
        import glob

        files = glob.glob(os.path.join(self.output_dir, pattern))
        if not files:
            logger.error(f"No files found matching {pattern}")
            return []

        latest = max(files, key=os.path.getctime)
        logger.info(f"Loading: {latest}")

        with open(latest, 'r', encoding='utf-8') as f:
            return json.load(f)

    def generate_report(self, lawyers: List[Dict], timestamp: str):
        """Generate collection summary report"""
        report = {
            'timestamp': timestamp,
            'total_lawyers': len(lawyers),
            'by_state': {},
            'by_city': {},
            'data_quality': {
                'with_website': 0,
                'with_description': 0,
                'with_phone': 0,
                'with_email': 0,
                'with_google_reviews': 0,
                'with_specializations': 0,
                'average_completeness': 0
            },
            'features': {
                'no_win_no_fee': 0,
                'free_consultation': 0,
                'home_visits': 0,
                'telehealth': 0
            }
        }

        completeness_scores = []

        for lawyer in lawyers:
            # By state
            state = lawyer.get('state_code', 'Unknown')
            report['by_state'][state] = report['by_state'].get(state, 0) + 1

            # By city
            city = lawyer.get('city', 'Unknown')
            report['by_city'][city] = report['by_city'].get(city, 0) + 1

            # Data quality
            if lawyer.get('website'):
                report['data_quality']['with_website'] += 1
            if lawyer.get('description') and len(lawyer.get('description', '')) > 100:
                report['data_quality']['with_description'] += 1
            if lawyer.get('phone'):
                report['data_quality']['with_phone'] += 1
            if lawyer.get('email'):
                report['data_quality']['with_email'] += 1
            if lawyer.get('google_review_count', 0) > 0:
                report['data_quality']['with_google_reviews'] += 1
            if lawyer.get('specializations'):
                report['data_quality']['with_specializations'] += 1

            # Calculate simple completeness
            fields = ['firm_name', 'address', 'phone', 'email', 'website', 'description', 'short_description']
            complete_fields = sum(1 for f in fields if lawyer.get(f))
            completeness = (complete_fields / len(fields)) * 100
            completeness_scores.append(completeness)

            # Features
            if lawyer.get('no_win_no_fee'):
                report['features']['no_win_no_fee'] += 1
            if lawyer.get('free_consultation'):
                report['features']['free_consultation'] += 1
            if lawyer.get('home_visits_available'):
                report['features']['home_visits'] += 1
            if lawyer.get('telehealth_available'):
                report['features']['telehealth'] += 1

        # Calculate average completeness
        if completeness_scores:
            report['data_quality']['average_completeness'] = sum(completeness_scores) / len(completeness_scores)

        # Save report
        report_file = os.path.join(self.output_dir, f'REPORT_{timestamp}.json')
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)

        # Print report summary
        self.print_report_summary(report)

        return report

    def print_report_summary(self, report: Dict):
        """Print report summary to console"""
        print("\n" + "="*60)
        print("DATA COLLECTION REPORT")
        print("="*60)
        print(f"\nTotal Lawyers Collected: {report['total_lawyers']}")

        print("\n📍 By State:")
        for state, count in sorted(report['by_state'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {state}: {count}")

        print("\n🏙️  Top Cities:")
        top_cities = sorted(report['by_city'].items(), key=lambda x: x[1], reverse=True)[:10]
        for city, count in top_cities:
            print(f"  {city}: {count}")

        print("\n✅ Data Quality:")
        dq = report['data_quality']
        total = report['total_lawyers']
        print(f"  With Website: {dq['with_website']} ({dq['with_website']/total*100:.1f}%)")
        print(f"  With Description: {dq['with_description']} ({dq['with_description']/total*100:.1f}%)")
        print(f"  With Phone: {dq['with_phone']} ({dq['with_phone']/total*100:.1f}%)")
        print(f"  With Email: {dq['with_email']} ({dq['with_email']/total*100:.1f}%)")
        print(f"  With Google Reviews: {dq['with_google_reviews']} ({dq['with_google_reviews']/total*100:.1f}%)")
        print(f"  Average Completeness: {dq['average_completeness']:.1f}%")

        print("\n🎯 Features:")
        feat = report['features']
        print(f"  No Win No Fee: {feat['no_win_no_fee']} ({feat['no_win_no_fee']/total*100:.1f}%)")
        print(f"  Free Consultation: {feat['free_consultation']} ({feat['free_consultation']/total*100:.1f}%)")
        print(f"  Home Visits: {feat['home_visits']} ({feat['home_visits']/total*100:.1f}%)")
        print(f"  Telehealth: {feat['telehealth']} ({feat['telehealth']/total*100:.1f}%)")

        print("\n" + "="*60 + "\n")


# ============================================================================
# Main execution
# ============================================================================

def main():
    """Main entry point"""
    # Get API key from environment
    API_KEY = os.environ.get('GOOGLE_PLACES_API_KEY', '')

    if not API_KEY:
        print("ERROR: GOOGLE_PLACES_API_KEY environment variable not set")
        print("\nTo get an API key:")
        print("1. Visit https://console.cloud.google.com/")
        print("2. Create a new project")
        print("3. Enable 'Places API' and 'Geocoding API'")
        print("4. Create an API key")
        print("5. Set environment variable:")
        print("   export GOOGLE_PLACES_API_KEY='your-api-key-here'")
        sys.exit(1)

    # Define cities to search
    # Start with major cities, can expand later
    australian_cities = [
        # Major cities
        ('Sydney', 'NSW'),
        ('Melbourne', 'VIC'),
        ('Brisbane', 'QLD'),
        ('Perth', 'WA'),
        ('Adelaide', 'SA'),

        # Secondary cities
        ('Gold Coast', 'QLD'),
        ('Newcastle', 'NSW'),
        ('Canberra', 'ACT'),
        ('Wollongong', 'NSW'),
        ('Geelong', 'VIC'),

        # Add more as needed
        # ('Hobart', 'TAS'),
        # ('Townsville', 'QLD'),
        # ('Cairns', 'QLD'),
    ]

    # Initialize pipeline
    pipeline = DataCollectionPipeline(
        google_api_key=API_KEY,
        output_dir='./collected_data'
    )

    # Run collection
    print("="*60)
    print("MEDICAL NEGLIGENCE LAWYERS DATA COLLECTION")
    print("="*60)
    print(f"\nSearching {len(australian_cities)} cities...")
    print("This will take some time due to API rate limiting.\n")

    # Option: Resume from previous run
    resume = '--resume' in sys.argv

    lawyers = pipeline.run_full_collection(
        cities_states=australian_cities,
        skip_google=resume,  # Skip Google if resuming
        skip_websites=False,
        skip_descriptions=False
    )

    print(f"\n✅ Collection complete!")
    print(f"📁 Data saved to: ./collected_data/")
    print(f"📊 Total lawyers collected: {len(lawyers)}")

    # Next steps
    print("\n" + "="*60)
    print("NEXT STEPS:")
    print("="*60)
    print("\n1. Review the collected data in ./collected_data/")
    print("2. Check the REPORT_*.json file for quality metrics")
    print("3. Review and clean the data as needed")
    print("4. Import into Supabase using:")
    print("   cd ..")
    print("   python import_to_supabase.py collected_data/03_final_*.json")
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    main()
