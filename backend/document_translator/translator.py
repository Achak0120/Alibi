import requests

# Translates english text to other language
def translate(text: str, target_lang: str) -> str:
    response = requests.post(
        "http://localhost:5000/translate",
        data={
            "q": text,
            "source":"en",
            "target":target_lang,
            "format":"text"
        }
    )
    if response.status_code == 200:
        return response.json().get("translatedText", "")
    else:
        raise Exception(f"Translation failed: {response.status_code} {response.text}")