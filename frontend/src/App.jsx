import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import PostDetails from './pages/PostDetails';
import ExtractLeads from './pages/ExtractLeads';

function App() {
  return (
    <Router>
      <div className="app">
        <header style={headerStyle}>
          <div className="container" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h1 style={{ color: 'white', fontSize: '24px' }}>
              <Link to="/" style={{ color: 'white', textDecoration: 'none' }}>
                LinkedIn Leads Extractor
              </Link>
            </h1>
            <nav style={{ display: 'flex', gap: '20px' }}>
              <Link to="/" style={navLinkStyle}>Dashboard</Link>
              <Link to="/extract" style={navLinkStyle}>Extract Leads</Link>
            </nav>
          </div>
        </header>

        <main className="container" style={{ marginTop: '30px' }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/extract" element={<ExtractLeads />} />
            <Route path="/posts/:postId" element={<PostDetails />} />
          </Routes>
        </main>

        <footer style={footerStyle}>
          <div className="container" style={{ textAlign: 'center', color: '#666' }}>
            <p>LinkedIn Leads Extractor © 2025 - Powered by Unipile API</p>
          </div>
        </footer>
      </div>
    </Router>
  );
}

const headerStyle = {
  background: 'linear-gradient(135deg, #0a66c2 0%, #004182 100%)',
  padding: '20px 0',
  boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
};

const navLinkStyle = {
  color: 'white',
  textDecoration: 'none',
  fontWeight: '500',
  padding: '8px 16px',
  borderRadius: '6px',
  transition: 'background 0.2s',
};

const footerStyle = {
  marginTop: '60px',
  padding: '20px 0',
  borderTop: '1px solid #eee',
};

export default App;
