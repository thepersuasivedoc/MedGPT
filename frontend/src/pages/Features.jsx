import React, { useEffect } from 'react';
import Navbar from '../components/Navbar';

const Features = () => {
  useEffect(() => {
    document.body.className = 'theme-other';
    // Clean up overflow when leaving
    document.body.style.overflowY = 'auto';
    return () => {
      document.body.style.overflowY = '';
    };
  }, []);

  return (
    <>
      <Navbar />

      <main className="landing-page">
        {/* Hero Section */}
        <section className="hero-section fade-in">
          <div className="pill-badge">Revolutionizing Medical Study</div>
          <h1 className="hero-title">Your Textbooks,<br/><span className="gradient-text">Now Intelligent.</span></h1>
          <p className="hero-subtitle">Stop flipping through thousands of pages. MedGPT uses advanced retrieval-augmented generation to pinpoint exact paragraphs in seconds.</p>
          <a href="/login" className="cta-button">Get Started Now</a>
        </section>

        {/* How it Works Section */}
        <section className="how-it-works fade-in delay-1">
          <h2>How MedGPT Works</h2>
          <div className="steps-container">
            <div className="step-item">
              <div className="step-number">1</div>
              <h3>Upload Knowledge</h3>
              <p>Upload your heavy MBBS PDFs—from Gray's Anatomy to Harrison's. We index every single sentence into our vector database.</p>
            </div>
            <div className="step-item">
              <div className="step-number">2</div>
              <h3>Ask Complex Questions</h3>
              <p>Type in clinical scenarios, dosage queries, or mechanism of action. MedGPT understands the medical context.</p>
            </div>
            <div className="step-item">
              <div className="step-number">3</div>
              <h3>Instant Verified Answers</h3>
              <p>Receive highly accurate answers complete with exact source document citations so you can verify instantly.</p>
            </div>
          </div>
        </section>

        {/* Deep Dive Section */}
        <section className="deep-dive fade-in delay-2">
          <div className="deep-dive-content">
            <h2>Strict Medical Guardrails</h2>
            <p>Unlike generic AI, MedGPT is purpose-built for medical students and professionals. It strictly declines non-medical queries, refuses to hallucinate, and protects its internal configurations.</p>
            <ul className="feature-list">
              <li>✓ Zero Hallucination Mode</li>
              <li>✓ Verified Source Tracking</li>
              <li>✓ Clinical Safety Warnings</li>
            </ul>
          </div>
          <div className="deep-dive-image">
            <div className="mock-chat">
               <div className="mock-msg ai">
                 <strong>MedGPT:</strong> The recommended dosage is 50mg daily.<br/>
                 <span className="sources" style={{ display: 'block', marginTop: '10px' }}>• Harrison's Principles, Page 1204</span>
               </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="landing-footer fade-in delay-2">
        <p>© 2026 MedGPT Technologies. Built for Team Unknown Orchestra.</p>
      </footer>
    </>
  );
};

export default Features;
