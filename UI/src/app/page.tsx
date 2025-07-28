"use client";

import Link from "next/link";
import { useUser } from "@clerk/nextjs";
import { useEffect, useState } from "react";

const authEnabled = process.env.NEXT_PUBLIC_AUTH_ENABLED !== "false";

export default function Home() {
  const { isSignedIn, user, isLoaded } = useUser();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Don't render until component is mounted to avoid hydration mismatch
  if (!mounted) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen">
        <h1 className="text-2xl font-bold mb-4">Kleio Dashboard</h1>
        <p className="text-gray-500">Loading...</p>
      </div>
    );
  }

  if (!authEnabled) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen">
        <h1 className="text-2xl font-bold mb-4">Kleio Dashboard</h1>
        <p className="mb-2">
          Authentication is <b>disabled</b> for testing.
        </p>
        <p className="text-gray-500">
          All features are accessible without login.
        </p>
        <Link href="/dashboard">
          <button className="mt-6 px-4 py-2 bg-blue-600 text-white rounded">
            Go to Dashboard
          </button>
        </Link>
      </div>
    );
  }

  // Show loading while Clerk is loading
  if (!isLoaded) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen">
        <h1 className="text-2xl font-bold mb-4">Kleio Dashboard</h1>
        <p className="text-gray-500">Loading authentication...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen">
      <h1 className="text-2xl font-bold mb-4">Kleio Dashboard</h1>
      {isSignedIn ? (
        <div className="flex flex-col items-center gap-4">
          <p className="text-gray-500">
            Welcome, {user?.username || user?.primaryEmailAddress?.emailAddress}
            !
          </p>
          <Link href="/dashboard">
            <button className="mt-6 px-4 py-2 bg-blue-600 text-white rounded">
              Go to Dashboard
            </button>
          </Link>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-4">
          <p className="text-gray-500">
            Please sign in to access the dashboard
          </p>
        </div>
      )}
    </div>
  );
}
