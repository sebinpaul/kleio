"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { AnimatePresence, motion } from "framer-motion";
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
import { FlickeringGrid } from "@/components/ui/flickering-grid";
import { AuroraText } from "@/components/ui/aurora-text";

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
  },
  {
    icon: Globe,
    title: "Multi-Platform Coverage",
    description:
      "Reddit, Hacker News, and more platforms coming soon. One dashboard for everything.",
  },
  {
    icon: Mail,
    title: "Smart Email Alerts",
    description:
      "Rich notifications with context and direct links. Know exactly what was said and where.",
  },
  {
    icon: Shield,
    title: "Noise Reduction",
    description:
      "Smart deduplication filters out repeated matches and bot content. Signal, not spam.",
  },
  {
    icon: Target,
    title: "Keyword Intelligence",
    description:
      "Track unlimited keywords across platforms. Monitor brands, competitors, and industry terms.",
  },
  {
    icon: TrendingUp,
    title: "Growth Insights",
    description:
      "Track trending mentions and sentiment over time to inform your strategy.",
  },
];

const steps = [
  {
    number: "01",
    title: "Add Your Keywords",
    description:
      "Enter brand names, product terms, or competitor keywords you want to track.",
    icon: Search,
  },
  {
    number: "02",
    title: "We Monitor 24/7",
    description:
      "Kleio continuously scans Reddit, Hacker News, and other platforms for your keywords.",
    icon: Activity,
  },
  {
    number: "03",
    title: "Get Instant Alerts",
    description:
      "Receive email notifications the moment a mention is detected, with direct source links.",
    icon: Bell,
  },
];

const testimonials = [
  {
    name: "Sarah Chen",
    role: "Founder, DevTools.io",
    content:
      "Kleio helped us discover our product was being discussed on HN before we even launched. We joined the conversation and got 200+ signups that day.",
    initials: "SC",
  },
  {
    name: "Marcus Rivera",
    role: "Head of Growth, Stackbase",
    content:
      "We replaced three different tools with Kleio. The deduplication alone saves us hours every week.",
    initials: "MR",
  },
  {
    name: "Aisha Patel",
    role: "Product Lead, CloudSync",
    content:
      "The speed of detection is incredible. We caught a competitor mention within minutes and responded with our own solution.",
    initials: "AP",
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
    a: "Kleio currently monitors Reddit and Hacker News in real time. We're actively building integrations for X (Twitter), LinkedIn, and Product Hunt.",
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

/* ─── Animation helper ─────────────────────────────────────────────────── */

const fadeUp = {
  initial: { opacity: 0, y: 24 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: "-60px" as const },
  transition: { duration: 0.5 },
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
        <FlickeringGrid
          squareSize={4}
          gridGap={6}
          flickerChance={0.03}
          color="rgb(79, 70, 229)"
          maxOpacity={0.12}
          className="absolute inset-0 w-full h-full"
        />
        <div className="absolute inset-0 bg-gradient-to-b from-white via-white/80 to-white [mask-image:radial-gradient(ellipse_at_center,transparent_20%,black_70%)]" />
      </div>
      <div className="max-w-6xl mx-auto px-4 sm:px-6 relative z-10">
        <div className="max-w-3xl mx-auto text-center">
          <motion.div {...fadeUp}>
            <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3.5 py-1.5 mb-6 shadow-sm">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-xs text-slate-600 font-medium">
                Now monitoring Reddit & Hacker News
              </span>
            </div>
          </motion.div>

          <motion.h1
            {...fadeUp}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-slate-900 tracking-tight leading-[1.1]"
          >
            Know when your brand{" "}
            <AuroraText colors={["#4f46e5", "#7c3aed", "#06b6d4", "#8b5cf6"]}>
              gets mentioned.
            </AuroraText>
          </motion.h1>

          <motion.p
            {...fadeUp}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="mt-6 text-lg text-slate-500 max-w-xl mx-auto leading-relaxed"
          >
            Kleio monitors Reddit and Hacker News for your keywords and sends
            you instant email alerts. Stop guessing. Start listening.
          </motion.p>

          <motion.div
            {...fadeUp}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3"
          >
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
          </motion.div>

          <motion.div
            {...fadeUp}
            transition={{ duration: 0.5, delay: 0.5 }}
            className="mt-12 flex items-center justify-center gap-6"
          >
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
              <div className="flex items-center gap-0.5">
                {[...Array(5)].map((_, i) => (
                  <Star
                    key={i}
                    className="w-3.5 h-3.5 fill-amber-400 text-amber-400"
                  />
                ))}
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Loved by 500+ product teams
              </p>
            </div>
          </motion.div>
        </div>

        {/* Dashboard Preview */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7, delay: 0.2 }}
          className="mt-16 max-w-4xl mx-auto"
        >
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
                <span className="text-[11px] text-slate-400">
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
                    <p className="text-[10px] text-slate-400 font-medium">
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
                    <span className="text-[10px] text-slate-400 shrink-0">
                      {m.time}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

function PlatformStrip() {
  const platforms = [
    { name: "Reddit", active: true },
    { name: "Hacker News", active: true },
    { name: "X (Twitter)", active: false },
    { name: "LinkedIn", active: false },
    { name: "Product Hunt", active: false },
  ];

  return (
    <section className="py-10 border-y border-slate-100">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <p className="text-center text-xs text-slate-400 mb-5 uppercase tracking-widest font-medium">
          Platforms we monitor
        </p>
        <div className="flex flex-wrap items-center justify-center gap-3">
          {platforms.map((p) => (
            <div
              key={p.name}
              className={`flex items-center gap-2 px-4 py-2 rounded-full border ${
                p.active
                  ? "border-slate-200 bg-white shadow-sm"
                  : "border-slate-100 bg-slate-50 opacity-50"
              }`}
            >
              <div
                className={`w-1.5 h-1.5 rounded-full ${
                  p.active ? "bg-emerald-500" : "bg-slate-300"
                }`}
              />
              <span
                className={`text-xs font-medium ${
                  p.active ? "text-slate-700" : "text-slate-400"
                }`}
              >
                {p.name}
              </span>
              {!p.active && (
                <span className="text-[9px] text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">
                  Soon
                </span>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function FeaturesSection() {
  return (
    <section id="features" className="py-24 bg-slate-50/50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <motion.div {...fadeUp} className="text-center mb-16">
          <p className="text-sm font-semibold text-indigo-600 mb-2">
            Features
          </p>
          <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 tracking-tight">
            Everything you need to listen smarter
          </h2>
          <p className="mt-4 text-slate-500 max-w-xl mx-auto">
            From instant detection to intelligent filtering, Kleio gives you the
            tools to stay ahead of every conversation.
          </p>
        </motion.div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
          {features.map((feature, i) => (
            <motion.div
              key={feature.title}
              {...fadeUp}
              transition={{ delay: i * 0.06, duration: 0.5 }}
            >
              <div className="relative h-full rounded-2xl border border-slate-200 bg-white p-6 hover:shadow-lg hover:shadow-slate-100 hover:border-slate-300 transition-all duration-300 overflow-hidden">
                <ShineBorder
                  shineColor={["#4f46e5", "#06b6d4"]}
                  borderWidth={1}
                  duration={14 + i * 2}
                />
                <div className="w-10 h-10 rounded-xl bg-indigo-50 flex items-center justify-center mb-4">
                  <feature.icon className="w-5 h-5 text-indigo-600" />
                </div>
                <h3 className="text-base font-semibold text-slate-900 mb-2">
                  {feature.title}
                </h3>
                <p className="text-sm text-slate-500 leading-relaxed">
                  {feature.description}
                </p>
              </div>
            </motion.div>
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
        <motion.div {...fadeUp} className="text-center mb-16">
          <p className="text-sm font-semibold text-indigo-600 mb-2">
            How It Works
          </p>
          <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 tracking-tight">
            Three steps. Full coverage.
          </h2>
          <p className="mt-4 text-slate-500 max-w-lg mx-auto">
            Get started in under two minutes. No complex setup, no credit card
            required.
          </p>
        </motion.div>

        <div className="grid md:grid-cols-3 gap-8 relative">
          <div className="hidden md:block absolute top-7 left-[20%] right-[20%] h-px bg-slate-200" />

          {steps.map((step, i) => (
            <motion.div
              key={step.number}
              {...fadeUp}
              transition={{ delay: i * 0.12, duration: 0.5 }}
              className="text-center relative"
            >
              <div className="relative inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-indigo-50 border border-indigo-100 mb-5">
                <step.icon className="w-6 h-6 text-indigo-600" />
                <div className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-indigo-600 flex items-center justify-center">
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
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

function TestimonialsSection() {
  return (
    <section className="py-24 bg-slate-50/50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <motion.div {...fadeUp} className="text-center mb-16">
          <p className="text-sm font-semibold text-indigo-600 mb-2">
            Testimonials
          </p>
          <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 tracking-tight">
            Teams that ship faster with Kleio
          </h2>
        </motion.div>

        <div className="grid md:grid-cols-3 gap-6">
          {testimonials.map((t, i) => (
            <motion.div
              key={t.name}
              {...fadeUp}
              transition={{ delay: i * 0.1, duration: 0.5 }}
            >
              <div className="h-full rounded-2xl border border-slate-200 bg-white p-6">
                <div className="flex items-center gap-0.5 mb-4">
                  {[...Array(5)].map((_, j) => (
                    <Star
                      key={j}
                      className="w-4 h-4 fill-amber-400 text-amber-400"
                    />
                  ))}
                </div>
                <p className="text-sm text-slate-600 leading-relaxed mb-6">
                  &ldquo;{t.content}&rdquo;
                </p>
                <div className="flex items-center gap-3 pt-4 border-t border-slate-100">
                  <div className="w-9 h-9 rounded-full bg-indigo-100 flex items-center justify-center text-xs font-bold text-indigo-600">
                    {t.initials}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-900">
                      {t.name}
                    </p>
                    <p className="text-xs text-slate-500">{t.role}</p>
                  </div>
                </div>
              </div>
            </motion.div>
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
        <motion.div {...fadeUp} className="text-center mb-16">
          <p className="text-sm font-semibold text-indigo-600 mb-2">Pricing</p>
          <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 tracking-tight">
            Simple, transparent pricing
          </h2>
          <p className="mt-4 text-slate-500 max-w-lg mx-auto">
            Start free. Upgrade when you need more keywords, platforms, and
            features.
          </p>
        </motion.div>

        <div className="grid lg:grid-cols-3 gap-6 max-w-5xl mx-auto">
          {pricingPlans.map((plan, i) => (
            <motion.div
              key={plan.name}
              {...fadeUp}
              transition={{ delay: i * 0.1, duration: 0.5 }}
            >
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
                          plan.featured ? "text-indigo-600" : "text-slate-400"
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
            </motion.div>
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
        <motion.div {...fadeUp} className="text-center mb-16">
          <p className="text-sm font-semibold text-indigo-600 mb-2">FAQ</p>
          <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 tracking-tight">
            Questions & Answers
          </h2>
        </motion.div>

        <div className="space-y-3">
          {faqs.map((faq, i) => (
            <motion.div
              key={faq.q}
              {...fadeUp}
              transition={{ delay: i * 0.05, duration: 0.5 }}
            >
              <button
                onClick={() => setOpenIndex(openIndex === i ? null : i)}
                className="w-full text-left rounded-xl border border-slate-200 bg-white hover:border-slate-300 transition-colors"
              >
                <div className="flex items-center justify-between p-4">
                  <span className="text-sm font-medium text-slate-900 pr-4">
                    {faq.q}
                  </span>
                  <ChevronDown
                    className={`w-4 h-4 text-slate-400 shrink-0 transition-transform duration-200 ${
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
            </motion.div>
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
        <motion.div
          {...fadeUp}
          className="relative rounded-3xl border border-indigo-100 bg-gradient-to-br from-indigo-50 via-white to-slate-50 p-10 sm:p-16 text-center overflow-hidden"
        >
          <ShineBorder
            shineColor={["#4f46e5", "#8b5cf6", "#06b6d4"]}
            borderWidth={1}
            duration={12}
          />
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-indigo-100 mb-6">
            <Bell className="w-5 h-5 text-indigo-600" />
          </div>
          <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 tracking-tight">
            Start listening today.
          </h2>
          <p className="mt-4 text-slate-500 max-w-md mx-auto">
            Join hundreds of teams using Kleio to catch every mention, respond
            faster, and grow with confidence.
          </p>
          <div className="mt-8">
            <Link href="/sign-up">
              <ShimmerButton
                background="rgba(79, 70, 229, 1)"
                borderRadius="0.75rem"
                className="h-12 px-8 font-semibold"
                shimmerColor='rgb(14, 196, 203)'
                shimmerSize="0.2em"
              >
                Get Started Free
                <ArrowRight className="w-4 h-4 ml-1.5" />
              </ShimmerButton>
            </Link>
          </div>
          <p className="mt-4 text-xs text-slate-400">
            No credit card required. Free plan available.
          </p>
        </motion.div>
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
          <p className="text-xs text-slate-400">
            &copy; {new Date().getFullYear()} Kleio. All rights reserved.
          </p>
          <div className="flex items-center gap-4">
            <a
              href="#"
              className="text-xs text-slate-400 hover:text-slate-600 transition-colors"
            >
              Privacy
            </a>
            <a
              href="#"
              className="text-xs text-slate-400 hover:text-slate-600 transition-colors"
            >
              Terms
            </a>
            <a
              href="#"
              className="text-xs text-slate-400 hover:text-slate-600 transition-colors"
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

export default function LandingPage() {
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
