"""
Description Generator for Lawyer Profiles
Generates professional descriptions based on collected data
"""

import json
from typing import Dict, List, Optional
import re


class LawyerDescriptionGenerator:
    """
    Generate professional descriptions for lawyer profiles
    Combines data from multiple sources into cohesive, SEO-friendly descriptions
    """

    def __init__(self):
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict:
        """Load description templates"""
        return {
            'intro_patterns': [
                "{firm_name} is a {adjective} medical negligence law firm serving {city}, {state}.",
                "Based in {city}, {state}, {firm_name} specializes in medical negligence and malpractice cases.",
                "{firm_name} has been representing medical negligence victims in {city} and throughout {state}.",
            ],
            'experience_patterns': [
                "With {years} years of experience, our team has successfully handled {cases} cases.",
                "Since {founded_year}, we have been dedicated to securing justice for medical negligence victims.",
                "Our experienced team has over {years} years of combined experience in medical malpractice law.",
            ],
            'specialization_patterns': [
                "We specialize in {specializations}, providing expert legal representation for victims of medical errors.",
                "Our practice areas include {specializations}.",
                "We handle a wide range of medical negligence cases, including {specializations}.",
            ],
            'features_patterns': [
                "We offer {features} to make it easier for clients to get the legal help they need.",
                "Our client-focused approach includes {features}.",
            ],
            'success_patterns': [
                "Our track record includes a {success_rate}% success rate in securing compensation for our clients.",
                "We have successfully recovered compensation for hundreds of medical negligence victims.",
                "Our commitment to excellence has resulted in numerous successful outcomes for our clients.",
            ],
            'closing_patterns': [
                "Contact us today for a free consultation to discuss your medical negligence case.",
                "If you or a loved one has been a victim of medical negligence, we're here to help.",
                "Get in touch with our experienced team to learn how we can assist with your case.",
            ]
        }

    def generate_description(self, lawyer_data: Dict) -> str:
        """
        Generate a full description (200-400 words) based on lawyer data

        Args:
            lawyer_data: Dictionary containing lawyer information

        Returns:
            Professional description string
        """
        paragraphs = []

        # Paragraph 1: Introduction
        intro = self._generate_intro(lawyer_data)
        if intro:
            paragraphs.append(intro)

        # Paragraph 2: Specializations
        spec_para = self._generate_specializations_paragraph(lawyer_data)
        if spec_para:
            paragraphs.append(spec_para)

        # Paragraph 3: Experience and credentials
        exp_para = self._generate_experience_paragraph(lawyer_data)
        if exp_para:
            paragraphs.append(exp_para)

        # Paragraph 4: Client service features
        features_para = self._generate_features_paragraph(lawyer_data)
        if features_para:
            paragraphs.append(features_para)

        # Paragraph 5: Call to action
        cta = self._generate_call_to_action(lawyer_data)
        if cta:
            paragraphs.append(cta)

        return '\n\n'.join(paragraphs)

    def generate_short_description(self, lawyer_data: Dict) -> str:
        """
        Generate a short description (50-150 characters) for listings

        Args:
            lawyer_data: Dictionary containing lawyer information

        Returns:
            Short description string
        """
        firm = lawyer_data.get('firm_name', 'This law firm')
        city = lawyer_data.get('city', '')
        state_code = lawyer_data.get('state_code', '')
        years = lawyer_data.get('years_experience')

        # Get primary specialization
        specs = lawyer_data.get('specializations', [])
        spec = specs[0] if specs else 'medical negligence'

        # Build short description
        parts = []

        if years:
            parts.append(f"{years}+ years experience")

        parts.append(spec.lower())

        location = f"{city}" if city else f"{state_code}"
        if location:
            parts.append(f"in {location}")

        # Check for key features
        features = []
        if lawyer_data.get('no_win_no_fee'):
            features.append("no win no fee")
        if lawyer_data.get('free_consultation'):
            features.append("free consultation")

        if features:
            parts.append(" | ".join(features).title())

        short_desc = f"{firm} - {', '.join(parts)}."

        # Ensure it's not too long
        if len(short_desc) > 200:
            short_desc = f"{firm} - {spec.title()} lawyers in {city}. {features[0].title() if features else 'Expert representation'}."

        return short_desc

    def _generate_intro(self, lawyer_data: Dict) -> str:
        """Generate introduction paragraph"""
        firm_name = lawyer_data.get('firm_name', 'This law firm')
        city = lawyer_data.get('city', '')
        state = lawyer_data.get('state', '')
        years = lawyer_data.get('years_experience')
        rating = lawyer_data.get('google_rating')

        # Choose adjective based on data quality
        adjectives = []
        if years and years > 20:
            adjectives.append('highly experienced')
        elif years and years > 10:
            adjectives.append('experienced')

        if rating and rating >= 4.5:
            adjectives.append('top-rated')
        elif rating and rating >= 4.0:
            adjectives.append('well-regarded')

        if lawyer_data.get('awards'):
            adjectives.append('award-winning')

        adjective = ', '.join(adjectives[:2]) if adjectives else 'dedicated'

        # Build intro
        intro = f"{firm_name} is a {adjective} medical negligence law firm"

        if city and state:
            intro += f" serving {city}, {state}"
        elif city:
            intro += f" based in {city}"
        elif state:
            intro += f" serving {state}"

        intro += "."

        # Add experience sentence if available
        if years:
            if lawyer_data.get('founded_year'):
                intro += f" Since {lawyer_data['founded_year']}, we have been dedicated to representing victims of medical malpractice."
            else:
                intro += f" With over {years} years of experience, we have successfully represented numerous medical negligence victims."

        # Add success rate if available
        if lawyer_data.get('success_rate'):
            intro += f" Our team maintains an impressive {lawyer_data['success_rate']}% success rate."

        return intro

    def _generate_specializations_paragraph(self, lawyer_data: Dict) -> str:
        """Generate paragraph about specializations"""
        specs = lawyer_data.get('specializations', [])

        if not specs:
            return "We handle all types of medical negligence and malpractice cases, providing expert legal representation for victims of medical errors."

        if len(specs) == 1:
            spec_text = specs[0].lower()
        elif len(specs) == 2:
            spec_text = f"{specs[0].lower()} and {specs[1].lower()}"
        else:
            spec_text = ', '.join([s.lower() for s in specs[:-1]]) + f", and {specs[-1].lower()}"

        para = f"Our practice areas include {spec_text}. "
        para += "We understand the complex medical and legal issues involved in these cases "
        para += "and work diligently to secure the compensation our clients deserve for their injuries and suffering."

        return para

    def _generate_experience_paragraph(self, lawyer_data: Dict) -> str:
        """Generate paragraph about experience and credentials"""
        parts = []

        # Experience
        if lawyer_data.get('total_cases_handled'):
            parts.append(f"Our experienced team has successfully handled over {lawyer_data['total_cases_handled']} medical negligence cases")

        # Awards
        awards = lawyer_data.get('awards', [])
        if awards:
            award_text = awards[0] if len(awards) == 1 else f"{len(awards)} professional awards and recognitions"
            parts.append(f"We have received {award_text}")

        # Accreditations
        accreds = lawyer_data.get('accreditations', [])
        if accreds:
            parts.append(f"Our lawyers hold specialist accreditations in personal injury and medical negligence law")

        # Team
        team = lawyer_data.get('team_members', [])
        if team and len(team) > 1:
            parts.append(f"Our team of {len(team)} dedicated legal professionals brings diverse expertise to every case")

        if not parts:
            return "Our experienced legal team is dedicated to providing exceptional representation for medical negligence victims. We stay current with the latest developments in medical malpractice law to best serve our clients."

        para = ". ".join(parts) + "."
        return para

    def _generate_features_paragraph(self, lawyer_data: Dict) -> str:
        """Generate paragraph about client service features"""
        features = []

        if lawyer_data.get('no_win_no_fee'):
            features.append("no win, no fee arrangements")

        if lawyer_data.get('free_consultation'):
            features.append("free initial consultations")

        if lawyer_data.get('home_visits_available'):
            features.append("home and hospital visits")

        if lawyer_data.get('telehealth_available'):
            features.append("virtual consultations")

        if not features:
            return "We are committed to providing accessible, compassionate legal services to medical negligence victims. Our client-focused approach ensures you receive the personal attention and expert representation your case deserves."

        feature_text = ', '.join(features[:-1]) + f" and {features[-1]}" if len(features) > 1 else features[0]

        para = f"We understand that pursuing a medical negligence claim can be daunting, which is why we offer {feature_text}. "
        para += "Our compassionate approach means we take the time to understand your situation and guide you through every step of the legal process."

        # Add response time if available
        if lawyer_data.get('average_response_time'):
            para += f" We pride ourselves on our responsiveness, typically responding to inquiries {lawyer_data['average_response_time'].lower()}."

        return para

    def _generate_call_to_action(self, lawyer_data: Dict) -> str:
        """Generate call to action paragraph"""
        firm = lawyer_data.get('firm_name', 'our firm')
        city = lawyer_data.get('city', '')

        cta = "If you or a loved one has been a victim of medical negligence, don't wait to seek legal advice. "

        if lawyer_data.get('free_consultation'):
            cta += f"Contact {firm} today for a free, confidential consultation. "
        else:
            cta += f"Contact {firm} today to discuss your case. "

        cta += "We'll review your situation, explain your legal options, and help you understand your rights. "

        if city:
            cta += f"Let our experienced {city} medical negligence lawyers fight for the justice and compensation you deserve."
        else:
            cta += "Let our experienced medical negligence lawyers fight for the justice and compensation you deserve."

        return cta

    def generate_meta_description(self, lawyer_data: Dict) -> str:
        """
        Generate SEO meta description (150-160 characters)
        """
        firm = lawyer_data.get('firm_name', 'Medical negligence lawyers')
        city = lawyer_data.get('city', '')
        years = lawyer_data.get('years_experience')
        success_rate = lawyer_data.get('success_rate')

        # Build meta description
        parts = [firm]

        if city:
            parts.append(f"in {city}")

        if years:
            parts.append(f"{years}+ yrs exp")

        if success_rate:
            parts.append(f"{success_rate}% success rate")

        features = []
        if lawyer_data.get('no_win_no_fee'):
            features.append("No win no fee")
        if lawyer_data.get('free_consultation'):
            features.append("Free consultation")

        meta = " | ".join(parts)
        if features:
            meta += ". " + ", ".join(features)

        meta += ". Call today."

        # Ensure within character limit
        if len(meta) > 160:
            meta = meta[:157] + "..."

        return meta

    def generate_meta_title(self, lawyer_data: Dict) -> str:
        """
        Generate SEO meta title (50-60 characters)
        """
        firm = lawyer_data.get('firm_name', 'Medical Negligence Lawyers')
        city = lawyer_data.get('city', '')
        state_code = lawyer_data.get('state_code', '')

        if len(firm) > 30:
            # Use generic title if firm name is too long
            title = f"Medical Negligence Lawyers {city}"
        else:
            title = f"{firm} - {city} {state_code}"

        # Ensure within character limit
        if len(title) > 60:
            title = title[:57] + "..."

        return title


# ============================================================================
# Batch processing
# ============================================================================

def generate_descriptions_for_all(lawyers: List[Dict]) -> List[Dict]:
    """
    Generate descriptions for all lawyers in the list

    Args:
        lawyers: List of lawyer dictionaries

    Returns:
        List of lawyers with generated descriptions
    """
    generator = LawyerDescriptionGenerator()

    for lawyer in lawyers:
        # Only generate if description is missing or poor quality
        existing_desc = lawyer.get('description', '')

        if not existing_desc or len(existing_desc) < 100:
            lawyer['description'] = generator.generate_description(lawyer)

        # Always generate short description
        lawyer['short_description'] = generator.generate_short_description(lawyer)

        # Generate meta tags
        lawyer['meta_title'] = generator.generate_meta_title(lawyer)
        lawyer['meta_description'] = generator.generate_meta_description(lawyer)

    return lawyers


if __name__ == "__main__":
    import sys

    # Example usage
    try:
        input_file = sys.argv[1] if len(sys.argv) > 1 else 'lawyers_enriched.json'

        with open(input_file, 'r', encoding='utf-8') as f:
            lawyers = json.load(f)

        print(f"Loaded {len(lawyers)} lawyers")
        print("Generating descriptions...\n")

        lawyers = generate_descriptions_for_all(lawyers)

        # Save with descriptions
        output_file = input_file.replace('.json', '_with_descriptions.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(lawyers, f, indent=2, ensure_ascii=False)

        print(f"Descriptions generated and saved to: {output_file}")

        # Show example
        if lawyers:
            print("\n" + "="*60)
            print("EXAMPLE GENERATED DESCRIPTION:")
            print("="*60)
            print(f"\nFirm: {lawyers[0].get('firm_name')}")
            print(f"\nShort Description:\n{lawyers[0].get('short_description')}")
            print(f"\nFull Description:\n{lawyers[0].get('description')}")
            print(f"\nMeta Title: {lawyers[0].get('meta_title')}")
            print(f"Meta Description: {lawyers[0].get('meta_description')}")

    except FileNotFoundError:
        print(f"File not found: {input_file}")
        print("\nUsage: python description_generator.py <input_file.json>")
        print("Run the data collection scripts first")
