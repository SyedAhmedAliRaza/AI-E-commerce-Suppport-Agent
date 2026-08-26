import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'TechMania AI | E-Commerce Support Agent & Refund Portal',
  description: 'AI-powered customer support assistant for TechMania. Real-time product lookup, order tracking, .docx policy RAG evaluation, ChromaDB persistent conversation, and automated refund confirmation emails.',
  keywords: ['AI Support Agent', 'TechMania', 'E-Commerce', 'Refund Processing', 'ChromaDB', 'Google Sheets Integration', 'Next.js'],
  authors: [{ name: 'TechMania AI Engineering Team' }],
  viewport: 'width=device-width, initial-scale=1',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet" />
      </head>
      <body className="antialiased selection:bg-cyan-500/30 selection:text-cyan-200">
        {children}
      </body>
    </html>
  );
}
