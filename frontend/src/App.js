import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import SearchBar from './components/SearchBar';
import Dashboard from './components/Dashboard';
import VideoAnalysis from './components/VideoAnalysis';
import ChannelAnalysis from './components/ChannelAnalysis';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <header className="App-header">
          <SearchBar />
        </header>
        <main className="App-main">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/analyze/:videoId" element={<VideoAnalysis />} />
            <Route path="/channel/id/:channelId" element={<ChannelAnalysis />} />
            <Route path="/channel/username/:username" element={<ChannelAnalysis />} />
          </Routes>
        </main>
        <footer className="App-footer">
          <p>YouTube Sentiment Analysis Tool &copy; {new Date().getFullYear()}</p>
        </footer>
      </div>
    </Router>
  );
}

export default App;
