async function typeWriter(element, text, speed = 15) {
  element.innerHTML = "";
  for (let i = 0; i < text.length; i++) {
    element.innerHTML += text.charAt(i);
    await new Promise(r => setTimeout(r, speed));
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('video-gen-form');
  const btn = document.getElementById('generate-btn');
  const loader = document.getElementById('loader');
  const loaderText = document.getElementById('loader-text');
  const resultContainer = document.getElementById('result-container');
  
  const outputVideo = document.getElementById('output-video');
  const scriptTitle = document.getElementById('script-title');
  const scriptCaption = document.getElementById('script-caption');
  const scriptHashtags = document.getElementById('script-hashtags');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // UI state
    btn.disabled = true;
    loader.style.display = 'block';
    loaderText.textContent = "Starting...";
    resultContainer.style.display = 'none';
    
    // Clear old text
    scriptTitle.innerHTML = "";
    scriptCaption.innerHTML = "";
    scriptHashtags.innerHTML = "";

    // Get values
    const payload = {
      topic: document.getElementById('topic').value,
      style: document.getElementById('style').value,
      voice: document.getElementById('voice').value,
      duration: parseInt(document.getElementById('duration').value, 10),
      custom_context: document.getElementById('context').value || null
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
      
      // Polling loop
      while (true) {
        await new Promise(r => setTimeout(r, 1500));
        const statusRes = await fetch(`http://127.0.0.1:8000/api/video_status/${taskId}`);
        const data = await statusRes.json();
        
        loaderText.textContent = data.status || "Building...";
        
        if (data.done) {
          if (data.success) {
            outputVideo.src = `http://127.0.0.1:8000${data.video_url}?t=${Date.now()}`;
            resultContainer.style.display = 'block';
            
            const titleTxt = data.script.title || payload.topic;
            const captionTxt = data.script.caption || "";
            const hashTxt = (data.script.hashtags || []).map(h => `#${h.replace('#', '')}`).join(' ');
            
            await typeWriter(scriptTitle, titleTxt, 30);
            await typeWriter(scriptCaption, captionTxt, 15);
            await typeWriter(scriptHashtags, hashTxt, 15);
            
          } else {
            alert("Failed to generate video: " + data.error);
          }
          break; // Exit loop
        }
      }
      
    } catch (error) {
      alert("Error: " + error.message);
    } finally {
      btn.disabled = false;
      loader.style.display = 'none';
    }
  });
});
