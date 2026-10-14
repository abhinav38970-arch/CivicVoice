"""CivicVoice demo web app — Congressional App Challenge 2026 (CA-14).

GET / serves the UI; POST /api/ask runs retrieval over the parsed corpus.
GET /api/golden serves hand-verified featured examples (curated cards).
GET /api/golden/<id> renders one featured example in the requested language.
GET /api/chunk?file=<name>&page=<n> returns the exact source chunk behind a
citation so anyone can verify a claim against its source.

Summarizing behavior:
- Hand-verified FEATURED examples render fully, in any language, with no key.
- With CIVICVOICE_LLM_API_KEY set: arbitrary queries get a live cited summary
  (retrieve -> summarize -> evaluate).
- Without a key: arbitrary queries NEVER get a mock/fabricated summary.
  The API returns the retrieved sources with their real citations plus an
  honest message instead.

Repo stays key-free: the LLM key is read only from the environment.
"""
import glob
import json
import os

from flask import Flask, jsonify, render_template, request

from retriever import retrieve
from summarizer import summarize, SUPPORTED_LANGUAGES
from eval import evaluate

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARSED_DIR = os.path.join(BASE_DIR, "data", "parsed")
GOLDEN_DIR = os.path.join(BASE_DIR, "data", "golden")

app = Flask(__name__)

LANG_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "pa": "Punjabi",
    "zh": "Mandarin (Simplified)",
    "es": "Spanish",
    "fa": "Farsi",
}

NATIVE_LANG_NAMES = {
    "en": "English",
    "hi": "हिन्दी",
    "pa": "ਪੰਜਾਬੀ",
    "zh": "中文",
    "es": "Español",
    "fa": "فارسی",
}

# True when no LLM key is configured -> /api/ask returns sources + honest
# message instead of fabricating a summary. Featured (golden) examples always
# render fully regardless of key status.
MOCK_MODE = not bool(os.environ.get("CIVICVOICE_LLM_API_KEY"))

LOW_CONFIDENCE_THRESHOLD = 0.30


# ---------------------------------------------------------------------------
# Featured (golden) examples: hand-verified cited summaries in all 6 languages.
# ---------------------------------------------------------------------------

def _load_golden_entries():
    entries = []
    if not os.path.isdir(GOLDEN_DIR):
        return entries
    for path in sorted(glob.glob(os.path.join(GOLDEN_DIR, "*.json"))):
        if os.path.basename(path) == "eval_log.json":
            continue  # Worker A's eval log is not a featured example
        try:
            with open(path, encoding="utf-8") as f:
                entry = json.load(f)
        except (OSError, ValueError):
            continue
        if isinstance(entry, dict) and entry.get("id") and entry.get("claims"):
            entries.append(entry)
    return entries


GOLDEN_ENTRIES = None  # lazy: re-read per request so new curated files appear live


def _get_golden_entries():
    """Load golden entries fresh on each call — cheap (a few small JSONs)
    and picks up files added while the server is running."""
    global GOLDEN_ENTRIES
    GOLDEN_ENTRIES = _load_golden_entries()
    return GOLDEN_ENTRIES


def _golden_by_id():
    return {e["id"]: e for e in _get_golden_entries()}


def _derive_card_title(entry):
    """Human card title, from the entry when provided, else from its slug."""
    if entry.get("card_title"):
        return entry["card_title"]
    eid = (entry.get("id") or "").lower()
    if "ballot" in eid:
        return "🗳️ What's on the ballot?"
    if "council" in eid:
        return "🏛️ Council labor negotiations"
    if "school" in eid:
        return "🏫 School funding"
    return "✨ " + (entry.get("id") or "featured").replace("-", " ").replace("_", " ").title()


def _validate_language(language):
    if not isinstance(language, str):
        return None
    language = language.strip().lower()
    if language not in SUPPORTED_LANGUAGES:
        return None
    return language


def _clean_str(value, default=""):
    return value.strip() if isinstance(value, str) else default


MAX_QUERY_CHARS = 2000


@app.get("/")
def index():
    return render_template(
        "index.html",
        languages=[
            {"code": c, "name": LANG_NAMES[c], "native": NATIVE_LANG_NAMES[c]}
            for c in SUPPORTED_LANGUAGES
        ],
        mock_mode=MOCK_MODE,
    )


@app.get("/api/golden")
def golden_list():
    """One-click cards for the front page."""
    return jsonify(
        [
            {
                "id": e["id"],
                "title": _derive_card_title(e),
                "query": e.get("query", ""),
                "topic": e.get("topic", ""),
            }
            for e in _get_golden_entries()
        ]
    )


@app.get("/api/golden/<entry_id>")
def golden_entry(entry_id):
    """Full hand-verified cited summary for one featured example."""
    entry = _golden_by_id().get(entry_id)
    if entry is None:
        return jsonify({"error": "unknown featured example"}), 404
    language = _validate_language(request.args.get("language"))
    if language is None:
        return jsonify({"error": "unsupported language"}), 400
    claims = []
    for c in entry.get("claims", []):
        texts = c.get("text", {}) or {}
        available = language in texts and bool(texts[language])
        # Never show English text under a non-English label silently; when the
        # requested translation is missing, say so plainly.
        claims.append(
            {
                "id": c.get("id"),
                "text": texts[language] if available else texts.get("en"),
                "language_available": available,
                "citation": c.get("citation", {}),
            }
        )
    return jsonify(
        {
            "id": entry["id"],
            "title": _derive_card_title(entry),
            "query": entry.get("query", ""),
            "topic": entry.get("topic", ""),
            "language": language,
            "featured": True,
            "featured_label": "✨ Featured example — hand-verified",
            "claims": claims,
        }
    )


# ---------------------------------------------------------------------------
# Citation verification: return the exact source chunk behind a citation.
# ---------------------------------------------------------------------------

def _safe_parsed_path(filename):
    """Resolve a source filename (the .pdf citation name) to its parsed
    .jsonl inside data/parsed/; None if unsafe or missing."""
    if not filename or os.path.basename(filename) != filename:
        return None
    jsonl = filename
    if jsonl.endswith(".pdf"):
        jsonl = jsonl[:-4] + ".jsonl"
    if not jsonl.endswith(".jsonl"):
        return None
    path = os.path.join(PARSED_DIR, jsonl)
    return path if os.path.isfile(path) else None


def _chunk_matches_page(chunk_page, page):
    if isinstance(chunk_page, (list, tuple)):
        return page in chunk_page
    return chunk_page == page


@app.get("/api/eval-summary")
def eval_summary():
    """On-screen proof for the verification story: the real results of running
    eval.py over every hand-verified golden claim in every language. Honest
    labeling: this evaluates the featured examples, not live model output."""
    try:
        with open(os.path.join(GOLDEN_DIR, "eval_log.json"), encoding="utf-8") as f:
            log = json.load(f)
    except (OSError, json.JSONDecodeError):
        return jsonify({"error": "eval log unavailable"}), 404
    per_lang = log.get("per_language", {})
    total_claims = sum(v.get("claims", 0) for v in per_lang.values())
    total_grounded = sum(v.get("grounded", 0) for v in per_lang.values())
    total_flags = sum(v.get("advisory_flags_total", 0) for v in per_lang.values())
    return jsonify(
        {
            "generated": log.get("generated"),
            "entries": len(log.get("entries", [])),
            "languages": sorted(per_lang.keys()),
            "total_claims": total_claims,
            "grounded": total_grounded,
            "advisory_flags": total_flags,
            "verdict": "PASS" if total_flags == 0 and total_claims > 0
            and total_grounded == total_claims else "FAIL",
            "note": "Hand-verified featured examples evaluated by eval.py; "
                    "not live model output.",
        }
    )


@app.get("/api/chunk")
def chunk():
    filename = request.args.get("file", "")
    try:
        page = int(request.args.get("page", ""))
    except (TypeError, ValueError):
        return jsonify({"error": "page must be an integer"}), 400
    path = _safe_parsed_path(filename)
    if path is None:
        return jsonify({"error": "unknown source file"}), 404
    matches = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                c = json.loads(line)
            except ValueError:
                continue
            if c.get("source_file") == filename and _chunk_matches_page(
                c.get("page"), page
            ):
                matches.append(c)
    if not matches:
        return jsonify({"error": "no chunk found for that file and page"}), 404
    c = matches[0]
    return jsonify(
        {
            "source_file": c.get("source_file"),
            "page": c.get("page"),
            "section_title": c.get("section_title", ""),
            "text": c.get("text", ""),
            "num_chunks_on_page": len(matches),
        }
    )


# ---------------------------------------------------------------------------
# /api/ask: arbitrary queries.
# ---------------------------------------------------------------------------

def _serialize_source(c):
    return {
        "source_file": c["source_file"],
        "page": c["page"],
        "section_title": c.get("section_title", ""),
        "text": c["text"],
    }


@app.post("/api/ask")
def ask():
    data = request.get_json(force=True, silent=True)
    if not isinstance(data, dict):
        # A JSON array / string / number body would crash .get() below —
        # reject it as JSON instead of a 500 page.
        return jsonify({"error": "request body must be a JSON object"}), 400
    query = _clean_str(data.get("query"))
    topic = _clean_str(data.get("topic")) or query  # topic falls back to query
    language = _validate_language(data.get("language"))
    try:
        k = int(data.get("k", 5))
    except (TypeError, ValueError):
        k = 5
    k = max(1, min(k, 10))

    if not query:
        return jsonify({"error": "query is required"}), 400
    if len(query) > MAX_QUERY_CHARS:
        return jsonify(
            {"error": f"query too long (max {MAX_QUERY_CHARS} characters)"}
        ), 400
    if language is None:
        return jsonify({"error": "unsupported language"}), 400

    try:
        chunks = retrieve(query, k=k)
    except Exception as e:  # noqa: BLE001 - surface as JSON, never a 500 page
        return jsonify({"error": str(e)}), 500
    if not chunks:
        return jsonify({"error": "no matching documents found"}), 404

    top_score = chunks[0].get("score", 0.0) or 0.0
    low_confidence = top_score < LOW_CONFIDENCE_THRESHOLD
    sources = [_serialize_source(c) for c in chunks]

    if MOCK_MODE:
        # Honesty architecture: with no LLM key, we must not fabricate a
        # summary (mock or otherwise) — show the real retrieved sources and
        # say so plainly.
        if low_confidence:
            message = (
                "We couldn't find strong sources for this — "
                "here are the closest matches."
            )
        else:
            message = (
                "Live summaries need an LLM key — "
                "here are the sources we found."
            )
        return jsonify(
            {
                "mode": "mock_sources",
                "language": language,
                "mock_mode": True,
                "low_confidence": low_confidence,
                "top_score": round(top_score, 4),
                "message": message,
                "sources": sources,
            }
        )

    # Live mode: summarize + evaluate.
    try:
        summary = summarize(chunks, language, topic)
        result = evaluate(summary, chunks)
    except Exception as e:  # noqa: BLE001 - surface as JSON, never a 500 page
        return jsonify({"error": str(e)}), 500

    response = {
        "mode": "live_summary",
        "summary": summary["summary"],
        "language": summary["language"],
        "mock_mode": False,
        "low_confidence": low_confidence,
        "top_score": round(top_score, 4),
        "eval": {
            "citation_validity": result["citation_validity"],
            "grounding_score": result["grounding_score"],
            "advisory_flags": result["advisory_flags"],
            "verdict": result["verdict"],
        },
        "sources_used": [
            {
                "source_file": c["source_file"],
                "page": c["page"],
                "section_title": c.get("section_title", ""),
            }
            for c in chunks
        ],
    }
    if low_confidence:
        response["note"] = (
            "We couldn't find strong sources for this — "
            "treat this summary with care."
        )
    return jsonify(response)


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="CivicVoice demo web app")
    ap.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("CIVICVOICE_PORT", "5000")),
        help="port to listen on (default 5000; env CIVICVOICE_PORT overrides)",
    )
    ap.add_argument(
        "--smoke",
        action="store_true",
        help="run the pipeline smoke test (retrieve -> evaluate) and exit",
    )
    args = ap.parse_args()

    if args.smoke:
        from smoke_test import main as smoke_main

        raise SystemExit(smoke_main())

    print(
        f"CivicVoice starting on http://127.0.0.1:{args.port}"
        + ("  [demo mode: no LLM key set]" if MOCK_MODE else "")
    )
    # Pre-check the port ourselves: Werkzeug's own "in use" message doesn't
    # suggest the fix, and we want the --port hint every time.
    import socket

    probe = socket.socket()
    try:
        probe.bind(("127.0.0.1", args.port))
    except OSError:
        print(f"\nERROR: port {args.port} is already in use by another program.")
        print(f"Fix: run with a different port —  python app.py --port {args.port + 1}")
        print("     (or set the CIVICVOICE_PORT environment variable)")
        raise SystemExit(1)
    finally:
        probe.close()
    try:
        app.run(host="127.0.0.1", port=args.port, debug=False)
    except OSError as e:
        # Tiny race window between the probe and app.run; same advice.
        print(f"\nERROR: could not start CivicVoice on port {args.port}: {e}")
        print(f"Fix: run with a different port —  python app.py --port {args.port + 1}")
        raise SystemExit(1)
