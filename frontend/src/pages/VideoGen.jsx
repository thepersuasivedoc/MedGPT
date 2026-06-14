import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import Navbar from '../components/Navbar';

const TypeWriterText = ({ text, speed = 15 }) => {
  const [displayedText, setDisplayedText] = useState('');

  useEffect(() => {
    let i = 0;
    let isCancelled = false;
    
    setDisplayedText('');

    const type = async () => {
      while (i < text.length && !isCancelled) {
        setDisplayedText(prev => prev + text.charAt(i));
        i++;
        await new Promise(r => setTimeout(r, speed));
      }
    };
    
    if (text) type();
    
    return () => { isCancelled = true; };
  }, [text, speed]);

  return <>{displayedText}</>;
};

const VideoGen = () => {
  const location = useLocation();
  const state = location.state || {};

  const [topic, setTopic] = useState(state.topic || '');
  const [style, setStyle] = useState(state.style || 'educational');
  const [voice, setVoice] = useState('male_professional');
  const [duration, setDuration] = useState('60');
  const [context, setContext] = useState(state.context || '');

  const [isLoading, setIsLoading] = useState(false);
  const [statusText, setStatusText] = useState('');
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [audioPreview, setAudioPreview] = useState(null);

  useEffect(() => {
    document.body.className = 'theme-video';
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setResult(null);
    setAudioPreview(null);
    setStatusText("Starting...");

    const payload = {
      topic,
      style,
      voice,
      duration: parseInt(duration, 10),
      custom_context: context || null
    };

    try {
      const response = await fetch('http://127.0.0.1:8000/api/generate_video', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const initData = await response.json();
      if (!initData.task_id) {
        throw new Error(initData.error || "Failed to start generation");
      }
      
      const taskId = initData.task_id;

      while (true) {
        await new Promise(r => setTimeout(r, 1500));
        const statusRes = await fetch(`http://127.0.0.1:8000/api/video_status/${taskId}`);
        const data = await statusRes.json();
        
        setStatusText(data.status || "Building...");
        
        if (data.audio_url && !audioPreview) {
          setAudioPreview(`http://127.0.0.1:8000${data.audio_url}?t=${Date.now()}`);
        }
        
        if (data.done) {
          if (data.success) {
            setResult({
              videoUrl: `http://127.0.0.1:8000${data.video_url}?t=${Date.now()}`,
              title: data.script.title || payload.topic,
              caption: data.script.caption || "",
              hashtags: (data.script.hashtags || []).map(h => `#${h.replace('#', '')}`).join(' ')
            });
          } else {
            setError(data.error);
          }
          break;
        }
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container">
      <Navbar />

      <main className="chat-area" style={{ paddingTop: '2rem' }}>
        <div className="glass-card full-width-card" style={{ maxWidth: '800px', margin: '0 auto' }}>
          <h2>🎬 Video Generator</h2>
          <p style={{ color: '#a1a1aa', margin: '0 0 2rem 0' }}>
            Turn a medical topic into an Instagram Reel script, voiceover, and video.
          </p>
          
          <form id="video-gen-form" onSubmit={handleSubmit}>
            <div className="input-group">
              <label htmlFor="topic">Reel Topic</label>
              <input 
                type="text" 
                id="topic" 
                className="auth-input" 
                placeholder="e.g., Why does diabetes cause nerve damage?" 
                required 
                value={topic}
                onChange={e => setTopic(e.target.value)}
                disabled={isLoading}
              />
            </div>

            <div style={{ display: 'flex', gap: '1rem' }}>
              <div className="input-group" style={{ flex: 1 }}>
                <label htmlFor="style">Video Style</label>
                <select id="style" className="auth-input" value={style} onChange={e => setStyle(e.target.value)} disabled={isLoading}>
                  <option value="educational">Educational</option>
                  <option value="storytelling">Storytelling</option>
                  <option value="myth_busting">Myth Busting</option>
                  <option value="quick_facts">Quick Facts</option>
                  <option value="exam_prep">Exam Prep</option>
                </select>
              </div>
              <div className="input-group" style={{ flex: 1 }}>
                <label htmlFor="voice">Voice</label>
                <select id="voice" className="auth-input" value={voice} onChange={e => setVoice(e.target.value)} disabled={isLoading}>
                  <option value="male_professional">Male Professional</option>
                  <option value="male_energetic">Male Energetic</option>
                  <option value="female_warm">Female Warm</option>
                </select>
              </div>
              <div className="input-group" style={{ flex: 1 }}>
                <label htmlFor="duration">Target Duration</label>
                <select id="duration" className="auth-input" value={duration} onChange={e => setDuration(e.target.value)} disabled={isLoading}>
                  <option value="30">30 seconds</option>
                  <option value="45">45 seconds</option>
                  <option value="60">60 seconds</option>
                  <option value="75">75 seconds</option>
                  <option value="90">90 seconds</option>
                </select>
              </div>
            </div>

            <div className="input-group">
              <label htmlFor="context">Custom Context (Optional)</label>
              <textarea 
                id="context" 
                className="auth-input" 
                rows="4" 
                placeholder="Paste relevant text from your textbook here, or leave blank to auto-retrieve context."
                value={context}
                onChange={e => setContext(e.target.value)}
                disabled={isLoading}
              ></textarea>
            </div>

            <button type="submit" className="primary-btn" disabled={isLoading}>
              {isLoading ? 'Generating...' : 'Generate Reel'}
            </button>
          </form>

          {error && (
            <div style={{ marginTop: '2rem', padding: '1rem', background: 'rgba(239, 68, 68, 0.2)', border: '1px solid #ef4444', borderRadius: '12px' }}>
              <p style={{ color: '#ef4444' }}><strong>Error:</strong> {error}</p>
            </div>
          )}

          {isLoading && (
            <div id="loader" style={{ textAlign: 'center', marginTop: '2rem' }}>
              <div className="spinner" style={{ margin: '0 auto' }}></div>
              <p style={{ marginTop: '1rem', color: '#a1a1aa' }}>{statusText}</p>
              
              {audioPreview && (
                <div style={{ marginTop: '1.5rem', padding: '1.5rem', background: 'rgba(236, 72, 153, 0.1)', border: '1px solid #ec4899', borderRadius: '12px' }}>
                  <p style={{ color: '#ec4899', marginBottom: '1rem', fontWeight: 'bold' }}>🎧 Voiceover Ready! Preview it while the video assembles:</p>
                  <audio controls src={audioPreview} style={{ width: '100%' }}></audio>
                </div>
              )}
            </div>
          )}

          {result && !isLoading && (
            <div id="result-container" style={{ marginTop: '3rem', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '2rem' }}>
              <h3 style={{ color: 'var(--primary-light)', marginBottom: '1.5rem' }}>Your Reel is Ready!</h3>
              
              <video src={result.videoUrl} controls style={{ width: '100%', borderRadius: '12px', marginBottom: '2rem', border: '1px solid rgba(255,255,255,0.1)' }}></video>

              <div style={{ background: 'rgba(0,0,0,0.3)', padding: '1.5rem', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)' }}>
                <h4 style={{ marginBottom: '1rem', color: '#fff' }}>
                  <TypeWriterText text={result.title} speed={30} />
                </h4>
                <p style={{ color: '#e4e4e7', marginBottom: '1rem' }}>
                  <strong>Caption:</strong> <TypeWriterText text={result.caption} speed={15} />
                </p>
                <p style={{ color: 'var(--primary-light)', fontSize: '0.9rem' }}>
                  <TypeWriterText text={result.hashtags} speed={15} />
                </p>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default VideoGen;
