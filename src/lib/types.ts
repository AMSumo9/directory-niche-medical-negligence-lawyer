export interface Lawyer {
  id: string;
  firm_name: string;
  slug: string;
  state: string;
  state_code: string;
  city: string;
  address: string | null;
  phone: string | null;
  email: string | null;
  website: string | null;
  show_phone_link: boolean;
  show_email_link: boolean;
  show_website_link: boolean;
  description: string | null;
  short_description: string | null;
  subscription_tier: 'free' | 'basic' | 'premium' | 'featured';
  is_featured: boolean;
  featured_priority: number;
  is_published: boolean;
  created_at?: string;
}

export interface Specialization {
  id: string;
  name: string;
  slug: string;
}

export interface LawyerSpecialization {
  lawyer_id: string;
  specialization_id: string;
}

export interface Lead {
  id: string;
  created_at: string;
  lawyer_id: string;
  customer_name: string;
  customer_email: string;
  customer_phone: string | null;
  message: string | null;
}
