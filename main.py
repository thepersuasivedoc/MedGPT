from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
import uuid
from fastapi.background import BackgroundTasks

# Ensure normal_mode is accessible
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from normal_mode.retriever import build_qa_chain_normal, build_qa_chain_visual_explainer, ask_question
from video_generator.script_gen import generate_script, script_to_voiceover_text
from video_generator.voiceover import generate_voiceover, get_audio_duration
from video_generator.assemble import assemble_full_video
from fastapi.staticfiles import StaticFiles

os.makedirs("outputs", exist_ok=True)

app = FastAPI(title="MedGPT API")
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

# Allow requests from our Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the global QA chains
try:
    chain_normal = build_qa_chain_normal()
    chain_visual_explainer = build_qa_chain_visual_explainer()
except Exception as e:
    print(f"Warning: Could not initialize QA chains. Error: {e}")
    chain_normal = None
    chain_visual_explainer = None

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    chat_history: list[ChatMessage] = []
    mode: str = "normal"

class VideoRequest(BaseModel):
    topic: str
    custom_context: str | None = None
    style: str = "educational"
    duration: int = 60
    voice: str = "male_professional"

@app.post("/api/chat")
async def chat(request: ChatRequest):
    if not chain_normal or not chain_visual_explainer:
        return {"answer": "The QA chains are not initialized.", "sources": []}
        
    # Convert history for Langchain
    lc_history = []
    for msg in request.chat_history:
        role = "human" if msg.role == "user" else "ai"
        lc_history.append((role, msg.content))
        
    # Route to the appropriate model based on mode
    selected_chain = chain_visual_explainer if request.mode == "visual_explainer" else chain_normal
        
    result = ask_question(selected_chain, request.message, lc_history)
    
VIDEO_TASKS = {}

def _run_video_generation(task_id: str, request: VideoRequest):
    try:
        context = request.custom_context if (request.custom_context and request.custom_context.strip()) else None
        
        # 1. Script
        VIDEO_TASKS[task_id] = {"status": "Writing script...", "progress": 20, "done": False}
        script = generate_script(
            request.topic, context=context, duration=request.duration, style=request.style
        )
        
        # 2. Voiceover
        VIDEO_TASKS[task_id] = {"status": "Generating voiceover...", "progress": 50, "done": False}
        vo_text = script_to_voiceover_text(script)
        audio_path = generate_voiceover(vo_text, "outputs/voiceover.mp3", request.voice)
        dur = get_audio_duration(audio_path)
        
        # 3. Assemble
        VIDEO_TASKS[task_id] = {"status": "Assembling video scenes...", "progress": 80, "done": False}
        out_path = "outputs/reel.mp4"
        assemble_full_video(script, audio_path, out_path)
        
        VIDEO_TASKS[task_id] = {
            "status": "Done!",
            "progress": 100,
            "done": True,
            "success": True,
            "video_url": "/outputs/reel.mp4",
            "script": script,
            "duration": dur
        }
    except Exception as e:
        VIDEO_TASKS[task_id] = {
            "status": "Failed",
            "progress": 0,
            "done": True,
            "success": False,
            "error": str(e)
        }

@app.post("/api/generate_video")
def api_generate_video(request: VideoRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    VIDEO_TASKS[task_id] = {"status": "Starting...", "progress": 5, "done": False}
    background_tasks.add_task(_run_video_generation, task_id, request)
    return {"task_id": task_id}

@app.get("/api/video_status/{task_id}")
def api_video_status(task_id: str):
    if task_id not in VIDEO_TASKS:
        return {"status": "Not found", "done": True, "success": False, "error": "Invalid task ID"}
    return VIDEO_TASKS[task_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
