
from __future__ import annotations
import logging
from typing import Dict, Tuple, Optional, Set

log = logging.getLogger(__name__)

# --- 1) Normalize language codes per service (fix well-known quirks) ---

def normalize_for_service(code: str, service: str) -> str:
    c = code.lower()

    # Common aliases you’re likely to hit from your SUPPORTED_LANGUAGES
    aliases = {
        # Google uses legacy codes; Azure/DeepL use ISO
        ("he", "google"): "iw",
        ("jv", "google"): "jw",
        ("yi", "google"): "yi",  # some libs map to 'ji', keep 'yi' if supported
        ("zh", "azure"): "zh-Hans",  # default to Simplified; change to zh-Hant if you prefer
        ("zh", "deepl"): "zh",       # DeepL expects 'zh'
        ("zh", "google"): "zh",      # Google expects 'zh' (or region variants)
        # Scripts under Arabic family that you mapped to NotoNaskh (these keep ISO)
        ("ku", "azure"): "ku", ("ku", "google"): "ku", ("ku", "deepl"): "ku",
        ("ps", "azure"): "ps", ("ps", "google"): "ps", ("ps", "deepl"): "ps",
        ("fa", "azure"): "fa", ("fa", "google"): "fa", ("fa", "deepl"): "fa",
        # Oriya vs Odia: most APIs use 'or'
        ("or", "azure"): "or",
        ("or", "google"): "or",
        ("or", "deepl"): "or",
    }
    return aliases.get((c, service), c)

# --- 2) Discover supported targets at startup (no hardcoding) ---

def get_azure_supported() -> Set[str]:
    """
    Return set of target language codes Azure Translator actually supports.
    Implement this to call Azure's 'languages' endpoint or your SDK once at startup.
    Fallback: a cached/set you persist.
    """
    # Example stub (replace with live fetch):
    # from azure.ai.translation.text import TextTranslationClient
    # ...
    return set()  # <- fill from Azure

def get_google_supported() -> Set[str]:
    """
    Return set of Google target codes from the library you use.
    If you're using googletrans, use googletrans.LANGUAGES keys (lowercase).
    """
    try:
        from googletrans import LANGUAGES as GT_LANGUAGES  # type: ignore
        return set(GT_LANGUAGES.keys())
    except Exception:
        return set()  # if you swapped libs, populate from that SDK

def get_deepl_supported() -> Set[str]:
    """
    Query DeepL /v2/languages?type=target and return the set of language codes (lowercase).
    """
    # Example stub (replace with live fetch):
    # import deepl
    # translator = deepl.Translator(DEEPL_API_KEY)
    # langs = translator.get_target_languages()
    # return {l.code.lower() for l in langs}
    return set()

def build_router(supported_product_codes: Set[str]) -> "TranslatorRouter":
    azure = {x.lower() for x in get_azure_supported()}
    google = {x.lower() for x in get_google_supported()}
    deepl = {x.lower() for x in get_deepl_supported()}

    # Log a summary
    log.info("Azure targets:  %d", len(azure))
    log.info("Google targets: %d", len(google))
    log.info("DeepL targets:  %d", len(deepl))

    return TranslatorRouter(azure_supported=azure, google_supported=google, deepl_supported=deepl, product_codes=supported_product_codes)

# --- 3) The router ---

class TranslatorRouter:
    def __init__(self, azure_supported: Set[str], google_supported: Set[str], deepl_supported: Set[str], product_codes: Set[str]):
        self.azure_supported = azure_supported
        self.google_supported = google_supported
        self.deepl_supported = deepl_supported
        self.product_codes = {c.lower() for c in product_codes}

    def pick(self, lang_code: str) -> Tuple[str, str]:
        """
        Return (service, normalized_code_for_service).
        Priority: Azure -> Google -> DeepL. Raises if none support it.
        """
        code = lang_code.lower()
        if code not in self.product_codes:
            raise ValueError(f"Language '{lang_code}' not in product SUPPORTED_LANGUAGES")

        # Try Azure
        a_code = normalize_for_service(code, "azure")
        if self._is_supported("azure", a_code):
            return ("azure", a_code)

        # Try Google
        g_code = normalize_for_service(code, "google")
        if self._is_supported("google", g_code):
            return ("google", g_code)

        # Try DeepL
        d_code = normalize_for_service(code, "deepl")
        if self._is_supported("deepl", d_code):
            return ("deepl", d_code)

        raise RuntimeError(f"No translator supports target='{code}' (after normalization: azure={a_code}, google={g_code}, deepl={d_code})")

    def _is_supported(self, service: str, code: str) -> bool:
        s = code.lower()
        if service == "azure":
            # Azure often lists region/script variants (e.g., 'pt', 'pt-pt', 'pt-br', 'zh-hans/zh-hant')
            return s in self.azure_supported
        if service == "google":
            return s in self.google_supported
        if service == "deepl":
            return s in self.deepl_supported
        return False