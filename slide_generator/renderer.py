import os
import zipfile
import textwrap
import urllib.parse
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = "./outputs/slides"

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

def render_slide(slide_data: dict, output_path: str, w=1080, h=1080):
    """Renders a single 1080x1080 slide and saves it to output_path."""
    text = slide_data.get("text", "")
    prompt = slide_data.get("image_prompt", "medical background")
    slide_type = slide_data.get("type", "text")
    code = slide_data.get("code", "")

    safe_prompt = urllib.parse.quote(prompt)
    img_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width={w}&height={h}&nologo=true"
    
    try:
        resp = requests.get(img_url, timeout=15)
        resp.raise_for_status()
        img = Image.open(BytesIO(resp.content)).convert("RGBA")
    except Exception as e:
        print(f"Fallback background due to: {e}")
        img = Image.new("RGBA", (w, h), "#1a1a2e")

    # Dark overlay to make text readable
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 180))
    img = Image.alpha_composite(img, overlay).convert("RGB")
    
    draw = ImageDraw.Draw(img)
    
    if slide_type == "flowchart" and code:
        import base64
        try:
            # Get transparent mermaid image
            encoded = base64.b64encode(code.encode('utf-8')).decode('utf-8')
            mermaid_url = f"https://mermaid.ink/img/{encoded}?bgColor=!transparent"
            mr = requests.get(mermaid_url, timeout=15)
            mr.raise_for_status()
            flowchart_img = Image.open(BytesIO(mr.content)).convert("RGBA")
            
            # Resize flowchart to fit within canvas with padding
            max_w = w - 100
            max_h = h - 250
            fw, fh = flowchart_img.size
            ratio = min(max_w / fw, max_h / fh)
            new_fw = int(fw * ratio)
            new_fh = int(fh * ratio)
            flowchart_img = flowchart_img.resize((new_fw, new_fh), Image.Resampling.LANCZOS)
            
            # Paste flowchart in the center
            fx = (w - new_fw) // 2
            fy = (h - new_fh) // 2 + 50
            img.paste(flowchart_img, (fx, fy), flowchart_img)
            
            # Draw title at top
            fontsize = 48
            font = _load_font(fontsize)
            lines = textwrap.wrap(text, width=35) or [" "]
            y = 50
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                line_w = bbox[2] - bbox[0]
                draw.text(((w - line_w) // 2, y), line, fill="white", font=font)
                y += (fontsize + 10)
                
        except Exception as e:
            print(f"Failed to fetch mermaid image: {e}")
            draw.text((100, h//2), "Failed to render flowchart.", fill="red", font=_load_font(40))
            
    else:
        # Standard text slide
        fontsize = 64
        font = _load_font(fontsize)
        
        lines = textwrap.wrap(text, width=28) or [" "]
        line_h = fontsize + 24
        block_h = line_h * len(lines)
        y = (h - block_h) // 2
        
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_w = bbox[2] - bbox[0]
            draw.text(((w - line_w) // 2, y), line, fill="white", font=font)
            y += line_h

    img.save(output_path)

def create_slide_zip(slides_data: list, zip_filename: str) -> str:
    """Renders all slides and packages them into a ZIP file."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    zip_path = os.path.join(OUTPUT_DIR, zip_filename)
    
    temp_files = []
    
    for i, slide in enumerate(slides_data):
        filename = f"slide_{i+1:02d}.png"
        file_path = os.path.join(OUTPUT_DIR, filename)
        
        render_slide(slide, file_path)
        temp_files.append(file_path)
        
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for file in temp_files:
            zipf.write(file, os.path.basename(file))
            
    # Cleanup individual images
    for file in temp_files:
        try:
            os.remove(file)
        except OSError:
            pass
            
    return zip_path
