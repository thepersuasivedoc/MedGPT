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
from slide_generator.generator import generate_slide_structure
from slide_generator.renderer import create_slide_zip
from fastapi.staticfiles import StaticFiles
from visual_explainer.explainer import generate_explanation, generate_ideas, get_context_for_topic

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

class ExplanationRequest(BaseModel):
    topic: str
    mode: str = "story"
    custom_context: str | None = None

class IdeasRequest(BaseModel):
    topic: str
    mode: str = "story"
    custom_context: str | None = None
    num_ideas: int = 3

class SlideRequest(BaseModel):
    text: str

from fastapi.responses import StreamingResponse

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
        
    from normal_mode.retriever import ask_question_stream
    return StreamingResponse(
        ask_question_stream(selected_chain, request.message, lc_history),
        media_type="text/event-stream"
    )

@app.post("/api/generate_explanation")
async def api_generate_explanation(request: ExplanationRequest):
    try:
        topic = request.topic.strip() if request.topic.strip() else "the concept described in the provided context"
        context = request.custom_context if (request.custom_context and request.custom_context.strip()) else get_context_for_topic(topic)
        result = generate_explanation(topic, context, request.mode)
        return {"success": True, "result": result, "topic": topic}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/generate_ideas")
async def api_generate_ideas(request: IdeasRequest):
    try:
        topic = request.topic.strip() if request.topic.strip() else "the concept described in the provided context"
        context = request.custom_context if (request.custom_context and request.custom_context.strip()) else get_context_for_topic(topic)
        ideas = generate_ideas(topic, context, request.mode, n=request.num_ideas)
        return {"success": True, "ideas": ideas, "topic": topic}
    except Exception as e:
        return {"success": False, "error": str(e)}

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
        VIDEO_TASKS[task_id] = {
            "status": "Assembling video scenes...", 
            "progress": 80, 
            "done": False,
            "audio_url": "/outputs/voiceover.mp3"
        }
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

@app.post("/api/generate_slides")
async def api_generate_slides(request: SlideRequest):
    try:
        # Generate the JSON structure
        slides_data = generate_slide_structure(request.text)
        
        # Render and Zip
        zip_filename = f"slides_{uuid.uuid4().hex[:8]}.zip"
        zip_path = create_slide_zip(slides_data, zip_filename)
        
        return {"success": True, "download_url": f"/outputs/slides/{zip_filename}"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
