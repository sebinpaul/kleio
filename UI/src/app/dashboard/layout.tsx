"use client";

import { useUser } from "@clerk/nextjs";
import Sidebar from "../../components/Sidebar";

const authEnabled = process.env.NEXT_PUBLIC_AUTH_ENABLED !== "false";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isSignedIn } = useUser();

  if (!authEnabled) {
    return (
      <div className="min-h-screen bg-background">
        <Sidebar />
        <div className="ml-64">
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
        <main className="p-6">{children}</main>
      </div>
    </div>
  );
}
