import type { NextConfig } from "next";

// Dev: /api/* đi thẳng vào FastAPI local. Production: Caddy đảm nhiệm /api,
// không hardcode URL tuyệt đối trong standalone build.
const apiUrl = process.env.API_PROXY_URL || "http://localhost:8000";

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${apiUrl}/:path*` }];
  },
};

export default nextConfig;
