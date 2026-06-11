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

# macOS `say` voices used for the offline fallback.
SAY_VOICES = {
    "male_professional": "Daniel",
    "male_energetic": "Fred",
    "female_warm": "Samantha",
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


def _generate_say(text: str, output_path: str, voice: str) -> str:
    """Offline fallback: macOS `say` → AIFF → MP3 via ffmpeg."""
    if not shutil.which("say"):
        raise RuntimeError(
            "No ELEVENLABS_API_KEY set and macOS `say` is unavailable. "
            "Set ELEVENLABS_API_KEY in .env to generate voiceovers."
        )
    say_voice = SAY_VOICES.get(voice, SAY_VOICES["male_professional"])
    aiff_path = output_path.rsplit(".", 1)[0] + ".aiff"
    subprocess.run(["say", "-v", say_voice, "-o", aiff_path, text], check=True)
    # Convert AIFF → MP3 so downstream ffmpeg assembly is uniform.
    subprocess.run(
        ["ffmpeg", "-y", "-i", aiff_path, output_path],
        check=True,
        capture_output=True,
    )
    os.remove(aiff_path)
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
        path = _generate_say(text, output_path, voice)
        engine = "macOS say (offline fallback)"

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
