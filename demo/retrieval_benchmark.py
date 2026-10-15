"""Multilingual retrieval benchmark — before/after the embedding swap.

For every golden claim, in each of the 6 verified languages, the claim text
is used as the query and the claim's cited source_file is the expected
answer. Measures recall@1/3/5 and top-1 score per language.

Run:  .venv/bin/python demo/retrieval_benchmark.py --tag before
Saves: demo/retrieval_benchmark_<tag>.json
"""
import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from retriever import MODEL_NAME, retrieve  # noqa: E402

LANGS = ("en", "es", "hi", "pa", "zh", "fa")
K = 5


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True, help="e.g. before / after")
    args = ap.parse_args()

    cases = []
    for path in sorted(glob.glob("data/golden/*.json")):
        if "eval_log" in path:
            continue
        data = json.load(open(path, encoding="utf-8"))
        for claim in data.get("claims", []):
            expected = (claim.get("citation") or {}).get("source_file")
            if not expected:
                continue
            for lang in LANGS:
                q = (claim.get("text") or {}).get(lang, "").strip()
                if q:
                    cases.append({"query": q, "lang": lang,
                                  "expected": expected,
                                  "claim": claim.get("id"),
                                  "file": os.path.basename(path)})

    print(f"{len(cases)} cases ({len(cases)//len(LANGS)} claims x {len(LANGS)} langs), "
          f"model={MODEL_NAME}")
    results = []
    for i, c in enumerate(cases):
        hits = retrieve(c["query"], k=K)
        rank = next((r + 1 for r, h in enumerate(hits)
                     if h["source_file"] == c["expected"]), None)
        results.append({
            "lang": c["lang"], "claim": c["claim"], "file": c["file"],
            "expected": c["expected"],
            "rank": rank,
            "top1_file": hits[0]["source_file"] if hits else None,
            "top1_score": hits[0]["score"] if hits else 0.0,
            "expected_score": next((h["score"] for h in hits
                                    if h["source_file"] == c["expected"]), 0.0),
        })
        if (i + 1) % 20 == 0:
            print(f"  {i + 1}/{len(cases)}...")

    summary = {}
    for lang in LANGS:
        rs = [r for r in results if r["lang"] == lang]
        n = len(rs)
        summary[lang] = {
            "n": n,
            "recall@1": sum(1 for r in rs if r["rank"] == 1) / n,
            "recall@3": sum(1 for r in rs if r["rank"] and r["rank"] <= 3) / n,
            "recall@5": sum(1 for r in rs if r["rank"] and r["rank"] <= 5) / n,
            "mean_top1_score": sum(r["top1_score"] for r in rs) / n,
            "mean_expected_score": sum(r["expected_score"] for r in rs) / n,
        }
        s = summary[lang]
        print(f"  {lang}: R@1={s['recall@1']:.2f} R@3={s['recall@3']:.2f} "
              f"R@5={s['recall@5']:.2f} top1={s['mean_top1_score']:.3f}")

    out = {"model": MODEL_NAME, "k": K, "summary": summary, "results": results}
    path = f"demo/retrieval_benchmark_{args.tag}.json"
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"saved {path}")


if __name__ == "__main__":
    main()
