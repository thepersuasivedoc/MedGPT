# MedAI Study Tool — Project Workflow & Build Guide

> **For:** MBBS Student | **Goal:** Personal learning → Business → Instagram content

---

## Project Overview

Three progressively complex versions of the same core idea: turn medical textbooks into interactive, visual, and video-based learning tools.

```
PDFs → RAG Engine → Q&A (V1)
                  → Visual Explainers (V2)
                  → AI Videos for Instagram (V3)
```

---

## Version 1 — PDF Q&A (RAG Chatbot)

### What It Does
Upload your medical textbooks (PDFs), ask any question, get accurate answers with source references.

### How It Works

```
[PDFs] → [Extract Text] → [Chunk Text] → [Embed & Store in Vector DB]
                                                        ↓
                                         [User asks question]
                                                        ↓
                                         [Query → Retrieve relevant chunks]
                                                        ↓
                                         [LLM answers using retrieved context]
```

### Tech Stack

| Component | Tool | Why |
|---|---|---|
| PDF Parsing | `PyMuPDF` or `pdfplumber` | Handles complex medical textbook layouts |
| Text Chunking | `LangChain` or `LlamaIndex` | Smart chunking with overlap |
| Embeddings | `OpenAI text-embedding-3-small` | Cost-effective, high quality |
| Vector DB | `Chroma` (local) → `Pinecone` (prod) | Start free, scale later |
| LLM | `Claude Sonnet` or `GPT-4o` | Strong reasoning for medical content |
| UI | `Streamlit` (fast) or `Gradio` | Get it running in hours, not days |

### Build Steps
1. Install: `pip install langchain chromadb openai pymupdf streamlit`
2. Parse PDFs → extract raw text
3. Chunk text (500–800 tokens, 100 token overlap)
4. Embed chunks → store in Chroma
5. Build retrieval chain with LangChain
6. Wrap in Streamlit UI

### ⚠️ Real Problems to Expect
- Medical textbooks have **images, diagrams, tables** — plain text extraction will miss them
- PDFs with **scanned pages** (many Indian textbooks like Robbins, Gray's) need OCR (`Tesseract` or `AWS Textract`) — adds cost and complexity
- Chunking poorly = garbage answers. Medical content is dense; tuning chunk size matters a lot
- Hallucination risk is real. The model can sound confident and be wrong about drug dosages, mechanisms, etc.

---

## Version 2 — Visual Explainer Generator

### What It Does
Pick a confusing topic → generate a story-style explanation or a flowchart/mind map to understand and retain it.

### How It Works

```
[User selects topic] → [RAG retrieves relevant content from V1]
                                    ↓
              [LLM generates: Story / Analogy / Flowchart / Mnemonics]
                                    ↓
              [Render output: Markdown story OR Mermaid.js diagram]
```

### Output Types

| Format | Tool | Good For |
|---|---|---|
| Story/Analogy | LLM (Claude/GPT-4o) | Pathophysiology, mechanisms |
| Flowchart | `Mermaid.js` rendered in browser | Clinical algorithms, diagnosis |
| Mind Map | `Markmap` or `Obsidian` export | Pharmacology, anatomy groupings |
| Flashcards | `Anki` export format | High-yield revision |

### Build Steps
1. Add a "mode selector" to V1 UI (Q&A / Explain / Visualize)
2. Write prompt templates for each mode:
   - Story mode: *"Explain [topic] as a story where each part of the process is a character..."*
   - Flowchart mode: *"Output a Mermaid.js diagram for the clinical approach to [topic]..."*
3. Render Mermaid diagrams in Streamlit using `streamlit-mermaid`

### ⚠️ Real Problems to Expect
- LLMs generate **medically inaccurate analogies**. A fun story that teaches wrong concepts is worse than no story
- Flowcharts for complex topics (e.g., coagulation cascade) hit Mermaid.js limits fast
- You'll need to **manually verify every output** before using it to learn — time-consuming

---

## Version 3 — AI Video Generator for Instagram

### What It Does
Input: a topic + script style preference → Output: a short educational video for Instagram Reels

### How It Works

```
[Topic from Textbook (V1 context)]
            ↓
[LLM generates: Script + Visual prompts + Voiceover text]
            ↓
      [Split into components]
      /          |          \
[Voiceover]  [Visuals]  [Captions]
(ElevenLabs) (Video AI) (auto-gen)
            ↓
      [Assemble with FFmpeg or Runway]
            ↓
     [Final video: 9:16, 60–90 sec]
```

### Video Generation Tool Comparison

| Tool | Quality | Cost | Control | Medical Content Fit |
|---|---|---|---|---|
| **Higgsfield** | Good | Medium | Limited prompt control | Generic — not built for diagrams/anatomy |
| **Runway ML Gen-3** | Excellent | High | Good | Better for realistic/cinematic |
| **Kling 1.6** | Very Good | Medium-Low | Good | Strong motion, good quality |
| **Pika Labs** | Good | Low | Medium | Good for quick clips |
| **HeyGen** | Good | Medium | High | Best for talking-head explainers |
| **Synthesia** | Good | Medium-High | High | Best for structured medical explainers |

### Honest Recommendation: Don't lead with Higgsfield

**Higgsfield is better for cinematic/aesthetic videos.** For medical education content:

- If you want **talking-head style** (like Dr. Mike, Ninja Nerd): → **HeyGen** or **Synthesia**
- If you want **animated explainers** (like Kurzgesagt-style): → **Runway + custom motion** or **Pictory.ai**
- If you want **diagram-driven content**: → Build in **Canva/Adobe Express API** + static visuals with voiceover
- Higgsfield works if you want **lifestyle/teaser b-roll** over a voiceover, not educational diagrams

**Recommended Stack for Instagram Medical Content:**

```
Script (GPT-4o / Claude) 
    → Voiceover (ElevenLabs) 
    → Visuals (Canva API or HeyGen avatar) 
    → Captions (Captions.ai or auto-subtitle)
    → Final edit (CapCut API or FFmpeg)
```

### Build Steps
1. Build script generator prompt: topic → hook + 3 key points + CTA
2. Integrate ElevenLabs API for voiceover
3. Choose visual approach (avatar vs. animation vs. b-roll)
4. Use FFmpeg to merge audio + visuals + captions
5. Output: MP4, 1080x1920, <90 seconds

### ⚠️ Real Problems to Expect
- AI-generated medical visuals are **often anatomically wrong** — wrong organ placement, wrong structures
- Instagram's algorithm doesn't care about accuracy. Viral ≠ correct. You're a future doctor — this tension is real
- Video generation APIs are **expensive at scale**. One video can cost $2–10 in API calls
- ElevenLabs + Runway + Claude + Pinecone = **4 separate subscriptions** before you've made a rupee
- Copyright: textbook content is copyrighted. Using it verbatim in monetized content is a legal risk
- **MBBS curriculum time** — building this while studying is genuinely hard. Most students abandon it in 2 months

---

## Full Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    MEDAI PLATFORM                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  [Textbook PDFs]                                         │
│       ↓                                                  │
│  [PDF Parser + OCR]  ←── PyMuPDF / Tesseract            │
│       ↓                                                  │
│  [Text Chunker]      ←── LangChain                      │
│       ↓                                                  │
│  [Vector Database]   ←── Chroma (dev) / Pinecone (prod) │
│       ↓                                                  │
│  ┌────────────────────────────────┐                      │
│  │        RAG CORE ENGINE         │                      │
│  │  Retriever + LLM (Claude/GPT)  │                      │
│  └────┬───────────┬───────────────┘                      │
│       ↓           ↓           ↓                          │
│   [Q&A Mode] [Visual Mode] [Video Mode]                  │
│   (V1)       (V2)          (V3)                          │
│                ↓              ↓                          │
│           [Mermaid /    [Script Gen]                     │
│            Stories]         ↓                            │
│                        [Voiceover]  ←── ElevenLabs       │
│                             ↓                            │
│                        [Video AI]   ←── HeyGen/Runway    │
│                             ↓                            │
│                        [Final Video]                     │
│                             ↓                            │
│                        [Instagram]                       │
└─────────────────────────────────────────────────────────┘
```

---

## Build Order (What to Actually Do)

Build in phases. Don't try to build V3 first.

### Phase 1 — Weeks 1–2: Basic RAG (V1)
- [ ] Set up Python env, install LangChain, Chroma, OpenAI
- [ ] Write PDF parser for 2–3 of your textbooks
- [ ] Build basic Q&A chain
- [ ] Streamlit UI with file upload + chat

### Phase 2 — Weeks 3–4: Visual Explainers (V2)
- [ ] Add mode selector to UI
- [ ] Write story + flowchart prompt templates
- [ ] Integrate Mermaid.js rendering
- [ ] Test on 10 topics you personally find confusing

### Phase 3 — Weeks 5–8: Video Pipeline (V3)
- [ ] Pick and test one video tool (start with HeyGen free tier)
- [ ] Script → Voiceover pipeline (ElevenLabs)
- [ ] Manual assembly first (CapCut) before automating
- [ ] Automate with FFmpeg once format is decided

### Phase 4 — Month 3+: Business Layer
- [ ] Deploy on cloud (Railway.app or Render — cheap)
- [ ] Add user auth (Supabase)
- [ ] Monetize: subscription for MBBS students (INR 199–499/month is realistic)
- [ ] Instagram: 3 videos/week minimum to test algorithm

---

## Cost Estimates (Monthly, INR approx.)

| Service | Free Tier | Paid Estimate |
|---|---|---|
| OpenAI API (embeddings + LLM) | $5 free | ₹1,500–4,000 |
| ElevenLabs (voiceover) | 10k chars/month | ₹1,700 (Starter) |
| HeyGen (video) | 1 min/month | ₹4,200 (Basic) |
| Pinecone (vector DB) | 1 index free | ₹0 (free tier ok) |
| Railway/Render (hosting) | 500 hrs free | ₹700–1,500 |
| **Total (basic production)** | | **~₹8,000–12,000/month** |

---

## Honest Business Reality Check

- The **RAG Q&A** market is crowded. Dozens of tools already do this. Your edge has to be **medical specificity and Indian curriculum focus** (MBBS, NEXT exam, clinical cases)
- **Instagram medical education** works but is a long game — 6–12 months before meaningful reach
- Your biggest competitor is YouTube (free, SEO-indexed, long-form). Instagram works for short clips but discovery is harder for niche medical content
- The business moat isn't the tech — it's **your clinical knowledge** to verify outputs and build trust. That's genuinely rare and valuable
- Start **using the tool yourself** before selling it. If it doesn't actually help you study, it won't help others

---

## Recommended Learning Path

1. **Python basics** (if not already) → 2 weeks on YouTube
2. **LangChain RAG tutorial** → official docs, build V1
3. **Prompt engineering** → learn to write reliable medical prompts
4. **API basics** (REST, JSON, authentication) → needed for all integrations
5. **FFmpeg basics** → for video assembly

---

*Built by an MBBS student, for MBBS students. Start small, validate ruthlessly, scale what works.*
