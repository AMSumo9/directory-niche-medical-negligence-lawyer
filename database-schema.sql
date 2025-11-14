-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Lawyers table
CREATE TABLE lawyers (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  firm_name TEXT NOT NULL,
  slug TEXT UNIQUE NOT NULL,
  state TEXT NOT NULL,
  state_code TEXT NOT NULL,
  city TEXT NOT NULL,
  address TEXT,
  phone TEXT,
  email TEXT,
  website TEXT,
  show_phone_link BOOLEAN DEFAULT false,
  show_email_link BOOLEAN DEFAULT false,
  show_website_link BOOLEAN DEFAULT false,
  description TEXT,
  short_description TEXT,
  subscription_tier TEXT DEFAULT 'free',
  is_featured BOOLEAN DEFAULT false,
  featured_priority INTEGER DEFAULT 0,
  is_published BOOLEAN DEFAULT true
);

-- Specializations table
CREATE TABLE specializations (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  slug TEXT UNIQUE NOT NULL
);

-- Junction table for lawyer specializations
CREATE TABLE lawyer_specializations (
  lawyer_id UUID REFERENCES lawyers(id) ON DELETE CASCADE,
  specialization_id UUID REFERENCES specializations(id) ON DELETE CASCADE,
  PRIMARY KEY (lawyer_id, specialization_id)
);

-- Leads table
CREATE TABLE leads (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  lawyer_id UUID REFERENCES lawyers(id),
  customer_name TEXT NOT NULL,
  customer_email TEXT NOT NULL,
  customer_phone TEXT,
  message TEXT
);

-- Create indexes for better query performance
CREATE INDEX idx_lawyers_state_code ON lawyers(state_code);
CREATE INDEX idx_lawyers_city ON lawyers(city);
CREATE INDEX idx_lawyers_featured ON lawyers(is_featured, featured_priority);
CREATE INDEX idx_lawyers_published ON lawyers(is_published);

-- Insert default specializations
INSERT INTO specializations (name, slug) VALUES
  ('Surgical Errors', 'surgical-errors'),
  ('Misdiagnosis', 'misdiagnosis'),
  ('Birth Injuries', 'birth-injuries'),
  ('Medication Errors', 'medication-errors'),
  ('Hospital Negligence', 'hospital-negligence'),
  ('Anesthesia Errors', 'anesthesia-errors'),
  ('Emergency Room Errors', 'emergency-room-errors'),
  ('Nursing Home Abuse', 'nursing-home-abuse');
