# MedAI

MedAI is an agentic RAG application built to serve as a medical learning assistant. It uses LangChain, Ollama, and a local ChromaDB vector store to answer medical queries accurately based on textbooks.

## Key Features

- **Normal Mode**: Fast, accurate responses directly sourced from local medical PDFs with citations.
- **Deep Dive Mode**: Uses structured prompt engineering and visual knowledge graph extraction (via Vis.js) to help learners understand complex physiological and pathophysiological concepts.

## Tech Stack

- **Backend:** FastAPI, LangChain, HuggingFaceEmbeddings, ChromaDB, Ollama
- **Frontend:** Vanilla JS/HTML/CSS, Vite, Vis.js (for static Network Graphs)

## Setup

Please refer to [how to run.md](./how\ to\ run.md) for detailed instructions on getting the project up and running!
