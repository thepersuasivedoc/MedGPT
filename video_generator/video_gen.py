# v3_video/video_gen.py
#
# V3 Step 3 (optional) — HeyGen avatar "talking head" video.
# This is the cloud path and requires HEYGEN_API_KEY in .env.
# If you don't want avatars, skip this and use assemble.py (voiceover + slides).

import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

HEYGEN_API_KEY = os.getenv("HEYGEN_API_KEY")
if HEYGEN_API_KEY and "your_" in HEYGEN_API_KEY:
    HEYGEN_API_KEY = None

HEYGEN_BASE = "https://api.heygen.com"

# A commonly-available default avatar/voice; override from the HeyGen dashboard.
DEFAULT_AVATAR_ID = "Daisy-inskirt-20220818"
DEFAULT_VOICE_ID = "2d5b0e6cf36f460aa7fc47e3eee4ba54"


def _require_key():
    if not HEYGEN_API_KEY:
        raise RuntimeError(
            "HEYGEN_API_KEY is not set. Add it to .env to use the avatar video "
            "path, or use assemble.py for the local voiceover + slides path."
        )


def create_heygen_video(
    script: dict,
    avatar_id: str = None,
    voice_id: str = None,
) -> str:
    """Create a talking-head video from a script dict. Returns a video_id."""
    _require_key()

    voiceover_text = " ".join(
        [
            script.get("hook", ""),
            *[seg.get("voiceover", "") for seg in script.get("segments", [])],
            script.get("outro", ""),
        ]
    ).strip()

    payload = {
        "video_inputs": [
            {
                "character": {
                    "type": "avatar",
                    "avatar_id": avatar_id or DEFAULT_AVATAR_ID,
                    "avatar_style": "normal",
                },
                "voice": {
                    "type": "text",
                    "input_text": voiceover_text,
                    "voice_id": voice_id or DEFAULT_VOICE_ID,
                },
            }
        ],
        # 9:16 for Instagram Reels.
        "dimension": {"width": 1080, "height": 1920},
    }

    response = requests.post(
        f"{HEYGEN_BASE}/v2/video/generate",
        headers={"X-Api-Key": HEYGEN_API_KEY, "Content-Type": "application/json"},
        json=payload,
        timeout=60,
    )
    if response.status_code != 200:
        raise Exception(f"HeyGen error {response.status_code}: {response.text}")

    return response.json()["data"]["video_id"]


def wait_for_video(video_id: str, poll_seconds: int = 10, timeout: int = 900) -> str:
    """Poll HeyGen until the video is ready. Returns the download URL."""
    _require_key()
    deadline = time.time() + timeout

    while time.time() < deadline:
        response = requests.get(
            f"{HEYGEN_BASE}/v1/video_status.get",
            headers={"X-Api-Key": HEYGEN_API_KEY},
            params={"video_id": video_id},
            timeout=60,
        )
        data = response.json().get("data", {})
        status = data.get("status")

        if status == "completed":
            return data["video_url"]
        if status == "failed":
            raise Exception(f"HeyGen video failed: {data.get('error')}")

        time.sleep(poll_seconds)

    raise TimeoutError(f"HeyGen video {video_id} not ready after {timeout}s")


def download_video(url: str, output_path: str) -> str:
    """Download a finished video to disk."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    response = requests.get(url, stream=True, timeout=120)
    response.raise_for_status()
    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    return output_path
