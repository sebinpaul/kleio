import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  env: {
    NEXT_PUBLIC_AUTH_ENABLED: process.env.NEXT_PUBLIC_AUTH_ENABLED || "true",
  },
};

export default nextConfig;
