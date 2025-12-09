"use client";

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { motion, AnimatePresence, useScroll, useTransform } from 'framer-motion';
import { 
  Radio, Menu, X, Search, Bell, BarChart2, MessageSquare, RefreshCw, Filter, MoreHorizontal, 
  ArrowRight, Play, Sparkles, ShieldCheck, Globe2, Layers, Zap, Database, Lock, 
  Facebook, Twitter, Linkedin, Youtube, Share2, HelpCircle, Code, Server, Shield, Cpu, Github 
} from 'lucide-react';
import { AreaChart, Area, ResponsiveContainer, Tooltip, XAxis } from 'recharts';

// -----------------------------------------------------------------------------
// TYPES & INTERFACES
// -----------------------------------------------------------------------------

interface Feature {
  title: string;
  description: string;
  icon: React.ElementType;
}

interface Platform {
  id: string;
  name: string;
  icon: React.ElementType;
  color: string;
  bg: string;
  border: string;
  features: string[];
  desc: string;
}

// -----------------------------------------------------------------------------
// UI COMPONENTS
// -----------------------------------------------------------------------------

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
  fullWidth?: boolean;
}

const Button: React.FC<ButtonProps> = ({ 
  variant = 'primary', 
  size = 'md', 
  children, 
  fullWidth = false,
  className = '',
  ...props 
}) => {
  const baseStyles = "inline-flex items-center justify-center rounded-lg font-semibold transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed";
  
  const variants = {
    primary: "bg-gradient-to-r from-brand-indigo to-brand-purple text-white hover:shadow-lg hover:shadow-brand-indigo/30 focus:ring-brand-indigo",
    secondary: "bg-white text-brand-slate-800 border border-slate-200 hover:bg-slate-50 hover:border-brand-indigo/30 focus:ring-slate-200",
    outline: "border-2 border-brand-indigo text-brand-indigo hover:bg-brand-indigo/5 focus:ring-brand-indigo",
    ghost: "text-brand-slate-800 hover:bg-slate-100 focus:ring-slate-200"
  };
  const sizes = {
    sm: "px-3 py-1.5 text-sm",
    md: "px-6 py-3 text-base",
    lg: "px-8 py-4 text-lg"
  };
  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${fullWidth ? 'w-full' : ''} ${className}`}
      {...props}
    >
      {children}
    </motion.button>
  );
};

// -----------------------------------------------------------------------------
// NAVIGATION COMPONENT
// -----------------------------------------------------------------------------

const Navigation: React.FC = () => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navClasses = isScrolled
    ? 'bg-white/90 backdrop-blur-md shadow-md py-3 border-b border-slate-100'
    : 'bg-transparent py-6';

  const textClasses = isScrolled
    ? 'text-brand-slate-800'
    : 'text-white';

  const logoBg = isScrolled
    ? 'bg-gradient-to-br from-brand-indigo to-brand-purple text-white shadow-brand-indigo/20'
    : 'bg-white text-brand-indigo shadow-black/20';

  return (
    <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${navClasses}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center">
          <Link href="/" className="flex items-center space-x-2 cursor-pointer group">
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center shadow-lg transition-all duration-300 ${logoBg}`}>
              <Radio size={24} />
            </div>
            <span className={`text-2xl font-bold transition-colors duration-300 ${textClasses}`}>
              Kleio
            </span>
          </Link>
          <div className="hidden md:flex items-center space-x-8">
            {['Features', 'Platforms', 'Tech'].map((item) => (
               <a 
                 key={item}
                 href={`#${item.toLowerCase()}`} 
                 className={`font-medium transition-colors hover:text-brand-cyan ${textClasses}`}
               >
                 {item}
               </a>
            ))}
          </div>
          <div className="hidden md:flex items-center space-x-4">
            <Link href="/sign-in">
              <Button 
                  variant={isScrolled ? 'secondary' : 'ghost'} 
                  className={!isScrolled ? 'text-white hover:bg-white/10 hover:text-white' : ''}
                  size="sm"
              >
                Log In
              </Button>
            </Link>
            <Link href="/sign-up">
              <Button variant={isScrolled ? 'primary' : 'secondary'} size="sm">
                Get Beta Access
              </Button>
            </Link>
          </div>
          <div className="md:hidden">
            <button onClick={() => setMobileMenuOpen(!mobileMenuOpen)} className={textClasses}>
              {mobileMenuOpen ? <X /> : <Menu />}
            </button>
          </div>
        </div>
      </div>
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="md:hidden bg-white border-b border-slate-100 overflow-hidden shadow-xl"
          >
            <div className="px-4 py-6 space-y-4 flex flex-col">
              <a href="#features" onClick={() => setMobileMenuOpen(false)} className="text-lg font-medium text-brand-slate-800">Features</a>
              <a href="#platforms" onClick={() => setMobileMenuOpen(false)} className="text-lg font-medium text-brand-slate-800">Platforms</a>
              <a href="#tech" onClick={() => setMobileMenuOpen(false)} className="text-lg font-medium text-brand-slate-800">Technology</a>
              <div className="pt-4 flex flex-col space-y-3">
                <Link href="/sign-in"><Button variant="secondary" fullWidth>Log In</Button></Link>
                <Link href="/sign-up"><Button variant="primary" fullWidth>Get Beta Access</Button></Link>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
};

// -----------------------------------------------------------------------------
// HERO DASHBOARD COMPONENT
// -----------------------------------------------------------------------------

const data = [
  { name: 'Mon', value: 40 },
  { name: 'Tue', value: 30 },
  { name: 'Wed', value: 65 },
  { name: 'Thu', value: 45 },
  { name: 'Fri', value: 80 },
  { name: 'Sat', value: 55 },
  { name: 'Sun', value: 95 },
];

const mentions = [
  { id: 1, source: 'Twitter', user: '@tech_guru', text: 'Just tried the new Kleio app for social listening. The latency is incredible.', sentiment: 'positive', time: '2m ago' },
  { id: 2, source: 'Reddit', user: 'u/startup_founder', text: 'How are you guys handling anti-bot measures? Looking for alternatives...', sentiment: 'neutral', time: '15m ago' },
  { id: 3, source: 'LinkedIn', user: 'Sarah Jenkins', text: 'Excited to announce our partnership leveraging advanced monitoring tools.', sentiment: 'positive', time: '1h ago' },
];

const HeroDashboard: React.FC = () => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 50, rotateX: 5 }}
      animate={{ opacity: 1, y: 0, rotateX: 0 }}
      transition={{ duration: 1, delay: 0.2, type: "spring", stiffness: 50 }}
      className="relative w-full max-w-4xl mx-auto z-20"
    >
      <div className="relative bg-white rounded-2xl shadow-2xl overflow-hidden flex flex-col md:flex-row h-auto md:h-[500px]">
        
        {/* Sidebar - Hidden on mobile */}
        <div className="w-20 bg-slate-900 flex flex-col items-center py-6 space-y-8 hidden md:flex z-10 shrink-0">
          <div className="w-10 h-10 bg-brand-indigo rounded-xl flex items-center justify-center text-white shadow-lg shadow-brand-indigo/50">
            <span className="font-bold text-xl">K</span>
          </div>
          <div className="space-y-6 text-slate-400 w-full flex flex-col items-center">
            <div className="p-3 bg-white/10 rounded-xl text-brand-cyan shadow-inner cursor-pointer"><BarChart2 size={20} /></div>
            <div className="p-3 hover:bg-white/5 rounded-xl transition-colors cursor-pointer hover:text-white"><MessageSquare size={20} /></div>
            <div className="p-3 hover:bg-white/5 rounded-xl transition-colors cursor-pointer hover:text-white"><Bell size={20} /></div>
          </div>
          <div className="mt-auto pb-4">
             <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700"></div>
          </div>
        </div>
        {/* Main Content */}
        <div className="flex-1 flex flex-col bg-slate-50">
          {/* Header */}
          <div className="h-16 bg-white border-b border-slate-100 flex items-center justify-between px-6 shadow-sm z-10">
            <div className="flex items-center space-x-3 text-slate-400 bg-slate-50 px-4 py-2 rounded-xl w-full md:w-auto border border-slate-100 focus-within:ring-2 ring-brand-indigo/10 transition-shadow">
              <Search size={18} />
              <span className="text-sm font-medium">Search mentions...</span>
            </div>
            <div className="hidden md:flex items-center space-x-4">
              <div className="px-3 py-1 bg-emerald-50 text-emerald-600 text-xs font-bold rounded-full flex items-center border border-emerald-100">
                <span className="w-2 h-2 bg-emerald-500 rounded-full mr-2 animate-pulse"></span>
                System Operational
              </div>
            </div>
          </div>
          {/* Dashboard Body */}
          <div className="flex-1 p-4 md:p-6 overflow-hidden flex flex-col space-y-6">
            
            {/* Stats Row */}
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div className="bg-white p-4 rounded-2xl shadow-sm border border-slate-100 group hover:border-brand-indigo/20 transition-colors">
                <div className="text-slate-400 text-xs font-bold uppercase tracking-wider mb-2 flex justify-between">Total Mentions <MoreHorizontal size={14}/></div>
                <div className="text-3xl font-black text-slate-800 tracking-tight">12.4k</div>
                <div className="text-emerald-500 text-xs mt-2 flex items-center font-bold bg-emerald-50 w-fit px-2 py-0.5 rounded-full">↑ 12.5%</div>
              </div>
              <div className="bg-white p-4 rounded-2xl shadow-sm border border-slate-100 group hover:border-brand-indigo/20 transition-colors">
                <div className="text-slate-400 text-xs font-bold uppercase tracking-wider mb-2 flex justify-between">Sentiment <MoreHorizontal size={14}/></div>
                <div className="text-3xl font-black text-slate-800 tracking-tight">8.4</div>
                <div className="text-brand-indigo text-xs mt-2 font-bold bg-indigo-50 w-fit px-2 py-0.5 rounded-full">Positive</div>
              </div>
              <div className="bg-gradient-to-br from-brand-indigo to-brand-purple p-4 rounded-2xl shadow-lg shadow-brand-indigo/20 text-white col-span-2 md:col-span-1 hidden md:block">
                 <div className="text-white/60 text-xs font-bold uppercase tracking-wider mb-1">Active Sources</div>
                <div className="text-3xl font-black mt-1">7/7</div>
                <div className="text-white/80 text-xs mt-2">All scrapers running</div>
              </div>
            </div>
            {/* Chart Area */}
            <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-100 flex-1 min-h-[180px] flex flex-col relative overflow-hidden">
               {/* Decorative background grid for chart */}
              <div className="absolute inset-0 opacity-[0.03] pointer-events-none" style={{ backgroundImage: 'linear-gradient(#000 1px, transparent 1px), linear-gradient(90deg, #000 1px, transparent 1px)', backgroundSize: '20px 20px' }}></div>
              
              <div className="flex justify-between items-center mb-4 relative z-10">
                <h3 className="font-bold text-slate-800">Volume Trends</h3>
                <div className="flex space-x-2">
                   <button className="p-1.5 hover:bg-slate-50 rounded-lg text-slate-400 hover:text-brand-indigo transition-colors"><RefreshCw size={14} /></button>
                </div>
              </div>
              <div className="flex-1 w-full h-full min-h-[100px] relative z-10">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={data}>
                    <defs>
                      <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fontSize: 10, fill: '#94a3b8', fontWeight: 600}} dy={10} />
                    <Tooltip 
                        contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)' }}
                        itemStyle={{ color: '#6366f1', fontWeight: 'bold' }}
                        cursor={{ stroke: '#6366f1', strokeWidth: 1, strokeDasharray: '4 4' }}
                    />
                    <Area type="monotone" dataKey="value" stroke="#6366f1" strokeWidth={4} fillOpacity={1} fill="url(#colorValue)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
            {/* Mention List (Preview) */}
            <div className="space-y-3 hidden md:block">
              {mentions.map((m) => (
                <div key={m.id} className="bg-white p-3 rounded-xl border border-slate-100 shadow-sm flex items-start space-x-3 hover:shadow-md hover:border-brand-indigo/30 transition-all cursor-default group">
                  <div className={`w-2 h-2 mt-1.5 rounded-full ${m.source === 'Twitter' ? 'bg-sky-400' : m.source === 'Reddit' ? 'bg-orange-500' : 'bg-blue-700'}`}></div>
                  <div className="flex-1">
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-sm text-slate-800">{m.user} <span className="text-slate-400 font-normal text-xs ml-1 opacity-70">via {m.source}</span></span>
                      <span className="text-xs text-slate-400 font-medium">{m.time}</span>
                    </div>
                    <p className="text-sm text-slate-600 mt-0.5 line-clamp-1 group-hover:text-slate-900 transition-colors">{m.text}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

// -----------------------------------------------------------------------------
// HERO SECTION
// -----------------------------------------------------------------------------

const Hero: React.FC = () => {
  const { scrollY } = useScroll();
  const opacity = useTransform(scrollY, [0, 300], [1, 0]);
  return (
    <section className="relative pt-32 pb-20 lg:pt-48 lg:pb-32 overflow-hidden bg-[#020617] isolate">
      
      {/* 1. Cyber Grid Background */}
      <div className="absolute inset-0 z-0 opacity-20"
           style={{
             backgroundImage: `linear-gradient(to right, #334155 1px, transparent 1px), linear-gradient(to bottom, #334155 1px, transparent 1px)`,
             backgroundSize: '40px 40px',
             maskImage: 'linear-gradient(to bottom, black 40%, transparent 100%)'
           }}>
      </div>
      {/* 2. Top Spotlight / Aurora Effect */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[500px] bg-brand-indigo/30 rounded-full blur-[120px] -translate-y-1/2 z-0 mix-blend-screen pointer-events-none"></div>
      <div className="absolute top-0 left-1/4 w-[600px] h-[400px] bg-brand-cyan/20 rounded-full blur-[100px] -translate-y-2/3 z-0 pointer-events-none animate-blob"></div>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="flex flex-col items-center text-center">
          
          {/* Badge */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="inline-flex items-center space-x-2 bg-white/5 backdrop-blur-md border border-white/10 rounded-full px-4 py-1.5 mb-8 shadow-2xl ring-1 ring-white/10 hover:bg-white/10 transition-colors cursor-default"
          >
            <Sparkles className="w-3 h-3 text-brand-cyan" />
            <span className="text-xs font-bold text-brand-cyan tracking-widest uppercase">The Future of Listening</span>
          </motion.div>
          {/* Headline */}
          <motion.h1 
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.1, ease: "easeOut" }}
            className="text-5xl md:text-7xl lg:text-8xl font-black tracking-tight text-white leading-[1.1] mb-8 drop-shadow-2xl"
          >
            Capture Every <br className="hidden md:block" />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-cyan via-brand-indigo to-brand-purple animate-pulse">
              Hidden Signal.
            </span>
          </motion.h1>
          {/* Subtext */}
          <motion.p 
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="text-lg md:text-xl text-slate-400 mb-10 leading-relaxed max-w-2xl mx-auto font-light"
          >
            Kleio is the resilient social intelligence engine that tracks your keywords across <span className="text-white font-semibold">7 major platforms</span>, bypassing bots to deliver the truth.
          </motion.p>
          {/* CTA Buttons */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.3 }}
            className="flex flex-col sm:flex-row items-center justify-center space-y-4 sm:space-y-0 sm:space-x-4 mb-20"
          >
            <Link href="/dashboard">
              <Button size="lg" className="w-full sm:w-auto shadow-xl shadow-brand-indigo/30 bg-white text-slate-950 hover:bg-slate-50 border-none font-bold text-lg px-8">
                Start Monitoring
              </Button>
            </Link>
            <a href="#tech">
              <Button variant="secondary" size="lg" className="w-full sm:w-auto bg-white/5 border-white/10 text-white hover:bg-white/10 backdrop-blur-sm px-8">
                <Play className="mr-2 w-4 h-4 fill-current" /> See How It Works
              </Button>
            </a>
          </motion.div>
          {/* Dashboard Visual */}
          <motion.div 
             initial={{ opacity: 0, y: 100, rotateX: 20 }}
             animate={{ opacity: 1, y: 0, rotateX: 0 }}
             transition={{ duration: 1.2, delay: 0.4, type: "spring", bounce: 0.2 }}
             style={{ opacity }}
             className="w-full max-w-5xl mx-auto relative perspective-1000"
          >
             {/* Glow behind dashboard */}
             <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[110%] h-[110%] bg-brand-indigo/20 blur-[80px] -z-10 rounded-full"></div>
             
             <div className="relative group">
                <div className="absolute -inset-1 bg-gradient-to-r from-brand-cyan via-brand-indigo to-brand-purple rounded-2xl opacity-30 blur group-hover:opacity-60 transition duration-1000"></div>
                <HeroDashboard />
             </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
};

// -----------------------------------------------------------------------------
// FEATURES COMPONENT
// -----------------------------------------------------------------------------

const FeatureCard: React.FC<{ 
  icon: React.ElementType, 
  title: string, 
  description: string, 
  index: number 
}> = ({ icon: Icon, title, description, index }) => (
  <motion.div
    initial={{ opacity: 0, y: 30 }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true, margin: "-50px" }}
    transition={{ duration: 0.5, delay: index * 0.1 }}
    className="relative bg-white p-8 rounded-2xl shadow-sm hover:shadow-2xl transition-all duration-300 group z-10 border border-slate-100 overflow-hidden"
  >
    {/* Hover Gradient Border Effect */}
    <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-brand-cyan to-brand-indigo transform scale-x-0 group-hover:scale-x-100 transition-transform duration-300 origin-left"></div>
    <div className="w-14 h-14 bg-slate-50 rounded-2xl flex items-center justify-center mb-6 text-brand-indigo group-hover:scale-110 transition-transform duration-300 shadow-inner border border-slate-100">
      <Icon size={28} strokeWidth={1.5} />
    </div>
    <h3 className="text-xl font-bold text-slate-900 mb-3 group-hover:text-brand-indigo transition-colors">{title}</h3>
    <p className="text-slate-500 leading-relaxed text-sm md:text-base">{description}</p>
  </motion.div>
);

const Features: React.FC = () => {
  return (
    <section id="features" className="py-24 bg-slate-50 relative overflow-hidden">
      
      {/* Dot Pattern Background */}
      <div className="absolute inset-0 z-0 opacity-[0.4]" 
           style={{ 
             backgroundImage: 'radial-gradient(#cbd5e1 1px, transparent 1px)', 
             backgroundSize: '24px 24px' 
           }}>
      </div>
      
      {/* Soft Vignette */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-slate-50/50 to-slate-50 pointer-events-none"></div>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        
        <div className="text-center max-w-3xl mx-auto mb-20">
          <motion.span 
             initial={{ opacity: 0, y: 10 }}
             whileInView={{ opacity: 1, y: 0 }}
             viewport={{ once: true }}
             className="text-sm font-bold text-brand-indigo tracking-widest uppercase mb-3 block"
          >
            Unmatched Resilience
          </motion.span>
          <motion.h2 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
            className="text-4xl md:text-5xl font-extrabold text-slate-900 mb-6 tracking-tight"
          >
            The Engine That <span className="bg-clip-text text-transparent bg-gradient-to-r from-brand-indigo to-brand-purple">Never Blinks.</span>
          </motion.h2>
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            className="text-lg text-slate-600 leading-relaxed"
          >
             Social platforms actively fight scrapers. Kleio fights back with enterprise-grade rotating proxies and human-mimicking browsers.
          </motion.p>
        </div>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
           <FeatureCard 
             index={0}
             icon={ShieldCheck} 
             title="Anti-Bot Evasion" 
             description="Proprietary rotation logic that mimics human behavior, bypassing Cloudflare and CAPTCHAs with 99.9% success rate." 
           />
           <FeatureCard 
             index={1}
             icon={Globe2} 
             title="Global Proxy Network" 
             description="Access localized content from 150+ countries. We rotate residential IPs automatically to prevent blocking." 
           />
           <FeatureCard 
             index={2}
             icon={Layers} 
             title="Deduplication Engine" 
             description="Smart fingerprinting ensures you never see the same post twice, even if it's cross-posted or retweeted." 
           />
           <FeatureCard 
             index={3}
             icon={Zap} 
             title="Real-time Webhooks" 
             description="Get alerted the millisecond a keyword is mentioned. Push data directly to Slack, Discord, or your API." 
           />
           <FeatureCard 
             index={4}
             icon={Database} 
             title="Historical Backfill" 
             description="Don't just look forward. Instantly access up to 3 years of historical conversation data for any keyword." 
           />
           <FeatureCard 
             index={5}
             icon={Lock} 
             title="Enterprise Security" 
             description="SOC2 Type II compliant. Your tracking data is encrypted at rest and in transit. Private instances available." 
           />
        </div>
      </div>
    </section>
  );
};

// -----------------------------------------------------------------------------
// PLATFORMS COMPONENT
// -----------------------------------------------------------------------------

const platforms: Platform[] = [
  {
    id: 'linkedin',
    name: 'LinkedIn',
    icon: Linkedin,
    color: 'text-blue-400',
    bg: 'bg-blue-500/10',
    border: 'border-blue-500/20',
    features: ['Company Pages', 'Personal Profiles', 'Hashtags', 'Groups'],
    desc: "Monitor professional discourse. Perfect for B2B intelligence and recruitment tracking."
  },
  {
    id: 'twitter',
    name: 'X (Twitter)',
    icon: Twitter,
    color: 'text-white',
    bg: 'bg-white/10',
    border: 'border-white/20',
    features: ['Keyword Search', 'User Timelines', 'Cashtags ($)', 'Geo-fenced Tweets'],
    desc: "Real-time pulse of the world. Leveraging Nitter instances for robust, non-rate-limited access."
  },
  {
    id: 'reddit',
    name: 'Reddit',
    icon: Share2, 
    color: 'text-orange-400',
    bg: 'bg-orange-500/10',
    border: 'border-orange-500/20',
    features: ['Subreddits', 'Comments', 'User Posts', 'Karma Tracking'],
    desc: "Dive deep into niche communities. Track sentiment in specific subreddits relevant to your brand."
  },
  {
    id: 'hackernews',
    name: 'HackerNews',
    icon: MessageSquare,
    color: 'text-orange-300',
    bg: 'bg-orange-500/10',
    border: 'border-orange-500/20',
    features: ['Show HN', 'Front Page', 'New Comments', 'User Activity'],
    desc: "Stay ahead of tech trends. Monitor the most critical discussions in the developer community."
  },
  {
    id: 'quora',
    name: 'Quora',
    icon: HelpCircle,
    color: 'text-red-400',
    bg: 'bg-red-500/10',
    border: 'border-red-500/20',
    features: ['Topic Tracking', 'Questions', 'Answer Monitoring'],
    desc: "Discover what people are asking about your industry. Identify pain points and intent."
  },
  {
    id: 'facebook',
    name: 'Facebook',
    icon: Facebook,
    color: 'text-blue-400',
    bg: 'bg-blue-600/10',
    border: 'border-blue-600/20',
    features: ['Public Pages', 'Groups (Public)', 'Events'],
    desc: "Monitor improved public page data. Requires user token for granular access."
  },
  {
    id: 'youtube',
    name: 'YouTube',
    icon: Youtube,
    color: 'text-red-500',
    bg: 'bg-red-500/10',
    border: 'border-red-500/20',
    features: ['Video Titles', 'Descriptions', 'Comments', 'Channel Activity'],
    desc: "Track video content and comment sentiment. Uses Invidious instances for privacy and reliability."
  }
];

const Platforms: React.FC = () => {
  const [activeTab, setActiveTab] = useState(platforms[0]);
  return (
    <section id="platforms" className="py-24 bg-slate-950 relative overflow-hidden">
      
      {/* Background Glows */}
      <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-brand-indigo/10 rounded-full blur-[100px] -translate-y-1/2 translate-x-1/2 pointer-events-none"></div>
      <div className="absolute bottom-0 left-0 w-[600px] h-[600px] bg-brand-cyan/5 rounded-full blur-[100px] translate-y-1/2 -translate-x-1/2 pointer-events-none"></div>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        
        <div className="mb-16">
          <motion.h2 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-4xl lg:text-5xl font-extrabold text-white mb-6"
          >
            Universal Coverage. <br/>
            <span className="text-slate-500">One Unified Stream.</span>
          </motion.h2>
        </div>
        <div className="flex flex-col lg:flex-row gap-8 lg:gap-12">
          
          {/* Scrollable Tabs for Mobile / List for Desktop */}
          <div className="lg:w-1/3 flex lg:flex-col overflow-x-auto lg:overflow-visible space-x-4 lg:space-x-0 lg:space-y-3 pb-4 lg:pb-0 px-1 scrollbar-hide">
            {platforms.map((p) => (
              <button
                key={p.id}
                onClick={() => setActiveTab(p)}
                className={`flex-shrink-0 flex items-center space-x-3 lg:space-x-4 p-3 lg:p-4 rounded-xl transition-all duration-200 text-left border ${
                  activeTab.id === p.id 
                  ? 'bg-slate-800 border-slate-700 text-white shadow-lg shadow-black/20' 
                  : 'bg-transparent border-transparent hover:bg-slate-900 text-slate-400 hover:text-slate-200'
                }`}
              >
                <div className={`p-2 rounded-lg ${activeTab.id === p.id ? p.bg : 'bg-slate-800'} ${activeTab.id === p.id ? p.color : 'text-slate-500'}`}>
                  <p.icon size={20} />
                </div>
                <span className={`font-semibold ${activeTab.id === p.id ? 'text-white' : 'text-slate-500'}`}>{p.name}</span>
              </button>
            ))}
          </div>
          {/* Details Card */}
          <div className="lg:w-2/3">
            <AnimatePresence mode="wait">
              <motion.div
                key={activeTab.id}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
                className="bg-slate-900/50 backdrop-blur-xl rounded-3xl p-8 lg:p-12 border border-slate-800 h-full flex flex-col justify-center relative overflow-hidden group"
              >
                {/* Accent Glow */}
                <div className={`absolute top-0 right-0 w-64 h-64 ${activeTab.bg} rounded-full blur-[80px] opacity-40 -mr-10 -mt-10 pointer-events-none transition-colors duration-500`}></div>
                <div className="flex items-center space-x-4 mb-8 relative z-10">
                  <div className={`p-4 rounded-2xl ${activeTab.bg} ${activeTab.color} border ${activeTab.border} shadow-lg backdrop-blur-sm`}>
                    <activeTab.icon size={40} />
                  </div>
                  <div>
                    <h3 className="text-3xl font-bold text-white">{activeTab.name}</h3>
                    <div className="text-sm font-medium text-slate-400 flex items-center mt-1">
                        <span className="w-2 h-2 rounded-full bg-green-500 mr-2 animate-pulse"></span>
                        APIv2 Connected
                    </div>
                  </div>
                </div>
                <p className="text-xl text-slate-300 mb-10 leading-relaxed relative z-10 font-light border-l-2 border-slate-700 pl-6">
                  {activeTab.desc}
                </p>
                <div className="bg-black/20 rounded-2xl p-6 lg:p-8 relative z-10 border border-white/5">
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-6 flex items-center">
                    <Layers className="w-4 h-4 mr-2" /> Data Points
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-y-4 gap-x-8">
                    {activeTab.features.map((feature, idx) => (
                      <div key={idx} className="flex items-center space-x-3 group/item">
                        <div className={`w-1.5 h-1.5 rounded-full ${activeTab.color.replace('text-', 'bg-')} opacity-60 group-hover/item:opacity-100 transition-opacity`}></div>
                        <span className="text-slate-300 group-hover/item:text-white transition-colors">{feature}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="mt-8 flex justify-end relative z-10">
                    <button className="text-sm font-semibold text-white flex items-center hover:text-brand-cyan transition-colors">
                        View Integration Docs <ArrowRight size={16} className="ml-2" />
                    </button>
                </div>
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </div>
    </section>
  );
};

// -----------------------------------------------------------------------------
// TECH STACK COMPONENT
// -----------------------------------------------------------------------------

const TechItem: React.FC<{ title: string; desc: string; icon: React.ElementType }> = ({ title, desc, icon: Icon }) => (
  <div className="flex items-start space-x-4 p-4 rounded-xl hover:bg-slate-100 transition-colors duration-200">
    <div className="mt-1 bg-white p-2 rounded-lg text-brand-indigo border border-slate-200 shadow-sm">
      <Icon size={20} />
    </div>
    <div>
      <h4 className="text-slate-900 font-bold text-lg">{title}</h4>
      <p className="text-slate-500 text-sm mt-1 leading-relaxed">{desc}</p>
    </div>
  </div>
);

const TechStack: React.FC = () => {
  return (
    <section id="tech" className="py-24 bg-slate-50 relative overflow-hidden border-t border-slate-200">
      
      {/* Technical Grid Background */}
      <div className="absolute inset-0 opacity-[0.03]" 
           style={{ 
             backgroundImage: `linear-gradient(#000 1px, transparent 1px), linear-gradient(90deg, #000 1px, transparent 1px)`, 
             backgroundSize: '40px 40px' 
           }}>
      </div>
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          
          {/* Left: Animation (Technical Diagram) */}
          <div className="relative h-[400px] flex items-center justify-center bg-white rounded-2xl border border-slate-200 shadow-xl overflow-hidden">
            {/* Grid on Card */}
            <div className="absolute inset-0 opacity-[0.05] pointer-events-none" style={{ backgroundImage: 'radial-gradient(#6366f1 1px, transparent 1px)', backgroundSize: '20px 20px' }}></div>
            
            <div className="text-center w-full h-full flex flex-col items-center justify-center relative">
               
               {/* Center Node */}
               <motion.div 
                 animate={{ boxShadow: ["0 0 0 0px rgba(99, 102, 241, 0.2)", "0 0 0 20px rgba(99, 102, 241, 0)"] }}
                 transition={{ duration: 2, repeat: Infinity }}
                 className="w-24 h-24 bg-brand-indigo rounded-full flex items-center justify-center z-20 shadow-2xl relative"
               >
                 <Server className="text-white" size={32} />
                 {/* Pulse rings */}
                 <div className="absolute inset-0 border-2 border-white/20 rounded-full animate-ping"></div>
               </motion.div>
               {/* Orbiting Nodes */}
               {[0, 72, 144, 216, 288].map((deg, i) => (
                 <motion.div
                    key={i}
                    style={{ position: 'absolute' }}
                    animate={{ rotate: 360 }}
                    transition={{ duration: 25, ease: "linear", repeat: Infinity }}
                    className="w-full h-full flex items-center justify-center"
                 >
                    <motion.div
                        style={{ transform: `rotate(${deg}deg) translateX(130px) rotate(-${deg}deg)` }} 
                        className="w-14 h-14 bg-white rounded-xl border-2 border-slate-100 flex items-center justify-center shadow-lg z-10"
                    >
                         <Shield size={20} className="text-slate-600" />
                    </motion.div>
                 </motion.div>
               ))}
                {/* Connecting Lines (Simulated via overlay SVG) */}
               <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-20">
                   <circle cx="50%" cy="50%" r="130" stroke="#6366f1" strokeWidth="2" fill="none" strokeDasharray="8,8" />
               </svg>
               
               <div className="absolute bottom-6 right-6 bg-slate-900 px-4 py-2 rounded-lg shadow-lg flex items-center space-x-3 z-20">
                 <RefreshCw className="animate-spin text-brand-emerald" size={14} />
                 <span className="text-xs text-white font-mono font-bold tracking-wider">SYSTEM_OPTIMAL</span>
               </div>
            </div>
          </div>
          {/* Right: Content */}
          <div>
            <div className="inline-block px-3 py-1 bg-brand-indigo/10 rounded-full text-brand-indigo font-bold text-xs uppercase tracking-wider mb-4">
                Architecture
            </div>
            <h2 className="text-3xl lg:text-5xl font-extrabold text-slate-900 mb-6">Deep Tech.<br/>Simple Results.</h2>
            <p className="text-slate-600 text-lg mb-10 leading-relaxed">
               Beneath the clean interface lies a complex infrastructure designed for data resilience. 
               We handle the dirty work of scraping, parsing, and verifying so you don't have to.
            </p>
            <div className="space-y-4">
               <TechItem 
                 icon={Code} 
                 title="High-Scale Django Backend" 
                 desc="Optimized query handling for massive datasets, capable of ingesting millions of mentions per hour." 
               />
               <TechItem 
                 icon={Cpu} 
                 title="Undetected Headless Browsers" 
                 desc="Leveraging customized Selenium and Chromium instances to mimic human behavior perfectly." 
               />
               <TechItem 
                 icon={Server} 
                 title="Residential Proxy Network" 
                 desc="Automatic IP rotation through a global pool of residential proxies prevents IP bans." 
               />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

// -----------------------------------------------------------------------------
// FOOTER CTA COMPONENT
// -----------------------------------------------------------------------------

const FooterCTA: React.FC = () => {
  return (
    <section className="py-32 relative overflow-hidden bg-slate-950">
        
        {/* Intense Gradient Background */}
        <div className="absolute inset-0 bg-gradient-to-tr from-brand-indigo via-brand-purple to-brand-cyan opacity-90"></div>
        
        {/* Noise Texture */}
        <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-40 mix-blend-overlay"></div>
        
        {/* Animated Orbs */}
        <div className="absolute top-0 left-0 w-[500px] h-[500px] bg-white opacity-20 rounded-full blur-[100px] mix-blend-soft-light animate-blob"></div>
        <div className="absolute bottom-0 right-0 w-[500px] h-[500px] bg-brand-indigo opacity-30 rounded-full blur-[100px] mix-blend-multiply animate-blob animation-delay-2000"></div>
        <div className="max-w-4xl mx-auto px-4 text-center relative z-10">
            <motion.h2 
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="text-5xl md:text-7xl font-black text-white mb-8 tracking-tight drop-shadow-lg"
            >
              Don't Let the <br/> Conversation Fade.
            </motion.h2>
            <motion.p 
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.1 }}
              className="text-xl md:text-2xl text-indigo-100 mb-12 max-w-2xl mx-auto font-medium"
            >
                Join the beta program today and get the social intelligence your brand deserves.
            </motion.p>
            <motion.div 
               initial={{ opacity: 0, y: 30 }}
               whileInView={{ opacity: 1, y: 0 }}
               viewport={{ once: true }}
               transition={{ delay: 0.2 }}
               className="flex flex-col sm:flex-row justify-center items-center space-y-4 sm:space-y-0 sm:space-x-6"
            >
                <Link href="/dashboard">
                  <Button size="lg" className="px-10 py-5 text-lg bg-white text-brand-indigo hover:bg-indigo-50 shadow-2xl shadow-black/20 border-none font-bold min-w-[200px]">
                    Get Started
                  </Button>
                </Link>
                <Button variant="outline" size="lg" className="px-10 py-5 text-lg border-2 border-white/30 text-white hover:bg-white/10 hover:border-white focus:ring-white/50 backdrop-blur-sm min-w-[200px]">
                  Book Demo
                </Button>
            </motion.div>
        </div>
    </section>
  );
};

// -----------------------------------------------------------------------------
// FOOTER COMPONENT
// -----------------------------------------------------------------------------

const Footer: React.FC = () => {
  return (
    <footer className="bg-slate-50 border-t border-slate-200 pt-16 pb-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-12">
          <div className="col-span-2 md:col-span-1">
            <div className="flex items-center space-x-2 mb-4">
               <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-indigo to-brand-purple flex items-center justify-center text-white">
                  <Radio size={18} />
               </div>
               <span className="text-xl font-bold text-slate-900">Kleio</span>
            </div>
            <p className="text-slate-500 text-sm">
              The intelligent social listening tool for modern brands.
            </p>
          </div>
          
          <div>
            <h4 className="font-bold text-slate-900 mb-4">Product</h4>
            <ul className="space-y-2 text-sm text-slate-600">
              <li><a href="#features" className="hover:text-brand-indigo">Features</a></li>
              <li><a href="#pricing" className="hover:text-brand-indigo">Pricing</a></li>
              <li><a href="#tech" className="hover:text-brand-indigo">API</a></li>
            </ul>
          </div>
          
          <div>
            <h4 className="font-bold text-slate-900 mb-4">Company</h4>
            <ul className="space-y-2 text-sm text-slate-600">
              <li><a href="#" className="hover:text-brand-indigo">About</a></li>
              <li><a href="#" className="hover:text-brand-indigo">Blog</a></li>
              <li><a href="#" className="hover:text-brand-indigo">Careers</a></li>
            </ul>
          </div>
          
          <div>
            <h4 className="font-bold text-slate-900 mb-4">Legal</h4>
            <ul className="space-y-2 text-sm text-slate-600">
              <li><a href="#" className="hover:text-brand-indigo">Privacy</a></li>
              <li><a href="#" className="hover:text-brand-indigo">Terms</a></li>
            </ul>
          </div>
        </div>
        
        <div className="border-t border-slate-200 pt-8 flex flex-col md:flex-row justify-between items-center">
          <p className="text-slate-400 text-sm">© 2024 Kleio Inc. All rights reserved.</p>
          <div className="flex space-x-4 mt-4 md:mt-0 text-slate-400">
             <Github size={20} className="hover:text-brand-indigo cursor-pointer" />
             <Twitter size={20} className="hover:text-brand-indigo cursor-pointer" />
             <Linkedin size={20} className="hover:text-brand-indigo cursor-pointer" />
          </div>
        </div>
      </div>
    </footer>
  );
};

// -----------------------------------------------------------------------------
// MAIN APP COMPONENT
// -----------------------------------------------------------------------------

export default function Home() {
  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900 antialiased selection:bg-brand-indigo selection:text-white">
      <Navigation />
      <main>
        <Hero />
        <Features />
        <Platforms />
        <TechStack />
        <FooterCTA />
      </main>
      <Footer />
    </div>
  );
}
