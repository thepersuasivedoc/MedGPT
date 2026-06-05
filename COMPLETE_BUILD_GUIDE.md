# MedAI — Complete Build Guide
### All Three Versions: From Zero to Instagram-Ready

> **Prerequisites:** Basic Python knowledge, a code editor (VS Code), terminal access
> **Time to complete V1:** ~2 days | **V2:** ~1 week | **V3:** ~2–3 weeks

---

## Environment Setup (Do This First — All Versions)

### 1. Install Python & Tools

```bash
# Check Python version (need 3.10+)
python --version

# Install pip if missing
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python get-pip.py

# Create virtual environment (do this for every project)
python -m venv medai-env

# Activate it
# Mac/Linux:
source medai-env/bin/activate
# Windows:
medai-env\Scripts\activate
```

### 2. Project Folder Structure

```
medai/
├── .env                    ← API keys go here (NEVER commit this to GitHub)
├── requirements.txt
├── v1_qa/
│   ├── ingest.py           ← PDF parsing + embedding
│   ├── retriever.py        ← Query + retrieve chunks
│   └── app.py              ← Streamlit UI
├── v2_visual/
│   ├── explainer.py        ← Story/flowchart generator
│   └── app.py              ← Extended Streamlit UI
├── v3_video/
│   ├── script_gen.py       ← Script generator
│   ├── voiceover.py        ← ElevenLabs TTS
│   ├── video_gen.py        ← Video API integration
│   └── assemble.py         ← FFmpeg assembly
└── shared/
    └── config.py           ← Shared constants and settings
```

### 3. Get API Keys

Sign up and collect these keys (save all in `.env`):

| Service | Purpose | URL | Free Tier |
|---|---|---|---|
| OpenAI | Embeddings + LLM | platform.openai.com | $5 credit |
| Anthropic | Better LLM for medical | console.anthropic.com | $5 credit |
| ElevenLabs | Text-to-speech | elevenlabs.io | 10k chars/month |
| HeyGen | Video generation | heygen.com | 1 min/month |
| Pinecone | Vector DB (prod) | pinecone.io | 1 free index |

```bash
# .env file — replace with your actual keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
ELEVENLABS_API_KEY=...
HEYGEN_API_KEY=...
PINECONE_API_KEY=...
PINECONE_ENV=us-east-1
```

---

---

# VERSION 1 — PDF Q&A RAG System

---

## V1 Step 1: Install Dependencies

```bash
pip install langchain langchain-openai langchain-community \
            chromadb openai pymupdf pytesseract pillow \
            streamlit python-dotenv tiktoken
```

**If your PDFs are scanned (image-based):**
```bash
# Mac
brew install tesseract

# Ubuntu/Debian
sudo apt install tesseract-ocr

# Windows — download installer from:
# https://github.com/UB-Mannheim/tesseract/wiki
```

---

## V1 Step 2: PDF Parser (`v1_qa/ingest.py`)

This is the most critical piece. Medical textbooks have tables, images, multi-column layouts. This handles all of that.

```python
# v1_qa/ingest.py

import os
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv
import io

load_dotenv()

CHROMA_PATH = "./chroma_db"
PDF_FOLDER = "./pdfs"  # Put your textbook PDFs here


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts text from PDF.
    Falls back to OCR for scanned pages automatically.
    """
    doc = fitz.open(pdf_path)
    all_text = []

    print(f"Processing: {pdf_path} ({len(doc)} pages)")

    for page_num, page in enumerate(doc):
        # Try direct text extraction first
        text = page.get_text("text")

        if len(text.strip()) < 50:
            # Page is likely scanned — use OCR
            print(f"  Page {page_num + 1}: Scanned, using OCR...")
            pix = page.get_pixmap(dpi=300)
            img_bytes = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_bytes))
            text = pytesseract.image_to_string(img, lang="eng")
        else:
            print(f"  Page {page_num + 1}: Text extracted directly")

        # Add page metadata to text
        all_text.append(f"[Page {page_num + 1}]\n{text}\n")

    doc.close()
    return "\n".join(all_text)


def chunk_text(text: str, source_name: str) -> list:
    """
    Splits text into overlapping chunks.
    Medical content is dense — keep chunks smaller with more overlap.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,       # ~400–600 tokens is sweet spot for medical text
        chunk_overlap=120,    # Overlap ensures context isn't cut mid-topic
        separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""],
        length_function=len,
    )
    chunks = splitter.create_documents(
        texts=[text],
        metadatas=[{"source": source_name}]
    )
    print(f"  Created {len(chunks)} chunks from {source_name}")
    return chunks


def ingest_all_pdfs():
    """
    Main function: reads all PDFs, embeds, stores in ChromaDB.
    Run once, then reuse the database.
    """
    if not os.path.exists(PDF_FOLDER):
        os.makedirs(PDF_FOLDER)
        print(f"Created {PDF_FOLDER}/ folder. Add your PDF textbooks there and re-run.")
        return

    pdf_files = [f for f in os.listdir(PDF_FOLDER) if f.endswith(".pdf")]

    if not pdf_files:
        print(f"No PDFs found in {PDF_FOLDER}/")
        return

    all_chunks = []

    for pdf_file in pdf_files:
        pdf_path = os.path.join(PDF_FOLDER, pdf_file)
        print(f"\n{'='*50}")
        print(f"Ingesting: {pdf_file}")
        print(f"{'='*50}")

        raw_text = extract_text_from_pdf(pdf_path)
        chunks = chunk_text(raw_text, source_name=pdf_file)
        all_chunks.extend(chunks)

    print(f"\nTotal chunks to embed: {len(all_chunks)}")
    print("Embedding... (this takes time + costs money, do it once)")

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    # Store in Chroma — creates local folder
    vectorstore = Chroma.from_documents(
        documents=all_chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PATH,
    )

    print(f"\nDone! Vector DB saved to {CHROMA_PATH}/")
    print(f"Total documents stored: {vectorstore._collection.count()}")


if __name__ == "__main__":
    ingest_all_pdfs()
```

**Run it:**
```bash
mkdir pdfs
# Copy your textbook PDFs into the pdfs/ folder
python v1_qa/ingest.py
```

> ⚠️ **Warning:** Embedding a 1000-page textbook costs roughly $0.02–0.05 with `text-embedding-3-small`. Run ingest ONCE and reuse the DB.

---

## V1 Step 3: Retriever (`v1_qa/retriever.py`)

```python
# v1_qa/retriever.py

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()

CHROMA_PATH = "./chroma_db"

MEDICAL_QA_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""
You are a medical education assistant helping an MBBS student understand concepts from their textbooks.

RULES:
- Answer ONLY from the provided context
- If the answer is not in the context, say "This specific information is not in your uploaded textbooks"
- Include the page number or source when possible
- Be concise but complete
- For drug dosages or critical clinical info, always add: "Verify this in your official textbook before clinical use"

CONTEXT FROM TEXTBOOKS:
{context}

STUDENT QUESTION:
{question}

ANSWER:
"""
)


def build_qa_chain():
    """Build the RAG chain. Call once and reuse."""
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    vectorstore = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embeddings,
    )

    retriever = vectorstore.as_retriever(
        search_type="mmr",          # MMR avoids returning duplicate chunks
        search_kwargs={
            "k": 6,                 # Retrieve 6 chunks
            "fetch_k": 20,          # Consider top 20 before diversity filtering
        }
    )

    llm = ChatOpenAI(
        model="gpt-4o-mini",        # Cheaper, still good. Upgrade to gpt-4o if quality drops
        temperature=0,              # 0 = deterministic, critical for factual medical content
        max_tokens=1000,
    )

    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": MEDICAL_QA_PROMPT},
    )

    return chain


def ask_question(chain, question: str) -> dict:
    """Ask a question and return answer + sources."""
    result = chain.invoke({"query": question})

    answer = result["result"]
    sources = list(set([
        doc.metadata.get("source", "Unknown")
        for doc in result["source_documents"]
    ]))

    return {
        "answer": answer,
        "sources": sources,
        "num_chunks_used": len(result["source_documents"])
    }
```

---

## V1 Step 4: Streamlit UI (`v1_qa/app.py`)

```python
# v1_qa/app.py

import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from v1_qa.retriever import build_qa_chain, ask_question

# Page config
st.set_page_config(
    page_title="MedAI - Textbook Q&A",
    page_icon="🩺",
    layout="wide"
)

st.title("🩺 MedAI — Textbook Q&A")
st.caption("Ask anything from your uploaded MBBS textbooks")

# Load chain once per session
@st.cache_resource
def load_chain():
    return build_qa_chain()

# Check if DB exists
if not os.path.exists("./chroma_db"):
    st.error("⚠️ No textbook database found. Run `python v1_qa/ingest.py` first.")
    st.stop()

chain = load_chain()

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg.get("sources"):
            with st.expander("📚 Sources"):
                for src in msg["sources"]:
                    st.caption(f"• {src}")

# Input box
if question := st.chat_input("Ask a question from your textbooks..."):
    # Show user message
    with st.chat_message("user"):
        st.write(question)

    st.session_state.messages.append({"role": "user", "content": question})

    # Get answer
    with st.chat_message("assistant"):
        with st.spinner("Searching your textbooks..."):
            result = ask_question(chain, question)

        st.write(result["answer"])

        with st.expander(f"📚 Sources ({result['num_chunks_used']} chunks used)"):
            for src in result["sources"]:
                st.caption(f"• {src}")

    st.session_state.messages.append({
        "role": "assistant",
        "content": result["answer"],
        "sources": result["sources"]
    })
```

**Run V1:**
```bash
streamlit run v1_qa/app.py
```

---

---

# VERSION 2 — Visual Explainer Generator

---

## V2 Step 1: Additional Dependencies

```bash
pip install anthropic streamlit-mermaid markdown
```

---

## V2 Step 2: The Explainer Engine (`v2_visual/explainer.py`)

This is where the creativity happens. Four output modes, each with a different prompt strategy.

```python
# v2_visual/explainer.py

import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()

# ─── PROMPT TEMPLATES ────────────────────────────────────────────────────────

STORY_PROMPT = """
You are a brilliant medical educator who explains complex concepts through vivid stories and analogies.
The student is confused about: {topic}

Here is relevant context from their textbook:
{context}

Create a STORY-BASED EXPLANATION that:
1. Uses relatable characters or scenarios (the body as a city, cells as workers, etc.)
2. Covers every key concept in the textbook context
3. Is memorable and slightly dramatic
4. Ends with a 3-bullet "What to Remember" summary
5. Is appropriate for an MBBS student (not too simplified, not too jargon-heavy)

Be creative. Make it unforgettable.
"""

FLOWCHART_PROMPT = """
You are a medical education expert who creates crystal-clear Mermaid.js diagrams.
The student wants a flowchart/diagram for: {topic}

Here is relevant context from their textbook:
{context}

Create a Mermaid.js diagram that shows this concept visually.

STRICT RULES for Mermaid syntax:
- Use `flowchart TD` for top-down flow (clinical algorithms, pathophysiology)
- Use `flowchart LR` for left-right progression (mechanisms, cascades)
- Keep node labels SHORT (max 5 words)
- Use these shapes:
  - Rectangle [text] for processes/steps
  - Diamond {{text}} for decisions/conditions
  - Rounded (text) for start/end
  - Parallelogram[/text/] for inputs/outputs
- Add color classes at the end:
  classDef danger fill:#ff6b6b,stroke:#c0392b,color:#fff
  classDef warning fill:#ffd93d,stroke:#f39c12,color:#000
  classDef success fill:#6bcb77,stroke:#27ae60,color:#fff
  classDef info fill:#4d96ff,stroke:#2980b9,color:#fff
- Apply classes: class NodeName danger
- NO special characters inside node labels — use plain English only

Output ONLY the mermaid code block, nothing else.
Start with: ```mermaid
End with: ```
"""

MNEMONIC_PROMPT = """
You are a medical mnemonics expert with a talent for creating sticky memory aids.
The student wants mnemonics and memory tricks for: {topic}

Here is relevant context from their textbook:
{context}

Create:
1. **Primary Mnemonic** — An acronym, rhyme, or story that covers the most important points
2. **Visual Association** — A vivid mental image to anchor the concept
3. **Clinical Hook** — A real clinical scenario that makes this impossible to forget
4. **Quick-Fire Facts** — 5 rapid-fire key facts formatted as: ⚡ [fact]
5. **Common Exam Traps** — 2-3 things students frequently get wrong about this topic

Format clearly with headers. Be clever, be memorable.
"""

COMPARE_PROMPT = """
You are a medical educator expert at comparing similar concepts that students often confuse.
The student wants to compare/differentiate: {topic}

Here is relevant context from their textbook:
{context}

Create a structured comparison that includes:
1. **The Core Difference** — One sentence that captures the key distinction
2. **Side-by-Side Table** — Format as a markdown table comparing key features
3. **The "If you see X, think Y" Rule** — Clinical triggers for each concept
4. **Memory Trick** — How to never confuse these again
5. **Common Mistakes** — What students get wrong

Be direct and clinically focused.
"""


# ─── MAIN FUNCTION ────────────────────────────────────────────────────────────

def generate_explanation(
    topic: str,
    context: str,
    mode: str  # "story", "flowchart", "mnemonic", "compare"
) -> str:
    """
    Generates explanation in the requested mode.
    Uses Claude — better at creative/analytical tasks than GPT for this use case.
    """

    prompt_map = {
        "story": STORY_PROMPT,
        "flowchart": FLOWCHART_PROMPT,
        "mnemonic": MNEMONIC_PROMPT,
        "compare": COMPARE_PROMPT,
    }

    if mode not in prompt_map:
        raise ValueError(f"Invalid mode: {mode}. Choose from: {list(prompt_map.keys())}")

    prompt = prompt_map[mode].format(topic=topic, context=context)

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text


def get_context_for_topic(topic: str, qa_chain) -> str:
    """
    Pulls relevant textbook context using the V1 RAG engine.
    V2 builds ON TOP of V1 — don't duplicate the retrieval logic.
    """
    from v1_qa.retriever import ask_question

    result = ask_question(
        qa_chain,
        f"Explain everything important about: {topic}. Include mechanisms, clinical features, and key facts."
    )
    return result["answer"]
```

---

## V2 Step 3: Extended UI (`v2_visual/app.py`)

```python
# v2_visual/app.py

import streamlit as st
import sys, os, re

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from v1_qa.retriever import build_qa_chain
from v2_visual.explainer import generate_explanation, get_context_for_topic

st.set_page_config(
    page_title="MedAI - Visual Explainer",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 MedAI — Visual Explainer")
st.caption("Turn confusing topics into stories, diagrams, and mnemonics")

@st.cache_resource
def load_chain():
    return build_qa_chain()

chain = load_chain()

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("⚙️ Settings")

    mode = st.radio(
        "Explanation Style",
        options=["story", "flowchart", "mnemonic", "compare"],
        format_func=lambda x: {
            "story": "📖 Story / Analogy",
            "flowchart": "🔀 Flowchart / Diagram",
            "mnemonic": "🧲 Mnemonics & Memory Tricks",
            "compare": "⚖️ Compare & Differentiate",
        }[x]
    )

    use_custom_context = st.checkbox("Use custom context (paste text manually)")

    st.divider()
    st.caption("V2 builds on top of V1. Make sure you've run the PDF ingestor first.")

# ─── MAIN AREA ────────────────────────────────────────────────────────────────

col1, col2 = st.columns([1, 2])

with col1:
    topic = st.text_area(
        "What topic are you confused about?",
        placeholder="e.g., Cori Cycle\nor\nDifference between Type 1 and Type 2 Hypersensitivity\nor\nRenin-Angiotensin-Aldosterone System",
        height=120
    )

    if use_custom_context:
        custom_context = st.text_area(
            "Paste relevant text from your textbook:",
            height=200,
            placeholder="Paste the relevant section from your textbook here..."
        )
    else:
        custom_context = None
        st.info("💡 Will auto-retrieve context from your uploaded textbooks")

    generate_btn = st.button("Generate Explanation", type="primary", use_container_width=True)

with col2:
    if generate_btn and topic:
        with st.spinner(f"Generating {mode} explanation for: {topic}..."):
            # Get context
            if custom_context:
                context = custom_context
            else:
                context = get_context_for_topic(topic, chain)

            # Generate explanation
            result = generate_explanation(topic, context, mode)

        # Render based on mode
        if mode == "flowchart":
            # Extract mermaid code from the response
            mermaid_match = re.search(r'```mermaid\n(.*?)```', result, re.DOTALL)

            if mermaid_match:
                mermaid_code = mermaid_match.group(1).strip()

                st.subheader(f"Flowchart: {topic}")

                # Display the mermaid code for rendering
                st.markdown(f"```mermaid\n{mermaid_code}\n```")

                with st.expander("View Raw Mermaid Code"):
                    st.code(mermaid_code, language="markdown")

                st.caption("💡 Copy the code above to mermaid.live for an interactive version")
            else:
                st.write(result)

        else:
            st.subheader(f"{mode.capitalize()}: {topic}")
            st.markdown(result)

        # Download button
        st.download_button(
            label="📥 Save Explanation",
            data=result,
            file_name=f"{topic.replace(' ', '_')}_{mode}.md",
            mime="text/markdown"
        )

    elif generate_btn and not topic:
        st.warning("Enter a topic first")
    else:
        st.info("👈 Enter a topic and choose an explanation style to get started")
```

**Run V2:**
```bash
streamlit run v2_visual/app.py
```

---

---

# VERSION 3 — AI Video Generator for Instagram

---

## V3 Step 1: Additional Dependencies

```bash
pip install requests anthropic elevenlabs python-dotenv

# FFmpeg (for video assembly)
# Mac:
brew install ffmpeg

# Ubuntu:
sudo apt install ffmpeg

# Windows:
# Download from https://ffmpeg.org/download.html
# Add to PATH
```

---

## V3 Step 2: Script Generator (`v3_video/script_gen.py`)

```python
# v3_video/script_gen.py

import anthropic
import json
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()


INSTAGRAM_SCRIPT_PROMPT = """
You are a medical education content creator writing scripts for Instagram Reels.
Target audience: Medical students, nurses, and health-conscious public in India.
Topic: {topic}

Textbook context:
{context}

Video duration: {duration} seconds
Style: {style}

Create an Instagram Reel script with this EXACT JSON structure:
{{
  "title": "Catchy title for the video (max 8 words)",
  "hook": "First 3 seconds — must stop the scroll. One powerful sentence or question.",
  "segments": [
    {{
      "segment_number": 1,
      "voiceover": "Exact words to be spoken (10-15 seconds worth)",
      "visual_description": "What should appear on screen — be specific",
      "duration_seconds": 12
    }}
  ],
  "outro": "Final 3-5 second call to action",
  "hashtags": ["list", "of", "10", "relevant", "hashtags"],
  "caption": "Instagram caption (150 words max, engaging, ends with question)"
}}

RULES:
- Hook must be a question, shocking fact, or relatable pain point
- Keep medical accuracy — do NOT simplify to the point of being wrong
- Voiceover should sound natural and conversational, not like a textbook
- Visual descriptions should be achievable with AI video tools
- Total voiceover time should match requested duration
- Segments should be 3-5 for a 60-second video

Return ONLY valid JSON. No preamble, no explanation.
"""

VIDEO_STYLES = {
    "educational": "Clear, structured, step-by-step explanation",
    "storytelling": "Narrative-driven with a patient case or scenario",
    "myth_busting": "Start with common misconception, then reveal truth",
    "quick_facts": "Rapid-fire key points, energetic pacing",
    "exam_prep": "High-yield facts, exam tips, clinical correlations"
}


def generate_script(
    topic: str,
    context: str,
    duration: int = 60,
    style: str = "educational"
) -> dict:
    """
    Generates a structured Instagram Reel script.
    Returns a dict with all script components.
    """

    style_description = VIDEO_STYLES.get(style, VIDEO_STYLES["educational"])

    prompt = INSTAGRAM_SCRIPT_PROMPT.format(
        topic=topic,
        context=context,
        duration=duration,
        style=style_description
    )

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()

    # Strip markdown code blocks if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        script = json.loads(raw)
        return script
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print(f"Raw output: {raw}")
        raise ValueError("LLM returned invalid JSON. Try again.")


def script_to_voiceover_text(script: dict) -> str:
    """
    Extracts all voiceover text in sequence for TTS.
    """
    parts = [script["hook"]]

    for segment in script["segments"]:
        parts.append(segment["voiceover"])

    parts.append(script["outro"])

    return " ... ".join(parts)
```

---

## V3 Step 3: Voiceover Generator (`v3_video/voiceover.py`)

```python
# v3_video/voiceover.py

import os
import requests
from dotenv import load_dotenv

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# Voice IDs — copy from ElevenLabs dashboard after signing up
VOICE_IDS = {
    "male_professional": "21m00Tcm4TlvDq8ikWAM",   # Rachel (default)
    "male_energetic": "AZnzlk1XvdvUeBnXmlld",       # Domi
    "female_warm": "EXAVITQu4vr4xnSDxMaL",          # Bella
}


def generate_voiceover(
    text: str,
    output_path: str,
    voice: str = "male_professional",
    speaking_rate: float = 1.0
) -> str:
    """
    Converts text to speech using ElevenLabs.
    Returns path to the generated MP3 file.
    """

    voice_id = VOICE_IDS.get(voice, VOICE_IDS["male_professional"])

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY,
    }

    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",   # Supports Hindi-accented English
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.3,
            "use_speaker_boost": True,
        }
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code != 200:
        raise Exception(f"ElevenLabs API error {response.status_code}: {response.text}")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "wb") as f:
        f.write(response.content)

    print(f"Voiceover saved: {output_path}")
    return output_path


def get_audio_duration(audio_path: str) -> float:
    """Get audio duration in seconds using ffprobe."""
    import subprocess, json

    result = subprocess.run(
        [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format", audio_path
        ],
        capture_output=True, text=True
    )

    data = json.loads(result.stdout)
    return float(data["format"]["duration"])
```

---

## V3 Step 4: Video Generator (`v3_video/video_gen.py`)

This integrates with HeyGen for avatar-based talking head videos. If you want b-roll + voiceover, skip to the FFmpeg assembly.

```python
# v3_video/video_gen.py

import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

HEYGEN_API_KEY = os.getenv("HEYGEN_API_KEY")
HEYGEN_BASE = "https://api.heygen.com"


# ─── HEYGEN AVATAR VIDEO ──────────────────────────────────────────────────────

def create_heygen_video(
    script: dict,
    avatar_id: str = None,   # Get from HeyGen dashboard
    voice_id: str = None,    # Get from HeyGen dashboard
) -> str:
    """
    Creates a talking-head video using HeyGen.
    Returns video_id (poll for completion).
    """

    voiceover_text = " ".join([
        script["hook"],
        *[seg["voiceover"] for seg in script["segments"]],
        script["outro"]
    ])

    # Default to a free HeyGen avatar if none specified
    avatar_id = avatar_id or "Daisy-inskirt-20220818"
    voice_id = voice_id or "2d5b0e6cf36f460aa7fc47e3eee4ba54"  # English male

    headers = {
        "X-Api-Key": HEYGEN_API_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "video_inputs": [{
            "character": {
                "type": "avatar",
                "avatar_id": avatar_id,
                "avatar_style": "normal"
            },
            "voice": {
                "type": "text",
                "input_text": voiceover_text,
                "voice_id": voice_id,
                "speed": 1.0
            },
            "background": {
                "type": "color",
                "value": "#1a1a2e"  # Dark blue — works well for medical content
            }
        }],
        "dimension": {
            "width": 1080,
            "height": 1920    # Vertical 9:16 for Instagram Reels
        },
        "test": True           # Set to False for production (test = watermarked but free)
    }

    response = requests.post(
        f"{HEYGEN_BASE}/v2/video/generate",
        json=payload,
        headers=headers
    )

    if response.status_code != 200:
        raise Exception(f"HeyGen error {response.status_code}: {response.text}")

    video_id = response.json()["data"]["video_id"]
    print(f"Video job started. ID: {video_id}")
    return video_id


def poll_heygen_video(video_id: str, timeout_minutes: int = 10) -> str:
    """
    Polls HeyGen until video is ready. Returns download URL.
    """
    headers = {"X-Api-Key": HEYGEN_API_KEY}
    deadline = time.time() + (timeout_minutes * 60)

    while time.time() < deadline:
        response = requests.get(
            f"{HEYGEN_BASE}/v1/video_status.get?video_id={video_id}",
            headers=headers
        )

        data = response.json()["data"]
        status = data["status"]

        print(f"Status: {status}...")

        if status == "completed":
            video_url = data["video_url"]
            print(f"Video ready: {video_url}")
            return video_url
        elif status == "failed":
            raise Exception(f"Video generation failed: {data.get('error')}")

        time.sleep(15)  # Check every 15 seconds

    raise TimeoutError("Video generation timed out")


def download_video(url: str, output_path: str) -> str:
    """Downloads video from URL to local path."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    response = requests.get(url, stream=True)
    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"Video downloaded: {output_path}")
    return output_path
```

---

## V3 Step 5: Video Assembly with FFmpeg (`v3_video/assemble.py`)

For the alternative approach: voiceover + background video + auto-captions.

```python
# v3_video/assemble.py
# Use this if you DON'T want avatar videos — voiceover over visuals

import os
import subprocess
import json
from dotenv import load_dotenv

load_dotenv()

OUTPUT_DIR = "./outputs"


def create_text_slide(
    text: str,
    output_path: str,
    duration: float,
    background_color: str = "#1a1a2e",
    text_color: str = "white",
    fontsize: int = 60
):
    """
    Creates a simple text slide as a video using FFmpeg.
    Use when you don't have visual assets.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Wrap long text
    wrapped = text.replace("'", "\\'")

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c={background_color}:size=1080x1920:duration={duration}",
        "-vf", (
            f"drawtext=text='{wrapped}'"
            f":fontsize={fontsize}"
            f":fontcolor={text_color}"
            f":x=(w-text_w)/2"
            f":y=(h-text_h)/2"
            f":line_spacing=20"
            f":fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        ),
        "-c:v", "libx264",
        "-t", str(duration),
        output_path
    ]

    subprocess.run(cmd, check=True, capture_output=True)
    return output_path


def add_audio_to_video(video_path: str, audio_path: str, output_path: str) -> str:
    """Merges audio and video. Trims to audio length."""
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",     # Trim to shortest stream
        output_path
    ]

    subprocess.run(cmd, check=True, capture_output=True)
    return output_path


def add_subtitles(video_path: str, subtitle_srt: str, output_path: str) -> str:
    """
    Burn subtitles into video using SRT file.
    Hard-coded subtitles look more professional on Instagram.
    """
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", (
            f"subtitles={subtitle_srt}"
            f":force_style='FontName=Arial,FontSize=24,PrimaryColour=&Hffffff,"
            f"Bold=1,Alignment=2,MarginV=40'"
        ),
        "-c:a", "copy",
        output_path
    ]

    subprocess.run(cmd, check=True, capture_output=True)
    return output_path


def assemble_full_video(script: dict, audio_path: str, output_path: str) -> str:
    """
    Full pipeline: script + audio → final video with text slides + captions.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    temp_segments = []

    # Get audio duration
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", audio_path],
        capture_output=True, text=True
    )
    audio_duration = float(json.loads(result.stdout)["format"]["duration"])

    # Calculate segment durations
    total_segments = len(script["segments"])
    segment_duration = audio_duration / total_segments

    # Create one slide per segment
    for i, segment in enumerate(script["segments"]):
        slide_path = f"{OUTPUT_DIR}/slide_{i}.mp4"
        create_text_slide(
            text=segment["visual_description"][:100],  # Truncate for display
            output_path=slide_path,
            duration=segment_duration
        )
        temp_segments.append(slide_path)

    # Concatenate all slides
    concat_list = f"{OUTPUT_DIR}/concat.txt"
    with open(concat_list, "w") as f:
        for seg in temp_segments:
            f.write(f"file '{os.path.abspath(seg)}'\n")

    combined_video = f"{OUTPUT_DIR}/combined.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list,
        "-c", "copy",
        combined_video
    ], check=True, capture_output=True)

    # Merge with audio
    final = add_audio_to_video(combined_video, audio_path, output_path)

    # Cleanup temp files
    for seg in temp_segments:
        os.remove(seg)
    os.remove(concat_list)
    os.remove(combined_video)

    print(f"Final video: {output_path}")
    return output_path
```

---

## V3 Step 6: Full Pipeline UI (`v3_video/app.py`)

```python
# v3_video/app.py

import streamlit as st
import sys, os, json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from v1_qa.retriever import build_qa_chain
from v2_visual.explainer import get_context_for_topic
from v3_video.script_gen import generate_script, VIDEO_STYLES
from v3_video.voiceover import generate_voiceover, get_audio_duration
from v3_video.video_gen import create_heygen_video, poll_heygen_video, download_video

st.set_page_config(
    page_title="MedAI - Video Generator",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 MedAI — Instagram Video Generator")
st.caption("From textbook topic to Instagram Reel in minutes")

@st.cache_resource
def load_chain():
    return build_qa_chain()

chain = load_chain()

# ─── SIDEBAR SETTINGS ─────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🎬 Video Settings")

    duration = st.slider("Target Duration (seconds)", 30, 90, 60, step=15)

    style = st.selectbox(
        "Video Style",
        options=list(VIDEO_STYLES.keys()),
        format_func=lambda x: x.replace("_", " ").title()
    )

    video_mode = st.radio(
        "Video Type",
        ["Avatar (HeyGen)", "Text Slides (FFmpeg)"],
        help="Avatar = talking head. Text Slides = text + voiceover over background."
    )

    voice = st.selectbox(
        "Voice",
        ["male_professional", "male_energetic", "female_warm"]
    )

# ─── MAIN PIPELINE ────────────────────────────────────────────────────────────
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Enter Topic")
    topic = st.text_input("Medical topic for the video", placeholder="e.g., Mechanism of Action of Beta Blockers")

    custom_context = st.text_area(
        "Custom context (optional — leave empty to auto-retrieve from textbooks)",
        height=100
    )

    generate_script_btn = st.button("📝 Generate Script", type="primary")

with col2:
    st.subheader("2. Review & Edit Script")

    if "script" not in st.session_state:
        st.info("Generate a script first")
    else:
        script = st.session_state.script

        st.write(f"**Hook:** {script['hook']}")

        for seg in script["segments"]:
            with st.expander(f"Segment {seg['segment_number']} ({seg['duration_seconds']}s)"):
                seg["voiceover"] = st.text_area(
                    "Voiceover text:", seg["voiceover"],
                    key=f"vo_{seg['segment_number']}"
                )
                st.caption(f"🎨 Visual: {seg['visual_description']}")

        st.write(f"**Outro:** {script['outro']}")

        with st.expander("📱 Instagram Caption"):
            st.write(script["caption"])
            st.write(" ".join([f"#{h}" for h in script["hashtags"]]))

        create_video_btn = st.button("🎬 Create Video", type="primary")

# ─── Script generation ────────────────────────────────────────────────────────
if generate_script_btn and topic:
    with st.spinner("Retrieving context from textbooks..."):
        context = custom_context if custom_context else get_context_for_topic(topic, chain)

    with st.spinner("Generating script..."):
        script = generate_script(topic, context, duration, style)
        st.session_state.script = script
        st.rerun()

# ─── Video creation ───────────────────────────────────────────────────────────
if "create_video_btn" in dir() and create_video_btn:
    script = st.session_state.script
    output_dir = "./outputs"
    os.makedirs(output_dir, exist_ok=True)

    progress = st.progress(0, "Starting...")

    # Step 1: Voiceover
    from v3_video.script_gen import script_to_voiceover_text
    voiceover_text = script_to_voiceover_text(script)

    audio_path = f"{output_dir}/{topic.replace(' ', '_')}_audio.mp3"

    with st.spinner("Generating voiceover..."):
        generate_voiceover(voiceover_text, audio_path, voice)
    progress.progress(33, "Voiceover done ✅")

    # Step 2: Video
    final_video = f"{output_dir}/{topic.replace(' ', '_')}_final.mp4"

    if video_mode == "Avatar (HeyGen)":
        with st.spinner("Creating avatar video (this takes 2–5 minutes)..."):
            video_id = create_heygen_video(script)
            video_url = poll_heygen_video(video_id)
            download_video(video_url, final_video)
    else:
        from v3_video.assemble import assemble_full_video
        with st.spinner("Assembling video..."):
            assemble_full_video(script, audio_path, final_video)

    progress.progress(100, "Done! ✅")

    # Show download button
    with open(final_video, "rb") as f:
        st.download_button(
            "📥 Download Video",
            data=f,
            file_name=f"{topic.replace(' ', '_')}_reel.mp4",
            mime="video/mp4"
        )

    st.video(final_video)
```

**Run V3:**
```bash
streamlit run v3_video/app.py
```

---

---

# COMBINED: Run All Three Versions Together

Build one unified app that switches between all three modes:

```python
# main_app.py

import streamlit as st

pg = st.navigation([
    st.Page("v1_qa/app.py", title="📚 Textbook Q&A", icon="🩺"),
    st.Page("v2_visual/app.py", title="🧠 Visual Explainer", icon="🧠"),
    st.Page("v3_video/app.py", title="🎬 Video Generator", icon="🎬"),
])

pg.run()
```

```bash
streamlit run main_app.py
```

---

---

# DEPLOYMENT (When Ready to Share)

## Option A — Railway.app (Recommended, Easiest)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# From your project folder
railway init
railway up
```

Add your `.env` keys as environment variables in the Railway dashboard.
Cost: ~₹700/month for basic usage.

## Option B — Render.com

Create a `render.yaml`:
```yaml
services:
  - type: web
    name: medai
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: streamlit run main_app.py --server.port $PORT --server.address 0.0.0.0
```

---

# REQUIREMENTS.TXT (Full)

```txt
langchain==0.3.0
langchain-openai==0.2.0
langchain-community==0.3.0
chromadb==0.5.0
openai==1.45.0
anthropic==0.34.0
pymupdf==1.24.10
pytesseract==0.3.13
pillow==10.4.0
streamlit==1.38.0
python-dotenv==1.0.1
tiktoken==0.7.0
requests==2.32.3
elevenlabs==1.3.0
markdown==3.7
```

---

# COST CONTROL — Critical for MBBS Students

```python
# shared/config.py — hard limits to avoid surprise bills

MAX_TOKENS_PER_RESPONSE = 1000     # Don't let LLM go on forever
MAX_CHUNKS_PER_QUERY = 6           # Fewer chunks = cheaper
EMBEDDING_MODEL = "text-embedding-3-small"  # Not the expensive one
LLM_MODEL = "gpt-4o-mini"          # Cheap, fast, good enough
CLAUDE_MODEL = "claude-haiku-4-5"  # Fastest/cheapest Claude for V2/V3

# Set hard monthly spend limits in:
# OpenAI → platform.openai.com/account/limits
# Anthropic → console.anthropic.com/settings/limits
# Set both to ₹500–1000/month while testing
```

---

# WHAT WILL ACTUALLY GO WRONG (And How to Fix It)

| Problem | When | Fix |
|---|---|---|
| OCR gives garbage text | Scanned PDFs | Use `--psm 6` in Tesseract, or switch to AWS Textract |
| Flowchart renders broken | Complex topics | Simplify node labels, use shorter text |
| LLM gives wrong medical info | Always possible | Add fact-check step: retrieve textbook chunk alongside answer |
| HeyGen video looks stiff | Always | Use "Expressive" mode, shorter sentences in script |
| Audio and video out of sync | FFmpeg assembly | Use `-vsync 2` flag in FFmpeg concat command |
| ChromaDB corrupts | App crashes mid-ingest | Add a `try/except` around ingest, delete `chroma_db/` and re-run |
| Rate limits on APIs | Heavy use | Add `time.sleep(1)` between API calls |
| Instagram removes your video | Copyright | Never use textbook images. Only your generated content |

---

*Build V1 first. Make sure it actually helps you study. Then build V2. Only build V3 if V2 works well.*
*The best medical education tool is the one that's actually accurate. Don't ship something that teaches wrong concepts.*
