"use client";

import { UserButton, useUser } from "@clerk/nextjs";
import Sidebar from "../../components/Sidebar";

const authEnabled = process.env.NEXT_PUBLIC_AUTH_ENABLED !== "false";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isSignedIn, user } = useUser();

  if (!authEnabled) {
    return (
      <div className="min-h-screen bg-background">
        <Sidebar />
        <div className="ml-64">
          <header className="bg-background border-b">
            <div className="px-6 py-4 flex justify-between items-center">
              <h1 className="text-2xl font-bold">Kleio Dashboard</h1>
              <div className="text-sm text-muted-foreground">
                Authentication disabled for testing
              </div>
            </div>
          </header>
          <main className="p-6">{children}</main>
        </div>
      </div>
    );
  }

  if (!isSignedIn) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">
            Please sign in to access the dashboard
          </h1>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <div className="ml-64">
        <header className="bg-background border-b">
          <div className="px-6 py-4 flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold">Kleio Dashboard</h1>
              <p className="text-sm text-muted-foreground">
                Monitor your keywords across platforms
              </p>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm text-muted-foreground">
                {user?.username || user?.primaryEmailAddress?.emailAddress}
              </span>
              <UserButton afterSignOutUrl="/" />
            </div>
          </div>
        </header>
        <main className="p-6">{children}</main>
      </div>
    </div>
  );
}
