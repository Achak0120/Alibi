import os, requests
from functools import lru_cache
from font_map import LANGUAGE_FONT_MAP

AZ_T_ENDPOINT = os.getenv("AZURE_TRANSLATOR_ENDPOINT", "").rstrip("/")

@lru_cache(maxsize=1)
def azure_supported_targets():
    if not AZ_T_ENDPOINT:
        raise SystemExit("AZURE_TRANSLATOR_ENDPOINT is not set in this terminal session.")
    url = f"{AZ_T_ENDPOINT}/languages?api-version=3.0&scope=translation"
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    data = r.json().get("translation", {})
    return {code.lower(): meta.get("name", "") for code, meta in data.items()}

def main():
    try:
        supported = azure_supported_targets()
    except Exception as e:
        print("[ERR] Could not fetch Azure languages:", e)
        return

    # Keys you care about from your map
    yours = set(LANGUAGE_FONT_MAP.keys())
    azure = set(supported.keys())

    overlap = sorted(yours & azure)
    missing = sorted(yours - azure)

    print(f"Azure reports {len(azure)} total languages.")
    print(f"Your map has {len(yours)} codes.")
    print(f"\nSUPPORTED in Azure (intersection: {len(overlap)}):\n{overlap}")
    print(f"\nNOT supported by Azure (from your map: {len(missing)}):\n{missing}")

if __name__ == "__main__":
    main()