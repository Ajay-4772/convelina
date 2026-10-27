import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const host = request.headers.get("host") || "";
  const adminDomain = process.env.NEXT_PUBLIC_ADMIN_DOMAIN || "admin.localhost:3000";
  const { pathname } = request.nextUrl;

  // Check if current host is an admin subdomain
  const isAdminHost = host === adminDomain || host.startsWith("admin.");

  if (isAdminHost) {
    // If accessing root of admin subdomain, show admin dashboard
    if (pathname === "/") {
      return NextResponse.rewrite(new URL("/admin", request.url));
    }
    // If accessing login on admin subdomain, show dedicated admin login
    if (pathname === "/login") {
      return NextResponse.rewrite(new URL("/admin/login", request.url));
    }
    // Public citizen registration routes are forbidden on admin subdomain
    if (pathname === "/signup" || pathname === "/verify-email" || pathname === "/setup-profile") {
      return NextResponse.redirect(new URL("/admin/login", request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - api routes
     */
    "/((?!_next/static|_next/image|favicon.ico|api).*)",
  ],
};
