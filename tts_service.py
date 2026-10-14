"""CivicVoice text-to-speech layer.

Primary path is the browser's built-in Web Speech API (free, no key) — the
frontend uses it by default. This module is the upgrade path for Abhinav's
own TTS API keys: when configured, /api/tts returns MP3 audio in the
requested language; when not, it reports unavailable and the frontend falls
back to the browser voice.

Environment:
  CIVICVOICE_TTS_PROVIDER  "google" (default; only provider implemented)
  CIVICVOICE_TTS_KEY       provider API key

Google Cloud Text-to-Speech v1 REST:
  POST https://texttospeech.googleapis.com/v1/text:synthesize?key=KEY
  {input: {text}, voice: {languageCode}, audioConfig: {audioEncoding: "MP3"}}
"""
import base64
import json
import os
import urllib.request
import urllib.error

PROVIDER = os.environ.get("CIVICVOICE_TTS_PROVIDER", "google").lower()
KEY = os.environ.get("CIVICVOICE_TTS_KEY", "")

# Max characters per request (Google v1 limit is 5000; stay well under).
MAX_CHARS = 2000


def available():
    return bool(KEY)


def synthesize(text, language_code):
    """Return MP3 bytes for the text, or None when unavailable.

    language_code is a BCP-47 tag like 'es-US'. Never raises for network
    issues; callers treat None as 'fall back to browser TTS'.
    """
    if not text or not available():
        return None
    text = text[:MAX_CHARS]
    if PROVIDER == "google":
        return _google_synthesize(text, language_code)
    return None


def _google_synthesize(text, language_code):
    url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={KEY}"
    payload = json.dumps({
        "input": {"text": text},
        "voice": {"languageCode": language_code},
        "audioConfig": {"audioEncoding": "MP3"},
    }).encode()
    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.load(resp)
    except (urllib.error.URLError, OSError, ValueError):
        return None
    try:
        return base64.b64decode(data["audioContent"])
    except (KeyError, TypeError, ValueError):
        return None
