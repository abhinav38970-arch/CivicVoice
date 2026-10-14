"""CivicVoice translation layer.

Abhinav supplies the API keys ("several free api keys working in the
background"). This module is the seam: when keys are present it translates
through the configured provider; when they are absent every function degrades
honestly (returns None / reports unavailable) instead of faking output.

Environment:
  CIVICVOICE_TRANSLATE_PROVIDER  "google" (default; only provider implemented)
  CIVICVOICE_TRANSLATE_KEY       provider API key

Google Cloud Translation v2 REST:
  POST https://translation.googleapis.com/language/translate/v2?key=KEY
  {q, target, source, format: "text"}
"""
import json
import os
import urllib.request
import urllib.error

PROVIDER = os.environ.get("CIVICVOICE_TRANSLATE_PROVIDER", "google").lower()
KEY = os.environ.get("CIVICVOICE_TRANSLATE_KEY", "")


def available():
    """True when a translation key is configured."""
    return bool(KEY)


def provider_name():
    return PROVIDER if available() else "none"


def _google_translate(text, target, source):
    url = f"https://translation.googleapis.com/language/translate/v2?key={KEY}"
    payload = json.dumps({
        "q": text,
        "target": target,
        "source": source,
        "format": "text",
    }).encode()
    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.load(resp)
    except (urllib.error.URLError, OSError, ValueError):
        return None
    try:
        return data["data"]["translations"][0]["translatedText"]
    except (KeyError, IndexError, TypeError):
        return None


def translate(text, target, source="en"):
    """Translate text; returns the translated string, or None when the
    service is unavailable/unconfigured. Never raises for network issues."""
    if not text or not available():
        return None
    if PROVIDER == "google":
        return _google_translate(text, target, source)
    return None


def translate_ui_strings(strings, target, source="en"):
    """Translate a dict of UI strings. Returns (translated_dict, failures).
    Untranslatable values keep their source text so the UI never blanks."""
    out, failures = {}, 0
    for k, v in strings.items():
        t = translate(v, target, source) if isinstance(v, str) and v else v
        if t is None and isinstance(v, str) and v:
            failures += 1
            t = v
        out[k] = t
    return out, failures
