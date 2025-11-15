import { supabase } from './supabase';
import type { User } from '@supabase/supabase-js';

export interface AuthResponse {
  user: User | null;
  error: string | null;
}

/**
 * Sign in with email and password
 */
export async function signIn(email: string, password: string): Promise<AuthResponse> {
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  });

  if (error) {
    return { user: null, error: error.message };
  }

  return { user: data.user, error: null };
}

/**
 * Sign out the current user
 */
export async function signOut(): Promise<{ error: string | null }> {
  const { error } = await supabase.auth.signOut();

  if (error) {
    return { error: error.message };
  }

  return { error: null };
}

/**
 * Get the current authenticated user
 */
export async function getCurrentUser(): Promise<User | null> {
  const { data: { user } } = await supabase.auth.getUser();
  return user;
}

/**
 * Get the current session
 */
export async function getSession() {
  const { data: { session } } = await supabase.auth.getSession();
  return session;
}

/**
 * Check if the current user is an admin
 * For now, we'll check if the user's email is in the admin list
 * In production, you'd want to use Supabase RLS policies and user metadata
 */
export async function isAdmin(): Promise<boolean> {
  const user = await getCurrentUser();

  if (!user) {
    return false;
  }

  // List of admin emails - in production, store this in Supabase user metadata or a separate admins table
  const adminEmails = [
    'admin@mnldirectory.com',
    // Add your admin email here
  ];

  return adminEmails.includes(user.email || '');
}

/**
 * Sign in with Google OAuth
 */
export async function signInWithGoogle() {
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: `${window.location.origin}/admin/`,
    }
  });

  if (error) {
    return { error: error.message };
  }

  return { error: null };
}

/**
 * Sign in with GitHub OAuth
 */
export async function signInWithGitHub() {
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: 'github',
    options: {
      redirectTo: `${window.location.origin}/admin/`,
    }
  });

  if (error) {
    return { error: error.message };
  }

  return { error: null };
}
