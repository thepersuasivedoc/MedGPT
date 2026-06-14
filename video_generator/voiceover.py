# v3_video/voiceover.py
#
# V3 Step 2 — Text-to-speech voiceover.
# Primary path: ElevenLabs (set ELEVENLABS_API_KEY in .env).
# Offline fallback: macOS `say` → MP3 via ffmpeg, so the pipeline runs
# end-to-end with no cloud key (lower quality, but fully local).

import os
import json
import shutil
import subprocess

import requests
from dotenv import load_dotenv

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
# Treat the .env.example placeholder as "not set".
if ELEVENLABS_API_KEY and "your_" in ELEVENLABS_API_KEY:
    ELEVENLABS_API_KEY = None

# Voice IDs — copy from your ElevenLabs dashboard.
VOICE_IDS = {
    "male_professional": "21m00Tcm4TlvDq8ikWAM",   # Rachel (default)
    "male_energetic": "AZnzlk1XvdvUeBnXmlld",       # Domi
    "female_warm": "EXAVITQu4vr4xnSDxMaL",          # Bella
}

# Microsoft Edge Neural Voices used for the ultra-realistic free tier.
EDGE_VOICES = {
    "male_professional": "en-US-ChristopherNeural",
    "male_energetic": "en-US-GuyNeural",
    "female_warm": "en-US-AriaNeural",
}


def _generate_elevenlabs(text: str, output_path: str, voice: str) -> str:
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
        },
    }
    response = requests.post(url, json=payload, headers=headers, timeout=120)
    if response.status_code != 200:
        raise Exception(
            f"ElevenLabs API error {response.status_code}: {response.text}"
        )
    with open(output_path, "wb") as f:
        f.write(response.content)
    return output_path


def _generate_edge_tts(text: str, output_path: str, voice: str) -> str:
    """Free tier: Ultra-realistic Microsoft Edge Neural TTS."""
    if not shutil.which("edge-tts"):
        # We assume it's installed via pip in the venv, so we can run it with python -m edge_tts
        import sys
        cmd_prefix = [sys.executable, "-m", "edge_tts"]
    else:
        cmd_prefix = ["edge-tts"]
        
    edge_voice = EDGE_VOICES.get(voice, EDGE_VOICES["male_professional"])
    
    subprocess.run([*cmd_prefix, "--voice", edge_voice, "--text", text, "--write-media", output_path], check=True)
    return output_path


def generate_voiceover(
    text: str,
    output_path: str,
    voice: str = "male_professional",
) -> str:
    """Convert `text` to an MP3 at `output_path`.

    Uses ElevenLabs if a key is configured, otherwise the local macOS `say`
    fallback. Returns the output path.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    if ELEVENLABS_API_KEY:
        path = _generate_elevenlabs(text, output_path, voice)
        engine = "ElevenLabs"
    else:
        path = _generate_edge_tts(text, output_path, voice)
        engine = "Microsoft Edge Neural TTS (Free)"

    print(f"Voiceover saved: {path}  [{engine}]")
    return path


def get_audio_duration(audio_path: str) -> float:
    """Audio duration in seconds via ffprobe."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format", audio_path,
        ],
        capture_output=True,
        text=True,
    )
    return float(json.loads(result.stdout)["format"]["duration"])


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="MedAI V3 voiceover generator")
    parser.add_argument("text", help="Text to speak")
    parser.add_argument("--out", default="./outputs/voiceover.mp3")
    parser.add_argument("--voice", default="male_professional", choices=list(VOICE_IDS))
    args = parser.parse_args()

    path = generate_voiceover(args.text, args.out, args.voice)
    print(f"Duration: {get_audio_duration(path):.1f}s")
