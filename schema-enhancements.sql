-- RECOMMENDED SCHEMA ENHANCEMENTS FOR PREMIUM MEDICAL NEGLIGENCE DIRECTORY

-- Additional columns for lawyers table to add quality differentiation
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS years_experience INTEGER;
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS founded_year INTEGER;
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS languages TEXT[]; -- Array of languages spoken
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS awards TEXT[]; -- Professional awards and recognitions
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS accreditations TEXT[]; -- Legal accreditations
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS profile_image_url TEXT;
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS office_images_urls TEXT[]; -- Multiple office photos

-- Success metrics (huge differentiator)
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS total_cases_handled INTEGER;
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS success_rate DECIMAL(5,2); -- Percentage
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS total_compensation_won BIGINT; -- In cents to avoid decimal issues
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS average_case_value BIGINT; -- In cents
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS largest_settlement BIGINT; -- In cents

-- Client experience features
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS free_consultation BOOLEAN DEFAULT false;
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS no_win_no_fee BOOLEAN DEFAULT false;
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS home_visits_available BOOLEAN DEFAULT false;
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS telehealth_available BOOLEAN DEFAULT false;
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS accepts_legal_aid BOOLEAN DEFAULT false;

-- Responsiveness indicators
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS average_response_time TEXT; -- e.g., "Within 24 hours"
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS business_hours JSONB; -- Structured hours data

-- SEO and marketing
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS meta_title TEXT;
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS meta_description TEXT;
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS service_areas TEXT[]; -- Additional cities/regions served

-- Quality scores (internal use)
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS profile_completeness_score INTEGER DEFAULT 0; -- 0-100
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS last_verified_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE lawyers ADD COLUMN IF NOT EXISTS verification_status TEXT DEFAULT 'unverified'; -- unverified, pending, verified

-- Social proof
CREATE TABLE IF NOT EXISTS lawyer_reviews (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  lawyer_id UUID REFERENCES lawyers(id) ON DELETE CASCADE,
  reviewer_name TEXT NOT NULL,
  reviewer_initials TEXT, -- For privacy: "J.S." instead of full name
  rating INTEGER CHECK (rating >= 1 AND rating <= 5),
  review_text TEXT,
  case_type TEXT, -- Which specialization this review relates to
  is_verified BOOLEAN DEFAULT false,
  is_published BOOLEAN DEFAULT false,
  helpful_count INTEGER DEFAULT 0
);

-- Lawyer team members (adds credibility)
CREATE TABLE IF NOT EXISTS lawyer_team_members (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  lawyer_id UUID REFERENCES lawyers(id) ON DELETE CASCADE,
  full_name TEXT NOT NULL,
  role TEXT, -- e.g., "Senior Partner", "Associate", "Paralegal"
  specialization TEXT,
  photo_url TEXT,
  bio TEXT,
  years_experience INTEGER,
  display_order INTEGER DEFAULT 0
);

-- Case studies / Notable cases (powerful differentiator)
CREATE TABLE IF NOT EXISTS case_studies (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  lawyer_id UUID REFERENCES lawyers(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  slug TEXT UNIQUE NOT NULL,
  case_type TEXT, -- Links to specialization
  year INTEGER,
  settlement_amount BIGINT, -- In cents, NULL if confidential
  summary TEXT NOT NULL,
  outcome TEXT,
  is_published BOOLEAN DEFAULT false
);

-- Qualifications and credentials (builds trust)
CREATE TABLE IF NOT EXISTS lawyer_qualifications (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  lawyer_id UUID REFERENCES lawyers(id) ON DELETE CASCADE,
  qualification_type TEXT NOT NULL, -- 'education', 'admission', 'membership', 'certification'
  institution TEXT NOT NULL, -- University or organization
  qualification_name TEXT NOT NULL, -- e.g., "Bachelor of Laws (LLB)"
  year_obtained INTEGER,
  is_verified BOOLEAN DEFAULT false
);

-- FAQ specific to each lawyer (improves SEO and user experience)
CREATE TABLE IF NOT EXISTS lawyer_faqs (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  lawyer_id UUID REFERENCES lawyers(id) ON DELETE CASCADE,
  question TEXT NOT NULL,
  answer TEXT NOT NULL,
  display_order INTEGER DEFAULT 0
);

-- Service areas with more detail (for local SEO)
CREATE TABLE IF NOT EXISTS lawyer_service_areas (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  lawyer_id UUID REFERENCES lawyers(id) ON DELETE CASCADE,
  state TEXT NOT NULL,
  state_code TEXT NOT NULL,
  city TEXT NOT NULL,
  postcode TEXT,
  is_primary_location BOOLEAN DEFAULT false
);

-- Track lawyer engagement metrics (for internal quality scoring)
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

-- Create indexes for new tables
CREATE INDEX idx_lawyer_reviews_lawyer_id ON lawyer_reviews(lawyer_id);
CREATE INDEX idx_lawyer_reviews_published ON lawyer_reviews(is_published, created_at);
CREATE INDEX idx_lawyer_team_members_lawyer_id ON lawyer_team_members(lawyer_id);
CREATE INDEX idx_case_studies_lawyer_id ON case_studies(lawyer_id);
CREATE INDEX idx_case_studies_published ON case_studies(is_published);
CREATE INDEX idx_lawyer_qualifications_lawyer_id ON lawyer_qualifications(lawyer_id);
CREATE INDEX idx_lawyer_service_areas_lawyer_id ON lawyer_service_areas(lawyer_id);
CREATE INDEX idx_lawyer_service_areas_location ON lawyer_service_areas(state_code, city);
CREATE INDEX idx_lawyer_analytics_lawyer_date ON lawyer_analytics(lawyer_id, date);

-- Add indexes for new lawyer columns
CREATE INDEX idx_lawyers_verification_status ON lawyers(verification_status);
CREATE INDEX idx_lawyers_no_win_no_fee ON lawyers(no_win_no_fee) WHERE no_win_no_fee = true;
CREATE INDEX idx_lawyers_free_consultation ON lawyers(free_consultation) WHERE free_consultation = true;

-- View for lawyer search with aggregated data
CREATE OR REPLACE VIEW lawyer_search_view AS
SELECT
  l.*,
  COALESCE(AVG(r.rating), 0) as average_rating,
  COUNT(DISTINCT r.id) as review_count,
  COUNT(DISTINCT cs.id) as case_study_count,
  ARRAY_AGG(DISTINCT s.name) FILTER (WHERE s.name IS NOT NULL) as specialization_names
FROM lawyers l
LEFT JOIN lawyer_reviews r ON l.id = r.lawyer_id AND r.is_published = true
LEFT JOIN case_studies cs ON l.id = cs.lawyer_id AND cs.is_published = true
LEFT JOIN lawyer_specializations ls ON l.id = ls.lawyer_id
LEFT JOIN specializations s ON ls.specialization_id = s.id
WHERE l.is_published = true
GROUP BY l.id;
