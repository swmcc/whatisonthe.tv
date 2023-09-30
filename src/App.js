import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import './App.css';
import Search from './Search';
import Footer from './Footer';
import Media from './Media';

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
          <Route path="/media/:id" element={<Media />} />
          <Route path="/" element={<Search />} />
        </Routes>

        <Footer />
      </div>
    </Router>
  );
}

export default App;
