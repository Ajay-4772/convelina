"use client";

import React from "react";
import Navbar from "../components/landing/Navbar";
import Hero from "../components/landing/Hero";
import VideoPlaceholder from "../components/landing/VideoPlaceholder";
import InteractiveShowcaseTabs from "../components/landing/InteractiveShowcaseTabs";
import ProductCapabilities from "../components/landing/ProductCapabilities";
import HowItWorksInteractive from "../components/landing/HowItWorksInteractive";
import FaqSection from "../components/landing/FaqSection";
import PrivacySection from "../components/landing/PrivacySection";
import FinalCTA from "../components/landing/FinalCTA";
import Footer from "../components/landing/Footer";
import SmoothScrollProvider from "../components/ui/SmoothScrollProvider";

export default function LandingPage() {
  return (
    <SmoothScrollProvider>
      <div className="min-h-screen bg-[#faf9f6] text-[#18181b] flex flex-col font-sans selection:bg-[#18181b] selection:text-white">
        <Navbar />

        <main className="flex-1">
          <Hero />
          <VideoPlaceholder />
          <InteractiveShowcaseTabs />
          <ProductCapabilities />
          <HowItWorksInteractive />
          <FaqSection />
          <PrivacySection />
          <FinalCTA />
        </main>

        <Footer />
      </div>
    </SmoothScrollProvider>
  );
}
