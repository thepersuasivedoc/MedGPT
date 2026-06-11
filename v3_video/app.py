# v3_video/app.py
#
# V3 — AI Video Generator UI (Streamlit).
# Run with:  streamlit run v3_video/app.py
#
# Pipeline: topic -> script (Ollama) -> voiceover (ElevenLabs or local say)
#           -> assemble (ffmpeg) -> 9:16 Reel MP4.

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from v3_video.script_gen import generate_script, script_to_voiceover_text, VIDEO_STYLES
from v3_video.voiceover import generate_voiceover, get_audio_duration, VOICE_IDS
from v3_video.assemble import assemble_full_video
from shared.llm import active_backend

OUTPUT_DIR = "./outputs"

st.set_page_config(page_title="MedAI - AI Video Generator", page_icon="🎬", layout="wide")
st.title("🎬 MedAI — AI Video Generator")
st.caption("Turn a topic into an Instagram Reel: script → voiceover → video")

with st.sidebar:
    st.header("⚙️ Settings")
    style = st.selectbox(
        "Video Style",
        options=list(VIDEO_STYLES.keys()),
        format_func=lambda s: s.replace("_", " ").title(),
    )
    duration = st.slider("Target duration (seconds)", 30, 90, 60, step=15)
    voice = st.selectbox(
        "Voice", options=list(VOICE_IDS.keys()),
        format_func=lambda v: v.replace("_", " ").title(),
    )
    eleven = bool(os.getenv("ELEVENLABS_API_KEY") and "your_" not in os.getenv("ELEVENLABS_API_KEY", ""))
    st.caption(
        f"Voiceover engine: {'ElevenLabs' if eleven else 'macOS say (offline fallback)'}"
    )
    st.caption(f"Script engine: {active_backend()}")
    st.divider()
    st.caption("Builds on V1. Ingest PDFs first for grounded scripts.")

topic = st.text_input("Reel topic", placeholder="e.g., Why does diabetes cause nerve damage?")

use_custom_context = st.checkbox("Use custom context (paste text manually)")
if use_custom_context:
    custom_context = st.text_area(
        "Paste relevant text from your textbook:",
        height=200,
        placeholder="Paste the section you want the reel based on here...",
    )
else:
    custom_context = None
    st.info("💡 Will auto-retrieve context from your ingested textbooks")

if st.button("Generate Reel", type="primary"):
    if not topic.strip():
        st.warning("Enter a topic first.")
        st.stop()

    context = custom_context if (custom_context and custom_context.strip()) else None

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1) Script
    with st.spinner("Writing the script..."):
        try:
            script = generate_script(
                topic, context=context, duration=duration, style=style
            )
        except Exception as e:
            st.error(f"Script generation failed: {e}")
            st.stop()

    st.subheader(script.get("title", topic))
    st.markdown(f"**Hook:** {script.get('hook', '')}")
    with st.expander("Full script JSON"):
        st.json(script)

    # 2) Voiceover
    with st.spinner("Generating voiceover..."):
        try:
            vo_text = script_to_voiceover_text(script)
            audio_path = generate_voiceover(vo_text, f"{OUTPUT_DIR}/voiceover.mp3", voice)
            dur = get_audio_duration(audio_path)
        except Exception as e:
            st.error(f"Voiceover failed: {e}")
            st.stop()
    st.audio(audio_path)
    st.caption(f"Voiceover length: {dur:.1f}s")

    # 3) Assemble
    with st.spinner("Assembling video with ffmpeg..."):
        try:
            out_path = f"{OUTPUT_DIR}/reel.mp4"
            assemble_full_video(script, audio_path, out_path)
        except Exception as e:
            st.error(f"Assembly failed: {e}")
            st.stop()

    st.success("Reel ready!")
    st.video(out_path)

    # Caption + hashtags for posting
    st.text_area("Caption", script.get("caption", ""), height=120)
    st.code(" ".join(f"#{h.lstrip('#')}" for h in script.get("hashtags", [])))
    with open(out_path, "rb") as f:
        st.download_button("Download MP4", f, file_name="reel.mp4", mime="video/mp4")
