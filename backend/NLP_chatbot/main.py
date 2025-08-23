import os
import io
import logging
from pathlib import Path
from typing import Optional

from langdetect import detect, DetectorFactory
DetectorFactory.seed = 0  # deterministic language detection

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image

# CORS
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "*")

app = FastAPI(title="Document QA Chatbot")
from collections import defaultdict
SESSION_LANG = defaultdict(lambda: "en")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN] if FRONTEND_ORIGIN != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gemini setup
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()

GEMINI_KEY = os.getenv("GOOGLE_API_KEY")
if not GEMINI_KEY:
    raise RuntimeError("Missing GOOGLE_API_KEY in .env")

genai.configure(api_key=GEMINI_KEY)
# Fast + cost‑effective + multimodal
model = genai.GenerativeModel("gemini-1.5-flash")

# Paths from your pipeline (point to .../CareBridge/backend/document_translator)
BACKEND_DIR = Path(__file__).resolve().parents[1]  # .../CareBridge/backend
DOC_DIR = BACKEND_DIR / "document_translator" / "document_translator"
OUTPUT_DIR = DOC_DIR / "output"
INPUT_DIR  = DOC_DIR / "input"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger= logging.getLogger(__name__)
class ChatRequest(BaseModel):
    message: str
    image_filename: Optional[str] = None          # optional: specific file
    source: Optional[str] = "output"              # "output" or "input"
    target_lang: Optional[str] = "auto"           # e.g., "bn", "es", "ar", or "auto"

def _latest_image(folder: Path) -> Path:
    candidates = []
    for ext in ("*.png", "*.jpg", "*.jpeg", "*.webp"):
        candidates.extend(folder.glob(ext))
    if not candidates:
        raise FileNotFoundError(f"No images found in {folder}")
    # newest by modified time
    return max(candidates, key=lambda p: p.stat().st_mtime)

def _load_image_bytes(path: Path) -> tuple[bytes, str]:
    # ensure it's a valid image and grab a mime
    with Image.open(path) as im:
        buf = io.BytesIO()
        fmt = (im.format or "PNG").upper()  # Preserve format if possible
        im.save(buf, fmt)
        data = buf.getvalue()
        mime = {
            "PNG": "image/png",
            "JPG": "image/jpeg",
            "JPEG": "image/jpeg",
            "WEBP": "image/webp"
        }.get(fmt, "image/png")
        return data, mime

def _resolve_lang(user_msg: str, preferred: Optional[str], user_id: str) -> str:
    if preferred and preferred.lower() != "auto":
        lang = preferred.lower()
        SESSION_LANG[user_id] = lang
        return lang
    
    if user_id in SESSION_LANG and SESSION_LANG[user_id] != "en":
        return SESSION_LANG[user_id]

    try:
        lang = detect(user_msg).lower()
        SESSION_LANG[user_id] = lang
        return lang
    except Exception as e:
        logger.warning(f"Language detection failed for '{user_msg}': {e}")
        return "en"


@app.post("/api/chat")
def chat(req: ChatRequest):
    folder = OUTPUT_DIR if (req.source or "output").lower() == "output" else INPUT_DIR
    if req.image_filename:
        img_path = (folder / req.image_filename)
        if not img_path.exists():
            raise FileNotFoundError(f"{img_path} not found.")
    else:
        img_path = _latest_image(folder)

    img_bytes, mime = _load_image_bytes(img_path)
    user_q = (req.message or "").strip()
    user_id = "anon"
    target_lang = _resolve_lang(user_q, req.target_lang, user_id)

    # System prompt: grounded, concise, reply in target_lang
    system_instruction = (
        "You are a careful assistant. Only answer using information visible in the image. "
        "If the answer is not visible, say you cannot find it. "
        f"Always respond in the user's language: {target_lang}. "
        "Use clear, simple wording and keep answers concise."
    )

    # Gemini multimodal call
    result = model.generate_content([
        system_instruction,
        {"mime_type": mime, "data": img_bytes},
        f"User question (reply in {target_lang}): {user_q}"
    ])

    reply = (getattr(result, "text", "") or "").strip()
    if not reply:
        # Minimal language-agnostic fallback:
        reply = "Sorry, I couldn’t extract an answer from the document."

    return {
        "reply": reply,
        "image_used": str(img_path.name),
        "target_lang": target_lang
    }

# Simple health check
@app.get("/api/health")
def health():
    return {"status": "ok"}