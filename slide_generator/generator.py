import json
from shared.llm import generate

SLIDE_PROMPT = """You are an expert presentation designer.
Convert the following medical explanation into a sequence of 4 to 8 highly visual slides optimized for an Instagram Carousel.
Each slide should have:
- "text": A short, punchy sentence or bullet points (max 30 words per slide).
- "image_prompt": A very short (3-5 words) prompt describing the background image (e.g. "red blood cells microscopic", "stethoscope on blue background"). No long descriptions.

The first slide MUST be a Title Slide.

Explanation:
{text}

Output ONLY valid JSON in the following format. Do not include markdown codeblocks or any other text.
[
  {{"text": "Your text here", "image_prompt": "your image prompt"}},
  ...
]
"""

import re

def generate_slide_structure(explanation_text: str) -> list:
    """Takes an explanation and uses the LLM to format it into JSON slides."""
    
    # Fast path: If it's a Mermaid flowchart, just return it as a special slide!
    mermaid_match = re.search(r'```mermaid\n([\s\S]*?)```', explanation_text)
    if mermaid_match:
        code = mermaid_match.group(1).strip()
        # Grab some text before the flowchart as a title if possible
        title = explanation_text.split('```')[0].strip()
        if len(title) > 50 or len(title) < 2:
            title = "Flowchart"
        return [{"type": "flowchart", "code": code, "text": title, "image_prompt": "clean gradient background"}]
        
    prompt = SLIDE_PROMPT.format(text=explanation_text)
    
    # We use a lower temperature for JSON strictness
    raw_response = generate(prompt, temperature=0.2)
    
    # Use regex to extract the JSON array, ignoring any conversational text
    json_match = re.search(r'\[\s*\{.*\}\s*\]', raw_response, re.DOTALL)
    cleaned = json_match.group(0) if json_match else raw_response.strip()
    
    try:
        slides = json.loads(cleaned)
        if not isinstance(slides, list):
            raise ValueError("LLM did not return a list.")
        return slides
    except Exception as e:
        # Fallback to a basic single slide if JSON parsing completely fails
        print(f"Failed to parse slide JSON: {e}\nRaw output: {raw_response}")
        return [{"text": explanation_text[:200] + "...", "image_prompt": "medical abstract background"}]
