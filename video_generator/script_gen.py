# v3_video/script_gen.py
#
# V3 Step 1 — Instagram Reel script generator.
# Produces a structured JSON script (hook / segments / outro / hashtags / caption)
# from a topic, grounded in the V1 textbook context.
#
# Runs locally on Ollama (no cloud key required), consistent with V1/V2.

import os
import re
import sys
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

from shared.config import MAX_CHUNKS_PER_QUERY
from shared.llm import generate
from normal_mode.retriever import vectorstore

load_dotenv()

INSTAGRAM_SCRIPT_PROMPT = """You are a medical education content creator writing scripts for Instagram Reels.
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

Return ONLY valid JSON. No preamble, no explanation, no <think> blocks.
"""

VIDEO_STYLES = {
    "educational": "Clear, structured, step-by-step explanation",
    "storytelling": "Narrative-driven with a patient case or scenario",
    "myth_busting": "Start with common misconception, then reveal truth",
    "quick_facts": "Rapid-fire key points, energetic pacing",
    "exam_prep": "High-yield facts, exam tips, clinical correlations",
}


def get_context_for_topic(topic: str) -> str:
    """Pull relevant textbook context from the V1 ChromaDB vector store."""
    docs = vectorstore.max_marginal_relevance_search(
        f"Key facts, mechanisms and clinical features of: {topic}",
        k=MAX_CHUNKS_PER_QUERY,
        fetch_k=MAX_CHUNKS_PER_QUERY * 3,
    )
    if not docs:
        return ""
    return "\n\n".join(
        f"--- Document {i + 1} (Source: {d.metadata.get('source', 'Unknown')}) ---\n{d.page_content}"
        for i, d in enumerate(docs)
    )


def _extract_json(raw: str) -> str:
    """Pull the JSON object out of a model response.

    Local models (qwen3) may wrap output in ```json fences or emit <think>
    reasoning first. Strip both, then grab the outermost {...} block.
    """
    # Drop any <think>...</think> reasoning blocks.
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()

    # Prefer a fenced ```json block if present.
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", raw, re.DOTALL)
    if fenced:
        return fenced.group(1)

    # Otherwise take the first balanced-looking top-level object.
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        return raw[start : end + 1]
    return raw


def generate_script(
    topic: str,
    context: str = None,
    duration: int = 60,
    style: str = "educational",
) -> dict:
    """Generate a structured Instagram Reel script as a dict.

    If `context` is None, it is auto-retrieved from the V1 vector store.
    """
    if context is None:
        context = get_context_for_topic(topic)
    if not context or not context.strip():
        context = (
            "(No textbook context retrieved — use accurate general medical "
            "knowledge and keep it factually correct.)"
        )

    style_description = VIDEO_STYLES.get(style, VIDEO_STYLES["educational"])
    prompt = INSTAGRAM_SCRIPT_PROMPT.format(
        topic=topic,
        context=context,
        duration=duration,
        style=style_description,
    )

    # temperature 0 → more reliable JSON (applies to the Ollama backend)
    raw = generate(prompt, temperature=0)

    cleaned = _extract_json(raw)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Model returned invalid JSON ({e}). Raw output:\n{raw[:1000]}"
        )


def script_to_voiceover_text(script: dict) -> str:
    """Flatten hook + segments + outro into one TTS-ready string."""
    parts = [script.get("hook", "")]
    parts += [seg.get("voiceover", "") for seg in script.get("segments", [])]
    parts.append(script.get("outro", ""))
    return " ... ".join(p for p in parts if p)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="MedAI V3 Instagram script generator")
    parser.add_argument("topic", help="Topic for the reel")
    parser.add_argument("--duration", type=int, default=60)
    parser.add_argument("--style", default="educational", choices=list(VIDEO_STYLES))
    args = parser.parse_args()

    script = generate_script(args.topic, duration=args.duration, style=args.style)
    print(json.dumps(script, indent=2, ensure_ascii=False))
