import React, { useState, useEffect, useRef } from 'react';
import Navbar from '../components/Navbar';
import { Network } from 'vis-network';
import ReactMarkdown from 'react-markdown';
import mermaid from 'mermaid';
import { useNavigate } from 'react-router-dom';
import html2pdf from 'html2pdf.js';
import { motion, AnimatePresence } from 'framer-motion';
import Sidebar from '../components/Sidebar';

const MermaidRenderer = ({ chart }) => {
  const ref = useRef(null);

  useEffect(() => {
    mermaid.initialize({ startOnLoad: true, theme: 'dark' });
    if (ref.current && chart) {
      mermaid.render(`mermaid-${Math.random().toString(36).substring(7)}`, chart)
        .then(({ svg }) => {
          ref.current.innerHTML = svg;
        })
        .catch((e) => {
          console.error("Mermaid parsing failed", e);
          ref.current.innerHTML = `<pre style="color: red;">Mermaid error: ${e.message}</pre><pre>${chart}</pre>`;
        });
    }
  }, [chart]);

  return <div ref={ref} className="mermaid-container" style={{ background: 'rgba(0,0,0,0.5)', padding: '1rem', borderRadius: '12px', marginTop: '1rem' }} />;
};

const ResultView = ({ result, mode }) => {
  if (mode === 'flowchart') {
    const match = result.match(/```mermaid\n([\s\S]*?)```/);
    const chart = match ? match[1].trim() : result;
    return <MermaidRenderer chart={chart} />;
  }
  return (
    <div className="markdown-body" style={{ color: '#e4e4e7', lineHeight: '1.6', marginTop: '1rem' }}>
      <ReactMarkdown>{result}</ReactMarkdown>
    </div>
  );
};

function parseMarkdownAndExtractJSON(text) {
  if (typeof text !== 'string') {
    text = String(text || '');
  }
  let graphJSON = null;
  const jsonRegex = /```json\s*([\s\S]*?)\s*```/i;
  const match = text.match(jsonRegex);
  
  if (match && match[1]) {
    try {
      graphJSON = JSON.parse(match[1]);
      text = text.replace(jsonRegex, '');
    } catch (e) {
      console.error("Failed to parse JSON graph data", e);
    }
  }

  let html = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
  html = html.replace(/\n/g, '<br>');

  return { html, graphJSON };
}

const VisNetwork = ({ graphJSON, onNodeClick }) => {
  const containerRef = useRef(null);
  
  useEffect(() => {
    if (!containerRef.current || !graphJSON) return;

    if (!Array.isArray(graphJSON.nodes) || !Array.isArray(graphJSON.edges)) {
      console.error("Invalid graphJSON format: nodes and edges must be arrays", graphJSON);
      return;
    }

    const primaryColor = getComputedStyle(document.body).getPropertyValue('--primary-color').trim() || '#10b981';
    const primaryBg = getComputedStyle(document.body).getPropertyValue('--primary-bg').trim() || 'rgba(16, 185, 129, 0.2)';
    const primaryLight = getComputedStyle(document.body).getPropertyValue('--primary-light').trim() || '#34d399';
    const gradStart = getComputedStyle(document.body).getPropertyValue('--gradient-start').trim() || '#06b6d4';
    
    const options = {
      nodes: {
        shape: 'box',
        borderWidth: 2,
        margin: 10,
        color: {
          background: 'rgba(24, 24, 27, 0.9)',
          border: primaryColor,
          highlight: { background: primaryColor, border: '#ffffff' },
          hover: { background: primaryBg, border: primaryLight }
        },
        font: { color: '#ffffff', face: 'Outfit', size: 16 },
        shadow: { enabled: true, color: primaryBg, size: 10, x: 0, y: 0 }
      },
      edges: {
        width: 2,
        color: { color: '#3f3f46', highlight: primaryColor, hover: gradStart },
        arrows: { to: { enabled: true, scaleFactor: 0.5 } },
        smooth: { type: 'cubicBezier' }
      },
      layout: {
        hierarchical: {
          enabled: true,
          direction: 'UD',
          sortMethod: 'directed',
          nodeSpacing: 150,
          levelSeparation: 150
        }
      },
      physics: { enabled: false },
      interaction: {
        hover: true,
        tooltipDelay: 100,
        zoomView: false,
        dragView: false,
        dragNodes: false,
        selectable: true
      }
    };

    let network;
    try {
      network = new Network(containerRef.current, graphJSON, options);
      
      network.on("click", function (params) {
        if (params.nodes.length > 0) {
          const nodeId = params.nodes[0];
          const node = graphJSON.nodes.find(n => n.id == nodeId);
          if (node && onNodeClick) {
            onNodeClick(`Tell me more about ${node.label}`);
          }
        }
      });
    } catch (e) {
      console.error("Failed to initialize VisNetwork", e);
    }

    return () => {
      if (network) network.destroy();
    };
  }, [graphJSON, onNodeClick]);

  return <div className="vis-network-wrapper"><div ref={containerRef} className="vis-network-container"></div></div>;
};

const TypeWriterMessage = ({ htmlString, speed = 15, onComplete }) => {
  const [displayedHtml, setDisplayedHtml] = useState('');

  useEffect(() => {
    let i = 0;
    let isTag = false;
    let text = "";
    let isCancelled = false;

    const type = async () => {
      while (i < htmlString.length && !isCancelled) {
        let char = htmlString.charAt(i);
        if (char === '<') isTag = true;
        
        text += char;
        i++;
        
        if (char === '>') {
          isTag = false;
          continue;
        }
        
        if (!isTag) {
          setDisplayedHtml(text);
          window.scrollTo(0, document.body.scrollHeight);
          await new Promise(r => setTimeout(r, speed));
        }
      }
      if (!isCancelled) {
        setDisplayedHtml(htmlString);
        if (onComplete) onComplete();
      }
    };
    
    type();
    
    return () => { isCancelled = true; };
  }, [htmlString, speed]);

  return <div className="content" dangerouslySetInnerHTML={{ __html: displayedHtml }} />;
};

const Chat = () => {
  const navigate = useNavigate();
  const [mode, setMode] = useState('normal');
  const [explainerStyle, setExplainerStyle] = useState('auto');
  const [numIdeas, setNumIdeas] = useState(1);
  const [outputFormat, setOutputFormat] = useState('video');
  const [generatingSlides, setGeneratingSlides] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [hasStarted, setHasStarted] = useState(false);
  
  // Sidebar and Session state
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [sessions, setSessions] = useState(() => {
    const saved = localStorage.getItem('medai_sessions');
    return saved ? JSON.parse(saved) : [];
  });
  const [currentSessionId, setCurrentSessionId] = useState(() => `session_${Date.now()}`);
  
  const userName = localStorage.getItem('medai_user_name') || 'Karthikeyan';

  useEffect(() => {
    // Save session whenever messages change
    if (messages.length > 0) {
      setSessions(prev => {
        const existing = prev.find(s => s.id === currentSessionId);
        let title = existing?.title;
        // Generate title from first user message if not set
        if (!title) {
          const firstUserMsg = messages.find(m => m.role === 'user');
          title = firstUserMsg ? firstUserMsg.content.substring(0, 30) + '...' : 'New Chat';
        }
        
        const newSession = { id: currentSessionId, title, messages, mode, explainerStyle };
        const filtered = prev.filter(s => s.id !== currentSessionId);
        const updated = [newSession, ...filtered];
        localStorage.setItem('medai_sessions', JSON.stringify(updated));
        return updated;
      });
    }
  }, [messages, currentSessionId, mode, explainerStyle]);

  useEffect(() => {
    // Clear chat history when switching modes
    setMessages([]);
    setHasStarted(false);
    setInput('');
    setCurrentSessionId(`session_${Date.now()}`);

    if (mode === 'normal') {
      document.body.className = 'theme-normal';
    } else if (mode === 'visual_explainer') {
      document.body.className = 'theme-visual';
    } else if (mode === 'visual_idea_generator') {
      document.body.className = 'theme-idea-generator';
    }
  }, [mode]);

  const loadSession = (id) => {
    const session = sessions.find(s => s.id === id);
    if (session) {
      setCurrentSessionId(session.id);
      setMessages(session.messages || []);
      setHasStarted((session.messages || []).length > 0);
      if (session.mode) setMode(session.mode);
      if (session.explainerStyle) setExplainerStyle(session.explainerStyle);
      setIsSidebarOpen(false);
    }
  };

  const startNewSession = () => {
    setCurrentSessionId(`session_${Date.now()}`);
    setMessages([]);
    setHasStarted(false);
    setInput('');
    setIsSidebarOpen(false);
  };

  const deleteSession = (id) => {
    setSessions(prev => {
      const updated = prev.filter(s => s.id !== id);
      localStorage.setItem('medai_sessions', JSON.stringify(updated));
      return updated;
    });
    if (currentSessionId === id) {
      startNewSession();
    }
  };

  const goToVideoGen = (sourceText, generatedTopic) => {
    navigate('/video-gen', {
      state: {
        topic: generatedTopic,
        context: sourceText,
        style: 'educational'
      }
    });
  };

  const handleGenerateSlides = async (text) => {
    setGeneratingSlides(true);
    try {
      const response = await fetch('http://localhost:8000/api/generate_slides', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      });
      const data = await response.json();
      if (data.success && data.download_url) {
        const link = document.createElement('a');
        link.href = `http://localhost:8000${data.download_url}`;
        link.setAttribute('download', '');
        document.body.appendChild(link);
        link.click();
        link.parentNode.removeChild(link);
      } else {
        alert("Slide generation failed: " + (data.error || "Unknown error"));
      }
    } catch (err) {
      console.error(err);
      alert("Error calling slide generator.");
    } finally {
      setGeneratingSlides(false);
    }
  };

  const exportPDF = () => {
    const element = document.getElementById('chat-history-content');
    if (!element) return;
    
    // Create a wrapper to add some padding for the PDF
    const wrapper = document.createElement('div');
    wrapper.style.padding = '20px';
    wrapper.style.background = '#09090b';
    wrapper.style.color = '#e4e4e7';
    wrapper.innerHTML = element.innerHTML;
    
    const opt = {
      margin:       10,
      filename:     'MedicinaI_Study_Guide.pdf',
      image:        { type: 'jpeg', quality: 0.98 },
      html2canvas:  { scale: 2, useCORS: true, backgroundColor: '#09090b' },
      jsPDF:        { unit: 'mm', format: 'a4', orientation: 'portrait' }
    };
    html2pdf().set(opt).from(wrapper).save();
  };

  const handleSend = async (e, forcedInput = null) => {
    if (e) e.preventDefault();
    const userMsg = forcedInput || input.trim();
    if (!userMsg) return;

    if (!hasStarted) setHasStarted(true);

    const newMessages = [...messages, { role: 'user', content: userMsg }];
    setMessages(newMessages);
    setInput('');
    setIsLoading(true);

    try {
      if (mode === 'visual_idea_generator') {
        const endpoint = numIdeas > 1 ? '/api/generate_ideas' : '/api/generate_explanation';
        const payload = {
          topic: userMsg,
          mode: explainerStyle === 'auto' ? 'story' : explainerStyle,
          custom_context: null
        };
        if (numIdeas > 1) payload.num_ideas = parseInt(numIdeas, 10);

        const response = await fetch(`http://127.0.0.1:8000${endpoint}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        if (!response.ok) throw new Error('API Error');
        const data = await response.json();
        if (!data.success) throw new Error(data.error);

        setMessages(prev => [...prev, { 
          role: 'ai', 
          isExplainer: true,
          explainerStyle: payload.mode,
          topic: data.topic,
          content: numIdeas > 1 ? '' : data.result,
          ideas: numIdeas > 1 ? data.ideas : null
        }]);

      } else {
        const response = await fetch('http://127.0.0.1:8000/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: userMsg,
            chat_history: messages.map(m => ({ role: m.role, content: m.rawContent || m.content })),
            mode: mode
          })
        });

        if (!response.ok) throw new Error('API Error');

        // Prepare an empty AI message to stream into
        setMessages(prev => [...prev, { role: 'ai', content: '', sources: [] }]);
        setIsLoading(false); // We got response headers, start streaming

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let done = false;

        while (!done) {
          const { value, done: doneReading } = await reader.read();
          done = doneReading;
          if (value) {
            const chunkValue = decoder.decode(value, { stream: true });
            const lines = chunkValue.split('\n').filter(line => line.trim() !== '');
            for (const line of lines) {
              try {
                const data = JSON.parse(line);
                if (data.type === 'chunk') {
                  setMessages(prev => {
                    const newMessages = [...prev];
                    const lastMsg = newMessages[newMessages.length - 1];
                    lastMsg.content += data.content;
                    lastMsg.rawContent = lastMsg.content;
                    return newMessages;
                  });
                } else if (data.type === 'done') {
                  setMessages(prev => {
                    const newMessages = [...prev];
                    const lastMsg = newMessages[newMessages.length - 1];
                    lastMsg.sources = data.sources;
                    return newMessages;
                  });
                }
              } catch (e) {
                // Ignore split JSON chunks, the browser streams can sometimes split lines
              }
            }
          }
        }
      }
    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, { id: Date.now(), sender: 'ai', text: "Sorry, I encountered an error." }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container" style={{ display: 'flex' }}>
      <Sidebar 
        isOpen={isSidebarOpen} 
        toggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
        sessions={sessions}
        currentSessionId={currentSessionId}
        onSelectSession={loadSession}
        onNewSession={startNewSession}
        onDeleteSession={deleteSession}
      />
      
      <div style={{ flex: 1, position: 'relative', display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
        <Navbar />
        
        <button 
          onClick={() => setIsSidebarOpen(true)}
          style={{
            position: 'absolute',
            top: '20px',
            left: '20px',
            zIndex: 50,
            background: 'rgba(0,0,0,0.5)',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: '8px',
            padding: '0.5rem',
            color: '#fff',
            cursor: 'pointer',
            backdropFilter: 'blur(10px)'
          }}
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="3" y1="12" x2="21" y2="12"></line>
            <line x1="3" y1="6" x2="21" y2="6"></line>
            <line x1="3" y1="18" x2="21" y2="18"></line>
          </svg>
        </button>

        <main className="chat-area" id="chat-area">
        <AnimatePresence>
          {!hasStarted && (
            <motion.div 
              className="greeting-container" 
              id="greeting-container"
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -30 }}
              transition={{ duration: 0.5 }}
            >
              <h1 className="greeting-text">
                Hi <span>{userName}</span>,<br />
                <span className="sub-greeting">What would you like to explore today?</span>
              </h1>
            </motion.div>
          )}
        </AnimatePresence>

        {hasStarted && (
          <button 
            onClick={exportPDF}
            style={{
              position: 'absolute',
              top: '80px',
              right: '2rem',
              zIndex: 50,
              padding: '0.6rem 1.2rem',
              backgroundColor: 'rgba(236, 72, 153, 0.1)',
              border: '1px solid #ec4899',
              color: '#fce7f3',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              cursor: 'pointer',
              fontWeight: 500,
              backdropFilter: 'blur(10px)',
              boxShadow: '0 4px 12px rgba(236, 72, 153, 0.2)'
            }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="7 10 12 15 17 10"></polyline>
              <line x1="12" y1="15" x2="12" y2="3"></line>
            </svg>
            Export PDF
          </button>
        )}

        <div className="chat-history" id="chat-history-content" style={{ display: hasStarted ? 'flex' : 'none', width: '100%' }}>
          <AnimatePresence>
            {messages.map((msg, idx) => {
              const { html, graphJSON } = parseMarkdownAndExtractJSON(msg.content || "");
              return (
                <motion.div 
                  key={idx} 
                  className={`message ${msg.role}`}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.4 }}
                >
                {msg.isExplainer ? (
                  <div style={{ width: '100%' }}>
                    {msg.ideas ? (
                      <div>
                        <p style={{ color: '#a1a1aa', marginBottom: '1rem' }}>Generated {msg.ideas.length} ideas:</p>
                        {msg.ideas.map((idea, i) => (
                          <div key={i} style={{ marginBottom: '2rem', padding: '1.5rem', background: 'rgba(0,0,0,0.3)', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)' }}>
                            <h4 style={{ color: 'var(--primary-light)', marginBottom: '0.5rem' }}>Option {i + 1}</h4>
                            <ResultView result={idea} mode={msg.explainerStyle} />
                            {outputFormat === 'video' ? (
                              <button 
                                className="auth-btn" 
                                style={{ width: '100%', marginTop: '1rem' }}
                                onClick={() => {
                                  navigate('/video-gen', { 
                                    state: { 
                                      topic: msg.topic || "Generated idea", 
                                      context: idea 
                                    } 
                                  });
                                }}
                              >
                                🎬 Generate this idea into Video
                              </button>
                            ) : (
                              <button 
                                className="auth-btn" 
                                style={{ width: '100%', marginTop: '1rem', backgroundColor: '#ec4899', borderColor: '#ec4899' }}
                                onClick={() => handleGenerateSlides(idea)}
                                disabled={generatingSlides}
                              >
                                {generatingSlides ? "⏳ Generating Slides..." : "📊 Generate Slides (ZIP)"}
                              </button>
                            )}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div style={{ padding: '0.5rem', width: '100%' }}>
                        <ResultView result={msg.content} mode={msg.explainerStyle} />
                        {outputFormat === 'video' ? (
                          <button 
                            className="auth-btn" 
                            style={{ width: '100%', marginTop: '1rem' }}
                            onClick={() => {
                              navigate('/video-gen', { 
                                state: { 
                                  topic: msg.topic || "Generated idea", 
                                  context: msg.content 
                                } 
                              });
                            }}
                          >
                            🎬 Generate this idea into Video
                          </button>
                        ) : (
                          <button 
                            className="auth-btn" 
                            style={{ width: '100%', marginTop: '1rem', backgroundColor: '#ec4899', borderColor: '#ec4899' }}
                            onClick={() => handleGenerateSlides(msg.content)}
                            disabled={generatingSlides}
                          >
                            {generatingSlides ? "⏳ Generating Slides..." : "📊 Generate Slides (ZIP)"}
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                ) : msg.role === 'ai' ? (
                  <TypeWriterMessage htmlString={html} onComplete={() => {
                    setTimeout(() => window.scrollTo(0, document.body.scrollHeight), 100);
                  }} />
                ) : (
                  <div className="content" dangerouslySetInnerHTML={{ __html: html }} />
                )}
                
                {msg.sources && msg.sources.length > 0 && (
                  <div className="sources">
                    <strong>Sources:</strong><br/>
                    {msg.sources.map((src, i) => <span key={i} className="source-item">• {src}</span>)}
                  </div>
                )}
                
                {graphJSON && (
                  <VisNetwork 
                    graphJSON={graphJSON} 
                    onNodeClick={(followUp) => handleSend(null, followUp)} 
                  />
                )}
              </motion.div>
            );
          })}
          
          {isLoading && (
            <motion.div 
              className="message ai loader" 
              id="typing-loader"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <div className="content"><div className="spinner"></div></div>
            </motion.div>
          )}
          </AnimatePresence>
        </div>
      </main>

      <div className="input-wrapper">
        <motion.div 
          className="input-island"
          layout
          transition={{ type: "spring", stiffness: 300, damping: 30 }}
        >
          <AnimatePresence mode="popLayout">
            {mode === 'visual_idea_generator' && (
              <motion.div 
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.3 }}
                style={{ display: 'flex', gap: '1rem', width: '100%', alignItems: 'center', overflow: 'hidden' }}
              >
              <div className="input-group" style={{ flex: 2, marginBottom: 0 }}>
                <select value={explainerStyle} onChange={e => setExplainerStyle(e.target.value)} className="auth-input" style={{ padding: '0.75rem', fontSize: '0.95rem' }}>
                  <option value="auto">🤖 Auto (Agentic RAG)</option>
                  <option value="professional">🩺 Professional / Clinical</option>
                  <option value="educational">🎓 Educational / Step-by-Step</option>
                  <option value="story">📖 Story / Analogy</option>
                  <option value="flowchart">🔀 Flowchart / Diagram</option>
                  <option value="mnemonic">🧲 Mnemonics & Memory Tricks</option>
                  <option value="compare">⚖️ Compare & Differentiate</option>
                </select>
              </div>
              <div className="input-group" style={{ flex: 1, marginBottom: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <label style={{ margin: 0, color: '#a1a1aa', whiteSpace: 'nowrap' }}>💡 Generate Ideas:</label>
                <select 
                  value={numIdeas} 
                  onChange={e => setNumIdeas(e.target.value)}
                  className="auth-input" 
                  style={{ padding: '0.75rem', marginBottom: 0 }}
                >
                  <option value="1">1 (Single Explanation)</option>
                  <option value="2">2 Ideas</option>
                  <option value="3">3 Ideas</option>
                  <option value="4">4 Ideas</option>
                  <option value="5">5 Ideas</option>
                </select>
              </div>
              <div className="input-group" style={{ flex: 1, marginBottom: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <label style={{ margin: 0, color: '#a1a1aa', whiteSpace: 'nowrap' }}>Output Format:</label>
                <select 
                  value={outputFormat} 
                  onChange={e => setOutputFormat(e.target.value)}
                  className="auth-input" 
                  style={{ padding: '0.75rem', marginBottom: 0 }}
                >
                  <option value="video">🎬 Video</option>
                  <option value="slides">📊 Slides</option>
                </select>
              </div>
            </motion.div>
          )}
          </AnimatePresence>
          <div style={{ display: 'flex', width: '100%', gap: '1rem', alignItems: 'center' }}>
            <div className="mode-select-container">
              <select value={mode} onChange={(e) => setMode(e.target.value)} className="mode-select">
                <option value="normal" className="mode-normal">Normal Mode</option>
                <option value="visual_explainer" className="mode-visual">Visual Explainer</option>
                <option value="visual_idea_generator" className="mode-idea-generator">Idea Generator</option>
              </select>
            </div>
            <form className="chat-input-form" onSubmit={(e) => handleSend(e)} style={{ flex: 1 }}>
              <input 
                type="text" 
                id="chat-input" 
                placeholder="Ask MedGPT" 
                autoComplete="off"
                autoFocus
                value={input}
                onChange={(e) => setInput(e.target.value)}
              />
              <button type="submit" id="send-btn" disabled={isLoading}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="12" y1="19" x2="12" y2="5"></line>
                  <polyline points="5 12 12 5 19 12"></polyline>
                </svg>
              </button>
            </form>
          </div>
        </motion.div>
      </div>
      </div>
    </div>
  );
};

export default Chat;
