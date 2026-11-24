import { NextResponse, type NextRequest } from "next/server";
import { createServerClient } from "@supabase/ssr";

/**
 * Runs before every page request. Two jobs:
 *
 * 1. Keep the session fresh. Supabase access tokens expire after about an hour.
 *    getClaims() refreshes an expired one, and setAll() writes the new
 *    tokens back as cookies on both the request (so the page rendering right
 *    now sees them) and the response (so the browser stores them).
 *
 * 2. Send anyone who isn't logged in to /login.
 *
 * This is the "optimistic" check: fast, and good for redirects. It is NOT the
 * security boundary. Pages still check the user themselves, and RLS in the
 * database has the final say.
 */
export async function proxy(request: NextRequest) {
  let response = NextResponse.next({ request });

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(cookiesToSet, headers) {
          cookiesToSet.forEach(({ name, value }) =>
            request.cookies.set(name, value),
          );
          response = NextResponse.next({ request });
          cookiesToSet.forEach(({ name, value, options }) =>
            response.cookies.set(name, value, options),
          );
          // Cache-Control: no-store, so a CDN never serves one user's
          // session cookie to someone else.
          Object.entries(headers).forEach(([key, value]) =>
            response.headers.set(key, value),
          );
        },
      },
    },
  );

  // Verifies the token's signature (not just "is there a cookie?"), and
  // refreshes it if it has expired.
  const { data } = await supabase.auth.getClaims();
  const isLoggedIn = Boolean(data?.claims);

  const isLoginPage = request.nextUrl.pathname.startsWith("/login");
  if (!isLoggedIn && !isLoginPage) {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    return NextResponse.redirect(url);
  }

  return response;
}

export const config = {
  matcher: [
    // Every path except Next.js internals and static files, so CSS, JS and
    // images still load on the login page.
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
