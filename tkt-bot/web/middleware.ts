import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// TIP-13: gate mời mức nhẹ bằng basic auth. Chưa cấu hình env thì mở (dev/local).
// Chạy được cả sau Caddy lẫn trực tiếp trên Render web service.
export function middleware(req: NextRequest) {
  const user = process.env.STAGING_USER;
  const pass = process.env.STAGING_PASS;
  if (!user || !pass) return NextResponse.next();

  const auth = req.headers.get("authorization");
  if (auth?.startsWith("Basic ")) {
    try {
      const [u, p] = atob(auth.slice(6)).split(":");
      if (u === user && p === pass) return NextResponse.next();
    } catch {
      /* header hỏng, rơi xuống 401 */
    }
  }
  return new NextResponse("Cần đăng nhập để xem bản thử nghiệm.", {
    status: 401,
    headers: { "WWW-Authenticate": 'Basic realm="tkt-staging"' },
  });
}

// Chừa robots.txt để crawler đọc được disallow; chừa asset tĩnh.
export const config = {
  matcher: ["/((?!robots.txt|_next/static|_next/image|favicon.ico).*)"],
};
