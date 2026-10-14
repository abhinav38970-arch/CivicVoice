"""Regenerate data/golden/eval_log.json from all golden entries.

Method (matches EVAL_REPORT.md): each golden claim is expanded into 6
per-language summaries (claim text + claim_en for non-English) and run
through eval.evaluate() against the full manifest-guarded parsed corpus.
"""
import json, glob, os, sys, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eval as ev
import retriever

REPO = os.path.dirname(os.path.abspath(__file__))
GOLDEN_DIR = os.path.join(REPO, "data", "golden")
LANGS = ["en", "hi", "pa", "zh", "es", "fa"]

chunks = retriever.load_chunks()
print(f"corpus chunks: {len(chunks)}")

entries = []
per_lang = {l: {"claims": 0, "grounded": 0, "evaluated": 0,
                "cross_lingual_unevaluated": 0, "advisory_flags_total": 0}
            for l in LANGS}

for path in sorted(glob.glob(os.path.join(GOLDEN_DIR, "*.json"))):
    if os.path.basename(path) == "eval_log.json":
        continue
    entry = json.load(open(path, encoding="utf-8"))
    langs_out = {}
    for lang in LANGS:
        claims = []
        for c in entry["claims"]:
            item = {"claim": c["text"][lang], "citation": c["citation"]}
            if lang != "en":
                item["claim_en"] = c["text"]["en"]
            claims.append(item)
        res = ev.evaluate({"summary": claims}, chunks)
        langs_out[lang] = {
            "verdict": res["verdict"],
            "citation_validity": res["citation_validity"],
            "grounding_score": res["grounding_score"],
            "advisory_flags": res["advisory_flags"],
        }
        d = res["grounding_detail"]
        pl = per_lang[lang]
        pl["claims"] += len(claims)
        pl["grounded"] += d["grounded"]
        pl["evaluated"] += d["evaluated"]
        pl["cross_lingual_unevaluated"] += sum(
            1 for p in d["per_claim"] if p["status"] == "cross_lingual_unevaluated")
        pl["advisory_flags_total"] += len(res["advisory_flags"])
    entries.append({"id": entry["id"], "languages": langs_out})
    print(f"  {entry['id']}: " +
          ", ".join(f"{l}={langs_out[l]['verdict']}" for l in LANGS))

for lang, pl in per_lang.items():
    pl["grounding_rate_on_evaluated"] = round(
        pl["grounded"] / pl["evaluated"], 4) if pl["evaluated"] else 1.0

log = {
    "generated": datetime.date.today().isoformat(),
    "method": (
        "Each golden claim was expanded into 6 per-language summaries "
        "(claim text + claim_en for non-English) and run through "
        f"eval.evaluate() against the full parsed corpus ({len(chunks)} chunks). "
        "Non-English claims are scored via claim_en against English chunk text "
        "(overlap proves the CONTENT is in the source, not that the translation "
        "is faithful); citations are matched by (source_file, page)."
    ),
    "entries": entries,
    "per_language": per_lang,
}
out = os.path.join(GOLDEN_DIR, "eval_log.json")
json.dump(log, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"wrote {out} ({len(entries)} entries)")
fails = [(e["id"], l, v["verdict"])
         for e in entries for l, v in e["languages"].items()
         if v["verdict"] != "PASS"]
print("non-PASS:", fails if fails else "NONE — all PASS")
