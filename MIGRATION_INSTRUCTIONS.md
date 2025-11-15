# Database Migration Instructions

## Quick Start (2 minutes)

### Step 1: Open Supabase SQL Editor

1. Go to: https://app.supabase.com/project/gytjxufuxjuzkrqsplrc
2. Click **"SQL Editor"** in the left sidebar
3. Click **"New Query"**

### Step 2: Copy and Paste Migration SQL

1. Open the file: `supabase-schema-migration.sql`
2. Copy ALL the contents (Ctrl+A, Ctrl+C)
3. Paste into the SQL Editor
4. Click **"Run"** (or press Ctrl+Enter)

### Step 3: Verify Success

You should see:
- ✅ "Success. No rows returned"
- Or a completion message

### What This Does:

The migration adds to your database:

**New columns on lawyers table:**
- years_experience, founded_year
- languages, awards, accreditations
- Google rating & review data
- Service features (no win/no fee, free consultation, etc.)
- SEO metadata
- Profile completeness score

**New tables created:**
- `lawyer_reviews` - Client reviews
- `lawyer_team_members` - Team profiles
- `case_studies` - Success stories
- `lawyer_qualifications` - Credentials
- `lawyer_faqs` - Q&A content
- `lawyer_service_areas` - Multi-location support
- `lawyer_analytics` - Engagement tracking

**Also adds:**
- Performance indexes
- Helper functions
- Row Level Security policies
- Useful views for queries

---

## That's It!

Once you run the migration, your database is ready to receive the lawyer data.

The migration is safe to run multiple times (uses `IF NOT EXISTS` checks).

---

## Need Help?

If you see any errors, check:
- You're in the correct Supabase project
- The base `lawyers` table exists
- You have proper permissions

Most errors are harmless (like "already exists" if run twice).
