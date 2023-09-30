import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import './App.css';
import Search from './Search';
import Footer from './Footer';
import Media from './Media';

import About from './pages/about';
import Changelog from './pages/changelog';
import Privacy from './pages/privacy';

const App = () => {
  return (
    <Router>
      <div className="App">
        <div className="flex justify-center items-center">
          <a href="/">
            <img src="/images/icon.png" alt="whatisonthe.tv" className="object-contain" />
          </a>
        </div>

        <Routes>
          <Route path="/" element={<Search />} />
          <Route path="/media/:id" element={<Media />} />
          <Route path="/about" element={<About />} />
          <Route path="/changelog" element={<Changelog />} />
          <Route path="/privacy" element={<Privacy />} />
        </Routes>

        <Footer />
      </div>
    </Router>
  );
}

export default App;
