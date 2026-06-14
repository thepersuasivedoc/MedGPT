import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const Sidebar = ({ isOpen, toggleSidebar, sessions, currentSessionId, onSelectSession, onNewSession, onDeleteSession }) => {
  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ x: -300, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: -300, opacity: 0 }}
          transition={{ type: 'spring', stiffness: 300, damping: 30 }}
          style={{
            width: '280px',
            backgroundColor: '#09090b',
            borderRight: '1px solid rgba(255,255,255,0.05)',
            display: 'flex',
            flexDirection: 'column',
            height: '100vh',
            position: 'absolute',
            zIndex: 100,
            left: 0,
            top: 0
          }}
        >
          <div style={{ padding: '1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#fce7f3' }}>Chat History</h2>
            <button onClick={toggleSidebar} style={{ background: 'none', border: 'none', color: '#a1a1aa', cursor: 'pointer' }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>
          
          <div style={{ padding: '1rem' }}>
            <button 
              onClick={onNewSession}
              style={{
                width: '100%',
                padding: '0.75rem',
                backgroundColor: 'rgba(236, 72, 153, 0.1)',
                border: '1px solid #ec4899',
                color: '#ec4899',
                borderRadius: '8px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.5rem',
                fontWeight: 'bold'
              }}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="12" y1="5" x2="12" y2="19"></line>
                <line x1="5" y1="12" x2="19" y2="12"></line>
              </svg>
              New Chat
            </button>
          </div>

          <div style={{ flex: 1, overflowY: 'auto', padding: '0 1rem 1rem 1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {sessions.map(session => (
              <div 
                key={session.id}
                onClick={() => onSelectSession(session.id)}
                style={{
                  padding: '0.75rem 1rem',
                  borderRadius: '8px',
                  backgroundColor: currentSessionId === session.id ? 'rgba(255,255,255,0.1)' : 'transparent',
                  color: currentSessionId === session.id ? '#fff' : '#a1a1aa',
                  cursor: 'pointer',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  transition: 'all 0.2s'
                }}
              >
                <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '180px' }}>
                  {session.title || 'New Conversation'}
                </span>
                <button 
                  onClick={(e) => { e.stopPropagation(); onDeleteSession(session.id); }}
                  style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', opacity: 0.7 }}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M3 6h18"></path>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                  </svg>
                </button>
              </div>
            ))}
            {sessions.length === 0 && (
              <p style={{ color: '#71717a', textAlign: 'center', marginTop: '2rem', fontSize: '0.9rem' }}>No past chats yet.</p>
            )}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default Sidebar;
