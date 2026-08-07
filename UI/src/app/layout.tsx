import type { Metadata } from "next";
import { Inter, Raleway } from "next/font/google";
import "./globals.css";
import { ClerkProvider } from "@clerk/nextjs";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
  preload: true,
});

const raleway = Raleway({
  variable: "--font-raleway",
  subsets: ["latin"],
  display: "swap",
  preload: true,
});

export const metadata: Metadata = {
  title: {
    default: "Kleio — Social Mention Monitoring Platform",
    template: "%s | Kleio",
  },
  description:
    "Track mentions of your brand across Reddit, Hacker News, and more. Get instant email alerts with context and source links.",
  icons: { icon: "/favicon.ico" },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link rel="dns-prefetch" href="https://clerk.kleio.dev" />
        <link rel="dns-prefetch" href="https://api.clerk.dev" />
      </head>
      <body className={`${inter.variable} ${raleway.variable} font-sans antialiased`}>
        <ClerkProvider>{children}</ClerkProvider>
      </body>
    </html>
  );
}
