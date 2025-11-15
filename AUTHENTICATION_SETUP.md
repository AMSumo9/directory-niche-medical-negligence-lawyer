# Authentication System Setup Guide

This guide explains how to set up and use the authentication system for the MNL Directory admin dashboard.

## Features Implemented

### 1. **User Authentication**
- Email/password sign-in
- OAuth sign-in (Google and GitHub) - *requires Supabase configuration*
- Persistent sessions using localStorage
- Automatic session refresh

### 2. **Protected Admin Dashboard**
- Admin page requires authentication
- Automatic redirect to sign-in if not authenticated
- Dynamic navigation (shows "Sign In" or "Sign Out" based on auth state)

### 3. **Admin Dashboard Features**
- **Real-time stats**: Total lawyers, published, featured, premium tier
- **Lawyer management table** with inline editing:
  - Toggle featured status (★)
  - Set featured priority (0-100)
  - Change subscription tier (free/basic/premium/featured)
  - Publish/unpublish listings
  - View live lawyer profiles

## Setup Instructions

### Step 1: Create Supabase Auth Users

You need to create user accounts in your Supabase project for admin access.

1. Go to your Supabase project dashboard
2. Navigate to **Authentication** → **Users**
3. Click **Add User** → **Create new user**
4. Enter email and password for your admin account
5. Click **Create user**

**Important**: Save these credentials - you'll use them to sign in to the admin dashboard.

### Step 2: Set Up Environment Variables

Create a `.env` file in the root of your project:

```bash
# Copy from .env.example
cp .env.example .env
```

Then edit `.env` and add your Supabase credentials:

```env
PUBLIC_SUPABASE_URL=https://your-project.supabase.co
PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here
```

**Where to find these values:**
1. Go to your Supabase project
2. Click **Settings** → **API**
3. Copy:
   - **Project URL** → `PUBLIC_SUPABASE_URL`
   - **anon public** key → `PUBLIC_SUPABASE_ANON_KEY`

### Step 3: Configure Admin Access

By default, all authenticated users can access the admin dashboard. To restrict access to specific admin emails:

1. Open `src/lib/auth.ts`
2. Find the `isAdmin()` function (around line 60)
3. Add your admin email(s) to the `adminEmails` array:

```typescript
const adminEmails = [
  'admin@mnldirectory.com',
  'your-email@example.com',  // Add your email here
];
```

**Note**: For production, consider using Supabase user metadata or a dedicated `admins` table.

### Step 4: (Optional) Enable OAuth Sign-In

To enable Google or GitHub sign-in:

1. Go to Supabase **Authentication** → **Providers**
2. Enable **Google** or **GitHub**
3. Follow the setup instructions for each provider:
   - **Google**: Create OAuth 2.0 credentials in Google Cloud Console
   - **GitHub**: Create OAuth App in GitHub Settings

The OAuth buttons are already implemented in the sign-in page.

## How to Use

### For Admins

1. **Sign In**:
   - Go to `/sign-in/`
   - Enter your email and password (created in Step 1)
   - Or use OAuth (if configured)

2. **Access Admin Dashboard**:
   - After signing in, you'll be redirected to `/admin/`
   - Or click "Admin" in the navigation menu

3. **Manage Lawyers**:
   - **Toggle Featured**: Click the star button to feature/unfeature a lawyer
   - **Set Priority**: Enter a number (0-100) to set featured priority (higher = shows first)
   - **Change Tier**: Select from dropdown (free/basic/premium/featured)
   - **Publish/Unpublish**: Click the status button to toggle visibility
   - **View Profile**: Click "View →" to see the live lawyer profile

4. **Sign Out**:
   - Click "Sign Out" in the navigation
   - Confirm sign-out on the next page

### For Development

**Start the development server:**
```bash
npm run dev
```

**Access pages:**
- Home: `http://localhost:4321/`
- Sign In: `http://localhost:4321/sign-in/`
- Admin: `http://localhost:4321/admin/`
- Sign Out: `http://localhost:4321/sign-out/`

## Security Notes

### Current Implementation
- ✅ Client-side authentication checks
- ✅ Session persistence
- ✅ Automatic session refresh
- ❌ Server-side route protection (Astro is static)
- ❌ Row Level Security (RLS) policies

### Recommended for Production

1. **Enable Supabase Row Level Security (RLS)**:
   - Go to Supabase **Database** → **Tables** → `lawyers`
   - Click **RLS** and enable policies
   - Example policy for admin updates:
   ```sql
   CREATE POLICY "Admin users can update lawyers"
   ON lawyers
   FOR UPDATE
   USING (auth.email() IN (
     SELECT email FROM admins
   ));
   ```

2. **Create an admins table**:
   ```sql
   CREATE TABLE admins (
     id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
     email TEXT UNIQUE NOT NULL,
     created_at TIMESTAMP DEFAULT NOW()
   );

   -- Insert your admin email
   INSERT INTO admins (email) VALUES ('your-email@example.com');
   ```

3. **Use service role key for server-side operations** (if needed)

## File Structure

```
src/
├── lib/
│   ├── auth.ts           # Authentication helper functions
│   ├── supabase.ts       # Supabase client configuration
│   └── types.ts          # TypeScript type definitions
├── pages/
│   ├── sign-in.astro     # Sign-in page
│   ├── sign-out.astro    # Sign-out confirmation page
│   └── admin.astro       # Admin dashboard
└── layouts/
    └── BaseLayout.astro  # Layout with dynamic navigation
```

## Troubleshooting

### "Missing Supabase environment variables" error
- Make sure `.env` file exists in the project root
- Verify environment variables are correct
- Restart the dev server after creating/editing `.env`

### Sign-in not working
- Check that the user exists in Supabase Authentication → Users
- Verify the email and password are correct
- Check browser console for error messages

### Admin dashboard shows "Loading..." forever
- Check browser console for errors
- Verify Supabase credentials in `.env`
- Ensure the `lawyers` table exists and is accessible

### Changes not saving in admin dashboard
- Check that your Supabase `lawyers` table allows updates
- Consider enabling RLS policies (see Security Notes)
- Check browser console for error messages

## Next Steps

Consider implementing:
- Password reset functionality
- Email verification
- User roles (admin vs lawyer vs client)
- Audit logs for admin actions
- Bulk operations in admin dashboard
- Search and filter in lawyer table
- Pagination for large datasets

## Support

For issues or questions:
1. Check browser console for errors
2. Review Supabase logs (Dashboard → Logs)
3. Verify all environment variables are set correctly
