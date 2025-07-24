import type { Metadata } from "next";
import { Raleway } from "next/font/google";
import "./globals.css";

// Clerk imports
import {
  ClerkProvider,
  SignedIn,
  SignedOut,
  RedirectToSignIn,
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
            <SignedIn>{children}</SignedIn>
            <SignedOut>
              <RedirectToSignIn />
            </SignedOut>
          </ClerkProvider>
        ) : (
          <>
            {children}
          </>
        )}
      </body>
    </html>
  );
}
