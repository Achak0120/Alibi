# main.py
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance
from googletrans import Translator as GoogleTranslator
from googletrans import LANGUAGES as GT_LANGUAGES  # for support check
from font_map import LANGUAGE_FONT_MAP
from spellchecker import SpellChecker
from functools import lru_cache
from google.cloud import vision
import unicodedata
import wordninja
import requests
import json
import time
import deepl
import sys
import os

# Paths & env
FONT_DIR = os.path.join(os.path.dirname(__file__), "Noto")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"C:\Users\Aishik C\Desktop\vision_key.json"

AZ_T_ENDPOINT = os.getenv("AZURE_TRANSLATOR_ENDPOINT", "").rstrip("/")
AZ_T_KEY = os.getenv("AZURE_TRANSLATOR_KEY")
AZ_T_REGION = os.getenv("AZURE_TRANSLATOR_REGION")
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")


# Normalizers & helpers
def normalize_lang_code(code: str) -> str:
    """Canonicalize to simple, lowercase ISO 639-1 two-letter where possible."""
    if not code:
        return "en"
    c = code.lower().replace("_", "-")
    if c.startswith("zh"):  # fold to 'zh' and let per-provider handle script
        return "zh"
    return c.split("-")[0]

def normalize_for_azure(code: str) -> str:
    """Azure uses BCP-47 script variants for Chinese; else lower-case is fine."""
    if not code:
        return "en"
    c = code.lower()
    if c in ("zh", "zh-cn", "zh-hans"):
        return "zh-Hans"
    if c in ("zh-tw", "zh-hk", "zh-hant"):
        return "zh-Hant"
    return c

def normalize_for_google(code: str) -> str:
    """googletrans uses legacy codes for a couple languages."""
    c = normalize_lang_code(code)
    if c == "he":  # Hebrew
        return "iw"
    if c == "jv":  # Javanese
        return "jw"
    # Chinese in googletrans: 'zh-cn', 'zh-tw' work best; fall back to 'zh'
    if c == "zh":
        return "zh"
    return c

def normalize_for_deepl(code: str) -> str:
    """
    DeepL expects upper-case ISO; supports e.g. EN, EN-GB, PT-BR.
    We'll map a couple; else use 2-letter upper.
    """
    if not code:
        return "EN"
    c = code.lower()
    special = {
        "pt-br": "PT-BR", "pt-pt": "PT-PT",
        "en-gb": "EN-GB", "en-us": "EN-US",
    }
    if c in special:
        return special[c]
    return normalize_lang_code(c).upper()

def debug_text(text: str, lang_code: str, font_file: str):
    print(f"[DBG] lang={lang_code} font={font_file}")
    print(f"[DBG] text='{text}'")
    cps = [f"U+{ord(ch):04X}" for ch in text]
    names = []
    for ch in text:
        try:
            names.append(unicodedata.name(ch))
        except Exception:
            names.append("UNKNOWN")
    print(f"[DBG] cps={cps}")
    print(f"[DBG] names={names}")

def is_junk(text):
    return sum(1 for c in text if not c.isalnum() and c not in '.,:;!?') > len(text) * 0.4

def get_font_by_lang(lang_code: str, size: int = 20):
    font_name = LANGUAGE_FONT_MAP.get(lang_code, 'NotoSans-Regular.ttf')
    font_path = os.path.join(FONT_DIR, font_name)
    if os.path.isfile(font_path):
        return ImageFont.truetype(font_path, size)
    print(f"[WARN] Font not found for {lang_code} → {font_name}, using default.")
    return ImageFont.load_default()


# Provider support discovery
@lru_cache(maxsize=1)
def azure_supported_targets():
    """Fetch Azure Translator supported targets once (empty if not configured)."""
    if not AZ_T_ENDPOINT:
        return {}
    try:
        url = f"{AZ_T_ENDPOINT}/languages?api-version=3.0&scope=translation"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json().get("translation", {})
        return {code.lower(): meta.get("name", "") for code, meta in data.items()}
    except Exception as e:
        print(f"[WARN] Azure languages fetch failed: {e}")
        return {}

@lru_cache(maxsize=1)
def deepl_supported_targets():
    tr = _deepl_translator()
    if not tr:
        return set()
    try:
        langs = tr.get_target_languages()
        return {l.code.upper() for l in langs}
    except Exception as e:
        print(f"[WARN] DeepL list languages failed: {e}")
        return set()

def provider_chain_for(dest: str):
    """
    Decide which providers to try, in order Azure -> Google -> DeepL,
    filtered by (a) env/config present and (b) provider actually supports target.
    """
    chain = []
    # Azure
    if AZ_T_ENDPOINT and AZ_T_KEY and AZ_T_REGION:
        az_code = normalize_for_azure(dest).lower()
        if az_code in azure_supported_targets():
            chain.append("azure")
        else:
            print(f"[WARN] Azure does not list target='{az_code}'.")
    # Google
    try:
        g_code = normalize_for_google(dest)
        if g_code in set(GT_LANGUAGES.keys()):
            chain.append("google")
        else:
            print(f"[WARN] googletrans does not list target='{g_code}'.")
    except Exception as e:
        print(f"[WARN] googletrans LANGUAGES unavailable: {e}")
    # DeepL
    if DEEPL_API_KEY:
        d_code = normalize_for_deepl(dest)
        if d_code in deepl_supported_targets():
            chain.append("deepl")
        else:
            print(f"[WARN] DeepL does not list target='{d_code}'.")
    return chain


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


# Text layout / coordinate-drawing
def get_font(image, text, width, height, lang_code):
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
    opaque_pixels = [p[:3] for p in pixels if p[3] > 0]
    if not opaque_pixels:
        background_color = (255, 255, 255)
    else:
        from collections import Counter
        background_color = Counter(opaque_pixels).most_common(1)[0][0]
    return add_discoloration(background_color, 40)

def get_text_fill_color(background_color):
    luminance = (0.299 * background_color[0] + 0.587 * background_color[1] + 0.114 * background_color[2]) / 255
    return "black" if luminance > 0.5 else "white"

def replace_text_with_translation(image_path, translated_texts, text_boxes, lang_code):
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)
    for text_box, translated in zip(text_boxes, translated_texts):
        if not translated:
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
            font=font
        )
    return image


# Lang Providers
def _azure_headers():
    return {
        "Ocp-Apim-Subscription-Key": AZ_T_KEY,
        "Ocp-Apim-Subscription-Region": AZ_T_REGION,
        "Content-Type": "application/json"
    }

def azure_translate_batch(texts, src="en", dest="fr", max_chunk=50, sleep_sec=0.05):
    """Assumes caller already verified Azure supports 'dest'."""
    if not (AZ_T_ENDPOINT and AZ_T_KEY and AZ_T_REGION):
        raise RuntimeError("Azure env vars missing: AZURE_TRANSLATOR_KEY / _REGION / _ENDPOINT")
    dest_bcp = normalize_for_azure(dest)
    url = f"{AZ_T_ENDPOINT}/translate?api-version=3.0&from={src}&to={dest_bcp}"

    out = []
    i = 0
    while i < len(texts):
        chunk = texts[i:i+max_chunk]
        body = [{"Text": t} for t in chunk]
        resp = requests.post(url, headers=_azure_headers(), data=json.dumps(body), timeout=25)
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
        i += max_chunk
        time.sleep(sleep_sec)
    return out

@lru_cache(maxsize=1)
def _google_t():
    # googletrans is stateless; cache the instance
    return GoogleTranslator(service_urls=[
        'translate.googleapis.com',
        'translate.google.com'
    ])

def google_translate_batch(texts, src="en", dest="fr"):
    """Assumes caller already verified googletrans supports 'dest'."""
    tr = _google_t()
    out = []
    for t in texts:
        try:
            res = tr.translate(t, src=src, dest=dest)
            out.append(res.text)
        except Exception as e:
            print(f"[WARN] googletrans failed for '{t[:30]}...': {e}")
            out.append("")
    return out

@lru_cache(maxsize=1)
def _deepl_translator():
    if not DEEPL_API_KEY:
        return None
    return deepl.Translator(DEEPL_API_KEY)

def deepl_translate_batch(texts, src="EN", dest="FR"):
    """Assumes caller already verified DeepL supports 'dest'."""
    tr = _deepl_translator()
    if not tr:
        raise RuntimeError("DEEPL_API_KEY missing")
    dest_up = normalize_for_deepl(dest)
    out = []
    for t in texts:
        try:
            res = tr.translate_text(t, source_lang=src.upper(), target_lang=dest_up)
            out.append(res.text)
        except Exception as e:
            print(f"[WARN] DeepL failed for '{t[:30]}...': {e}")
            out.append("")
    return out



# Fallback cascade
def translate_with_fallbacks(texts, src_lang, dest_lang):
    """
    Try Azure → Google → DeepL for languages each provider supports.
    Returns a list[str] same length as texts. Only re-tries untranslated items.
    """
    chain = provider_chain_for(dest_lang)
    if not chain:
        print(f"[INFO] No providers support target='{dest_lang}'. Skipping translation.")
        return [""] * len(texts)

    results = [""] * len(texts)
    pending_idx = list(range(len(texts)))

    def run(service_name, batch):
        if service_name == 'azure':
            return azure_translate_batch(batch, src=src_lang, dest=dest_lang)
        if service_name == 'google':
            return google_translate_batch(batch, src=src_lang, dest=normalize_for_google(dest_lang))
        if service_name == 'deepl':
            return deepl_translate_batch(batch, src=src_lang, dest=dest_lang)
        return [""] * len(batch)

    for svc in chain:
        if not pending_idx:
            break
        outs = run(svc, [texts[i] for i in pending_idx])
        new_pending = []
        for j, i in enumerate(pending_idx):
            cand = outs[j] if j < len(outs) else ""
            if cand and cand.strip() and cand.strip() != texts[i].strip():
                results[i] = cand
            else:
                new_pending.append(i)
        pending_idx = new_pending
        print(f"[INFO] {svc.title()} translated {len(texts)-len(pending_idx)} / {len(texts)} so far")

    return results


# Main pipeline
def translate_image_pipeline(image_path, output_path, target_lang, font_map):
    extracted_text_boxes = perform_ocr_with_google_vision(image_path)

    # Choose font by the internal map key
    norm = normalize_lang_code(target_lang)
    selected_lang_code = norm if norm in font_map else "en"

    # Collect texts to translate, lightly clean
    src_texts = []
    index_map = []  # (idx_in_boxes, original_text)
    spell = SpellChecker()

    for idx, (_, text) in enumerate(extracted_text_boxes):
        if not text or is_junk(text):
            src_texts.append("")           # keep slot for alignment
            index_map.append((idx, None))  # mark as skipped
            continue

        words = text.split()
        corrected_words = [spell.correction(w) or w for w in words]
        corrected_text = " ".join(corrected_words)

        split_words = []
        for w in corrected_text.split():
            split_words.extend(wordninja.split(w) if len(w) > 10 else [w])
        final_text = " ".join(split_words)

        src_texts.append(final_text)
        index_map.append((idx, final_text))

    # Translate (en -> target) with provider fallback
    dest = normalize_lang_code(target_lang)
    translations = translate_with_fallbacks(src_texts, src_lang="en", dest_lang=dest)

    # Build final list aligned to boxes (None for unchanged/empty)
    translated_texts = []
    for (idx, original), tr in zip(index_map, translations):
        if original is None or not tr:
            translated_texts.append(None)
        else:
            translated_texts.append(tr)

    # Draw
    image = replace_text_with_translation(image_path, translated_texts, extracted_text_boxes, selected_lang_code)
    image.save(output_path)


# Script entry
if __name__ == "__main__":
    input_folder = "input"
    output_folder = "output"
    target_lang = sys.argv[1] if len(sys.argv) > 1 else "en"

    if AZ_T_ENDPOINT and AZ_T_KEY and AZ_T_REGION:
        print("[INFO] Azure Translator configured.")
    else:
        print("[INFO] Azure not configured. Will use other providers if available.")
    if DEEPL_API_KEY:
        print("[INFO] DeepL configured.")
    else:
        print("[INFO] DeepL not configured.")

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
