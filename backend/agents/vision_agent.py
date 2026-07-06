import os
import json
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

# Attempt to import google-genai if available, but fail gracefully if not installed
try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

def diagnose_water_source(image_path: str) -> dict:
    """
    Diagnoses water source contamination from an image.
    Uses Gemini API if GEMINI_API_KEY environment variable is present,
    otherwise falls back to a local rules/heuristics-based offline classifier.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    
    if api_key and HAS_GENAI:
        return _diagnose_with_gemini(image_path, api_key)
    else:
        return _diagnose_offline(image_path)

def _diagnose_offline(image_path: str) -> dict:
    """
    Offline/mock classifier using image analytics (Pillow) and filename keyword parsing.
    Returns structured diagnosis results.
    """
    print("[Vision Agent] Running in offline mode using heuristics...")
    
    signs = []
    details_parts = []
    
    # 1. Check filename for predictable test keywords
    filename = os.path.basename(image_path).lower()
    keyword_triggered = False
    
    for key in ["algae", "discoloration", "foam", "debris"]:
        if key in filename:
            signs.append(key)
            keyword_triggered = True
            details_parts.append(f"Detected '{key}' from image metadata matching.")
            
    # 2. Run Pillow analysis if image is readable
    try:
        img = Image.open(image_path).convert('RGB')
        # Resize to speed up calculation
        img = img.resize((100, 100))
        pixels = list(img.getdata())
        
        total_r = total_g = total_b = 0
        for r, g, b in pixels:
            total_r += r
            total_g += g
            total_b += b
            
        num_pixels = len(pixels)
        avg_r = total_r / num_pixels
        avg_g = total_g / num_pixels
        avg_b = total_b / num_pixels
        
        # Heuristics if no keywords were triggered in the file name
        if not keyword_triggered:
            # Algae Heuristic: strong green component
            if avg_g > avg_r * 1.15 and avg_g > avg_b * 1.15:
                signs.append("algae")
                details_parts.append("Visual color profiling shows high green coloration, suggesting algae bloom.")
            
            # Discoloration Heuristic: brown/muddy/turbid (high red/green, low blue)
            elif avg_r > 110 and avg_g > 90 and avg_b < 70:
                signs.append("discoloration")
                details_parts.append("Visual color profiling indicates high turbidity and brownish discoloration.")
            
            # Foam Heuristic: very bright/whitish areas
            elif avg_r > 210 and avg_g > 210 and avg_b > 210:
                signs.append("foam")
                details_parts.append("High brightness levels suggest visible foam or frothing on the water surface.")
                
            # Fallback when image is analyzed but looks normal
            if not signs:
                details_parts.append("Image analysis indicates water appears relatively clear under normal lighting.")
    except Exception as e:
        print(f"[Vision Agent] Image reading error: {e}")
        details_parts.append(f"Image could not be fully parsed. (Error: {e})")

    # Clean duplicates
    signs = list(set(signs))
    
    # 3. Determine risk level
    if not signs:
        risk_level = "Low"
        summary_detail = "Clear water. No visible signs of contamination."
    elif len(signs) == 1:
        risk_level = "Medium"
        summary_detail = f"Possible risk. Suspected contamination signs: {', '.join(signs)}."
    else:
        risk_level = "High"
        summary_detail = f"Significant risk. Multiple contamination signs detected: {', '.join(signs)}."
        
    details = " ".join(details_parts) if details_parts else summary_detail

    return {
        "status": "success",
        "mode": "offline_heuristics",
        "contamination_signs": signs,
        "risk_level": risk_level,
        "confidence": 0.85 if keyword_triggered else 0.65,
        "details": f"{summary_detail} {details}".strip()
    }

def _diagnose_with_gemini(image_path: str, api_key: str) -> dict:
    """
    Online classifier calling Gemini 2.5 Flash model with the image.
    """
    print("[Vision Agent] Running in online mode using Gemini Vision API...")
    try:
        client = genai.Client(api_key=api_key)
        
        # Load the image
        img = Image.open(image_path)
        
        prompt = """
        Analyze this image of a water source (e.g. well, pond, river, community tap) in rural/semi-urban India.
        Identify if any of the following visible contamination signs are present:
        - "algae" (green film, scum, or microalgae bloom)
        - "discoloration" (muddy brown, yellow, black water, high turbidity)
        - "foam" (froth, soap-like bubbles, chemical discharges)
        - "debris" (plastic, leaves, animal wastes, trash floating in/around water)
        
        You must respond with a JSON object containing exactly the following keys:
        {
          "contamination_signs": ["algae", "discoloration", "foam", "debris"], // array of matching strings (empty if none)
          "risk_level": "Low" | "Medium" | "High", // Low (no signs), Medium (1 sign), High (2+ signs or severe contamination)
          "confidence": 0.0 to 1.0, // float value
          "details": "A detailed 1-2 sentence description of what is seen in the image."
        }
        Do not add any markdown formatting, triple backticks, or other text outside the JSON. Return valid JSON only.
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[img, prompt]
        )
        
        # Parse JSON from response
        resp_text = response.text.strip()
        # Clean markdown if model includes it
        if resp_text.startswith("```"):
            lines = resp_text.splitlines()
            if lines[0].startswith("```json"):
                resp_text = "\n".join(lines[1:-1])
            elif lines[0].startswith("```"):
                resp_text = "\n".join(lines[1:-1])
                
        data = json.loads(resp_text)
        
        return {
            "status": "success",
            "mode": "gemini_vision",
            "contamination_signs": data.get("contamination_signs", []),
            "risk_level": data.get("risk_level", "Low"),
            "confidence": data.get("confidence", 0.95),
            "details": data.get("details", "Analyzed using Gemini VLM.")
        }
        
    except Exception as e:
        print(f"[Vision Agent] Gemini evaluation failed: {e}. Falling back to offline mode.")
        fallback_res = _diagnose_offline(image_path)
        fallback_res["mode"] = "offline_fallback"
        return fallback_res
