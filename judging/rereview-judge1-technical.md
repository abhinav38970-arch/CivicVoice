# RE-REVIEW — Judge 1 (technical skeptic)
**Date:** 2026-10-13 · **Reviewer:** the CS professor who called it "a prompt chain, not engineering"
**Prior scores:** (a) 7 · (b) 5 · (c) 4 → **NO**
**Method:** I ran the code myself. Every fix below was verified empirically, not taken on trust.

## Fix verification

### Kill 1 — ASCII-only eval regex → unicode-aware grounding
**Verdict: FIXED** (with a disclosed residual)
- `eval.py::_tokens` now uses `re.findall(r"\w+", text.lower(), re.UNICODE)` with a CJK character-bigram fallback when token count < 3, and English stopword removal applies to pure-Latin tokens only. The old `[a-z0-9]+` is gone.
- Ran `python eval.py` myself: **11/11 self-tests pass**, including grounded hi/pa/zh/fa claims (overlap 1.0) and the same-script Chinese bigram case (0.706).
- Residual (honest, disclosed in EVAL_REPORT §4): non-English golden claims are scored via an injected `claim_en` (the English source text) because the corpus contains zero non-English chunk text — same-script matching is impossible by construction. So the "1.00 grounding" for hi/pa/zh/fa proves the *content* is in the source, not that the *translation* is faithful. The report states this plainly; translation faithfulness remains untested. This is a ceiling of keyword methods, not a lie.
- Minor: `eval_log.json` was generated against 903 chunks; corpus is now 1,238. EVAL_REPORT §2 discloses this ("903 chunks as of 2026-10-13; the corpus grew after the scrape expansion") and gives the regen command. Disclosed, not hidden.

### Kill 2 — circular verification (mock grading its own homework)
**Verdict: FIXED**
- `data/golden/` holds 5 entries × 3 claims × 6 languages (15 claims/language), all labeled "hand-verified, not live model output" in the files, the UI, and EVAL_REPORT.
- I spot-checked 3 citations against `data/parsed/` myself:
  1. Prop 1 claim ($11.25B bonds, $5.1B multifamily) → `ca-voter-guide-2026-general.pdf` p.13: chunk contains "$11.25 billion in state general obligation bonds" and "$5.1 billion to build and rehabilitate multifamily rental housing". **Supported.**
  2. Closed-session claim (Mar 18 2025, Gov Code 54957.6) → `20250318_CC_Minutes__CLOSED_SESSION.pdf` p.0: chunk contains "CONVENED TO A CLOSED SESSION at 5:16 p.m. (California Government Code 54957.6)". **Supported.**
  3. Prop 2 claim ($10B, K-12) → `ca-voter-guide-2024-general.pdf` p.4: chunk contains "Authorizes $10 billion in general obligation bonds for repair, upgrade, and construction of facilities at K–12 public schools". **Supported.**
- The harness has still never graded real model output (no key exists) — disclosed in EVAL_REPORT §5.3, and the demo no longer presents mock verdicts as proof.

### Kill 3 — lorem-ipsum fixture live in the index
**Verdict: FIXED** (empirically)
- `retriever.load_chunks()` enforces `data/SOURCE_MANIFEST.json` (filename + sha256); unlisted/modified files are skipped with a loud stderr warning.
- I planted a fake fixture JSONL in `data/parsed/` and ran `load_chunks()`: it was **skipped with the warning**, 1,238 chunks loaded from manifest files only. Fake removed afterward.
- The original `fremont-council-2026-07-11-agenda` fixture is absent from `data/raw/` and `data/parsed/`; `tests/test_retrieval_golden.py::test_quarantined_fixture_never_retrieved` passes.
- (False alarm checked: `grep lorem` hits in 3 parsed files are "ad va**lorem**" — Latin for property-tax text, not placeholder.)

### New since last review — corpus 344→1,238 chunks; metadata boost
**Verdict: PRINCIPLED, not a hack**
- `_metadata_boost()`: query-term overlap against section title + filename, bounded at +0.15 on cosine scores (~0.4–0.7). This is field-weighted hybrid retrieval — standard practice, documented in the docstring with its rationale (embeddings ignore labels like "CONFERENCE WITH LABOR NEGOTIATOR:").
- Ran `tests/test_retrieval_golden.py` myself: **9/9 pass** on the full 1,238-chunk corpus (was 8/9 before the boost — the expansion had crowded out the labor-minutes case).
- Honest test design: asserts top-5 membership, not rank-1. Residual: rank-1 precision is still approximate (a Union City meeting-schedule doc outranks the Fremont labor minutes at top-1 on the labor query). Bounded, disclosed, acceptable.
- `low_confidence` threshold semantics intact (nonsense query still triggers it — test passes).
- Style nit (not a flaw): `import re` sits inside `_metadata_boost` instead of at module top.

### Honesty architecture (new, verified live)
- `POST /api/ask` in mock mode returns **zero fabricated non-English text** — I confirmed 0 Devanagari chars in the response; it returns sources + "Live summaries need an LLM key — here are the sources we found." The original sin (English placeholders labeled "Hindi") is dead.
- Homepage serves all key elements: Hindi-first language picker, 5 featured cards, "How we check our work" panel, demo-mode banner.
- `GET /api/golden` serves 5 cards; Prop 1 Nov 2026 card returns real Devanagari with real citations.
- Repo-wide key scan: **no API keys** anywhere outside `.venv`.

## Re-scores

**(a) Quality of the idea: 7/10** (unchanged)
The idea didn't change, and it was never the problem: a real, specific problem (CA-14 language access to civic documents), with a genuine differentiator (per-claim citations + an accuracy harness). RAG-with-citations remains a familiar pattern rather than an invention, and the Nov 2026 Prop 1 card sharpens timeliness without changing originality. 7 is where it belongs.

**(b) Implementation: 7/10** (was 5)
Real, verified improvement: five working featured cards with genuine non-English output, clickable citations resolving to exact source text, an honest mock mode that refuses to fabricate, and a verification panel that speaks human. Deducted: arbitrary queries still need a real LLM key (inherent to the mock architecture, honestly disclosed), and I reviewed UI structure rather than pixel-level polish.

**(c) Coding excellence: 7/10** (was 4)
The load-bearing claims now hold — verified by running the code, not reading promises. Unicode-aware eval, an empirically-tested manifest guard, a principled retrieval boost with 9/9 golden tests, ~2,400 lines of readable code, clean JSON error paths, honest documentation of ceilings. Deducted: translation faithfulness is untestable by this harness (disclosed), retrieval rank-1 precision is approximate, thresholds are uncalibrated heuristics, and no real LLM has ever run through the pipeline.

## New fatal flaws
**None.** The remaining items are disclosed limitations, not hidden failures. Coverage note (not a code flaw): no FUSD school-board documents in the corpus — the Simbli portal is unreachable from this environment; the student can add them from his own browser.

## Verdict: YES — it clears the bar now
My original NO was specific: "the code as it stands would not survive a careful judge." I was the careful judge this time — I attacked every fixed claim empirically, planted a fake fixture, checked citations against source text, and scanned for keys. Everything held or was honestly disclosed. The entry is now a real, working, defensible piece of engineering: the verifiability loop (cited claims → clickable source → published eval method with stated limits) is substantive, not theater, and it directly answers the "prompt chain" objection. Whether it wins CA-14 depends on the district field, which I cannot see — but nothing in the entry itself is disqualifying anymore, and I have no remaining technical objection to it winning.
