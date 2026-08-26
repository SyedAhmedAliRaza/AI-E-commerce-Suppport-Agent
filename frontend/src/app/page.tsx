'use client';

import React, { useState, useEffect } from 'react';
import { Header } from '@/components/Header';
import { ChatSection } from '@/components/ChatSection';
import { fetchHealth } from '@/lib/api';
import { SystemHealth } from '@/types';

export default function Home() {
  const [health, setHealth] = useState<SystemHealth | null>(null);

  const loadHealth = async () => {
    const data = await fetchHealth();
    setHealth(data);
  };

  useEffect(() => {
    loadHealth();
  }, []);

  return (
    <div className="min-h-screen pb-12">
      <Header health={health} />
      <main className="max-w-7xl mx-auto px-4 lg:px-8">
        <ChatSection />
      </main>
    </div>
  );
}
