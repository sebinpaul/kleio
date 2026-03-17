"use client";

import { useState, useEffect, type ReactNode } from "react";
import Link from "next/link";
import { AnimatePresence, motion } from "motion/react";
import {
  ArrowRight,
  Bell,
  Check,
  ChevronDown,
  Menu,
  X,
  Zap,
  Globe,
  Mail,
  Shield,
  Target,
  TrendingUp,
  Search,
  Activity,
  Star,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { ShimmerButton } from "@/components/ui/shimmer-button";
import { ShineBorder } from "@/components/ui/shine-border";
import { StripedPattern } from "@/components/magicui/striped-pattern";
import { AuroraText } from "@/components/ui/aurora-text";
import { Highlighter } from "@/components/ui/highlighter";
import {
  ScrollVelocityContainer,
  ScrollVelocityRow,
} from "@/components/ui/scroll-based-velocity";
import { useReveal } from "@/lib/use-reveal";

function Reveal({
  children,
  delay = 0,
  className = "",
  as: Tag = "div",
}: {
  children: ReactNode;
  delay?: number;
  className?: string;
  as?: "div" | "section" | "h1" | "p";
}) {
  const ref = useReveal<HTMLDivElement>(delay);
  return (
    <Tag ref={ref as React.RefObject<never>} className={`reveal ${className}`}>
      {children}
    </Tag>
  );
}

/* ─── Data ─────────────────────────────────────────────────────────────── */

const navLinks = [
  { label: "Features", href: "#features" },
  { label: "How it Works", href: "#how-it-works" },
  { label: "Pricing", href: "#pricing" },
  { label: "FAQ", href: "#faq" },
];

const features = [
  {
    icon: Zap,
    title: "Lightning-Fast Detection",
    description:
      "Mentions detected within minutes of posting. Never miss a conversation about your brand.",
    iconBg: "bg-indigo-50",
    iconColor: "text-indigo-600",
    shine: ["#4f46e5", "#818cf8"] as [string, string],
  },
  {
    icon: Globe,
    title: "Multi-Platform Coverage",
    description:
      "Reddit, Hacker News, Twitter, YouTube, LinkedIn, Facebook, and Quora. One dashboard for everything.",
    iconBg: "bg-rose-50",
    iconColor: "text-rose-600",
    shine: ["#e11d48", "#fb7185"] as [string, string],
  },
  {
    icon: Mail,
    title: "Smart Email Alerts",
    description:
      "Rich notifications with context and direct links. Know exactly what was said and where.",
    iconBg: "bg-amber-50",
    iconColor: "text-amber-600",
    shine: ["#d97706", "#fbbf24"] as [string, string],
  },
  {
    icon: Shield,
    title: "Noise Reduction",
    description:
      "Smart deduplication filters out repeated matches and bot content. Signal, not spam.",
    iconBg: "bg-emerald-50",
    iconColor: "text-emerald-600",
    shine: ["#059669", "#34d399"] as [string, string],
  },
  {
    icon: Target,
    title: "Keyword Intelligence",
    description:
      "Track unlimited keywords across platforms. Monitor brands, competitors, and industry terms.",
    iconBg: "bg-violet-50",
    iconColor: "text-violet-600",
    shine: ["#7c3aed", "#a78bfa"] as [string, string],
  },
  {
    icon: TrendingUp,
    title: "Growth Insights",
    description:
      "Track trending mentions and sentiment over time to inform your strategy.",
    iconBg: "bg-cyan-50",
    iconColor: "text-cyan-600",
    shine: ["#0891b2", "#22d3ee"] as [string, string],
  },
];

const steps = [
  {
    number: "01",
    title: "Add Your Keywords",
    description:
      "Enter brand names, product terms, or competitor keywords you want to track.",
    icon: Search,
    iconBg: "bg-violet-50",
    iconColor: "text-violet-600",
    numberBg: "bg-violet-600",
  },
  {
    number: "02",
    title: "We Monitor 24/7",
    description:
      "Kleio continuously scans Reddit, Hacker News, Twitter, YouTube, LinkedIn, Facebook, and Quora for your keywords.",
    icon: Activity,
    iconBg: "bg-amber-50",
    iconColor: "text-amber-600",
    numberBg: "bg-amber-600",
  },
  {
    number: "03",
    title: "Get Instant Alerts",
    description:
      "Receive email notifications the moment a mention is detected, with direct source links.",
    icon: Bell,
    iconBg: "bg-emerald-50",
    iconColor: "text-emerald-600",
    numberBg: "bg-emerald-600",
  },
];

const testimonials = [
  {
    name: "Sarah Chen",
    handle: "sarah_devtools",
    content:
      "Kleio helped us discover our product was being discussed on HN before we even launched. We joined the conversation and got 200+ signups that day.",
    highlight: "conversation",
    initials: "SC",
    quoteColor: "text-indigo-400",
    highlightColor: "decoration-indigo-400",
    avatarBg: "bg-indigo-100",
    avatarText: "text-indigo-600",
  },
  {
    name: "Marcus Rivera",
    handle: "marcus_growth",
    content:
      "We replaced three different tools with Kleio. The deduplication alone saves us hours every week. It's like having a social media analyst that never sleeps.",
    highlight: "deduplication",
    initials: "MR",
    quoteColor: "text-rose-400",
    highlightColor: "decoration-rose-400",
    avatarBg: "bg-rose-100",
    avatarText: "text-rose-600",
  },
  {
    name: "Aisha Patel",
    handle: "aisha_cloudsync",
    content:
      "The speed of detection is incredible. We caught a competitor mention within minutes and responded with our own solution. Game changer.",
    highlight: "detection",
    initials: "AP",
    quoteColor: "text-amber-400",
    highlightColor: "decoration-amber-400",
    avatarBg: "bg-amber-100",
    avatarText: "text-amber-600",
  },
  {
    name: "James Okoro",
    handle: "james_devrel",
    content:
      "As a DevRel, knowing when our SDK gets mentioned on Reddit is priceless. Kleio's alerts are fast, accurate, and incredibly relevant to our workflow.",
    highlight: "relevant",
    initials: "JO",
    quoteColor: "text-emerald-400",
    highlightColor: "decoration-emerald-400",
    avatarBg: "bg-emerald-100",
    avatarText: "text-emerald-600",
  },
  {
    name: "Priya Sharma",
    handle: "priya_saas",
    content:
      "We track competitor keywords alongside our own brand. The insights we get from Kleio have directly shaped our positioning and messaging strategy.",
    highlight: "positioning",
    initials: "PS",
    quoteColor: "text-violet-400",
    highlightColor: "decoration-violet-400",
    avatarBg: "bg-violet-100",
    avatarText: "text-violet-600",
  },
  {
    name: "Daniel Nguyen",
    handle: "dan_startups",
    content:
      "Setup took two minutes. Within an hour we had our first alert. The signal-to-noise ratio is excellent — no spam, just meaningful mentions.",
    highlight: "meaningful",
    initials: "DN",
    quoteColor: "text-cyan-400",
    highlightColor: "decoration-cyan-400",
    avatarBg: "bg-cyan-100",
    avatarText: "text-cyan-600",
  },
];

const pricingPlans = [
  {
    name: "Starter",
    price: "$0",
    period: "forever",
    description: "For indie hackers exploring social listening.",
    cta: "Start Free",
    featured: false,
    features: [
      "5 keywords",
      "Reddit monitoring",
      "Email alerts",
      "7-day mention history",
      "Basic deduplication",
    ],
  },
  {
    name: "Pro",
    price: "$17",
    period: "per month",
    description: "For founders and growth teams who need full coverage.",
    cta: "Get Pro",
    featured: true,
    features: [
      "Unlimited keywords",
      "Reddit + Hacker News",
      "Priority scan frequency",
      "90-day mention history",
      "Advanced deduplication",
      "Keyword analytics",
    ],
  },
  {
    name: "Team",
    price: "$37",
    period: "per month",
    description: "For teams managing multiple brands and products.",
    cta: "Contact Sales",
    featured: false,
    features: [
      "Everything in Pro",
      "Shared watchlists",
      "Role-based access",
      "Team notifications",
      "Weekly digest reports",
      "Priority support",
    ],
  },
];

const faqs = [
  {
    q: "What platforms does Kleio currently monitor?",
    a: "Kleio monitors Reddit, Hacker News, Twitter, YouTube, LinkedIn, Facebook, and Quora in real time from a single dashboard.",
  },
  {
    q: "How quickly will I receive mention alerts?",
    a: "Most mentions are detected within minutes of being posted. Pro and Team plans get priority scanning for even faster detection.",
  },
  {
    q: "Can I track competitor keywords alongside my own brand?",
    a: "Absolutely. You can create separate keyword groups for your brand, competitors, and industry terms. Track them all from a single dashboard.",
  },
  {
    q: "How does deduplication work?",
    a: "Kleio's deduplication engine filters out repeated matches, cross-posts, and bot content so you only receive meaningful, unique mentions.",
  },
  {
    q: "Is there a free plan available?",
    a: "Yes. Our Starter plan is free forever and includes 5 keywords with Reddit monitoring.",
  },
];

const footerLinks: Record<string, string[]> = {
  Product: ["Features", "Pricing", "Changelog", "Roadmap"],
  Resources: ["Documentation", "Blog", "API Reference", "Status"],
  Company: ["About", "Contact", "Privacy", "Terms"],
};

/* ─── Components ───────────────────────────────────────────────────────── */

function NavBar() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const authEnabled = process.env.NEXT_PUBLIC_AUTH_ENABLED !== "false";
  const signInHref = authEnabled ? "/sign-in" : "/dashboard";

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 10);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <nav
      className={`fixed inset-x-0 top-0 z-50 transition-all duration-300 ${
        scrolled
          ? "bg-white/80 backdrop-blur-xl border-b border-slate-200/60 shadow-sm"
          : "bg-transparent"
      }`}
    >
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="flex items-center justify-between h-16">
          <Link href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center">
              <Bell className="w-4 h-4 text-white" />
            </div>
            <span className="text-lg font-bold text-slate-900 tracking-tight">
              Kleio
            </span>
          </Link>

          <div className="hidden md:flex items-center gap-8">
            {navLinks.map((link) => (
              <a
                key={link.label}
                href={link.href}
                className="text-sm text-slate-500 hover:text-slate-900 transition-colors"
              >
                {link.label}
              </a>
            ))}
          </div>

          <div className="hidden md:flex items-center gap-3">
            <Link href={signInHref}>
              <Button
                variant="ghost"
                className="text-sm text-slate-600 hover:text-slate-900"
              >
                Log in
              </Button>
            </Link>
            <Link href="/sign-up">
              <ShimmerButton
                background="rgba(79, 70, 229, 1)"
                borderRadius="0.75rem"
                className="h-8 px-3 text-xs"
               shimmerColor='rgb(14, 196, 203)'
                shimmerSize="0.1em"
              >
                Get Started
              </ShimmerButton>
            </Link>
          </div>

          <button
            className="md:hidden text-slate-600"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label="Toggle menu"
          >
            {mobileOpen ? (
              <X className="w-5 h-5" />
            ) : (
              <Menu className="w-5 h-5" />
            )}
          </button>
        </div>
      </div>

      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="md:hidden overflow-hidden bg-white border-b border-slate-200"
          >
            <div className="px-4 py-4 space-y-1">
              {navLinks.map((link) => (
                <a
                  key={link.label}
                  href={link.href}
                  className="block py-2 px-3 text-sm text-slate-600 hover:text-slate-900 rounded-lg hover:bg-slate-50"
                  onClick={() => setMobileOpen(false)}
                >
                  {link.label}
                </a>
              ))}
              <div className="pt-3 flex gap-2">
                <Link href={signInHref} className="flex-1">
                  <Button variant="ghost" className="w-full text-sm">
                    Log in
                  </Button>
                </Link>
                <Link href="/sign-up" className="flex-1">
                  <ShimmerButton
                    background="rgba(79, 70, 229, 1)"
                    borderRadius="0.75rem"
                    className="w-full h-8 px-3 text-xs"
                  >
                    Get Started
                  </ShimmerButton>
                </Link>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
}

function Hero() {
  return (
    <section className="relative pt-28 pb-20 sm:pt-36 sm:pb-28 overflow-hidden">
      <div className="absolute inset-0">
        <StripedPattern
          className="text-indigo-600/[0.07] [mask-image:radial-gradient(ellipse_at_center,black_30%,transparent_70%)]"
        />
      </div>
      <div className="max-w-6xl mx-auto px-4 sm:px-6 relative z-10">
        <div className="max-w-3xl mx-auto text-center">
          <div className="hero-enter hero-enter-1">
            <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3.5 py-1.5 mb-6 shadow-sm">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-xs text-slate-600 font-medium">
                Monitoring 7 platforms in real time
              </span>
            </div>
          </div>

          <div className="hero-enter hero-enter-2 text-4xl sm:text-5xl lg:text-6xl font-extrabold text-slate-900 tracking-tight leading-[1.1]">
            Know when{" "}
            <Highlighter
              action="highlight"
              color="#FF9800"
              strokeWidth={3}
              delay={700}
            >
              your brand
            </Highlighter>{" "}
            <AuroraText colors={["#4f46e5", "#7c3aed", "#06b6d4", "#8b5cf6"]}>
              gets mentioned.
            </AuroraText>
          </div>

          <div className="hero-enter hero-enter-3 mt-6 text-lg text-slate-500 max-w-xl mx-auto leading-relaxed">
            Kleio monitors Reddit and Hacker News for your keywords and sends
            you instant email alerts. Stop guessing. Start listening.
          </div>

          <div className="hero-enter hero-enter-4 mt-8 flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link href="/sign-up">
              <ShimmerButton
                background="rgba(79, 70, 229, 1)"
                borderRadius="0.75rem"
                className="h-12 px-8 font-semibold"
                shimmerColor='rgb(14, 196, 203)'
                shimmerSize="0.2em"
              >
                Start Monitoring Free
                <ArrowRight className="w-4 h-4 ml-1.5" />
              </ShimmerButton>
            </Link>
            <a href="#how-it-works">
              <Button variant="outline" size="lg" className="h-12 font-semibold rounded-xl">
                See How It Works
              </Button>
            </a>
          </div>

          <div className="hero-enter hero-enter-5 mt-12 flex items-center justify-center gap-6">
            <div className="flex -space-x-2">
              {["#4f46e5", "#059669", "#d946ef", "#0ea5e9", "#f59e0b"].map(
                (color, i) => (
                  <div
                    key={i}
                    className="w-8 h-8 rounded-full border-2 border-white flex items-center justify-center text-[9px] font-bold text-white shadow-sm"
                    style={{ background: color }}
                  >
                    {["SC", "MR", "AP", "JK", "LD"][i]}
                  </div>
                ),
              )}
            </div>
            <div className="text-left">
              <div className="flex items-center gap-0.5" aria-label="5 out of 5 stars" role="img">
                {[...Array(5)].map((_, i) => (
                  <Star
                    key={i}
                    aria-hidden="true"
                    className="w-3.5 h-3.5 fill-amber-400 text-amber-400"
                  />
                ))}
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Loved by 500+ product teams
              </p>
            </div>
          </div>
        </div>

        {/* Dashboard Preview */}
        <Reveal delay={200} className="mt-16 max-w-4xl mx-auto">
          <div className="relative rounded-2xl border border-slate-200 bg-white shadow-2xl shadow-slate-200/50 overflow-hidden">
            <ShineBorder
              shineColor={["#4f46e5", "#06b6d4", "#8b5cf6"]}
              borderWidth={1}
              duration={10}
            />
            <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-100 bg-slate-50/80">
              <div className="flex gap-1.5">
                <div className="w-3 h-3 rounded-full bg-red-300" />
                <div className="w-3 h-3 rounded-full bg-amber-300" />
                <div className="w-3 h-3 rounded-full bg-emerald-300" />
              </div>
              <div className="ml-3 flex-1 h-7 rounded-md bg-white border border-slate-100 max-w-sm flex items-center px-3">
                <span className="text-[11px] text-slate-500">
                  app.kleio.dev/dashboard
                </span>
              </div>
            </div>

            <div className="p-5 sm:p-6">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
                {[
                  {
                    label: "Active Keywords",
                    value: "24",
                    color: "text-indigo-600",
                  },
                  {
                    label: "Mentions Today",
                    value: "47",
                    color: "text-emerald-600",
                  },
                  {
                    label: "Alerts Sent",
                    value: "12",
                    color: "text-violet-600",
                  },
                  {
                    label: "Avg Response",
                    value: "4m",
                    color: "text-sky-600",
                  },
                ].map((stat) => (
                  <div
                    key={stat.label}
                    className="rounded-xl border border-slate-100 bg-slate-50/50 p-3"
                  >
                    <p className="text-[10px] text-slate-500 font-medium">
                      {stat.label}
                    </p>
                    <p className={`text-xl font-bold ${stat.color} mt-0.5`}>
                      {stat.value}
                    </p>
                  </div>
                ))}
              </div>

              <div className="space-y-2">
                {[
                  {
                    platform: "Reddit",
                    sub: "r/reactjs",
                    title:
                      "What tools do you use for monitoring brand mentions?",
                    time: "3m ago",
                    color: "#ff4500",
                  },
                  {
                    platform: "HN",
                    sub: "Show HN",
                    title:
                      "We built an open-source social listening platform",
                    time: "8m ago",
                    color: "#ff6600",
                  },
                  {
                    platform: "Reddit",
                    sub: "r/SaaS",
                    title: "Best way to track competitor mentions in 2026?",
                    time: "15m ago",
                    color: "#ff4500",
                  },
                ].map((m, i) => (
                  <div
                    key={i}
                    className="flex items-center gap-3 rounded-lg border border-slate-100 px-4 py-2.5"
                  >
                    <div
                      className="w-6 h-6 rounded-md flex items-center justify-center text-[9px] font-bold shrink-0"
                      style={{
                        backgroundColor: `${m.color}12`,
                        color: m.color,
                      }}
                    >
                      {m.platform === "Reddit" ? "R" : "H"}
                    </div>
                    <span
                      className="text-[11px] font-medium shrink-0"
                      style={{ color: m.color }}
                    >
                      {m.sub}
                    </span>
                    <span className="text-xs text-slate-600 flex-1 truncate">
                      {m.title}
                    </span>
                    <span className="text-[10px] text-slate-500 shrink-0">
                      {m.time}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}

const PlatformIcon = {
  Reddit: ({ className }: { className?: string }) => (
    <svg className={className} fill="currentColor" viewBox="0 0 24 24">
      <path d="M12 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0zm5.01 4.744c.688 0 1.25.561 1.25 1.249a1.25 1.25 0 0 1-2.498.056l-2.597-.547-.8 3.747c1.824.07 3.48.632 4.674 1.488.308-.309.73-.491 1.207-.491.968 0 1.754.786 1.754 1.754 0 .716-.435 1.333-1.01 1.614a3.111 3.111 0 0 1 .042.52c0 2.694-3.13 4.87-7.004 4.87-3.874 0-7.004-2.176-7.004-4.87 0-.183.015-.366.043-.534A1.748 1.748 0 0 1 4.028 12c0-.968.786-1.754 1.754-1.754.463 0 .898.196 1.207.49 1.207-.883 2.878-1.43 4.744-1.487l.885-4.182a.342.342 0 0 1 .14-.197.35.35 0 0 1 .238-.042l2.906.617a1.214 1.214 0 0 1 1.108-.701zM9.25 12C8.561 12 8 12.562 8 13.25c0 .687.561 1.248 1.25 1.248.687 0 1.248-.561 1.248-1.249 0-.688-.561-1.249-1.249-1.249zm5.5 0c-.687 0-1.248.561-1.248 1.25 0 .687.561 1.248 1.249 1.248.688 0 1.249-.561 1.249-1.249 0-.687-.562-1.249-1.25-1.249zm-5.466 3.99a.327.327 0 0 0-.231.094.33.33 0 0 0 0 .463c.842.842 2.484.913 2.961.913.477 0 2.105-.056 2.961-.913a.361.361 0 0 0 .029-.463.33.33 0 0 0-.464 0c-.547.533-1.684.73-2.512.73-.828 0-1.979-.196-2.512-.73a.326.326 0 0 0-.232-.095z" />
    </svg>
  ),
  HackerNews: ({ className }: { className?: string }) => (
    <svg className={className} fill="currentColor" viewBox="0 0 24 24">
      <path d="M0 24V0h24v24H0zM6.951 5.896l4.112 15.173L19.088 5.896h-2.288l-2.219 8.2-4.036-8.2h-2.288z" />
    </svg>
  ),
  Twitter: ({ className }: { className?: string }) => (
    <svg className={className} fill="currentColor" viewBox="0 0 24 24">
      <path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z" />
    </svg>
  ),
  YouTube: ({ className }: { className?: string }) => (
    <svg className={className} fill="currentColor" viewBox="0 0 24 24">
      <path d="M23.498 6.186a2.995 2.995 0 00-2.109-2.12C19.483 3.5 12 3.5 12 3.5s-7.483 0-9.389.566A2.995 2.995 0 00.502 6.186 31.54 31.54 0 000 12a31.54 31.54 0 00.502 5.814 2.995 2.995 0 002.109 2.12C4.517 20.5 12 20.5 12 20.5s7.483 0 9.389-.566a2.995 2.995 0 002.109-2.12A31.54 31.54 0 0024 12a31.54 31.54 0 00-.502-5.814zM9.75 15.5v-7l6 3.5-6 3.5z" />
    </svg>
  ),
  LinkedIn: ({ className }: { className?: string }) => (
    <svg className={className} fill="currentColor" viewBox="0 0 24 24">
      <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
    </svg>
  ),
  Facebook: ({ className }: { className?: string }) => (
    <svg className={className} fill="currentColor" viewBox="0 0 24 24">
      <path d="M22.675 0h-21.35C.595 0 0 .594 0 1.326v21.348C0 23.406.595 24 1.326 24H12.82v-9.294H9.692V11.08h3.128V8.413c0-3.1 1.893-4.788 4.659-4.788 1.325 0 2.463.099 2.794.143v3.24l-1.918.001c-1.504 0-1.795.715-1.795 1.763v2.314h3.587l-.467 3.626h-3.12V24h6.116C23.406 24 24 23.406 24 22.674V1.326C24 .594 23.406 0 22.675 0z" />
    </svg>
  ),
  Quora: ({ className }: { className?: string }) => (
    <svg className={className} fill="currentColor" viewBox="0 0 24 24">
      <path d="M12 0C5.373 0 0 4.82 0 10.77 0 16.722 5.373 21.54 12 21.54c1.52 0 2.974-.243 4.313-.69l2.92 2.85c.208.205.548.06.548-.23v-4.87c2.961-1.957 4.219-4.778 4.219-7.83C24 4.82 18.627 0 12 0zm1.5 18.27c-3.584 0-6.49-2.87-6.49-6.407 0-3.538 2.906-6.406 6.49-6.406 3.583 0 6.49 2.868 6.49 6.406 0 3.537-2.907 6.407-6.49 6.407z" />
    </svg>
  ),
};

const platformItems = [
  { name: "Reddit", icon: PlatformIcon.Reddit, color: "text-[#FF4500]" },
  { name: "Hacker News", icon: PlatformIcon.HackerNews, color: "text-[#FF6600]" },
  { name: "Twitter", icon: PlatformIcon.Twitter, color: "text-[#1DA1F2]" },
  { name: "YouTube", icon: PlatformIcon.YouTube, color: "text-[#FF0000]" },
  { name: "LinkedIn", icon: PlatformIcon.LinkedIn, color: "text-[#0A66C2]" },
  { name: "Facebook", icon: PlatformIcon.Facebook, color: "text-[#1877F2]" },
  { name: "Quora", icon: PlatformIcon.Quora, color: "text-[#B92B27]" },
];

function PlatformStrip() {
  return (
    <section className="py-10 border-y border-slate-100 overflow-hidden">
      <p className="text-center text-xs text-slate-500 mb-6 uppercase tracking-widest font-medium">
        Platforms we monitor
      </p>
      <div className="relative max-w-6xl mx-auto px-4 sm:px-6">
        <div className="overflow-hidden py-2">
          <ScrollVelocityContainer>
            <ScrollVelocityRow baseVelocity={5} direction={1}>
              {platformItems.map((p) => {
                const Icon = p.icon;
                return (
                  <div
                    key={p.name}
                    className="flex items-center gap-2.5 mx-3 px-5 py-2.5 rounded-lg border border-slate-200 bg-white whitespace-nowrap"
                  >
                    <Icon className={`w-4 h-4 ${p.color}`} />
                    <span className="text-sm font-medium text-slate-700">{p.name}</span>
                  </div>
                );
              })}
            </ScrollVelocityRow>
          </ScrollVelocityContainer>
        </div>
        <div className="pointer-events-none absolute inset-y-0 left-0 w-20 bg-gradient-to-r from-white to-transparent z-10" />
        <div className="pointer-events-none absolute inset-y-0 right-0 w-20 bg-gradient-to-l from-white to-transparent z-10" />
      </div>
    </section>
  );
}

function FeaturesSection() {
  return (
    <section id="features" className="py-24">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <Reveal className="text-center mb-14">
          <p className="text-sm font-semibold text-indigo-600 mb-2">
            Features
          </p>
          <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 tracking-tight">
            Everything you need to{" "}
            <Highlighter action="highlight" color="#FF9800" strokeWidth={3} delay={600}>
              listen smarter
            </Highlighter>
          </h2>
          <p className="mt-4 text-slate-500 max-w-xl mx-auto">
            From instant detection to intelligent filtering, Kleio gives you the
            tools to stay ahead of every conversation.
          </p>
        </Reveal>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {features.map((feature, i) => (
            <Reveal key={feature.title} delay={i * 60}>
              <div className="group relative h-full rounded-3xl bg-slate-50 p-8 overflow-hidden hover:shadow-lg hover:shadow-slate-200/60 transition-all duration-300">
                <ShineBorder
                  shineColor={feature.shine}
                  borderWidth={1}
                  duration={14 + i * 2}
                />
                <div className={`w-11 h-11 rounded-xl ${feature.iconBg} flex items-center justify-center mb-5`}>
                  <feature.icon className={`w-5 h-5 ${feature.iconColor}`} />
                </div>
                <h3 className="text-lg font-bold text-slate-900 mb-2">
                  {feature.title}
                </h3>
                <p className="text-sm text-slate-500 leading-relaxed">
                  {feature.description}
                </p>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

function HowItWorksSection() {
  return (
    <section id="how-it-works" className="py-24">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <Reveal className="text-center mb-16">
          <p className="text-sm font-semibold text-indigo-600 mb-2">
            How It Works
          </p>
          <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 tracking-tight">
            Three steps.{" "}
            <Highlighter action="highlight" color="#FF9800" strokeWidth={3} delay={600}>
              Full coverage.
            </Highlighter>
          </h2>
          <p className="mt-4 text-slate-500 max-w-lg mx-auto">
            Get started in under two minutes. No complex setup, no credit card
            required.
          </p>
        </Reveal>

        <div className="grid md:grid-cols-3 gap-8 relative">
          <div className="hidden md:block absolute top-7 left-[20%] right-[20%] h-px bg-slate-200" />

          {steps.map((step, i) => (
            <Reveal key={step.number} delay={i * 120} className="text-center relative">
              <div className={`relative inline-flex items-center justify-center w-14 h-14 rounded-2xl ${step.iconBg} mb-5`}>
                <step.icon className={`w-6 h-6 ${step.iconColor}`} />
                <div className={`absolute -top-2 -right-2 w-6 h-6 rounded-full ${step.numberBg} flex items-center justify-center`}>
                  <span className="text-[10px] font-bold text-white">
                    {step.number}
                  </span>
                </div>
              </div>
              <h3 className="text-lg font-semibold text-slate-900 mb-2">
                {step.title}
              </h3>
              <p className="text-sm text-slate-500 leading-relaxed max-w-xs mx-auto">
                {step.description}
              </p>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

function TestimonialsSection() {
  const renderContent = (content: string, highlight: string, highlightColor: string) => {
    const idx = content.indexOf(highlight);
    if (idx === -1) return content;
    return (
      <>
        {content.slice(0, idx)}
        <span className={`font-semibold underline decoration-2 underline-offset-2 ${highlightColor} text-slate-900`}>
          {highlight}
        </span>
        {content.slice(idx + highlight.length)}
      </>
    );
  };

  return (
    <section className="py-24 bg-slate-50/50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <Reveal className="text-center mb-16">
          <p className="text-sm font-semibold text-indigo-600 mb-2">
            Testimonials
          </p>
          <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 tracking-tight">
            Teams that{" "}
            <Highlighter action="highlight" color="#FF9800" strokeWidth={3} delay={600}>
              ship faster
            </Highlighter>{" "}
            with Kleio
          </h2>
        </Reveal>

        <div className="grid md:grid-cols-3 gap-5">
          {testimonials.map((t, i) => (
            <Reveal key={t.name} delay={i * 80}>
              <div className="h-full rounded-2xl border border-slate-200/80 bg-white p-6 flex flex-col hover:shadow-md hover:border-slate-300/80 transition-all duration-300">
                <svg
                  aria-hidden="true"
                  width="32"
                  height="24"
                  viewBox="0 0 32 24"
                  fill="currentColor"
                  className={`${t.quoteColor} mb-4 shrink-0`}
                >
                  <path d="M0 24V14.4C0 11.7 0.5 9.3 1.5 7.2C2.5 5.1 4.2 3.1 6.6 1.2L10.2 4.2C8.6 5.6 7.4 7 6.6 8.4C5.8 9.8 5.4 11.4 5.4 13.2H9.6V24H0ZM17.6 24V14.4C17.6 11.7 18.1 9.3 19.1 7.2C20.1 5.1 21.8 3.1 24.2 1.2L27.8 4.2C26.2 5.6 25 7 24.2 8.4C23.4 9.8 23 11.4 23 13.2H27.2V24H17.6Z" />
                </svg>

                <p className="text-sm text-slate-600 leading-relaxed flex-1 mb-6">
                  {renderContent(t.content, t.highlight, t.highlightColor)}
                </p>

                <div className="flex items-center gap-3">
                  <div className={`w-9 h-9 rounded-full ${t.avatarBg} flex items-center justify-center text-xs font-bold ${t.avatarText}`}>
                    {t.initials}
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-900">{t.name}</p>
                    <p className="text-xs text-slate-500">{t.handle}</p>
                  </div>
                </div>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

function PricingSection() {
  return (
    <section id="pricing" className="py-24">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <Reveal className="text-center mb-16">
          <p className="text-sm font-semibold text-indigo-600 mb-2">Pricing</p>
          <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 tracking-tight">
            Simple,{" "}
            <Highlighter action="highlight" color="#FF9800" strokeWidth={3} delay={600}>
              transparent pricing
            </Highlighter>
          </h2>
          <p className="mt-4 text-slate-500 max-w-lg mx-auto">
            Start free. Upgrade when you need more keywords, platforms, and
            features.
          </p>
        </Reveal>

        <div className="grid lg:grid-cols-3 gap-6 max-w-5xl mx-auto">
          {pricingPlans.map((plan, i) => (
            <Reveal key={plan.name} delay={i * 100}>
              <div
                className={`relative h-full rounded-2xl border p-6 flex flex-col ${
                  plan.featured
                    ? "border-indigo-200 bg-indigo-50/30 shadow-lg shadow-indigo-100/50 ring-1 ring-indigo-100"
                    : "border-slate-200 bg-white"
                }`}
              >
                {plan.featured && (
                  <>
                    <ShineBorder
                      shineColor={["#4f46e5", "#06b6d4"]}
                      borderWidth={1}
                      duration={8}
                    />
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                      <span className="px-3 py-1 rounded-full bg-indigo-600 text-white text-[10px] font-semibold shadow-sm">
                        Most Popular
                      </span>
                    </div>
                  </>
                )}

                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-slate-900">
                    {plan.name}
                  </h3>
                  <p className="text-sm text-slate-500 mt-1">
                    {plan.description}
                  </p>
                </div>

                <div className="mb-6">
                  <span className="text-4xl font-bold text-slate-900">
                    {plan.price}
                  </span>
                  <span className="text-sm text-slate-500 ml-1.5">
                    / {plan.period}
                  </span>
                </div>

                <ul className="space-y-3 flex-1 mb-6">
                  {plan.features.map((f) => (
                    <li
                      key={f}
                      className="flex items-center gap-2.5 text-sm text-slate-600"
                    >
                      <Check
                        className={`w-4 h-4 shrink-0 ${
                          plan.featured ? "text-indigo-600" : "text-slate-500"
                        }`}
                      />
                      {f}
                    </li>
                  ))}
                </ul>

                <Link href="/sign-up">
                  {plan.featured ? (
                    <ShimmerButton
                      background="rgba(79, 70, 229, 1)"
                      borderRadius="0.75rem"
                      className="w-full h-11 px-8"
                      shimmerColor='rgb(14, 196, 203)'
                shimmerSize="0.2em"
                    >
                      {plan.cta}
                    </ShimmerButton>
                  ) : (
                    <Button variant="outline" size="lg" className="w-full rounded-xl">
                      {plan.cta}
                    </Button>
                  )}
                </Link>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

function FaqSection() {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  return (
    <section id="faq" className="py-24 bg-slate-50/50">
      <div className="max-w-3xl mx-auto px-4 sm:px-6">
        <Reveal className="text-center mb-16">
          <p className="text-sm font-semibold text-indigo-600 mb-2">FAQ</p>
          <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 tracking-tight">
            Questions &{" "}
            <Highlighter action="highlight" color="#FF9800" strokeWidth={3} delay={600}>
              Answers
            </Highlighter>
          </h2>
        </Reveal>

        <div className="space-y-3">
          {faqs.map((faq, i) => (
            <Reveal key={faq.q} delay={i * 50}>
              <button
                onClick={() => setOpenIndex(openIndex === i ? null : i)}
                className="w-full text-left rounded-xl border border-slate-200 bg-white hover:border-slate-300 transition-colors"
              >
                <div className="flex items-center justify-between p-4">
                  <span className="text-sm font-medium text-slate-900 pr-4">
                    {faq.q}
                  </span>
                  <ChevronDown
                    className={`w-4 h-4 text-slate-500 shrink-0 transition-transform duration-200 ${
                      openIndex === i ? "rotate-180" : ""
                    }`}
                  />
                </div>
                <AnimatePresence>
                  {openIndex === i && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      className="overflow-hidden"
                    >
                      <p className="px-4 pb-4 text-sm text-slate-500 leading-relaxed">
                        {faq.a}
                      </p>
                    </motion.div>
                  )}
                </AnimatePresence>
              </button>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

function CtaSection() {
  return (
    <section className="py-24">
      <div className="max-w-4xl mx-auto px-4 sm:px-6">
        <Reveal className="relative rounded-3xl border border-indigo-100 bg-gradient-to-br from-indigo-50 via-white to-slate-50 p-10 sm:p-16 text-center overflow-hidden">
          <ShineBorder
            shineColor={["#4f46e5", "#8b5cf6", "#06b6d4"]}
            borderWidth={1}
            duration={12}
          />
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-indigo-100 mb-6">
            <Bell className="w-5 h-5 text-indigo-600" />
          </div>
          <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 tracking-tight">
            Start{" "}
            <Highlighter action="highlight" color="#FF9800" strokeWidth={3} delay={600}>
              listening today.
            </Highlighter>
          </h2>
          <p className="mt-4 text-slate-500 max-w-md mx-auto">
            Join hundreds of teams using Kleio to catch every mention, respond
            faster, and grow with confidence.
          </p>
          <div className="mt-8 flex justify-center">
            <Link href="/sign-up">
              <ShimmerButton
                background="rgba(79, 70, 229, 1)"
                borderRadius="0.75rem"
                className="h-12 px-8 font-semibold"
                shimmerColor='rgb(14, 196, 203)'
                shimmerSize="0.2em"
              >
                Get Started for Free
                <ArrowRight className="w-4 h-4 ml-1.5" />
              </ShimmerButton>
            </Link>
          </div>
          <p className="mt-4 text-xs text-slate-500">
            No credit card required. Free plan available.
          </p>
        </Reveal>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="border-t border-slate-200 pt-16 pb-8 bg-white">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="grid md:grid-cols-5 gap-10 mb-12">
          <div className="md:col-span-2">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center">
                <Bell className="w-4 h-4 text-white" />
              </div>
              <span className="text-lg font-bold text-slate-900">Kleio</span>
            </div>
            <p className="text-sm text-slate-500 leading-relaxed max-w-xs">
              Social mention monitoring for founders, marketers, and product
              teams. Never miss what matters.
            </p>
          </div>

          {Object.entries(footerLinks).map(([title, links]) => (
            <div key={title}>
              <p className="text-sm font-semibold text-slate-900 mb-4">
                {title}
              </p>
              <ul className="space-y-2.5">
                {links.map((link) => (
                  <li key={link}>
                    <a
                      href="#"
                      className="text-sm text-slate-500 hover:text-slate-700 transition-colors"
                    >
                      {link}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="pt-8 border-t border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-xs text-slate-500">
            &copy; {new Date().getFullYear()} Kleio. All rights reserved.
          </p>
          <div className="flex items-center gap-4">
            <a
              href="#"
              className="text-xs text-slate-500 hover:text-slate-700 transition-colors"
            >
              Privacy
            </a>
            <a
              href="#"
              className="text-xs text-slate-500 hover:text-slate-700 transition-colors"
            >
              Terms
            </a>
            <a
              href="#"
              className="text-xs text-slate-500 hover:text-slate-700 transition-colors"
            >
              support@kleio.dev
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}

/* ─── Page ─────────────────────────────────────────────────────────────── */

export function LandingPage() {
  return (
    <div className="min-h-screen bg-white antialiased">
      <NavBar />
      <main>
        <Hero />
        <PlatformStrip />
        <FeaturesSection />
        <HowItWorksSection />
        <TestimonialsSection />
        <PricingSection />
        <FaqSection />
        <CtaSection />
      </main>
      <Footer />
    </div>
  );
}
