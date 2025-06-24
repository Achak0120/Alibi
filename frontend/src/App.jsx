import React from 'react';
import { Helmet } from 'react-helmet';
import { Toaster } from '@/components/ui/toaster';
import Header from '@/components/layout/Header';
import Hero from '@/components/sections/Hero';
import TranslationTool from '@/components/sections/TranslationTool';
import DocumentQA from '@/components/sections/DocumentQA';
import Features from '@/components/sections/Features';
import AnimatedBackground from '@/components/layout/AnimatedBackground';

function App() {
  return (
    <>
      <Helmet>
        <title>Alibi - AI Document Translation & Analysis</title>
        <meta name="description" content="Translate legal, medical, and financial documents, then ask questions to get simple, clear answers with Alibi's AI." />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="true" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet" />
      </Helmet>

      <div className="min-h-screen text-foreground relative">
        <AnimatedBackground />
        <Header />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 relative z-10">
          <Hero />
          <TranslationTool />
          <DocumentQA />
          <Features />
        </main>
        <Toaster />
      </div>
    </>
  );
}

export default App;