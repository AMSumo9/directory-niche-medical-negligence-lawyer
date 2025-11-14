-- SUPABASE MIGRATION: Medical Negligence Lawyers Directory Schema Enhancements
-- This migration adds premium features WITHOUT settlement amounts (privacy/legal concerns)

-- ============================================================================
-- STEP 1: Add columns to existing lawyers table
-- ============================================================================

-- Firm details
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS years_experience INTEGER;
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS founded_year INTEGER;
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS languages TEXT[];
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS awards TEXT[];
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS accreditations TEXT[];
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS profile_image_url TEXT;
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS office_images_urls TEXT[];

-- Success metrics (WITHOUT monetary amounts for legal/privacy reasons)
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS total_cases_handled INTEGER;
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS success_rate DECIMAL(5,2); -- Percentage (e.g., 94.50)

-- Client experience features
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS free_consultation BOOLEAN DEFAULT false;
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS no_win_no_fee BOOLEAN DEFAULT false;
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS home_visits_available BOOLEAN DEFAULT false;
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS telehealth_available BOOLEAN DEFAULT false;
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS accepts_legal_aid BOOLEAN DEFAULT false;

-- Responsiveness indicators
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS average_response_time TEXT;
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS business_hours JSONB;

-- SEO and marketing
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS meta_title TEXT;
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS meta_description TEXT;
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS service_areas TEXT[];

-- Quality scores and verification (internal use)
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS profile_completeness_score INTEGER DEFAULT 0;
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS last_verified_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS verification_status TEXT DEFAULT 'unverified';

-- Google/external data (for reference, not display without permission)
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS google_place_id TEXT;
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS google_rating DECIMAL(2,1);
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS google_review_count INTEGER;
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS external_data JSONB; -- Store other scraped data

-- ============================================================================
-- STEP 2: Create new tables for related data
-- ============================================================================

-- Reviews (lawyer can choose to show verified reviews from any source)
CREATE TABLE IF NOT EXISTS lawyer_reviews (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  lawyer_id UUID REFERENCES lawyers(id) ON DELETE CASCADE,
  reviewer_name TEXT NOT NULL,
  reviewer_initials TEXT, -- For privacy: "J.S." instead of full name
  rating INTEGER CHECK (rating >= 1 AND rating <= 5),
  review_text TEXT,
  case_type TEXT, -- Which specialization this review relates to
  review_source TEXT, -- 'google', 'facebook', 'direct', 'other'
  source_url TEXT, -- Link to original review if from external source
  is_verified BOOLEAN DEFAULT false,
  is_published BOOLEAN DEFAULT false, -- Lawyer controls if they want this shown
  helpful_count INTEGER DEFAULT 0,
  review_date DATE -- Original review date
);

-- Team members
CREATE TABLE IF NOT EXISTS lawyer_team_members (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  lawyer_id UUID REFERENCES lawyers(id) ON DELETE CASCADE,
  full_name TEXT NOT NULL,
  role TEXT,
  specialization TEXT,
  photo_url TEXT,
  bio TEXT,
  years_experience INTEGER,
  display_order INTEGER DEFAULT 0
);

-- Case studies (WITHOUT settlement amounts)
CREATE TABLE IF NOT EXISTS case_studies (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  lawyer_id UUID REFERENCES lawyers(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  slug TEXT UNIQUE NOT NULL,
  case_type TEXT,
  year INTEGER,
  summary TEXT NOT NULL,
  outcome TEXT, -- General outcome description (e.g., "Successful settlement", "Verdict in favor of client")
  client_testimonial TEXT, -- Optional quote from client
  is_published BOOLEAN DEFAULT false
);

-- Qualifications and credentials
CREATE TABLE IF NOT EXISTS lawyer_qualifications (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  lawyer_id UUID REFERENCES lawyers(id) ON DELETE CASCADE,
  qualification_type TEXT NOT NULL, -- 'education', 'admission', 'membership', 'certification'
  institution TEXT NOT NULL,
  qualification_name TEXT NOT NULL,
  year_obtained INTEGER,
  is_verified BOOLEAN DEFAULT false
);

-- FAQ specific to each lawyer
CREATE TABLE IF NOT EXISTS lawyer_faqs (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  lawyer_id UUID REFERENCES lawyers(id) ON DELETE CASCADE,
  question TEXT NOT NULL,
  answer TEXT NOT NULL,
  display_order INTEGER DEFAULT 0
);

-- Service areas with detail (for local SEO)
CREATE TABLE IF NOT EXISTS lawyer_service_areas (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  lawyer_id UUID REFERENCES lawyers(id) ON DELETE CASCADE,
  state TEXT NOT NULL,
  state_code TEXT NOT NULL,
  city TEXT NOT NULL,
  postcode TEXT,
  is_primary_location BOOLEAN DEFAULT false
);

-- Track engagement metrics (internal analytics)
CREATE TABLE IF NOT EXISTS lawyer_analytics (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  lawyer_id UUID REFERENCES lawyers(id) ON DELETE CASCADE,
  date DATE NOT NULL DEFAULT CURRENT_DATE,
  profile_views INTEGER DEFAULT 0,
  contact_clicks INTEGER DEFAULT 0,
  website_clicks INTEGER DEFAULT 0,
  phone_clicks INTEGER DEFAULT 0,
  email_clicks INTEGER DEFAULT 0,
  UNIQUE(lawyer_id, date)
);

-- ============================================================================
-- STEP 3: Create indexes for performance
-- ============================================================================

-- Indexes for new lawyer columns
CREATE INDEX IF NOT EXISTS idx_lawyers_verification_status ON lawyers(verification_status);
CREATE INDEX IF NOT EXISTS idx_lawyers_no_win_no_fee ON lawyers(no_win_no_fee) WHERE no_win_no_fee = true;
CREATE INDEX IF NOT EXISTS idx_lawyers_free_consultation ON lawyers(free_consultation) WHERE free_consultation = true;
CREATE INDEX IF NOT EXISTS idx_lawyers_google_place_id ON lawyers(google_place_id) WHERE google_place_id IS NOT NULL;

-- Indexes for related tables
CREATE INDEX IF NOT EXISTS idx_lawyer_reviews_lawyer_id ON lawyer_reviews(lawyer_id);
CREATE INDEX IF NOT EXISTS idx_lawyer_reviews_published ON lawyer_reviews(is_published, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_lawyer_reviews_rating ON lawyer_reviews(rating);

CREATE INDEX IF NOT EXISTS idx_lawyer_team_members_lawyer_id ON lawyer_team_members(lawyer_id);
CREATE INDEX IF NOT EXISTS idx_lawyer_team_members_display_order ON lawyer_team_members(lawyer_id, display_order);

CREATE INDEX IF NOT EXISTS idx_case_studies_lawyer_id ON case_studies(lawyer_id);
CREATE INDEX IF NOT EXISTS idx_case_studies_published ON case_studies(is_published, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_case_studies_slug ON case_studies(slug);

CREATE INDEX IF NOT EXISTS idx_lawyer_qualifications_lawyer_id ON lawyer_qualifications(lawyer_id);

CREATE INDEX IF NOT EXISTS idx_lawyer_faqs_lawyer_id ON lawyer_faqs(lawyer_id);
CREATE INDEX IF NOT EXISTS idx_lawyer_faqs_display_order ON lawyer_faqs(lawyer_id, display_order);

CREATE INDEX IF NOT EXISTS idx_lawyer_service_areas_lawyer_id ON lawyer_service_areas(lawyer_id);
CREATE INDEX IF NOT EXISTS idx_lawyer_service_areas_location ON lawyer_service_areas(state_code, city);

CREATE INDEX IF NOT EXISTS idx_lawyer_analytics_lawyer_date ON lawyer_analytics(lawyer_id, date DESC);

-- ============================================================================
-- STEP 4: Create helpful views
-- ============================================================================

-- View for lawyer search with aggregated data
CREATE OR REPLACE VIEW lawyer_search_view AS
SELECT
  l.*,
  COALESCE(AVG(r.rating), 0) as average_rating,
  COUNT(DISTINCT r.id) as review_count,
  COUNT(DISTINCT cs.id) as case_study_count,
  COUNT(DISTINCT tm.id) as team_member_count,
  ARRAY_AGG(DISTINCT s.name) FILTER (WHERE s.name IS NOT NULL) as specialization_names,
  ARRAY_AGG(DISTINCT s.slug) FILTER (WHERE s.slug IS NOT NULL) as specialization_slugs
FROM lawyers l
LEFT JOIN lawyer_reviews r ON l.id = r.lawyer_id AND r.is_published = true
LEFT JOIN case_studies cs ON l.id = cs.lawyer_id AND cs.is_published = true
LEFT JOIN lawyer_team_members tm ON l.id = tm.lawyer_id
LEFT JOIN lawyer_specializations ls ON l.id = ls.lawyer_id
LEFT JOIN specializations s ON ls.specialization_id = s.id
WHERE l.is_published = true
GROUP BY l.id;

-- View for featured lawyers
CREATE OR REPLACE VIEW featured_lawyers_view AS
SELECT
  l.*,
  COALESCE(AVG(r.rating), 0) as average_rating,
  COUNT(DISTINCT r.id) as review_count
FROM lawyers l
LEFT JOIN lawyer_reviews r ON l.id = r.lawyer_id AND r.is_published = true
WHERE l.is_published = true AND l.is_featured = true
GROUP BY l.id
ORDER BY l.featured_priority DESC, average_rating DESC;

-- ============================================================================
-- STEP 5: Enable Row Level Security (RLS) for Supabase
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE lawyer_reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE lawyer_team_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE case_studies ENABLE ROW LEVEL SECURITY;
ALTER TABLE lawyer_qualifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE lawyer_faqs ENABLE ROW LEVEL SECURITY;
ALTER TABLE lawyer_service_areas ENABLE ROW LEVEL SECURITY;
ALTER TABLE lawyer_analytics ENABLE ROW LEVEL SECURITY;

-- Public read access for published content
CREATE POLICY "Public can view published reviews" ON lawyer_reviews
  FOR SELECT USING (is_published = true);

CREATE POLICY "Public can view team members" ON lawyer_team_members
  FOR SELECT USING (true);

CREATE POLICY "Public can view published case studies" ON case_studies
  FOR SELECT USING (is_published = true);

CREATE POLICY "Public can view qualifications" ON lawyer_qualifications
  FOR SELECT USING (true);

CREATE POLICY "Public can view FAQs" ON lawyer_faqs
  FOR SELECT USING (true);

CREATE POLICY "Public can view service areas" ON lawyer_service_areas
  FOR SELECT USING (true);

-- Analytics only visible to authenticated users (admin)
CREATE POLICY "Authenticated users can view analytics" ON lawyer_analytics
  FOR SELECT USING (auth.role() = 'authenticated');

-- ============================================================================
-- STEP 6: Create helper functions
-- ============================================================================

-- Function to calculate profile completeness score
CREATE OR REPLACE FUNCTION calculate_profile_completeness(lawyer_uuid UUID)
RETURNS INTEGER AS $$
DECLARE
  score INTEGER := 0;
  lawyer_record RECORD;
  spec_count INTEGER;
  team_count INTEGER;
  review_count INTEGER;
  case_count INTEGER;
BEGIN
  -- Get lawyer data
  SELECT * INTO lawyer_record FROM lawyers WHERE id = lawyer_uuid;

  IF NOT FOUND THEN
    RETURN 0;
  END IF;

  -- Base information (20 points)
  IF lawyer_record.firm_name IS NOT NULL
     AND lawyer_record.address IS NOT NULL
     AND lawyer_record.phone IS NOT NULL
     AND lawyer_record.email IS NOT NULL
     AND lawyer_record.website IS NOT NULL THEN
    score := score + 20;
  END IF;

  -- Enhanced information (30 points)
  IF lawyer_record.description IS NOT NULL AND LENGTH(lawyer_record.description) > 200 THEN
    score := score + 5;
  END IF;

  IF lawyer_record.years_experience IS NOT NULL THEN
    score := score + 5;
  END IF;

  -- Specializations
  SELECT COUNT(*) INTO spec_count FROM lawyer_specializations WHERE lawyer_id = lawyer_uuid;
  IF spec_count > 0 THEN
    score := score + 5;
  END IF;

  -- Team members
  SELECT COUNT(*) INTO team_count FROM lawyer_team_members WHERE lawyer_id = lawyer_uuid;
  IF team_count > 0 THEN
    score := score + 5;
  END IF;

  -- Service features
  IF lawyer_record.free_consultation = true OR lawyer_record.no_win_no_fee = true THEN
    score := score + 10;
  END IF;

  -- Social proof (30 points)
  SELECT COUNT(*) INTO review_count FROM lawyer_reviews
  WHERE lawyer_id = lawyer_uuid AND is_published = true;

  IF review_count >= 3 THEN
    score := score + 15;
  ELSIF review_count > 0 THEN
    score := score + 10;
  END IF;

  -- Case studies
  SELECT COUNT(*) INTO case_count FROM case_studies
  WHERE lawyer_id = lawyer_uuid AND is_published = true;

  IF case_count > 0 THEN
    score := score + 10;
  END IF;

  -- Awards/accreditations
  IF lawyer_record.awards IS NOT NULL AND array_length(lawyer_record.awards, 1) > 0 THEN
    score := score + 5;
  END IF;

  -- Media (10 points)
  IF lawyer_record.profile_image_url IS NOT NULL THEN
    score := score + 5;
  END IF;

  IF lawyer_record.office_images_urls IS NOT NULL AND array_length(lawyer_record.office_images_urls, 1) > 0 THEN
    score := score + 5;
  END IF;

  -- Verification (10 points)
  IF lawyer_record.verification_status = 'verified' THEN
    score := score + 5;
  END IF;

  IF lawyer_record.last_verified_at IS NOT NULL
     AND lawyer_record.last_verified_at > NOW() - INTERVAL '6 months' THEN
    score := score + 5;
  END IF;

  RETURN score;
END;
$$ LANGUAGE plpgsql;

-- Function to update profile completeness for a lawyer
CREATE OR REPLACE FUNCTION update_profile_completeness(lawyer_uuid UUID)
RETURNS INTEGER AS $$
DECLARE
  new_score INTEGER;
BEGIN
  new_score := calculate_profile_completeness(lawyer_uuid);

  UPDATE lawyers
  SET profile_completeness_score = new_score
  WHERE id = lawyer_uuid;

  RETURN new_score;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- To update all existing lawyers' profile completeness scores, run:
-- SELECT update_profile_completeness(id) FROM lawyers;
