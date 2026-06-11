# v2_visual/app.py
#
# V2 — Visual Explainer UI (Streamlit).
# Run with:  streamlit run v2_visual/app.py
#
# Builds on V1: make sure you've ingested PDFs first (python v1_qa/ingest.py).

import os
import re
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import streamlit.components.v1 as components

from v2_visual.explainer import generate_explanation, generate_ideas, get_context_for_topic
from v3_video.script_gen import generate_script, script_to_voiceover_text
from v3_video.voiceover import generate_voiceover
from v3_video.assemble import assemble_full_video

st.set_page_config(
    page_title="MedAI - Visual Explainer",
    page_icon="🧠",
    layout="wide",
)

st.title("🧠 MedAI — Visual Explainer")
st.caption("Turn confusing topics into stories, diagrams, and mnemonics")


def render_mermaid(code: str, height: int = 600):
    """Render a Mermaid diagram client-side via the mermaid.js CDN."""
    html = f"""
    <div class="mermaid">{code}</div>
    <script type="module">
      import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
      mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
    </script>
    """
    components.html(html, height=height, scrolling=True)


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
        }[x],
    )

    use_custom_context = st.checkbox("Use custom context (paste text manually)")

    st.divider()
    st.caption(
        "V2 builds on top of V1. Make sure you've ingested your PDFs first "
        "(`python v1_qa/ingest.py`). Runs locally on Ollama."
    )

# ─── MAIN AREA ────────────────────────────────────────────────────────────────

col1, col2 = st.columns([1, 2])

with col1:
    topic = st.text_area(
        "What topic are you confused about?",
        placeholder=(
            "e.g., Cori Cycle\n"
            "or\n"
            "Difference between Type 1 and Type 2 Hypersensitivity\n"
            "or\n"
            "Renin-Angiotensin-Aldosterone System"
        ),
        height=120,
    )

    if use_custom_context:
        custom_context = st.text_area(
            "Paste relevant text from your textbook:",
            height=200,
            placeholder="Paste the relevant section from your textbook here...",
        )
    else:
        custom_context = None
        st.info("💡 Will auto-retrieve context from your ingested textbooks")

    generate_btn = st.button(
        "Generate Explanation", type="primary", use_container_width=True
    )

    num_ideas = st.number_input(
        "How many ideas?", min_value=2, max_value=5, value=3, step=1
    )
    ideas_btn = st.button(
        f"💡 Generate {int(num_ideas)} Ideas", use_container_width=True
    )


OUTPUT_DIR = "./outputs"
st.session_state.setdefault("v2_videos", {})


def render_result(result: str, mode: str):
    """Render a single explanation, rendering Mermaid for flowchart mode."""
    if mode == "flowchart":
        mermaid_match = re.search(r"```mermaid\n(.*?)```", result, re.DOTALL)
        if mermaid_match:
            mermaid_code = mermaid_match.group(1).strip()
            render_mermaid(mermaid_code)
            with st.expander("View Raw Mermaid Code"):
                st.code(mermaid_code, language="markdown")
        else:
            st.warning("Could not parse a Mermaid diagram. Raw output:")
            st.markdown(result)
    else:
        st.markdown(result)


def make_video(source_text: str, topic: str, key: str) -> str:
    """Turn an explanation/idea into a reel via the V3 pipeline. Returns MP4 path."""
    script = generate_script(topic, context=source_text, duration=60, style="educational")
    audio = generate_voiceover(
        script_to_voiceover_text(script), f"{OUTPUT_DIR}/v2_{key}.mp3"
    )
    return assemble_full_video(script, audio, f"{OUTPUT_DIR}/v2_{key}.mp4")


def render_video_section(source_text: str, topic: str, key: str):
    """A '🎬 Generate this idea into Video' button + cached video player."""
    if st.button("🎬 Generate this idea into Video", key=f"vid_{key}"):
        try:
            with st.spinner("Building reel: script → voiceover → video (~60s)..."):
                path = make_video(source_text, topic, key)
            st.session_state["v2_videos"][key] = path
        except Exception as e:
            st.error(f"Video generation failed: {e}")

    cached = st.session_state["v2_videos"].get(key)
    if cached and os.path.exists(cached):
        st.video(cached)
        with open(cached, "rb") as f:
            st.download_button(
                "⬇️ Download MP4", f,
                file_name=os.path.basename(cached),
                mime="video/mp4", key=f"dl_{key}",
            )


with col2:
    has_custom = bool(custom_context and custom_context.strip())
    has_input = bool(topic and topic.strip()) or has_custom

    # ── Generation: populate session_state (so results survive button reruns) ──
    if (generate_btn or ideas_btn) and not has_input:
        st.warning("Enter a topic or paste custom context first.")
    elif generate_btn or ideas_btn:
        # Topic is optional when custom context is supplied — fall back to the
        # context itself as the subject so the prompt still has something to name.
        effective_topic = (
            topic.strip()
            if (topic and topic.strip())
            else "the concept described in the provided context"
        )
        spinner_label = topic.strip() if (topic and topic.strip()) else "your pasted context"
        context = custom_context if has_custom else get_context_for_topic(effective_topic)

        # A fresh generation invalidates any previously made videos.
        st.session_state["v2_videos"] = {}

        if ideas_btn:
            with st.spinner(f"Generating {int(num_ideas)} {mode} ideas for: {spinner_label}..."):
                ideas = generate_ideas(effective_topic, context, mode, n=int(num_ideas))
            st.session_state.pop("v2_single", None)
            st.session_state["v2_ideas"] = {
                "topic": effective_topic, "label": spinner_label,
                "mode": mode, "items": ideas,
            }
        else:
            with st.spinner(f"Generating {mode} explanation for: {spinner_label}..."):
                result = generate_explanation(effective_topic, context, mode)
            st.session_state.pop("v2_ideas", None)
            st.session_state["v2_single"] = {
                "topic": effective_topic, "label": spinner_label,
                "mode": mode, "text": result,
            }

    # ── Rendering: always read from session_state so it persists across reruns ──
    if "v2_ideas" in st.session_state:
        data = st.session_state["v2_ideas"]
        st.caption(f"{len(data['items'])} idea(s) — pick the framing that clicks, then make it a reel.")
        tabs = st.tabs([f"Idea {i + 1}" for i in range(len(data["items"]))])
        for i, (tab, idea) in enumerate(zip(tabs, data["items"])):
            with tab:
                render_result(idea, data["mode"])
                st.divider()
                render_video_section(idea, data["topic"], f"idea_{i}")
    elif "v2_single" in st.session_state:
        data = st.session_state["v2_single"]
        if data["mode"] == "flowchart":
            st.subheader(f"Flowchart: {data['label']}")
        render_result(data["text"], data["mode"])
        st.divider()
        render_video_section(data["text"], data["topic"], "single")
