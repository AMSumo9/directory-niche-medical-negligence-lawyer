# Medical Negligence Lawyers Data Collection System

Automated data collection pipeline for gathering high-quality lawyer information across Australia.

## 🎯 Overview

This system collects comprehensive data about medical negligence lawyers from multiple sources:

1. **Google Places API** - Business info, ratings, reviews, contact details
2. **Lawyer Websites** - Detailed info about services, team, experience, features
3. **AI-Generated Descriptions** - Professional descriptions based on collected data

## 📋 Prerequisites

### Required

1. **Python 3.8+**
2. **Google Places API Key**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable "Places API" and "Geocoding API"
   - Create an API key
   - **Important**: Set usage limits to avoid unexpected charges

3. **Supabase Account** (for importing data)
   - Sign up at [supabase.com](https://supabase.com)
   - Create a new project
   - Get your project URL and service role key

### Python Packages

Install required packages:

```bash
pip install requests beautifulsoup4 supabase-py
```

Or use requirements.txt:

```bash
pip install -r requirements.txt
```

## 🚀 Quick Start

### Step 1: Set Up Environment Variables

```bash
# Google Places API
export GOOGLE_PLACES_API_KEY='your-google-api-key-here'

# Supabase (for importing)
export SUPABASE_URL='https://xxxxx.supabase.co'
export SUPABASE_SERVICE_ROLE_KEY='your-service-role-key'
```

### Step 2: Set Up Database Schema

Run the migration on your Supabase database:

```bash
# In Supabase SQL Editor, run:
cd ..
# Copy contents of supabase-schema-migration.sql and run in Supabase SQL Editor
```

Or use the Supabase CLI:

```bash
supabase db push
```

### Step 3: Run Data Collection

```bash
cd data-collection
python run_data_collection.py
```

This will:
- Search Google Places for lawyers in major Australian cities
- Scrape their websites for detailed information
- Generate professional descriptions
- Save all data to `./collected_data/`

**Expected time**: 2-4 hours depending on number of cities and rate limiting

### Step 4: Review Collected Data

Check the output:

```bash
# View the final data
cat collected_data/03_final_*.json | jq '.[0]' | less

# View the collection report
cat collected_data/REPORT_*.json | jq
```

### Step 5: Import to Supabase

```bash
cd ..
python import_to_supabase.py data-collection/collected_data/03_final_*.json
```

## 📁 File Structure

```
data-collection/
├── run_data_collection.py      # Main orchestration script
├── google_places_collector.py  # Google Places API integration
├── website_scraper.py           # Website scraping and enrichment
├── description_generator.py    # AI description generation
├── scraper_law_societies.py    # Law society directory scrapers (optional)
├── README.md                    # This file
├── requirements.txt             # Python dependencies
└── collected_data/              # Output directory (created automatically)
    ├── 01_google_places_*.json  # Raw Google Places data
    ├── 02_enriched_*.json       # After website scraping
    ├── 03_final_*.json          # Final data with descriptions
    └── REPORT_*.json            # Collection statistics

../
├── supabase-schema-migration.sql  # Database schema
├── import_to_supabase.py          # Import script
└── import-script-example.py       # Alternative CSV/JSON importer
```

## 🔧 Detailed Usage

### Individual Scripts

#### 1. Google Places Collector

Collect lawyer data from Google Places:

```bash
python google_places_collector.py
```

This searches all major Australian cities and saves to `google_places_lawyers.json`.

**Customize cities** by editing the `australian_cities` list in the script.

#### 2. Website Scraper

Enrich existing data by scraping lawyer websites:

```bash
python website_scraper.py
```

Reads `google_places_lawyers.json` and saves enriched data to `lawyers_enriched.json`.

#### 3. Description Generator

Generate professional descriptions:

```bash
python description_generator.py lawyers_enriched.json
```

Saves to `lawyers_enriched_with_descriptions.json`.

### Full Pipeline

Run everything automatically:

```bash
python run_data_collection.py
```

**Options**:

```bash
# Resume from previous run (skip Google Places collection)
python run_data_collection.py --resume
```

## 📊 Data Quality

### What Gets Collected

For each lawyer, the system attempts to collect:

**Basic Information** (from Google Places):
- Firm name
- Full address (street, city, state, postcode)
- Phone number
- Website URL
- Google rating and review count
- Business hours
- Google Place ID

**Enhanced Information** (from website scraping):
- Detailed description (200-400 words)
- Short description (50-150 chars)
- Specializations
- Years of experience
- Team member profiles
- Awards and accreditations
- Case studies
- Client testimonials
- Service features (no win no fee, free consultation, etc.)
- Contact email
- Social media links

**Generated Content**:
- Professional description
- Short tagline
- SEO meta title
- SEO meta description

### Expected Quality Metrics

Based on typical runs:

- **Total lawyers collected**: 100-300 (depends on cities searched)
- **With website**: ~80%
- **With phone**: ~95%
- **With description**: ~100% (generated if not found)
- **With Google reviews**: ~60%
- **No win no fee**: ~40%
- **Free consultation**: ~50%

## ⚙️ Configuration

### Customize Cities

Edit `run_data_collection.py`:

```python
australian_cities = [
    ('Sydney', 'NSW'),
    ('Melbourne', 'VIC'),
    # Add more cities here
    ('Your City', 'STATE'),
]
```

### Adjust Rate Limiting

In each collector script, adjust delay:

```python
# google_places_collector.py
time.sleep(0.5)  # Increase to 1.0 or 2.0 if hitting rate limits

# website_scraper.py
LawyerWebsiteScraper(delay_seconds=2.0)  # Increase if needed
```

### Filter Search Results

Modify Google Places search query:

```python
# In google_places_collector.py
def search_lawyers_in_city(
    self,
    city: str,
    state_code: str,
    query: str = 'medical negligence lawyer',  # Customize this
    radius: int = 50000  # Search radius in meters
):
```

## 🔍 Troubleshooting

### Google Places API Errors

**"REQUEST_DENIED"**
- Check that you've enabled Places API and Geocoding API
- Verify your API key is correct
- Check billing is enabled (free tier should be sufficient)

**"OVER_QUERY_LIMIT"**
- You've hit the rate limit
- Increase `time.sleep()` delays
- Or wait and resume later

**Rate Limiting**
- Free tier: 1000 requests/month for Places API
- Each city search uses ~5-15 requests
- Website scraping is unlimited but be respectful

### Website Scraping Issues

**"Connection refused" or timeouts**
- Some websites block automated access
- The script will skip these and continue
- Review failed sites manually if needed

**Missing data after scraping**
- Website structure varies greatly
- Some sites may not match the scraping patterns
- Data quality will vary by source

### Import Errors

**"Duplicate key violation"**
- Lawyer already exists in database
- Use `update_existing=True` to update instead of skipping

**"Foreign key constraint violation"**
- Make sure you've run the schema migration first
- Check that specializations table exists

## 📈 Optimizing Results

### Get More Lawyers

1. **Add more cities** to the search list
2. **Increase search radius** in Google Places
3. **Try different search terms**:
   - "medical malpractice lawyer"
   - "clinical negligence solicitor"
   - "birth injury lawyer"

### Improve Data Quality

1. **Manual review**: Review and enhance top listings manually
2. **Direct outreach**: Contact high-quality firms for verified data
3. **Multiple sources**: Cross-reference with law society directories
4. **Verify information**: Use phone verification services

### Better Descriptions

1. **Customize templates** in `description_generator.py`
2. **Add more data sources** before description generation
3. **Use AI services**: Integrate OpenAI GPT for better descriptions

## 🎯 Next Steps

After collecting data:

1. **Review Data Quality**
   - Check `REPORT_*.json` for statistics
   - Review sample profiles
   - Identify gaps or errors

2. **Clean and Verify**
   - Remove duplicates
   - Verify contact information
   - Check for outdated data

3. **Enrich Further**
   - Add missing specializations manually
   - Collect case studies from public records
   - Contact lawyers for verified profiles

4. **Import to Database**
   - Run migration SQL
   - Import using import script
   - Verify data in Supabase

5. **Build Directory**
   - Create search/filter interface
   - Build lawyer profile pages
   - Implement lead capture forms

## 💡 Tips

- **Start small**: Test with 2-3 cities first
- **Monitor costs**: Google Places API is mostly free but monitor usage
- **Be respectful**: Don't hammer websites with requests
- **Save intermediate results**: The pipeline saves at each step
- **Resume capability**: Use `--resume` flag to skip Google Places
- **Version your data**: Keep timestamped backups

## 🔐 Privacy and Legal

- **Google Reviews**: Store review stats but don't display review text without permission
- **Website Content**: Respect robots.txt and terms of service
- **Personal Data**: Follow Australian Privacy Act requirements
- **Accuracy**: Verify information before displaying publicly
- **Lawyer Consent**: Consider getting lawyer approval before publishing detailed profiles

## 📞 Support

Common issues and solutions:

1. **Script crashes**: Check Python version (need 3.8+)
2. **No data collected**: Verify API key and internet connection
3. **Import fails**: Check Supabase credentials and schema
4. **Poor quality data**: Review and manually enhance

## 📝 Requirements File

Create `requirements.txt`:

```
requests>=2.28.0
beautifulsoup4>=4.11.0
supabase>=1.0.0
lxml>=4.9.0
```

## 🚀 Production Checklist

Before going live:

- [ ] Collected data from all major cities
- [ ] Reviewed and cleaned data
- [ ] Verified contact information for top listings
- [ ] Generated quality descriptions
- [ ] Imported to Supabase
- [ ] Set appropriate lawyers to `is_published=true`
- [ ] Tested search and filter functionality
- [ ] Set up lead capture forms
- [ ] Implemented analytics tracking
- [ ] Created lawyer claim/verification process

---

**Ready to collect data?** Run:

```bash
export GOOGLE_PLACES_API_KEY='your-key'
python run_data_collection.py
```

Happy collecting! 🎉
