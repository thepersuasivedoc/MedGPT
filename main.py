from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os
import sys

# Ensure v1_qa is accessible
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from v1_qa.retriever import build_qa_chain_normal, build_qa_chain_deep_dive, ask_question

app = FastAPI(title="MedAI API")

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
    chain_deep_dive = build_qa_chain_deep_dive()
except Exception as e:
    print(f"Warning: Could not initialize QA chains. Error: {e}")
    chain_normal = None
    chain_deep_dive = None

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    chat_history: list[ChatMessage] = []
    mode: str = "normal"

@app.post("/api/chat")
async def chat(request: ChatRequest):
    if not chain_normal or not chain_deep_dive:
        return {"answer": "The QA chains are not initialized.", "sources": []}
        
    # Convert history for Langchain
    lc_history = []
    for msg in request.chat_history:
        role = "human" if msg.role == "user" else "ai"
        lc_history.append((role, msg.content))
        
    # Route to the appropriate model based on mode
    selected_chain = chain_deep_dive if request.mode == "deep_dive" else chain_normal
        
    result = ask_question(selected_chain, request.message, lc_history)
    
    return {
        "answer": result["answer"],
        "sources": result["sources"],
        "num_chunks_used": result["num_chunks_used"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
