import os
import requests
from zipfile import ZipFile
from io import BytesIO

# Map of font name to expected zip download
FONT_ZIPS = {
    "NotoSans": "https://noto-website-2.storage.googleapis.com/pkgs/NotoSans-unhinted.zip",
    "NotoSansArabic": "https://noto-website-2.storage.googleapis.com/pkgs/NotoSansArabic-unhinted.zip",
    "NotoSansBengali": "https://noto-website-2.storage.googleapis.com/pkgs/NotoSansBengali-unhinted.zip",
    "NotoSansDevanagari": "https://noto-website-2.storage.googleapis.com/pkgs/NotoSansDevanagari-unhinted.zip",
    "NotoSansJP": "https://noto-website-2.storage.googleapis.com/pkgs/NotoSansJP-unhinted.zip",
    "NotoSansKR": "https://noto-website-2.storage.googleapis.com/pkgs/NotoSansKR-unhinted.zip",
    "NotoSansSC": "https://noto-website-2.storage.googleapis.com/pkgs/NotoSansSC-unhinted.zip",
    "NotoNaskhArabic": "https://noto-website-2.storage.googleapis.com/pkgs/NotoNaskhArabic-unhinted.zip",
    "NotoNastaliqUrdu": "https://noto-website-2.storage.googleapis.com/pkgs/NotoNastaliqUrdu-unhinted.zip"
}

DEST = "C:/Fonts/Noto"

def download_and_extract():
    os.makedirs(DEST, exist_ok=True)
    for name, url in FONT_ZIPS.items():
        print(f"\n[+] Downloading: {name}")
        try:
            response = requests.get(url)
            if response.status_code != 200:
                print(f"[-] Failed to download {name}")
                continue

            with ZipFile(BytesIO(response.content)) as zf:
                for file in zf.namelist():
                    if file.endswith(".ttf") or file.endswith(".otf"):
                        font_path = os.path.join(DEST, os.path.basename(file))
                        if not os.path.exists(font_path):
                            zf.extract(file, DEST)
                            print(f"[✓] Extracted: {font_path}")
                        else:
                            print(f"[=] Already exists: {font_path}")
        except Exception as e:
            print(f"[X] Error downloading {name}: {e}")

if __name__ == "__main__":
    download_and_extract()

