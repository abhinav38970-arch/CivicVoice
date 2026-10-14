#!/usr/bin/env python3
"""
CivicVoice Phase 2 — LLM client.

- Reads env vars: CIVICVOICE_LLM_BASE_URL (default https://api.openai.com/v1),
  CIVICVOICE_LLM_API_KEY, CIVICVOICE_LLM_MODEL (default "gpt-4o-mini").
- LLMClient.complete(system_prompt, user_prompt) -> str (raw text, expected JSON).
- If a key is set: real OpenAI-compatible POST to {base_url}/chat/completions,
  temperature 0.2. Uses the `openai` package when importable, else `httpx`,
  else stdlib `urllib`. Raises a clear error on HTTP failure.
- If NO key is set: MockLLM — deterministic, schema-valid fake JSON that cites
  real chunk metadata (never invented filenames). Designed for offline work and
  for the eval harness; NOT a real summary.
"""

import json
import os


DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4o-mini"
TEMPERATURE = 0.2

LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "pa": "Punjabi",
    "zh": "Mandarin (simplified Chinese)",
    "es": "Spanish",
    "fa": "Farsi (Persian)",
}


def _first_page_as_int(page):
    """Normalize a chunk page (int or [start, end] list) to an int."""
    if isinstance(page, (list, tuple)):
        return int(page[0]) if page else 0
    return int(page)


class MockLLM:
    """Deterministic fake used when no CIVICVOICE_LLM_API_KEY is set.

    Returns schema-valid JSON with two generic DESCRIPTIVE claims that cite the
    first provided chunk's real source_file/page metadata. Never advisory.
    """

    def __init__(self, chunks, language, topic):
        self.chunks = chunks or []
        self.language = language
        self.topic = topic

    def complete(self, system_prompt, user_prompt):
        if self.chunks:
            first = self.chunks[0]
            source_file = str(first.get("source_file", "unknown.pdf"))
            page = _first_page_as_int(first.get("page", 0))
        else:
            source_file = "unknown.pdf"
            page = 0
        lang_name = LANGUAGE_NAMES.get(self.language, self.language)
        claim1 = (
            f"This is a mock summary in {lang_name} about '{self.topic}'. "
            f"The source document describes the topic as written; "
            f"see the cited page for the exact wording."
        )
        claim2 = (
            f"The document's section on '{self.topic}' contains the official "
            f"text, which readers can consult on the cited page."
        )
        return json.dumps(
            {
                "summary": [
                    {
                        "claim": claim1,
                        "citation": {"source_file": source_file, "page": page},
                    },
                    {
                        "claim": claim2,
                        "citation": {"source_file": source_file, "page": page},
                    },
                ],
                "language": self.language,
            },
            ensure_ascii=False,
        )


def _post_via_openai_pkg(base_url, api_key, model, system_prompt, user_prompt):
    import openai  # noqa

    client = openai.OpenAI(base_url=base_url, api_key=api_key)
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEMPERATURE,
        )
    except Exception as e:
        raise RuntimeError(f"LLM API call failed ({type(e).__name__}): {e}") from e
    try:
        return resp.choices[0].message.content
    except (AttributeError, IndexError) as e:
        raise RuntimeError(f"LLM API returned an unexpected response shape: {e}") from e


def _post_via_httpx(base_url, api_key, model, system_prompt, user_prompt):
    import httpx

    url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": TEMPERATURE,
    }
    try:
        r = httpx.post(
            url,
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
            timeout=60.0,
        )
    except Exception as e:
        raise RuntimeError(f"LLM HTTP request failed ({type(e).__name__}): {e}") from e
    if r.status_code >= 400:
        raise RuntimeError(
            f"LLM API HTTP {r.status_code} from {url}: {r.text[:500]}"
        )
    try:
        data = r.json()
        return data["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError) as e:
        raise RuntimeError(f"LLM API returned an unexpected response shape: {e}") from e


def _post_via_urllib(base_url, api_key, model, system_prompt, user_prompt):
    import urllib.request
    import urllib.error

    url = base_url.rstrip("/") + "/chat/completions"
    payload = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": TEMPERATURE,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:500]
        raise RuntimeError(f"LLM API HTTP {e.code} from {url}: {detail}") from e
    except Exception as e:
        raise RuntimeError(f"LLM HTTP request failed ({type(e).__name__}): {e}") from e
    try:
        data = json.loads(body)
        return data["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError) as e:
        raise RuntimeError(f"LLM API returned an unexpected response shape: {e}") from e


class LLMClient:
    """OpenAI-compatible chat client with automatic MockLLM fallback.

    Pass `chunks`, `language`, `topic` so the mock path can cite real chunk
    metadata. Signature of complete() stays (system_prompt, user_prompt).
    """

    def __init__(
        self, base_url=None, api_key=None, model=None,
        chunks=None, language="en", topic="",
    ):
        self.base_url = base_url or os.environ.get(
            "CIVICVOICE_LLM_BASE_URL", DEFAULT_BASE_URL
        )
        self.api_key = api_key or os.environ.get("CIVICVOICE_LLM_API_KEY", "")
        self.model = model or os.environ.get("CIVICVOICE_LLM_MODEL", DEFAULT_MODEL)
        self.chunks = chunks
        self.language = language
        self.topic = topic

    @property
    def is_mock(self):
        return not bool(self.api_key)

    def complete(self, system_prompt, user_prompt):
        """Return raw text (expected to be JSON)."""
        if not self.api_key:
            return MockLLM(self.chunks, self.language, self.topic).complete(
                system_prompt, user_prompt
            )
        return self._real_complete(system_prompt, user_prompt)

    def _real_complete(self, system_prompt, user_prompt):
        try:
            import openai  # noqa: F401
        except ImportError:
            openai = None
        if openai is not None:
            return _post_via_openai_pkg(
                self.base_url, self.api_key, self.model, system_prompt, user_prompt
            )
        try:
            import httpx  # noqa: F401
        except ImportError:
            httpx = None
        if httpx is not None:
            return _post_via_httpx(
                self.base_url, self.api_key, self.model, system_prompt, user_prompt
            )
        return _post_via_urllib(
            self.base_url, self.api_key, self.model, system_prompt, user_prompt
        )
