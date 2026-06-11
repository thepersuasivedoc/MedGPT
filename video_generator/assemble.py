# v3_video/assemble.py
#
# V3 Step 4 — Local video assembly with FFmpeg.
# Builds a 9:16 Instagram Reel from a script + voiceover audio:
# one text slide per segment, concatenated, then merged with the audio.
# Fully local — no cloud keys needed.

import os
import json
import textwrap
import subprocess
import urllib.parse
import requests
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

load_dotenv()

OUTPUT_DIR = "./outputs"

# Pick the first font that exists on this machine (macOS-first, Linux fallback).
_FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/Arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def _load_font(fontsize: int) -> ImageFont.FreeTypeFont:
    for path in _FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, fontsize)
            except OSError:
                continue
    return ImageFont.load_default()


def create_text_slide(
    text: str,
    output_path: str,
    duration: float,
    background_color: str = "#1a1a2e",
    text_color: str = "white",
    fontsize: int = 56,
) -> str:
    """Render a centered, word-wrapped text slide as a 1080x1920 MP4.

    The text is drawn with Pillow (this avoids depending on an ffmpeg build
    with the `drawtext`/libfreetype filter), saved as a PNG, then looped into
    a short video clip by ffmpeg.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    W, H = 1080, 1920
    
    # 1. Fetch dynamic AI background based on the visual description
    safe_prompt = urllib.parse.quote(text[:150])
    img_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width={W}&height={H}&nologo=true"
    try:
        resp = requests.get(img_url, timeout=30)
        resp.raise_for_status()
        img = Image.open(BytesIO(resp.content)).convert("RGBA")
    except Exception as e:
        print(f"Fallback background due to: {e}")
        img = Image.new("RGBA", (W, H), background_color)

    # 2. Add dark overlay for text readability
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 170))
    img = Image.alpha_composite(img, overlay).convert("RGB")
    
    draw = ImageDraw.Draw(img)
    font = _load_font(fontsize)

    lines = textwrap.wrap(text, width=24) or [" "]
    line_h = fontsize + 18
    block_h = line_h * len(lines)
    y = (H - block_h) // 2
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        draw.text(((W - line_w) // 2, y), line, fill=text_color, font=font)
        y += line_h

    png_path = output_path + ".png"
    img.save(png_path)

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", png_path,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-t", str(duration),
        "-r", "25",
        output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    os.remove(png_path)
    return output_path


def add_audio_to_video(video_path: str, audio_path: str, output_path: str) -> str:
    """Merge audio onto video, trimming to the shortest stream."""
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return output_path


def _audio_duration(audio_path: str) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", audio_path],
        capture_output=True,
        text=True,
    )
    return float(json.loads(result.stdout)["format"]["duration"])


def assemble_full_video(script: dict, audio_path: str, output_path: str) -> str:
    """Full local pipeline: script + voiceover audio → final Reel MP4.

    Slide durations are distributed proportionally to each segment's declared
    `duration_seconds` so the visuals track the narration length.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    segments = script.get("segments", [])
    if not segments:
        raise ValueError("Script has no segments to render.")

    audio_duration = _audio_duration(audio_path)

    # Weight slide durations by each segment's requested length.
    weights = [max(float(s.get("duration_seconds", 1)), 0.1) for s in segments]
    total_weight = sum(weights)
    durations = [audio_duration * w / total_weight for w in weights]

    temp_segments = []
    for i, (segment, dur) in enumerate(zip(segments, durations)):
        slide_path = f"{OUTPUT_DIR}/slide_{i}.mp4"
        create_text_slide(
            text=segment.get("visual_description", "")[:120],
            output_path=slide_path,
            duration=round(dur, 2),
        )
        temp_segments.append(slide_path)

    # Concatenate slides.
    concat_list = f"{OUTPUT_DIR}/concat.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for seg in temp_segments:
            f.write(f"file '{os.path.abspath(seg)}'\n")

    combined_video = f"{OUTPUT_DIR}/combined.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list, "-c", "copy", combined_video],
        check=True,
        capture_output=True,
    )

    final = add_audio_to_video(combined_video, audio_path, output_path)

    # Cleanup temp artifacts.
    for seg in temp_segments:
        os.remove(seg)
    os.remove(concat_list)
    os.remove(combined_video)

    print(f"Final video: {output_path}")
    return final
