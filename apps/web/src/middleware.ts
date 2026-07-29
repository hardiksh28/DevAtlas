import { NextResponse, type NextRequest } from "next/server";

const ACCESS_TOKEN_COOKIE = "access_token";
const REFRESH_TOKEN_COOKIE = "refresh_token";

// Deliberately a presence check, not a signature check: the JWT is
// signed with `api_secret_key` (apps/api/app/modules/auth/security.py),
// a symmetric key that lives only on the API. Verifying it here would
// mean shipping that same secret to the Next.js edge runtime, which
// widens the blast radius of a frontend compromise for no real benefit
// — the API re-validates the token's signature and expiry on every
// request regardless (that's the actual authorization boundary; see
// get_current_user). This middleware only exists to skip an obviously
// pointless render-then-redirect round trip for the common case of "no
// cookie at all." A present-but-expired access token still reaches the
// page; apps/web/src/app/dashboard/page.tsx's own 401 handling covers
// that case.
function hasAuthCookie(request: NextRequest): boolean {
  return (
    request.cookies.has(ACCESS_TOKEN_COOKIE) || request.cookies.has(REFRESH_TOKEN_COOKIE)
  );
}

export function middleware(request: NextRequest) {
  if (!hasAuthCookie(request)) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", request.nextUrl.pathname);
    return NextResponse.redirect(loginUrl);
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*"],
};
