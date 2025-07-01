import requests

def translate(text: str, target_lang: str) -> str:
    print("[TRANSLATE INPUT]", text)
    
    response = requests.post(
        "http://localhost:5000/translate",
        data={
            "q": text,
            "source": "en",
            "target": target_lang,
            "format": "text"
        }
    )

    if response.status_code == 200:
        translated = response.json().get("translatedText", "")
        print("[TRANSLATE OUTPUT]", translated)
        return translated
    else:
        print("[TRANSLATE ERROR]", response.status_code, response.text)
        raise Exception(f"Translation failed: {response.status_code} {response.text}")