import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';

import Navbar from './components/Navbar';
import Home from './pages/Home';
import Analytics from './pages/Analytics';
import History from './pages/History';
import Health from './pages/Health';

export default function App() {
  return (
    <BrowserRouter>
      {/* Global Toast Provider */}
      <Toaster
        position="bottom-right"
        toastOptions={{
          style: {
            background: 'var(--color-surface-2)',
            color: 'var(--text-primary)',
            border: '1px solid var(--color-border)',
            fontSize: '14px',
          },
          success: {
            iconTheme: {
              primary: 'var(--accent-emerald)',
              secondary: 'white',
            },
          },
        }}
      />

      {/* Navigation */}
      <Navbar />

      {/* Main Content */}
      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/analytics/:shortCode" element={<Analytics />} />
          <Route path="/history" element={<History />} />
          <Route path="/health" element={<Health />} />
          {/* Fallback */}
          <Route path="*" element={<Home />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
}
