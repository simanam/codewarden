import { createBrowserClient } from '@supabase/ssr';

// Placeholder values for build time - will be replaced at runtime
const PLACEHOLDER_URL = 'https://placeholder.supabase.co';
const PLACEHOLDER_KEY = 'placeholder-key';

export function createClient() {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || PLACEHOLDER_URL;
  const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY || PLACEHOLDER_KEY;

  // During build/SSG, use placeholders (client won't actually be used)
  // At runtime, real values must be provided
  if (typeof window !== 'undefined' && (supabaseUrl === PLACEHOLDER_URL || supabaseKey === PLACEHOLDER_KEY)) {
    console.error(
      "Supabase URL and Key are required!\n" +
      "Check your environment variables: NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY"
    );
  }

  return createBrowserClient(supabaseUrl, supabaseKey);
}
