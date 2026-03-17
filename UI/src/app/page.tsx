import type { Metadata } from "next";
import { LandingPage } from "./_landing";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "https://kleio.dev";

export const metadata: Metadata = {
  title: "Kleio — Social Mention Monitoring for Reddit, Hacker News & More",
  description:
    "Track keywords across Reddit, Hacker News, Twitter, LinkedIn, YouTube, Facebook and Quora. Get instant email alerts when your brand, product, or competitors are mentioned. Free plan available.",
  keywords: [
    "social listening",
    "mention monitoring",
    "brand monitoring",
    "Reddit monitoring",
    "Hacker News alerts",
    "keyword tracking",
    "social media monitoring",
    "competitor tracking",
    "brand mentions",
    "email alerts",
  ],
  metadataBase: new URL(SITE_URL),
  alternates: { canonical: "/" },
  robots: { index: true, follow: true },
  openGraph: {
    type: "website",
    locale: "en_US",
    url: SITE_URL,
    siteName: "Kleio",
    title: "Kleio — Know When Your Brand Gets Mentioned",
    description:
      "Monitor Reddit, Hacker News, and 5 more platforms for keyword mentions. Instant email alerts with context and source links. Free to start.",
    images: [
      {
        url: `${SITE_URL}/og-image.png`,
        width: 1200,
        height: 630,
        alt: "Kleio — Social Mention Monitoring Platform",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Kleio — Know When Your Brand Gets Mentioned",
    description:
      "Track mentions across Reddit, Hacker News & more. Instant email alerts. Free plan available.",
    images: [`${SITE_URL}/og-image.png`],
    creator: "@kleiohq",
  },
};

function JsonLd() {
  const schema = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "SoftwareApplication",
        name: "Kleio",
        url: SITE_URL,
        applicationCategory: "BusinessApplication",
        operatingSystem: "Web",
        description:
          "Social mention monitoring platform that tracks keywords across Reddit, Hacker News, and more. Instant email alerts with context and source links.",
        offers: [
          {
            "@type": "Offer",
            name: "Starter",
            price: "0",
            priceCurrency: "USD",
            description: "5 keywords, Reddit monitoring, email alerts",
          },
          {
            "@type": "Offer",
            name: "Pro",
            price: "17",
            priceCurrency: "USD",
            billingIncrement: "P1M",
            description:
              "Unlimited keywords, Reddit + Hacker News, priority scans",
          },
          {
            "@type": "Offer",
            name: "Team",
            price: "37",
            priceCurrency: "USD",
            billingIncrement: "P1M",
            description:
              "Shared watchlists, role-based access, weekly digests",
          },
        ],
        aggregateRating: {
          "@type": "AggregateRating",
          ratingValue: "4.9",
          reviewCount: "500",
          bestRating: "5",
        },
      },
      {
        "@type": "FAQPage",
        mainEntity: [
          {
            "@type": "Question",
            name: "What platforms does Kleio currently monitor?",
            acceptedAnswer: {
              "@type": "Answer",
              text: "Kleio monitors Reddit, Hacker News, Twitter, YouTube, LinkedIn, Facebook, and Quora in real time from a single dashboard.",
            },
          },
          {
            "@type": "Question",
            name: "How quickly will I receive mention alerts?",
            acceptedAnswer: {
              "@type": "Answer",
              text: "Most mentions are detected within minutes of being posted. Pro and Team plans get priority scanning for even faster detection.",
            },
          },
          {
            "@type": "Question",
            name: "Is there a free plan available?",
            acceptedAnswer: {
              "@type": "Answer",
              text: "Yes. The Starter plan is free forever and includes 5 keywords with Reddit monitoring.",
            },
          },
        ],
      },
      {
        "@type": "Organization",
        name: "Kleio",
        url: SITE_URL,
        logo: `${SITE_URL}/logo.png`,
        contactPoint: {
          "@type": "ContactPoint",
          email: "support@kleio.dev",
          contactType: "customer support",
        },
      },
    ],
  };

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
    />
  );
}

export default function Page() {
  return (
    <>
      <JsonLd />
      <LandingPage />
    </>
  );
}
