# CivicVoice — Eval Report (2026-10-12)

This report documents the accuracy harness (`eval.py`), what was actually run
through it, and — just as important — what it cannot prove. Written for
technical judges: no theater, only what the code did.

## 1. What the harness checks

`evaluate(summary_json, retrieved_chunks)` returns three metrics plus a
verdict:

- **citation_validity** — fraction of claims whose `(source_file, page)`
  citation matches a retrieved chunk (page ranges supported on both sides).
- **grounding_score** — fraction of *evaluated* claims whose keyword overlap
  with the cited chunk's text reaches the 0.15 threshold
  (`overlap = |claim keywords ∩ chunk keywords| / |claim keywords|`).
- **advisory_flags** — voting-advice language hits across all six languages,
  from the single shared pattern list in `advisory.py`.

**Verdict FAIL** iff any advisory flag fires, citation_validity < 1.0, or the
grounding score over *evaluated* claims is < 0.5.

## 2. Method: what was actually run

Two independent runs, both deterministic, no LLM, no API key:

1. **`python eval.py` self-tests (11/11 pass).** English control cases
   (clean PASS / bogus-citation FAIL / advisory FAIL), plus multilingual
   grounding cases: grounded Devanagari, Gurmukhi, Simplified Chinese, and
   Farsi claims (each ≥ 0.5 overlap), an ungrounded claim scoring 0.0, a
   cross-lingual claim with no English source marked `cross_lingual_unevaluated`
   (excluded from FAIL — verdict PASS on validity + no advisory flags), and a
   same-script Chinese claim exercising the character-bigram fallback
   (overlap 0.71).
2. **Golden-set run over `data/golden/`** — every claim in all 6 languages
   (English, Hindi, Punjabi, Simplified Chinese, Spanish, Farsi) passed
   through `evaluate()` against the full parsed corpus (1,258 chunks across
   49 official source files as of 2026-10-13; eval_log.json regenerated that day).
   Machine-readable log: `data/golden/eval_log.json`.
   Regenerate with: `python gen_eval_log.py` (repo root).

The golden set is **hand-written, hand-verified** — each claim was checked by
a person against the cited page text, then translated by hand. Every golden
file carries `"note": "curated featured example, hand-verified 2026-10-12;
not live model output"`. They are demonstration fixtures, not model output.

## 3. Results: per-language table

| Language | Claims | Grounded | Evaluated | Grounding rate (on evaluated) | Advisory flags |
|---|---|---|---|---|---|
| English (en) | 15 | 15 | 15 | 1.00 | 0 |
| Hindi (hi) | 15 | 15 | 15 | 1.00 | 0 |
| Punjabi (pa) | 15 | 15 | 15 | 1.00 | 0 |
| Chinese (zh) | 15 | 15 | 15 | 1.00 | 0 |
| Spanish (es) | 15 | 15 | 15 | 1.00 | 0 |
| Farsi (fa) | 15 | 15 | 15 | 1.00 | 0 |

- 15 claims per language = 5 curated entries × 3 claims each
  (`prop2-school-bonds`, `closed-session-labor`, `midyear-winter-relief`,
  `charter-advisory`, `prop1-2026-housing-bond` — the November 2026
  Proposition 1 housing bond, added 2026-10-13).
  The log was regenerated 2026-10-13 against the final set
  (`python gen_eval_log.py`).
- All citations valid; no advisory-language flags in any language.

## 4. Cross-lingual grounding policy (the honest version)

Keyword overlap can only validate a claim against chunk text written in the
**same script**. A Devanagari claim will never keyword-overlap English chunk
text — and scoring it that way would be meaningless. So:

- A claim dict may carry **`claim_en`**: the English source text the
  non-English claim was translated from.
- When claim and chunk are in different scripts, grounding is computed
  against `claim_en` if present. **This proves the *content* is in the
  source — it does NOT validate the translation.** We never claim otherwise.
- Without `claim_en`, the claim is marked `cross_lingual_unevaluated` and
  **excluded** from the FAIL threshold (verdict then rests on citation
  validity == 1.0 and zero advisory flags).

Real translation-quality checking (fluency, faithfulness, reading level)
requires bilingual human review or a dedicated MT-quality model. Neither has
been run in this project.

## 5. Limitations — what this harness cannot do

1. **Paraphrase evades advisory detection.** Both the summarizer's ban and
   the eval's flags are substring matches against an enumerated pattern list
   (`advisory.py`, 6 languages, 115 patterns). "You might consider
   supporting this measure" or any novel phrasing passes silently. This is a
   keyword backstop, not a demonstrated safety property. The guard has never
   fired on a real model path because no real model has ever run.
2. **Keyword grounding cannot check attribution or framing.** During review,
   a draft claim ("the state estimates Prop. 2 would cost about $18 billion")
   grounded at 0.44 against the **"ARGUMENT AGAINST Proposition 2"** section —
   the $18B figure was opponents' rhetoric, not a state estimate. The harness
   counts such claims as "grounded" because the words overlap; it cannot tell
   that a claim misattributes its source. This is a fundamental ceiling of
   keyword-overlap metrics, and the reason every golden claim was also
   hand-verified by a person against the cited page. (The offending draft was
   removed, not shipped.)
3. **Mock vs. real model.** No LLM API key exists in this project. The
   harness has graded mock English placeholders (whose grounding scored 0.50,
   exactly on the FAIL boundary) and these hand-written golden claims — never
   real model output in any language. The demo video must not present a
   mock-run verdict as proof of real accuracy.
4. **Grounding thresholds are weak by design.** The per-claim threshold (0.15)
   and verdict threshold (0.5) are heuristics, not calibrated measurements.
   A claim can be "grounded" at 0.16 while saying something the source only
   vaguely supports.
5. **Retrieval is measured and improved, not solved.** `tests/test_retrieval_golden.py`
   (9/9 pass on the 1,258-chunk corpus) asserts the right document lands in the top-5
   for 7 real queries, and `retrieve()` now returns `low_confidence: true` when the top
   score is below 0.30. A 2026-10-13 fix added a metadata boost: query terms matching a
   chunk's human-authored section title/filename add up to 0.15 to the cosine score
   (`METADATA_BOOST_WEIGHT` in `retriever.py`), because embeddings ignore labels like
   "CONFERENCE WITH LABOR NEGOTIATOR:". Residual weakness: top scores for some council
   queries are still 0.29–0.40, and ranking among near-duplicate council docs is
   approximate. Weak matches are *flagged*; the boost helps but ranking is not solved.

## 6. What was NOT tested

- Translation fluency, faithfulness, or the "8th-grade reading level" claim
  in any non-English language (no real translations exist yet).
- Retrieval recall on non-English queries.
- Advisory-language detection on real model output (only on curated claims
  and synthetic self-test strings).
- `parser.py`'s two-column recovery and header/footer stripping against
  ground truth (no parser golden tests exist yet).
- End-to-end pipeline with a real API key (`demo.py --lang hi` on real
  translations through `evaluate()`).

## 7. Files

- `eval.py` — harness (self-tests: `python eval.py`)
- `advisory.py` — single source of truth for advisory patterns (used by
  `eval.py` and `summarizer.py`)
- `data/golden/*.json` — 4 curated entries, hand-written and hand-verified
  2026-10-12 (a duplicate fifth entry was removed during review; the log was
  regenerated against the final set)
- `data/golden/eval_log.json` — machine-readable per-claim scores
- `tests/test_retrieval_golden.py` — retrieval golden tests
  (`pytest tests/test_retrieval_golden.py`, or plain `python`)
- `data/SOURCE_MANIFEST.json` — corpus allowlist enforced by
  `retriever.load_chunks()`

---

## 8. Addendum — Full honest build (2026-10-14)

**New claims:** 4 pass/fail impact claims added to the golden set (Prop 1 c4/c5,
Prop 2 c4/c5, `kind: impact_pass` / `impact_fail`), each translated by hand into
all 6 languages. Pass/fail claims are descriptive entailments of the official voter
guide text (e.g. "if it passes, the state issues $X in bonds and pays $Y/year to
repay them"), never voting advice — 0 advisory flags across all languages.

**One failure found and fixed:** the first draft of Prop 2's Spanish fail-claim
grounded at 0.091 against its cited chunk (below the 0.15 threshold) — the English
source wording shared too little vocabulary with the chunk text. The EN claim was
rewritten with source-grounded terms and all 5 translations redone; a per-claim
re-run across all 6 languages × all claims then showed **0 ungrounded**.

**Final numbers (`python gen_eval_log.py`, deterministic, no LLM):**

- Claims: **114** (19 per language × 6 languages)
- Grounded: **114/114**
- Advisory flags: **0**
- Entry verdicts: 5 entries × 6 languages = **30/30 PASS**
- `eval.py` self-tests: **11/11 PASS** (unchanged)

**What this still does not prove:** the non-English impact claims are scored via
their `claim_en` against English chunk text — overlap proves the *content* is in the
source, not that the translation is faithful or fluent. UI strings in `i18n.py` are
drafts, not native-speaker reviewed.

## Adversarial eval upgrade (2026-10-14, from outside AI feedback)

`eval_adversarial.py` adds the 4 test types keyword grounding cannot see:

1. **supported_claim** — key numbers in the claim must appear in the cited chunk.
2. **contradicted_claim** — a plausible-but-false claim (number swapped) must be
   REJECTED. Demonstrated: the old `evaluate()` PASSES "Prop 5 would RAISE the
   threshold to 75%" (high word overlap, wrong numbers); `evaluate_strict()`
   FAILS it via `contradiction_detected()`.
3. **missing_info** — `tests/test_eval_adversarial.py`: /api/ask in no-key mode
   returns sources + honest decline, never a fabricated summary.
4. **multilingual_fidelity** — amounts/dates across the 6 verified languages
   match English: 75/75 golden claims OK, with locale digits normalized
   (Devanagari/Arabic-Indic/Persian) and legitimate zh conversions accounted
   for (billion→yi ×10, million→yi ÷100, month words→month numbers).

`demo/eval_false_claim_demo.py` prints a human-readable false-claim injection
transcript for the demo video (synthetic fixture, clearly labeled).

pytest: 5/5. eval.py self-tests: 11/11. Adversarial self-tests: 6/6.

## Source-and-status panel (2026-10-14)

Every civic item now carries: issuing agency, document, date, and a
current/archived status chip. Golden entries have a `source` metadata block;
`/api/notices` adds agency + archived status. The ballot result card and
notice feed render the panel; citations still one-tap to the exact passage.

## Multilingual retrieval upgrade (2026-10-15, branch `multilingual-retrieval`)

Outside review (Claude Haiku 4.5, which read the repo) flagged the core
weakness: non-English retrieval is broken — the embedding model
(all-MiniLM-L6-v2) is English-oriented. Benchmark
(`demo/retrieval_benchmark.py`: golden claim text as query in 6 languages,
expected doc = claim's cited source file, 114 cases):

| lang | R@1  | R@3  | R@5  | mean top-1 |
|------|------|------|------|------------|
| en   | 0.63 | 0.84 | 0.84 | 0.647      |
| es   | 0.00 | 0.11 | 0.11 | 0.344      |
| hi   | 0.05 | 0.11 | 0.16 | 0.202      |
| pa   | 0.05 | 0.11 | 0.11 | 0.334      |
| zh   | 0.00 | 0.11 | 0.11 | 0.269      |
| fa   | 0.00 | 0.00 | 0.00 | 0.285      |

The fix (on this branch): swap to `intfloat/multilingual-e5-base` with the
required `query: `/`passage: ` prefixes; the cached index records its model
name in `data/index/model.txt` and rebuilds automatically on model change.
`tests/test_retriever_swap.py` verifies prefix + rebuild logic with a stubbed
model (2/2 pass).

Status: code complete, NOT yet end-to-end verified. The build VM's pipe to
Hugging Face is throttled (~2KB/s; the 1.1GB model would take days), so the
re-embedding and after-benchmark must run on a machine with normal internet
(Abhinav's Mac). See README "Multilingual retrieval upgrade" for the exact
commands. Do not merge to master until the after-benchmark is recorded here.
