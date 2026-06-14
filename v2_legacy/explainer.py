# v2_visual/explainer.py
#
# V2 — Visual Explainer Engine.
# Turns a confusing topic into a story, flowchart, mnemonic, or comparison.
# Builds ON TOP of the V1 RAG engine: it reuses the same local ChromaDB
# vector store for context and a local Ollama model for generation
# (no cloud API keys required — consistent with the rest of this project).

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

from shared.config import MAX_CHUNKS_PER_QUERY
from shared.llm import generate
# Reuse the V1 vector store directly — don't duplicate retrieval logic.
from normal_mode.retriever import vectorstore

load_dotenv()

# ─── PROMPT TEMPLATES ────────────────────────────────────────────────────────

STORY_PROMPT = """You are a brilliant medical educator who explains complex concepts through vivid stories and analogies.
The student is confused about: {topic}

Here is relevant context from their textbook:
{context}

Create a STORY-BASED EXPLANATION that:
1. Uses relatable characters or scenarios (the body as a city, cells as workers, etc.)
2. Covers every key concept in the textbook context
3. Is memorable and slightly dramatic
4. Ends with a 3-bullet "What to Remember" summary
5. Is appropriate for an MBBS student (not too simplified, not too jargon-heavy)

Base every fact on the textbook context above. Be creative. Make it unforgettable.
Respond in clean Markdown.
"""

FLOWCHART_PROMPT = """You are a medical education expert who creates crystal-clear Mermaid.js diagrams.
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

MNEMONIC_PROMPT = """You are a medical mnemonics expert with a talent for creating sticky memory aids.
The student wants mnemonics and memory tricks for: {topic}

Here is relevant context from their textbook:
{context}

Create:
1. **Primary Mnemonic** — An acronym, rhyme, or story that covers the most important points
2. **Visual Association** — A vivid mental image to anchor the concept
3. **Clinical Hook** — A real clinical scenario that makes this impossible to forget
4. **Quick-Fire Facts** — 5 rapid-fire key facts formatted as: ⚡ [fact]
5. **Common Exam Traps** — 2-3 things students frequently get wrong about this topic

Base everything on the textbook context above. Format clearly with headers. Be clever, be memorable.
Respond in clean Markdown.
"""

COMPARE_PROMPT = """You are a medical educator expert at comparing similar concepts that students often confuse.
The student wants to compare/differentiate: {topic}

Here is relevant context from their textbook:
{context}

Create a structured comparison that includes:
1. **The Core Difference** — One sentence that captures the key distinction
2. **Side-by-Side Table** — Format as a markdown table comparing key features
3. **The "If you see X, think Y" Rule** — Clinical triggers for each concept
4. **Memory Trick** — How to never confuse these again
5. **Common Mistakes** — What students get wrong

Base everything on the textbook context above. Be direct and clinically focused.
Respond in clean Markdown.
"""

PROMPT_MAP = {
    "story": STORY_PROMPT,
    "flowchart": FLOWCHART_PROMPT,
    "mnemonic": MNEMONIC_PROMPT,
    "compare": COMPARE_PROMPT,
}


# ─── CONTEXT RETRIEVAL (reuses V1) ──────────────────────────────────────────

def get_context_for_topic(topic: str) -> str:
    """Pull relevant textbook context from the V1 ChromaDB vector store.

    Uses MMR so the chunks are relevant *and* diverse, which gives the
    explainer broader material to work with. Returns "" if nothing is found
    (e.g. no PDFs ingested yet).
    """
    docs = vectorstore.max_marginal_relevance_search(
        f"Explain everything important about: {topic}. "
        "Include mechanisms, clinical features, and key facts.",
        k=MAX_CHUNKS_PER_QUERY,
        fetch_k=MAX_CHUNKS_PER_QUERY * 3,
    )
    if not docs:
        return ""

    context = ""
    for idx, doc in enumerate(docs):
        source = doc.metadata.get("source", "Unknown")
        context += f"--- Document {idx + 1} (Source: {source}) ---\n{doc.page_content}\n\n"
    return context


# ─── GENERATION ─────────────────────────────────────────────────────────────

def generate_explanation(topic: str, context: str, mode: str) -> str:
    """Generate an explanation for `topic` in the requested `mode`.

    Runs fully locally via Ollama (VISUAL_MODEL). `mode` is one of
    story / flowchart / mnemonic / compare.
    """
    if mode not in PROMPT_MAP:
        raise ValueError(
            f"Invalid mode: {mode}. Choose from: {list(PROMPT_MAP.keys())}"
        )

    if not context or not context.strip():
        context = (
            "(No textbook context was retrieved. Explain from general "
            "medical knowledge and clearly note that no source textbook "
            "was available.)"
        )

    prompt = PROMPT_MAP[mode].format(topic=topic, context=context)

    # Flowchart needs to stay literal; the others benefit from a little warmth.
    temperature = 0.3 if mode == "flowchart" else 0.7
    return generate(prompt, temperature=temperature)


IDEA_DELIMITER = "===IDEA==="


def generate_ideas(topic: str, context: str, mode: str, n: int = 3) -> list:
    """Generate `n` DISTINCT variations of an explanation for `topic`.

    Returns a list of strings (one per idea). Each idea takes a deliberately
    different angle so the student can pick the framing that clicks for them.
    """
    if mode not in PROMPT_MAP:
        raise ValueError(
            f"Invalid mode: {mode}. Choose from: {list(PROMPT_MAP.keys())}"
        )
    if not context or not context.strip():
        context = (
            "(No textbook context was retrieved. Explain from general "
            "medical knowledge and clearly note that no source textbook "
            "was available.)"
        )

    base = PROMPT_MAP[mode].format(topic=topic, context=context)
    wrapped = (
        f"{base}\n\n"
        f"---\n"
        f"IMPORTANT: Produce {n} DISTINCT versions of the above, each taking a "
        f"genuinely different angle, analogy, or framing (not minor rewordings). "
        f"Separate every version with a line containing exactly:\n{IDEA_DELIMITER}\n"
        f"Do not add any commentary before the first version or after the last."
    )

    raw = generate(wrapped, temperature=0.9)
    parts = [p.strip() for p in raw.split(IDEA_DELIMITER) if p.strip()]

    # If the model ignored the delimiter, fall back to whatever it returned.
    return parts if parts else [raw.strip()]


def explain(topic: str, mode: str = "story", custom_context: str = None) -> str:
    """Convenience one-shot: retrieve context (unless supplied) and generate."""
    context = custom_context if custom_context else get_context_for_topic(topic)
    return generate_explanation(topic, context, mode)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="MedAI V2 Visual Explainer")
    parser.add_argument("topic", help="Topic to explain")
    parser.add_argument(
        "--mode",
        default="story",
        choices=list(PROMPT_MAP.keys()),
        help="Explanation style",
    )
    args = parser.parse_args()

    print(explain(args.topic, args.mode))
