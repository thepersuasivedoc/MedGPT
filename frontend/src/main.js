import './style.css'

const userNameDisplay = document.getElementById('user-greeting-name');
if (userNameDisplay) {
  const storedName = localStorage.getItem('medai_user_name');
  if (storedName) {
    userNameDisplay.textContent = storedName;
  }
}

const subGreetingDisplay = document.getElementById('sub-greeting-text');
if (subGreetingDisplay) {
  const phrases = [
    "Ask away.",
    "What would you like to explore today?",
    "How can I help you study?",
    "What's on your mind?",
    "Let's dive into your textbooks.",
    "Ready for your next clinical question?"
  ];
  subGreetingDisplay.textContent = phrases[Math.floor(Math.random() * phrases.length)];
}

const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const chatHistory = document.getElementById('chat-history');
const greetingContainer = document.getElementById('greeting-container');
const sendBtn = document.getElementById('send-btn');

let history = [];

// Simple markdown to HTML parser
function parseMarkdown(text) {
  let html = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
  html = html.replace(/\n/g, '<br>');
  return html;
}

function appendMessage(role, content, sources = []) {
  if (greetingContainer && greetingContainer.style.display !== 'none') {
    greetingContainer.style.display = 'none';
    chatHistory.style.display = 'flex';
  }

  const msgDiv = document.createElement('div');
  msgDiv.className = `message ${role}`;
  
  let innerHTML = `<div class="content">${parseMarkdown(content)}</div>`;
  
  if (sources && sources.length > 0) {
    let sourcesHtml = '<div class="sources"><strong>Sources:</strong><br>';
    sources.forEach(src => {
      sourcesHtml += `<span class="source-item">• ${src}</span>`;
    });
    sourcesHtml += '</div>';
    innerHTML += sourcesHtml;
  }
  
  msgDiv.innerHTML = innerHTML;
  chatHistory.appendChild(msgDiv);
  
  // Scroll to bottom
  window.scrollTo(0, document.body.scrollHeight);
}

function appendLoader() {
  const loaderDiv = document.createElement('div');
  loaderDiv.className = 'message ai loader';
  loaderDiv.id = 'typing-loader';
  loaderDiv.innerHTML = `<div class="content"><div class="spinner"></div></div>`;
  chatHistory.appendChild(loaderDiv);
  window.scrollTo(0, document.body.scrollHeight);
}

function removeLoader() {
  const loader = document.getElementById('typing-loader');
  if (loader) loader.remove();
}

chatForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const userMsg = chatInput.value.trim();
  if (!userMsg) return;
  
  // Display user message
  appendMessage('user', userMsg);
  chatInput.value = '';
  
  // Save to history payload
  const currentHistory = [...history];
  history.push({ role: 'user', content: userMsg });
  
  // Display loader
  appendLoader();
  
  try {
    const response = await fetch('http://127.0.0.1:8000/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: userMsg,
        chat_history: currentHistory
      })
    });
    
    if (!response.ok) throw new Error('API Error');
    
    const data = await response.json();
    
    removeLoader();
    appendMessage('ai', data.answer, data.sources);
    
    // Save AI response to history
    history.push({ role: 'ai', content: data.answer });
    
  } catch (err) {
    console.error(err);
    removeLoader();
    appendMessage('ai', '⚠️ Sorry, there was an error connecting to the MedAI server. Ensure the backend is running on port 8000.');
  }
});
