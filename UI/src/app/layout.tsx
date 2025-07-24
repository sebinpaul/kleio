import type { Metadata } from "next";
import { Raleway } from "next/font/google";
import "./globals.css";

// Clerk imports
import {
  ClerkProvider,
  SignedIn,
  SignedOut,
  RedirectToSignIn,
  SignInButton,
  SignUpButton,
  UserButton,
} from "@clerk/nextjs";

const raleway = Raleway({
  variable: "--font-raleway",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "Kleio - Mention Monitoring Platform",
  description: "Track keywords across Reddit and Hacker News",
};

// Toggle authentication via env var (NEXT_PUBLIC_AUTH_ENABLED)
const authEnabled = true;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${raleway.variable} font-sans antialiased`}
      >
        {authEnabled ? (
          <ClerkProvider>
            <header className="flex justify-end items-center p-4 gap-4 h-16">
              <SignedOut>
                <SignInButton />
                <SignUpButton />
              </SignedOut>
              <SignedIn>
                <UserButton />
              </SignedIn>
            </header>
            <SignedIn>{children}</SignedIn>
            <SignedOut>
              <RedirectToSignIn />
            </SignedOut>
          </ClerkProvider>
        ) : (
          <>
            <header className="flex justify-end items-center p-4 gap-4 h-16">
              <div className="text-sm text-gray-500">
                Auth disabled for testing
              </div>
            </header>
            {children}
          </>
        )}
      </body>
    </html>
  );
}
