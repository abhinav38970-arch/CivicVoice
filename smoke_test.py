"""CivicVoice smoke test — verify the install in ~30 seconds.

Boots the real pipeline (retrieve -> evaluate) on one hand-verified golden
query and exits 0 on success, 1 on any failure. No LLM key needed.

Usage:
    python smoke_test.py
    python app.py --smoke
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GOLDEN_PATH = os.path.join(BASE_DIR, "data", "golden", "prop2-school-bonds.json")


def _fail(msg):
    print(f"SMOKE FAIL: {msg}")
    return 1


def main():
    from retriever import load_chunks, retrieve
    from eval import evaluate

    # [1] Corpus loads (clear human error if data files are missing).
    try:
        chunks = load_chunks()
    except RuntimeError as e:
        return _fail(str(e))
    if not chunks:
        return _fail("load_chunks() returned zero chunks")
    print(f"[1] corpus OK: {len(chunks)} chunks")

    # [2] Golden entry exists and is well-formed.
    try:
        with open(GOLDEN_PATH, encoding="utf-8") as f:
            golden = json.load(f)
    except (OSError, ValueError) as e:
        return _fail(f"could not read golden entry {GOLDEN_PATH}: {e}")
    query = golden.get("query", "")
    claims = golden.get("claims", [])
    if not query or not claims:
        return _fail("golden entry is missing its query or claims")
    print(f"[2] golden entry OK: {len(claims)} claims, query={query!r}")

    # [3] Retrieval works and returns well-formed chunks
    # (clear human error if the embedding model can't load, e.g. offline).
    try:
        retrieved = retrieve(query, k=5)
    except RuntimeError as e:
        return _fail(str(e))
    if not retrieved:
        return _fail("retrieve() returned no chunks")
    for c in retrieved:
        if not all(k in c for k in ("source_file", "page", "text", "score")):
            return _fail(f"malformed retrieved chunk keys: {sorted(c.keys())}")
    print(f"[3] retrieval OK: {len(retrieved)} chunks, "
          f"top score={retrieved[0]['score']:.3f}")

    # [4] Eval verdicts PASS on hand-verified golden claims (English) scored
    # against the full corpus, so every citation is guaranteed to match.
    summary = {
        "summary": [
            {"claim": c["text"]["en"], "citation": c["citation"]}
            for c in claims[:3]
        ],
        "language": "en",
    }
    result = evaluate(summary, chunks)
    print(f"[4] eval: citation_validity={result['citation_validity']:.2f} "
          f"grounding_score={result['grounding_score']:.2f} "
          f"advisory_flags={result['advisory_flags'] or 'none'} "
          f"verdict={result['verdict']}")
    if result["verdict"] != "PASS":
        return _fail(f"eval verdict was {result['verdict']}, expected PASS")

    print("SMOKE PASS: pipeline healthy (retrieve -> evaluate)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
