import React from 'react';
import { Link, useLocation } from 'react-router-dom';

const Navbar = ({ largeBrand = false }) => {
  const location = useLocation();
  const isChat = location.pathname === '/';
  const isFeatures = location.pathname === '/features';
  const isLogin = location.pathname === '/login';
  const isVideoGen = location.pathname === '/video-gen';

  return (
    <nav className="top-nav">
      <div className={largeBrand ? "brand-large" : "brand"}>✨ MedGPT</div>
      <div className="nav-links flex items-center">
        {!isChat && <Link to="/">Chat App</Link>}
        {!isVideoGen && (
          <Link to="/video-gen" className="nav-video-gen" style={{ fontWeight: 600 }}>
            Video Gen
          </Link>
        )}
        {!isFeatures && <Link to="/features">Features</Link>}
        {!isLogin && <Link to="/login">Login</Link>}
      </div>
    </nav>
  );
};

export default Navbar;
