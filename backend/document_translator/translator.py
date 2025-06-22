import os
from google.cloud import translate_v2 as translate

def main():
    # Check environment variable
    creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    print(f"Using credentials file: {creds}")

    # Initialize client
    translate_client = translate.Client()

    # Sample text to translate
    text = "Hello, world!"
    target_language = "es"  # Spanish

    # Call translate API
    result = translate_client.translate(text, target_language=target_language)
    print(f"Original: {text}")
    print(f"Translated: {result['translatedText']}")

if __name__ == "__main__":
    main()

