import { cookies } from "next/headers";
import { createServerClient } from "@supabase/ssr";

/**
 * A Supabase client for Server Components, Server Actions and Route Handlers.
 *
 * It reads the user's session from the request cookies, so every query it
 * makes runs as that user and your RLS policies apply. Create a new one per
 * request; never share one between requests (it would leak one user's
 * session into another user's request).
 */
export async function createClient() {
  const cookieStore = await cookies();

  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll();
        },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options),
            );
          } catch {
            // Server Components can't set cookies. That's fine: proxy.ts
            // refreshes the session on every request before rendering.
          }
        },
      },
    },
  );
}
