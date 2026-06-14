import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import BackgroundMesh from './components/BackgroundMesh';
import Chat from './pages/Chat';
import Features from './pages/Features';
import Login from './pages/Login';
import VideoGen from './pages/VideoGen';

function App() {
  return (
    <Router>
      {/* BackgroundMesh is always rendered globally so it never unmounts/resets */}
      <BackgroundMesh />
      <Routes>
        <Route path="/" element={<Chat />} />
        <Route path="/features" element={<Features />} />
        <Route path="/login" element={<Login />} />
        <Route path="/video-gen" element={<VideoGen />} />
      </Routes>
    </Router>
  );
}

export default App;
