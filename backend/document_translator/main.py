from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance
from spellchecker import SpellChecker
from font_map import LANGUAGE_FONT_MAP
from google.cloud import vision
import unicodedata
import requests
import json
import time
from functools import lru_cache
import numpy as np
import wordninja
import sys
import os

# ----------------------------
# Config
# ----------------------------

# Font folder
FONT_DIR = os.path.join(os.path.dirname(__file__), "Noto")

# Google Vision API Key Path
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"C:\Users\Aishik C\Desktop\vision_key.json"

# Azure Translator env vars (DO NOT hardcode)
AZ_T_ENDPOINT = os.getenv("AZURE_TRANSLATOR_ENDPOINT", "").rstrip("/")
AZ_T_KEY = os.getenv("AZURE_TRANSLATOR_KEY")
AZ_T_REGION = os.getenv("AZURE_TRANSLATOR_REGION")


# Lang helpers & debug
def normalize_lang_code(code: str) -> str:
    """Your internal (font) normalization: collapse region variants to base 639-1."""
    if not code:
        return "en"
    c = code.lower().replace('_', '-')
    if c.startswith('zh'): return 'zh'   # zh, zh-cn, zh-tw → zh (your font map logic)
    if c.startswith('pt'): return 'pt'
    if c.startswith('en'): return 'en'
    if c.startswith('sr'): return 'sr'
    return c.split('-')[0]               # e.g., nn-NO → nn

def normalize_for_azure(code: str) -> str:
    """Azure wants BCP‑47 (e.g., zh-Hans/zh-Hant)."""
    if not code:
        return "en"
    c = code.lower()
    if c in ("zh", "zh-cn", "zh-hans"):
        return "zh-Hans"
    if c in ("zh-tw", "zh-hk", "zh-hant"):
        return "zh-Hant"
    return c

def debug_text(text: str, lang_code: str, font_file: str):
    print(f"[DBG] lang={lang_code} font={font_file}")
    print(f"[DBG] text='{text}'")
    codepoints = [f"U+{ord(c):04X}" for c in text]
    names = []
    for c in text:
        try:
            names.append( unicodedata.name(c) )
        except:
            names.append('UNKNOWN')
    print(f"[DBG] cps={codepoints}")
    print(f"[DBG] names={names}")

def is_junk(text):
    return sum(1 for c in text if not c.isalnum() and c not in '.,:;!?') > len(text) * 0.4

def get_font_by_lang(lang_code: str, size: int = 20):
    font_name = LANGUAGE_FONT_MAP.get(lang_code, 'NotoSans-Regular.ttf')
    font_path = os.path.join(FONT_DIR, font_name)
    if os.path.isfile(font_path):
        return ImageFont.truetype(font_path, size)
    else:
        print(f"[WARN] Font not found for {lang_code} → {font_name}, using default.")
        return ImageFont.load_default()


# OCR
def preprocess_image_for_ocr(image_path):
    image = Image.open(image_path).convert("RGB")
    gray_image = ImageOps.grayscale(image)
    contrast_enhancer = ImageEnhance.Contrast(gray_image)
    contrast_image = contrast_enhancer.enhance(2.5)
    threshold = 180
    binarized_image = contrast_image.point(lambda x: 0 if x < threshold else 255).convert("L")
    return binarized_image

def perform_ocr_with_google_vision(image_path):
    client = vision.ImageAnnotatorClient()
    with open(image_path, "rb") as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    annotations = response.text_annotations

    extracted_text_boxes = []
    if annotations:
        for annotation in annotations[1:]:
            vertices = [(v.x, v.y) for v in annotation.bounding_poly.vertices]
            text = annotation.description
            extracted_text_boxes.append((vertices, text))
    return extracted_text_boxes


# Text layout/drawing
def get_font(image, text, width, height, lang_code):
    font_size = None
    font = None
    box = None
    x = 0
    y = 0
    draw = ImageDraw.Draw(image)

    for size in range(1, 500):
        new_font = get_font_by_lang(lang_code, size)
        new_box = draw.textbbox((0, 0), text, font=new_font)
        new_w = new_box[2] - new_box[0]
        new_h = new_box[3] - new_box[1]

        if new_w > width or new_h > height:
            break

        font_size = size
        font = new_font
        box = new_box
        w = new_w
        h = new_h
        x = (width - w) // 2 - box[0]
        y = (height - h) // 2 - box[1]

    return font, x, y

def add_discoloration(color, strength):
    r, g, b = color[:3]
    r = max(0, min(255, r + strength))
    g = max(0, min(255, g + strength))
    b = max(0, min(255, b + strength))
    if r == 255 and g == 255 and b == 255:
        r, g, b = 245, 245, 245
    return (r, g, b)

def get_background_color(image, x_min, y_min, x_max, y_max):
    image = image.convert('RGBA')
    margin = 10
    edge_region = image.crop((
        max(x_min - margin, 0),
        max(y_min - margin, 0),
        min(x_max + margin, image.width),
        min(y_max + margin, image.height),
    ))
    pixels = list(edge_region.getdata())
    opaque_pixels = [pixel[:3] for pixel in pixels if pixel[3] > 0]

    if not opaque_pixels:
        background_color = (255, 255, 255)
    else:
        from collections import Counter
        most_common = Counter(opaque_pixels).most_common(1)[0][0]
        background_color = most_common

    return add_discoloration(background_color, 40)

def get_text_fill_color(background_color):
    luminance = (0.299 * background_color[0] + 0.587 * background_color[1] + 0.114 * background_color[2]) / 255
    return "black" if luminance > 0.5 else "white"

def replace_text_with_translation(image_path, translated_texts, text_boxes, lang_code):
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)

    for text_box, translated in zip(text_boxes, translated_texts):
        if translated is None:
            continue

        x_min, y_min = text_box[0][0][0], text_box[0][0][1]
        x_max, y_max = text_box[0][0][0], text_box[0][0][1]

        for x, y in text_box[0]:
            x_min = min(x_min, x)
            x_max = max(x_max, x)
            y_min = min(y_min, y)
            y_max = max(y_max, y)

        background_color = get_background_color(image, x_min, y_min, x_max, y_max)
        draw.rectangle(((x_min, y_min), (x_max, y_max)), fill=background_color)

        font_name = LANGUAGE_FONT_MAP.get(lang_code, 'NotoSans-Regular.ttf')
        debug_text(translated, lang_code, font_name)

        font, x_offset, y_offset = get_font(image, translated, x_max - x_min, y_max - y_min, lang_code)

        draw.text(
            (x_min + x_offset, y_min + y_offset),
            translated,
            fill=get_text_fill_color(background_color),
            font=font,
        )

    return image


# Azure Translator
def _azure_headers():
    return {
        "Ocp-Apim-Subscription-Key": AZ_T_KEY,
        "Ocp-Apim-Subscription-Region": AZ_T_REGION,
        "Content-Type": "application/json"
    }

@lru_cache(maxsize=1)
def azure_supported_targets():
    """Fetch supported target languages once from Azure."""
    if not AZ_T_ENDPOINT:
        return {}
    url = f"{AZ_T_ENDPOINT}/languages?api-version=3.0&scope=translation"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    data = r.json().get("translation", {})
    return {code.lower(): meta.get("name", "") for code, meta in data.items()}

def azure_translate_batch(texts, src="en", dest="fr", max_chunk=50, sleep_sec=0.05):
    """
    Translate list[str] via Azure Translator REST API.
    Returns list[str] of same length.
    """
    if not (AZ_T_ENDPOINT and AZ_T_KEY and AZ_T_REGION):
        raise RuntimeError("Azure env vars missing: AZURE_TRANSLATOR_KEY / _REGION / _ENDPOINT")

    dest_bcp = normalize_for_azure(dest)
    supported = azure_supported_targets()
    if dest_bcp.lower() not in supported:
        print(f"[WARN] Azure does not list target='{dest_bcp}'. Returning originals.")
        return texts

    url = f"{AZ_T_ENDPOINT}/translate?api-version=3.0&from={src}&to={dest_bcp}"
    out = []
    i = 0
    while i < len(texts):
        chunk = texts[i:i+max_chunk]
        body = [{"Text": t} for t in chunk]
        try:
            resp = requests.post(url, headers=_azure_headers(), data=json.dumps(body), timeout=20)
            if resp.status_code == 429:
                time.sleep(1.0)
                continue
            resp.raise_for_status()
            data = resp.json()
            for item in data:
                if item.get("translations"):
                    out.append(item["translations"][0]["text"])
                else:
                    out.append("")
        except Exception as e:
            print(f"[ERROR] Azure translate chunk failed: {e}")
            out.extend(chunk)  # fallback to originals
        i += max_chunk
        time.sleep(sleep_sec)
    return out


# Main pipeline
def translate_image_pipeline(image_path, output_path, target_lang, font_map):
    # OCR
    extracted_text_boxes = perform_ocr_with_google_vision(image_path)

    # Font selection code
    norm = normalize_lang_code(target_lang)
    selected_lang_code = norm if norm in font_map else "en"

    # Collect texts to translate (skip junk/empty), cache by (lang, text)
    translated_texts = []
    src_texts = []
    index_map = []  # (idx_in_boxes, cache_key, final_text)
    cache = {}

    spell = SpellChecker()

    for idx, (_, text) in enumerate(extracted_text_boxes):
        if not text:
            translated_texts.append(None)
            continue
        if is_junk(text):
            print(f"[SKIP] Skipped junk: {text}")
            translated_texts.append(None)
            continue

        # light cleanup of English source
        words = text.split()
        corrected_words = [spell.correction(w) or w for w in words]
        corrected_text = " ".join(corrected_words)

        split_words = []
        for w in corrected_text.split():
            split_words.extend(wordninja.split(w) if len(w) > 10 else [w])
        final_text = " ".join(split_words)

        ck = (norm, final_text)
        if ck in cache:
            translated_texts.append(cache[ck])
            continue

        index_map.append((idx, ck, final_text))
        src_texts.append(final_text)
        translated_texts.append(None)  # placeholder

    # Call Azure in batch (fast + reliable)
    if src_texts:
        try:
            azure_out = azure_translate_batch(src_texts, src="en", dest=norm)
        except Exception as e:
            print(f"[ERROR] Azure call failed: {e}")
            azure_out = src_texts  # fallback: keep originals

        for (idx, ck, _src), tr in zip(index_map, azure_out):
            cache[ck] = tr
            translated_texts[idx] = tr

    # Draw
    image = replace_text_with_translation(
        image_path, translated_texts, extracted_text_boxes, selected_lang_code
    )
    image.save(output_path)


# Script entry
if __name__ == "__main__":
    input_folder = "input"
    output_folder = "output"
    target_lang = sys.argv[1] if len(sys.argv) > 1 else "en"

    # sanity check for Azure env
    if not (AZ_T_ENDPOINT and AZ_T_KEY and AZ_T_REGION):
        raise SystemExit("Set AZURE_TRANSLATOR_KEY, AZURE_TRANSLATOR_ENDPOINT, AZURE_TRANSLATOR_REGION and restart terminal.")

    files = os.listdir(input_folder)
    image_files = [file for file in files if file.lower().endswith((".jpg", ".jpeg", ".png"))]

    os.makedirs(output_folder, exist_ok=True)

    for filename in image_files:
        print(f'[INFO] Processing {filename}...')
        image_path = os.path.join(input_folder, filename)
        output_path = os.path.join(
            output_folder,
            f"{os.path.splitext(filename)[0]}-translated{os.path.splitext(filename)[1]}"
        )
        translate_image_pipeline(image_path, output_path, target_lang, LANGUAGE_FONT_MAP)
        print(f'[INFO] Saved as {output_path}...')