import React from 'react';
import { BrowserRouter as Router, Route, Routes, useLocation } from 'react-router-dom';
import './App.css';

import Search from './Search';
import Sha from './Sha';
import Footer from './Footer';
import Media from './Media';

import About from './pages/about';
import Changelog from './pages/changelog';
import Privacy from './pages/privacy';

const MainContent = () => {
  const location = useLocation();

  const showHeaderFooter = location.pathname !== '/sha';

  return (

    <div className="App">
      {showHeaderFooter && (
        <div className="flex justify-center items-center">
          <a href="/">
            <img src="/images/icon.png" alt="whatisonthe.tv" className="object-contain" />
          </a>
        </div>
      )}

      <Routes>
        <Route path="/" element={<Search />} />
        <Route path="/media/:id" element={<Media />} />
        <Route path="/about" element={<About />} />
        <Route path="/changelog" element={<Changelog />} />
        <Route path="/privacy" element={<Privacy />} />
        <Route path="/sha" element={<Sha />} />
      </Routes>

      {showHeaderFooter && <Footer />}
    </div>

  );
}

const App = () => {
  return (
    <Router>
      <MainContent />
    </Router>
  );
}

export default App;
