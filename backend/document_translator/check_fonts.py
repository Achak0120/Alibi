import os
from font_map import LANGUAGE_FONT_MAP

FONT_DIR = r"C:\Users\Aishik C\Desktop\Congressional Submission MAIN\CareBridge\backend\document_translator\Noto"

for lang, font in LANGUAGE_FONT_MAP.items():
    path = os.path.join(FONT_DIR, font)
    if not os.path.exists(path):
        print(f"❌ Missing: {lang} → {font}")
