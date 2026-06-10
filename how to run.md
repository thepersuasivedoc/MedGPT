# How to Run MedAI

Follow these steps to set up and run the MedAI application locally.

### 1. Prerequisites

- **Python 3.10+**
- **Node.js** (for running the Vite frontend)
- **Ollama**: Must be installed and running locally. Ensure you have pulled the required models referenced in `shared/config.py` (e.g., `llama3` or `mistral`).
- Ensure you have PDF textbooks inside the `pdfs/` directory to build your database.

### 2. Set Up the Backend

1. **Install Python dependencies:**
   It is recommended to use a virtual environment.
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables:**
   Copy `.env.example` to `.env` and fill in any required variables.

3. **Initialize ChromaDB (First Time Only):**
   If you have not built your local vector store yet, you will need to process the PDFs in the `pdfs/` folder into `chroma_db/`. (Refer to `COMPLETE_BUILD_GUIDE.md` if there is a specific ingest script for this).

### 3. Run the Application

You will need two separate terminal windows to run the Backend and the Frontend concurrently.

**Terminal 1: Start the Backend API**
```bash
# In the project root directory:
python main.py
```
*The FastAPI backend will start on `http://127.0.0.1:8000`*

**Terminal 2: Start the Frontend App**
```bash
# Open a new terminal and navigate to the frontend directory:
cd frontend

# Install Node modules (first time only):
npm install

# Start the Vite development server:
npm run dev
```
*The frontend UI will be available at `http://localhost:5173` (or whichever port Vite provides).*
