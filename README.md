# Medical Negligence Lawyers Directory

A static directory website built with Astro, TypeScript, Tailwind CSS, and Supabase for listing medical negligence lawyers across Australia.

## Tech Stack

- **Astro** - Static Site Generator
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **Supabase** - Backend database and APIs

## Project Structure

```
├── src/
│   ├── layouts/
│   │   └── BaseLayout.astro       # Main layout template
│   ├── pages/
│   │   ├── index.astro            # Homepage
│   │   ├── [state]/
│   │   │   └── index.astro        # State listing page
│   │   └── [state]/[city]/
│   │       └── index.astro        # City listing page
│   └── lib/
│       ├── supabase.ts            # Supabase client
│       └── types.ts               # TypeScript interfaces
├── scripts/
│   └── seed.ts                    # Database seed script
└── database-schema.sql            # Supabase database schema
```

## Setup Instructions

### 1. Database Setup

1. Go to your Supabase project SQL Editor: https://supabase.com/dashboard/project/gytjxufuxjuzkrqsplrc
2. Run the SQL commands in `database-schema.sql`
3. Verify that the tables were created successfully

### 2. Seed the Database

After running the schema, populate the database with test data:

```bash
npm install
npm run seed
```

This will create sample lawyer listings across all Australian states.

### 3. Local Development

```bash
npm run dev
```

Visit http://localhost:4321 to see your site.

### 4. Build for Production

```bash
npm run build
npm run preview
```

## GitHub Pages Deployment

### Configure GitHub Secrets

Add these secrets to your GitHub repository (Settings → Secrets → Actions):

- `PUBLIC_SUPABASE_URL`: https://gytjxufuxjuzkrqsplrc.supabase.co
- `PUBLIC_SUPABASE_ANON_KEY`: Your Supabase anon key

### Enable GitHub Pages

1. Go to Settings → Pages
2. Source: GitHub Actions
3. The workflow will automatically deploy on push to `main`

## Features

- **State-by-State Navigation**: Browse lawyers by Australian state
- **City Listings**: Detailed city pages with all local lawyers
- **Tiered Listings**:
  - Featured (premium placement with yellow highlight)
  - Premium (enhanced listing with blue highlight)
  - Free (basic listing)
- **Contact Options**: Phone, email, and website links (configurable per lawyer)
- **SEO Optimized**: Proper meta tags and sitemap generation
- **Responsive Design**: Mobile-friendly layout

## Database Schema

### Lawyers Table
- `firm_name`: Law firm name
- `slug`: URL-friendly identifier
- `state` / `state_code`: Location information
- `city`: City name
- `address`, `phone`, `email`, `website`: Contact details
- `show_phone_link`, `show_email_link`, `show_website_link`: Privacy controls
- `description` / `short_description`: Firm information
- `subscription_tier`: 'free', 'basic', 'premium', or 'featured'
- `is_featured`: Featured listing flag
- `is_published`: Publication status

### Specializations Table
Pre-populated with common medical negligence types:
- Surgical Errors
- Misdiagnosis
- Birth Injuries
- Medication Errors
- Hospital Negligence
- And more...

## Customization

### Adding More Lawyers
Use the Supabase dashboard or run custom insert queries.

### Styling
Edit Tailwind classes in `.astro` files or modify `tailwind.config.mjs`.

### Content
Update page content in the respective `.astro` files.

## License

MIT
