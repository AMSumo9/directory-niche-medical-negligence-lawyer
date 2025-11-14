# Setup and Run Guide - Medical Negligence Lawyers Directory

## 🎯 Quick Start Guide

This guide will help you collect high-quality data for your medical negligence lawyers directory.

---

## Step 1: Database Setup (5 minutes)

### Run Schema Migration

1. Log in to your Supabase dashboard: https://app.supabase.com
2. Go to **SQL Editor**
3. Copy the contents of `supabase-schema-migration.sql`
4. Paste and run in SQL Editor
5. Verify tables were created successfully

**Tables created:**
- `lawyers` (enhanced with new columns)
- `lawyer_reviews`
- `lawyer_team_members`
- `case_studies`
- `lawyer_qualifications`
- `lawyer_faqs`
- `lawyer_service_areas`
- `lawyer_analytics`

---

## Step 2: Get Google Places API Key (10 minutes)

### Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable the following APIs:
   - **Places API**
   - **Geocoding API**
4. Go to **Credentials** → **Create Credentials** → **API Key**
5. Copy your API key
6. (Optional) Restrict the API key to only Places and Geocoding APIs

### Set Usage Limits (Recommended)

To avoid unexpected charges:

1. Go to **APIs & Services** → **Places API** → **Quotas**
2. Set daily quota to reasonable limit (e.g., 1000 requests/day)
3. Same for Geocoding API

**Cost Estimate:**
- Free tier: $200/month credit
- Typical collection: ~100-300 requests (~$5-15)
- Well within free tier for initial collection

---

## Step 3: Install Dependencies (2 minutes)

```bash
cd data-collection

# Install Python packages
pip install -r requirements.txt
```

**Required packages:**
- `requests` - HTTP requests
- `beautifulsoup4` - Web scraping
- `supabase` - Database client
- `lxml` - HTML parsing

---

## Step 4: Configure Environment (1 minute)

```bash
# Set Google Places API Key
export GOOGLE_PLACES_API_KEY='your-google-api-key-here'

# Set Supabase credentials (for importing later)
export SUPABASE_URL='https://xxxxx.supabase.co'
export SUPABASE_SERVICE_ROLE_KEY='your-service-role-key'
```

**Get Supabase credentials:**
1. Go to Supabase Dashboard → Settings → API
2. Copy **Project URL** and **service_role key**

**Make it permanent** (optional):

```bash
# Add to ~/.bashrc or ~/.zshrc
echo "export GOOGLE_PLACES_API_KEY='your-key'" >> ~/.bashrc
echo "export SUPABASE_URL='your-url'" >> ~/.bashrc
echo "export SUPABASE_SERVICE_ROLE_KEY='your-key'" >> ~/.bashrc

source ~/.bashrc
```

---

## Step 5: Run Data Collection (2-4 hours)

### Start Collection

```bash
python run_data_collection.py
```

This will:
1. ✅ Search Google Places for lawyers in major Australian cities
2. ✅ Scrape lawyer websites for detailed information
3. ✅ Generate professional descriptions
4. ✅ Save data to `./collected_data/`

### What Happens During Collection

**Phase 1: Google Places (30-60 min)**
- Searches 10 major Australian cities
- Collects business info, ratings, contact details
- ~100-300 lawyers found typically

**Phase 2: Website Scraping (1-2 hours)**
- Visits each lawyer's website
- Extracts detailed information
- Respectful rate limiting (2 sec between requests)

**Phase 3: Description Generation (5-10 min)**
- Generates professional descriptions
- Creates SEO meta tags
- Calculates completeness scores

### Monitor Progress

The script shows detailed progress:

```
Processing 42/150: Smith Medical Negligence Lawyers
  ✓ Inserted lawyer with ID: abc-123
```

---

## Step 6: Review Collected Data (15 minutes)

### View Summary Report

```bash
cd collected_data
cat REPORT_*.json | jq
```

**Check:**
- Total lawyers collected
- Data completeness percentages
- Feature coverage (no win no fee, free consultation)

### View Sample Profiles

```bash
# View first lawyer profile
cat 03_final_*.json | jq '.[0]'

# Count total
cat 03_final_*.json | jq 'length'
```

### Quality Check

Look for:
- ✓ Descriptions are professional and relevant
- ✓ Contact information is present
- ✓ Specializations are correct
- ✓ No duplicate entries

---

## Step 7: Import to Supabase (10 minutes)

### Run Import Script

```bash
cd ..  # Back to root directory
python import_to_supabase.py data-collection/collected_data/03_final_*.json
```

### Verify Import

1. Go to Supabase Dashboard → Table Editor
2. View `lawyers` table
3. Check a few sample records
4. Verify related tables (specializations, service_areas, etc.)

### Set Some Lawyers to Published

By default, all lawyers are `is_published=false`. You need to review and publish them:

```sql
-- In Supabase SQL Editor

-- Publish all lawyers with complete profiles
UPDATE lawyers
SET is_published = true
WHERE profile_completeness_score >= 60;

-- Or publish specific high-quality lawyers
UPDATE lawyers
SET is_published = true
WHERE firm_name IN (
  'Smith Medical Negligence Lawyers',
  'Melbourne Medical Law Group'
  -- Add more
);
```

---

## Step 8: Calculate Profile Completeness (2 minutes)

Run the helper function to score all profiles:

```sql
-- In Supabase SQL Editor
SELECT update_profile_completeness(id) FROM lawyers;
```

This gives each lawyer a completeness score (0-100) based on:
- Basic information (20 pts)
- Enhanced information (30 pts)
- Social proof (30 pts)
- Media (10 pts)
- Verification (10 pts)

---

## 🎉 You're Done!

You now have a database of medical negligence lawyers with:
- ✅ Contact information
- ✅ Professional descriptions
- ✅ Specializations
- ✅ Google ratings
- ✅ Service features
- ✅ SEO metadata

---

## Next Steps

### Immediate (This Week)

1. **Review and enhance top listings**
   - Manually verify information
   - Add missing details
   - Correct any errors

2. **Build directory interface**
   - Search and filter functionality
   - Lawyer profile pages
   - City/specialization landing pages

3. **Implement lead capture**
   - Contact forms on profiles
   - Lead routing to lawyers
   - Analytics tracking

### Short Term (This Month)

1. **Expand coverage**
   - Add more cities
   - Run collection monthly to find new lawyers

2. **Lawyer outreach**
   - Email lawyers about their listing
   - Offer free profile claims
   - Pitch premium upgrades

3. **Add verified reviews**
   - Allow lawyers to add testimonials
   - Moderate and approve
   - Link to Google reviews (with permission)

### Long Term (Next 3 Months)

1. **Launch premium tiers**
   - Featured placements
   - Enhanced profiles
   - Lead analytics

2. **SEO optimization**
   - City + specialization pages
   - Blog content
   - Lawyer Q&A sections

3. **Scale to 500+ lawyers**
   - Automated monthly collection
   - Quality monitoring
   - Data freshness checks

---

## 💡 Pro Tips

### Better Data Collection

1. **Test with small sample first**
   ```python
   # In run_data_collection.py, limit to 2 cities
   australian_cities = [
       ('Sydney', 'NSW'),
       ('Melbourne', 'VIC'),
   ]
   ```

2. **Resume failed collections**
   ```bash
   python run_data_collection.py --resume
   ```

3. **Manual enhancements**
   - For top 20 lawyers, manually verify and enhance data
   - Add case studies from public records
   - Contact lawyers for verified information

### Cost Optimization

1. **Google Places API**
   - Stay within free tier ($200/month credit)
   - Set daily quotas to avoid surprises
   - Cache results and re-use

2. **Website scraping**
   - Completely free
   - Be respectful with rate limiting
   - Some sites may block - that's OK

### Data Quality

1. **Profile completeness matters**
   - Aim for 70%+ completeness for published lawyers
   - Use scoring to identify gaps
   - Prioritize high-traffic cities

2. **Verification builds trust**
   - Mark lawyer-verified profiles
   - Update verification dates regularly
   - Show "Last verified" on profiles

3. **Keep data fresh**
   - Re-run collection monthly
   - Update changed information
   - Remove closed businesses

---

## 🐛 Troubleshooting

### "API key not valid"
- Check you've enabled Places API and Geocoding API
- Verify key is correct (no extra spaces)
- Check API key restrictions

### "No data collected"
- Verify internet connection
- Check API quotas not exceeded
- Try reducing cities to 1-2 for testing

### "Import failed"
- Ensure migration ran successfully
- Check Supabase credentials
- Verify file path is correct

### "Slow collection"
- Normal - website scraping takes time
- Can skip with `skip_websites=True` initially
- Run overnight for large collections

---

## 📊 Expected Results

After successful collection:

**Data Volume:**
- 100-300 lawyers (10 cities)
- 500+ lawyers (all major cities)

**Data Quality:**
- 80%+ with website
- 90%+ with phone
- 100% with description (generated)
- 40-50% with no win no fee
- 50-60% with free consultation

**Database Size:**
- ~500 KB per 100 lawyers
- Minimal storage impact

---

## ✅ Checklist

Before launching your directory:

- [ ] Schema migration run successfully
- [ ] Data collected from major cities
- [ ] Import completed without errors
- [ ] Profile completeness calculated
- [ ] Top listings reviewed and verified
- [ ] Some lawyers set to `is_published=true`
- [ ] Test searches work correctly
- [ ] Lead forms functional
- [ ] Analytics tracking set up

---

## 🆘 Need Help?

**Common Issues:**
- Check environment variables are set
- Verify API keys are valid
- Ensure schema migration completed
- Review error messages carefully

**Useful Commands:**

```bash
# Check environment
echo $GOOGLE_PLACES_API_KEY
echo $SUPABASE_URL

# Test API key
curl "https://maps.googleapis.com/maps/api/place/textsearch/json?query=lawyer+sydney&key=$GOOGLE_PLACES_API_KEY"

# Check Python version
python --version  # Should be 3.8+

# Verify packages
pip list | grep -E "requests|beautifulsoup4|supabase"
```

---

**Ready to start?**

```bash
cd data-collection
export GOOGLE_PLACES_API_KEY='your-key-here'
python run_data_collection.py
```

Good luck building your directory! 🚀
