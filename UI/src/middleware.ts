import { clerkMiddleware } from "@clerk/nextjs/server";

// Protect only authenticated areas; leave landing and other public pages open.
export default clerkMiddleware();

export const config = {
  matcher: [
    "/dashboard(.*)",
  ],
};
