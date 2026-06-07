from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os
import sys

# Ensure v1_qa is accessible
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from v1_qa.retriever import build_qa_chain, ask_question

app = FastAPI(title="MedAI API")

# Allow requests from our Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the global QA chain
try:
    chain = build_qa_chain()
except Exception as e:
    print(f"Warning: Could not initialize QA chain. Database might not exist. Error: {e}")
    chain = None

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    chat_history: list[ChatMessage] = []

@app.post("/api/chat")
async def chat(request: ChatRequest):
    if not chain:
        return {"answer": "The QA chain is not initialized. Please ensure the Chroma database is created.", "sources": []}
        
    # Convert history for Langchain
    lc_history = []
    for msg in request.chat_history:
        role = "human" if msg.role == "user" else "ai"
        lc_history.append((role, msg.content))
        
    result = ask_question(chain, request.message, lc_history)
    
    return {
        "answer": result["answer"],
        "sources": result["sources"],
        "num_chunks_used": result["num_chunks_used"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
