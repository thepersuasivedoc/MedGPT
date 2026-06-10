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
let networkCounter = 0;

function parseMarkdownAndExtractJSON(text) {
  let graphJSON = null;
  
  // Extract json blocks (e.g. ```json ... ```)
  const jsonRegex = /```json\s*([\s\S]*?)\s*```/i;
  const match = text.match(jsonRegex);
  
  if (match && match[1]) {
    try {
      graphJSON = JSON.parse(match[1]);
      // Remove the JSON block from the text so it isn't displayed as raw text
      text = text.replace(jsonRegex, '');
    } catch (e) {
      console.error("Failed to parse JSON graph data", e);
    }
  }

  // Parse remaining text as simple markdown
  let html = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
  html = html.replace(/\n/g, '<br>');

  return { html, graphJSON };
}

async function appendMessage(role, content, sources = []) {
  if (greetingContainer && greetingContainer.style.display !== 'none') {
    greetingContainer.style.display = 'none';
    chatHistory.style.display = 'flex';
  }

  const msgDiv = document.createElement('div');
  msgDiv.className = `message ${role}`;
  
  const { html, graphJSON } = parseMarkdownAndExtractJSON(content);
  
  let innerHTML = `<div class="content">${html}</div>`;
  
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
  
  // If we found a JSON graph representation, render it using Vis.js
  if (graphJSON && window.vis) {
    networkCounter++;
    const containerId = `vis-network-${networkCounter}`;
    
    // Create container element
    const containerWrapper = document.createElement('div');
    containerWrapper.className = 'vis-network-wrapper';
    containerWrapper.innerHTML = `<div id="${containerId}" class="vis-network-container"></div>`;
    msgDiv.querySelector('.content').appendChild(containerWrapper);
    
    const container = document.getElementById(containerId);
    
    const options = {
      nodes: {
        shape: 'box',
        borderWidth: 2,
        margin: 10,
        color: {
          background: 'rgba(24, 24, 27, 0.9)',
          border: '#10b981',
          highlight: { background: '#10b981', border: '#ffffff' },
          hover: { background: 'rgba(16, 185, 129, 0.2)', border: '#34d399' }
        },
        font: { color: '#ffffff', face: 'Outfit', size: 16 },
        shadow: { enabled: true, color: 'rgba(16, 185, 129, 0.2)', size: 10, x: 0, y: 0 }
      },
      edges: {
        width: 2,
        color: { color: '#3f3f46', highlight: '#10b981', hover: '#06b6d4' },
        arrows: { to: { enabled: true, scaleFactor: 0.5 } },
        smooth: { type: 'cubicBezier' }
      },
      physics: {
        enabled: true,
        solver: 'forceAtlas2Based',
        forceAtlas2Based: { gravitationalConstant: -50, centralGravity: 0.01, springLength: 100, springConstant: 0.08 }
      },
      interaction: {
        hover: true,
        tooltipDelay: 100,
        zoomView: true,
        dragView: true
      }
    };
    
    // Initialize the network
    try {
      const network = new window.vis.Network(container, graphJSON, options);
      
      // Add click listener to ask follow up questions on node click
      network.on("click", function (params) {
        if (params.nodes.length > 0) {
          const nodeId = params.nodes[0];
          const node = graphJSON.nodes.find(n => n.id == nodeId);
          if (node) {
            chatInput.value = `Tell me more about ${node.label}`;
            chatInput.focus();
          }
        }
      });
    } catch (e) {
      console.error("Vis.js rendering error:", e);
      containerWrapper.innerHTML = `<div class="error-fallback">🎨 <em>Oops, couldn't draw the graph!</em></div>`;
    }
  }
  
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

chatInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    e.preventDefault();
    sendBtn.click();
  }
});

chatForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const userMsg = chatInput.value.trim();
  if (!userMsg) return;
  
  appendMessage('user', userMsg);
  chatInput.value = '';
  
  const currentHistory = [...history];
  history.push({ role: 'user', content: userMsg });
  
  appendLoader();
  
  const deepDiveToggle = document.getElementById('deep-dive-toggle');
  const mode = deepDiveToggle && deepDiveToggle.checked ? "deep_dive" : "normal";
  
  try {
    const response = await fetch('http://127.0.0.1:8000/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: userMsg, // Sent raw, without appending [DEEP_DIVE_MODE]
        chat_history: currentHistory,
        mode: mode
      })
    });
    
    if (!response.ok) throw new Error('API Error');
    
    const data = await response.json();
    
    removeLoader();
    await appendMessage('ai', data.answer, data.sources);
    
    history.push({ role: 'ai', content: data.answer });
    
  } catch (err) {
    console.error(err);
    removeLoader();
    appendMessage('ai', '⚠️ Sorry, there was an error connecting to the MedAI server.');
  }
});
