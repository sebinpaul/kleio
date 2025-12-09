import type { Metadata } from "next";
import { Raleway } from "next/font/google";
import "./globals.css";

// Clerk imports
import {
  ClerkProvider,
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
        <ClerkProvider>
          {children}
        </ClerkProvider>
      </body>
    </html>
  );
}
