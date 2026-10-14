#!/usr/bin/env python3
"""
CivicVoice Phase 2 — citation-grounded summarizer.

summarize(chunks, language, topic) -> {"summary": [...], "language": ...}

- Validates the 6 supported language codes.
- Loads system + user prompt templates from prompts/ (never hardcoded).
- Passes the top chunk texts as numbered SOURCES with source_file/page labels.
- Parses the LLM's JSON; one "valid JSON only" retry, then ValueError.
- Normalizes citation page to int (first element when a list).

The advisory-language ban (no vote advice) is enforced in the system prompt AND
re-checked in summarize() post-hoc: if a claim contains a banned advisory
phrase, ValueError is raised rather than emitting it.
"""

import json
import os

from llm_client import LLMClient, LANGUAGE_NAMES
from advisory import contains_advisory

SUPPORTED_LANGUAGES = ("en", "hi", "pa", "zh", "es", "fa")

PROMPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts")
SYSTEM_PROMPT_FILE = os.path.join(PROMPTS_DIR, "summarize_system.txt")
USER_PROMPT_FILE = os.path.join(PROMPTS_DIR, "summarize_user.txt")

MAX_SOURCES = 8        # cap on chunks passed in the prompt
SOURCE_CHAR_BUDGET = 1500  # max chars of text per source (head-truncated)

# Post-hoc advisory-language guard (also enforced in the system prompt).
# Patterns live in advisory.py — the single source of truth shared with
# eval.py. This check scans all six languages, not just English.


def _load_template(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError as e:
        raise RuntimeError(f"Could not load prompt template {path}: {e}") from e


def _fill(template, **values):
    """Replace {token} placeholders; all other braces are left untouched."""
    out = template
    for key, val in values.items():
        out = out.replace("{" + key + "}", str(val))
    return out


def _format_page(page):
    if isinstance(page, (list, tuple)):
        return str(page[0]) if page else "0"
    return str(page)


def _build_sources_block(chunks):
    """Numbered SOURCES block with source_file/page labels for the prompt."""
    lines = []
    for i, ch in enumerate(chunks[:MAX_SOURCES], start=1):
        src = ch.get("source_file", "unknown.pdf")
        page = _format_page(ch.get("page", 0))
        title = ch.get("section_title", "")
        text = (ch.get("text", "") or "").strip()
        if len(text) > SOURCE_CHAR_BUDGET:
            text = text[:SOURCE_CHAR_BUDGET] + " …"
        lines.append(
            f"[SOURCE {i}] file: {src} | page: {page} | section: {title}\n{text}"
        )
    return "\n\n".join(lines)


def _normalize_page(page):
    if isinstance(page, (list, tuple)):
        page = page[0] if page else 0
    try:
        return int(page)
    except (TypeError, ValueError) as e:
        raise ValueError(f"Citation page is not an int: {page!r}") from e


def _check_schema(result, language):
    if not isinstance(result, dict):
        raise ValueError(f"Summarizer output must be a JSON object, got: {type(result)}")
    if result.get("language") != language:
        raise ValueError(
            f"Language mismatch: expected {language!r}, got {result.get('language')!r}"
        )
    items = result.get("summary")
    if not isinstance(items, list) or not items:
        raise ValueError("Summarizer output must contain a non-empty 'summary' list")
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"summary[{i}] must be an object")
        if not isinstance(item.get("claim"), str) or not item["claim"].strip():
            raise ValueError(f"summary[{i}].claim must be a non-empty string")
        cit = item.get("citation")
        if not isinstance(cit, dict):
            raise ValueError(f"summary[{i}].citation must be an object")
        if not isinstance(cit.get("source_file"), str) or not cit["source_file"].strip():
            raise ValueError(f"summary[{i}].citation.source_file must be a non-empty string")
        cit["page"] = _normalize_page(cit.get("page"))
        claim_lc = item["claim"]
        hits = contains_advisory(claim_lc)
        if hits:
            lang, phrase = hits[0]
            raise ValueError(
                f"summary[{i}] contains banned advisory phrase {phrase!r} "
                f"(lang {lang}): descriptive-only output required"
            )
    return result


def _parse_json_or_retry(client, system_prompt, user_prompt):
    """Parse the LLM response; one 'valid JSON only' retry, then ValueError."""
    raw = client.complete(system_prompt, user_prompt)
    for attempt in (1, 2):
        try:
            return json.loads(raw), raw
        except json.JSONDecodeError:
            if attempt == 1:
                nudge = (
                    user_prompt
                    + "\n\nYour last reply was not valid JSON. "
                    "Return VALID JSON only: no prose, no markdown fences, "
                    "exactly matching the schema in the system instructions."
                )
                raw = client.complete(system_prompt, nudge)
            else:
                raise ValueError(
                    "LLM output was not valid JSON after retry. Raw text attached.",
                    raw,
                )
    # unreachable
    raise ValueError("unreachable")


def summarize(chunks, language, topic):
    """Summarize topic from chunks in the given language.

    chunks: list of {source_file, page (int or [start, end]), section_title, text}
    language: one of en, hi, pa, zh, es, fa
    topic: str describing what to summarize

    Returns {"summary": [{"claim", "citation": {"source_file", "page"}}], "language"}.
    """
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"Unknown language code {language!r}; supported: {list(SUPPORTED_LANGUAGES)}"
        )
    if not chunks:
        raise ValueError("summarize() requires at least one chunk")
    if not isinstance(topic, str) or not topic.strip():
        raise ValueError("topic must be a non-empty string")

    system_template = _load_template(SYSTEM_PROMPT_FILE)
    user_template = _load_template(USER_PROMPT_FILE)
    lang_name = LANGUAGE_NAMES[language]

    system_prompt = _fill(
        system_template, language_name=lang_name, language_code=language
    )
    user_prompt = _fill(
        user_template,
        topic=topic.strip(),
        language_name=lang_name,
        language_code=language,
        sources=_build_sources_block(chunks),
    )

    client = LLMClient(chunks=chunks, language=language, topic=topic.strip())
    result, _raw = _parse_json_or_retry(client, system_prompt, user_prompt)
    return _check_schema(result, language)


if __name__ == "__main__":
    demo_chunks = [
        {
            "source_file": "demo-guide.pdf",
            "page": 12,
            "section_title": "Measure A",
            "text": "Measure A would authorize a half-cent sales tax for road repairs for 20 years.",
        }
    ]
    print(json.dumps(summarize(demo_chunks, "en", "Measure A"), ensure_ascii=False, indent=2))
