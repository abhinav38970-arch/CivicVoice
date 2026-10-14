"""CivicVoice Phase 2 end-to-end demo.

Pipeline: retrieve(query) -> summarize(chunks, language, topic) -> evaluate(summary, chunks)
Runs fully on the deterministic MockLLM when no CIVICVOICE_LLM_API_KEY is set,
so the whole loop is testable with zero external dependencies.

Usage:
    .venv/bin/python demo.py [--query "..."] [--topic "..."] [--lang hi] [--k 5]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from retriever import retrieve
from summarizer import summarize
from eval import evaluate

LANG_NAMES = {
    "en": "English", "hi": "Hindi", "pa": "Punjabi",
    "zh": "Mandarin (Simplified)", "es": "Spanish", "fa": "Farsi",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", default="ballot measure school funding",
                    help="retrieval query")
    ap.add_argument("--topic", default="Proposition 2 school facilities bond measure",
                    help="topic handed to the summarizer")
    ap.add_argument("--lang", default="hi", choices=list(LANG_NAMES),
                    help="summary language code")
    ap.add_argument("--k", type=int, default=5, help="chunks to retrieve")
    args = ap.parse_args()

    key_set = bool(os.environ.get("CIVICVOICE_LLM_API_KEY"))
    print(f"LLM backend: {'REAL (' + os.environ.get('CIVICVOICE_LLM_MODEL', 'gpt-4o-mini') + ')' if key_set else 'MockLLM (no key set)'}")
    print(f"Query: {args.query!r} | topic: {args.topic!r} | language: {LANG_NAMES[args.lang]} | k={args.k}")
    print("=" * 70)

    # 1. RETRIEVE
    chunks = retrieve(args.query, k=args.k)
    print(f"\n[1] Retrieved {len(chunks)} chunks:")
    for i, c in enumerate(chunks, 1):
        print(f"    {i}. {c['section_title'][:60]!r} "
              f"({c['source_file']}, p.{c['page']}) score={c['score']:.3f}")

    # 2. SUMMARIZE
    summary = summarize(chunks, args.lang, args.topic)
    print(f"\n[2] Summary ({summary['language']}):")
    print(json.dumps(summary, ensure_ascii=False, indent=2)[:2000])

    # 3. EVALUATE
    result = evaluate(summary, chunks)
    print("\n[3] Eval verdict:")
    print(f"    citation_validity : {result['citation_validity']:.2f}")
    print(f"    grounding_score   : {result['grounding_score']:.2f}")
    print(f"    advisory_flags    : {result['advisory_flags'] or 'none'}")
    print(f"    VERDICT           : {result['verdict']}")

    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as e:
        # Startup failures (missing data, unloadable model) already carry a
        # human-readable explanation — print it, not a traceback.
        print(f"\nERROR: {e}")
        raise SystemExit(1)
