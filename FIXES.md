# CivicVoice — Fix Log: Two-Judge Verdict → Fix Pass

**Date:** 2026-10-13 (overnight, before the Oct 26 CAC deadline)
**Judges:** Judge 1 (technical skeptic, official CAC rubric a/b/c) and Judge 2
(impact/presentation, official CAC rubric a/b/c). Both voted **NO** on 2026-10-12.
Reports: `judging/judge1-technical.md`, `judging/judge2-impact.md`.
**Fix crew:** 3 workers (data+eval / UX / demo+submission), coordinator regression
pass. Every fix below was re-verified by the coordinator — outputs quoted are
from the coordinator's own runs, not worker self-reports.

Convergent kills (both judges found independently): **(1)** synthetic lorem-ipsum
fixture live in the retrieval index; **(2)** zero real non-English words anywhere,
eval regex blind to 5 of 6 languages; **(3)** circular verification (mock grading
its own homework). All three are dead now.

---

## Judge 1 — Technical fixes

### FATAL 1 — Grounding regex was Latin-script-only → FIXED
`eval.py` used `re.compile(r"[a-z0-9]+")`: any Devanagari/Gurmukhi/Han/Perso-Arabic
claim scored grounding 0.0 → auto-FAIL. The harness provably failed the very
languages the app exists for.
**Fix:** unicode-aware tokenization (`re.findall(r"\w+", text.lower(), re.UNICODE)`,
English stopwords on Latin tokens only) + character-bigram fallback when < 3 tokens
(CJK). Plus an honest cross-lingual policy: non-English claims carry `claim_en`
(their English source text) and are grounded through it — overlap proves the
*content* is in the source, never that the translation is faithful; without
`claim_en` a cross-script claim is marked `cross_lingual_unevaluated` and excluded
from the FAIL threshold (verdict then needs validity 1.0 + zero advisory flags).
**Verify:** `.venv/bin/python eval.py` → **11/11 self-tests pass**, including
grounded hi/pa/zh/fa claims ≥ 0.5, an ungrounded claim at 0.0, and the
no-`claim_en` case not forcing FAIL. Policy documented in `EVAL_REPORT.md` §4.

### FATAL 2 — Circular verification (mock graded its own homework) → FIXED (as far as honestly possible)
**Fix:** `data/golden/` — 4 curated entries (`prop2-school-bonds`,
`closed-session-labor`, `midyear-winter-relief`, `charter-advisory`), 3 claims each
in all 6 languages (72 claim-texts), every citation hand-verified against
`data/parsed/*.jsonl`, each file labeled "curated featured example, hand-verified;
not live model output". The fixed eval was run over all of them:
`data/golden/eval_log.json` (machine-readable) + `EVAL_REPORT.md` (human-readable,
with a Limitations §5 that states what the harness *cannot* prove).
**Result:** 12 claims × 6 languages, grounding rate 1.00, 0 advisory flags,
all 24 verdicts PASS.
**Verify:** read `EVAL_REPORT.md`; inspect `data/golden/eval_log.json`.
**Honest remainder:** no real model output has ever been graded — no LLM key
exists. The log grades curated examples, and says so on its face.

### FATAL 3 — Lorem-ipsum fixture live in the index → FIXED
**Fix:** deleted `data/raw/fremont-council-2026-07-11-agenda.pdf` and its parsed
JSONL; created `data/SOURCE_MANIFEST.json` (9 files, filename + sha256 +
description) enforced in `retriever.load_chunks()` — unlisted or modified files
are skipped with a loud stderr warning; commented the fixture's mirror URL out of
`scraper.py` so it can't be re-downloaded; rebuilt the index (344 chunks).
**Verify:** probe `city council closed session labor negotiations` → top hits are
real minutes, **0 fixture hits**; `tests/test_retrieval_golden.py` includes a
`fixture-quarantine` case (planted-fake-file test skipped with warning, then
removed).

### FATAL 4 — Retrieval unmeasured and weak → MEASURED; quality flagged, not solved
**Fix:** `tests/test_retrieval_golden.py` — 7 real queries with expected documents
in top-5, plus quarantine + low-confidence cases: **9/9 pass** (plain python),
**3/3 pass** under pytest. `retrieve()` now returns `low_confidence: true` when
the top score < 0.30, and the UI presents weak matches honestly instead of as
answers.
**Verify:** `.venv/bin/python -m pytest tests/ -q` → 3 passed.
**Honest remainder:** ranking quality itself is unimproved — some council queries
still top out at 0.29–0.40 cosine and the charter Q&A outranks the labor minutes.
Measured, flagged, not fixed. (A separate modeling task, documented in README.)

### FATAL 5 — "Six languages" was an untested claim → PARTIALLY FIXED
**Fix:** real translated text now exists and is served: 12 claims × 6 languages
of hand-verified Devanagari, Gurmukhi, Simplified Chinese, Spanish, and Farsi in
`data/golden/`, rendered by `/api/golden/<id>?language=`.
**Verify:** `curl "/api/golden/prop2-school-bonds?language=hi"` → 3 claims of
real Hindi, `featured_label: "✨ Featured example — hand-verified"`.
**Honest remainder:** translation fluency and 8th-grade reading level are
untested (no key); the docs claim nothing about them.

### FATAL 6 — Two inconsistent advisory lists → FIXED
**Fix:** new `advisory.py` — single source of truth, 115 patterns across all 6
languages, imported by both `summarizer.py` and `eval.py`.
**Verify:** `grep -n "ADVISORY_PATTERNS\|BANNED_ADVISORY" summarizer.py eval.py` →
both import from `advisory`.
**Honest remainder:** substring matching can't catch paraphrase; documented in
`EVAL_REPORT.md` §5.

### Non-fatal — Reproducibility → FIXED
`requirements.txt` now pins `==` versions (Flask 3.1.3, sentence-transformers
6.1.0, numpy 2.5.4, httpx 0.28.1, pymupdf 1.28.2, pdfplumber 0.11.10, pytest
9.1.1); `tests/` runs under pytest. `openai` deliberately unpinned/absent — the
venv doesn't have it and `llm_client.py` falls back to httpx → urllib (noted in
requirements.txt).

---

## Judge 2 — Impact/presentation fixes

### FATAL 1 — Demo couldn't show the core promise (zero non-English words) → FIXED
**Fix:** featured-example cards serve real translated summaries. The video script
is written to show a Hindi/Punjabi summary on screen in the 15–45s "magic" beat.
**Verify:** golden endpoints above; `demo/VIDEO_SCRIPT.md` shot 2.

### FATAL 2 — Developer tool wearing an app costume → FIXED
**Fix:** language picker first (persisted in `localStorage`), one-click featured
cards (🗳️ What's on the ballot? / 🏛️ Council labor talks / 🏠 Winter relief &
safe parking / 📋 Charter committee Q&A), free-text demoted to "Ask your own
question", topic merged, k-sources removed.
**Verify:** `GET /` → cards render; `GET /api/golden` → 4 cards with titles.

### FATAL 3 — Verification panel destroyed its own credibility → FIXED
**Fix:** rewritten as "How we check our work" in plain human language; raw
metrics moved to collapsed `<details>For the technically curious</details>`;
the words "prompt chain" appear **0 times** on the served home page (verified via
`curl | grep -ci`).
**Honesty architecture:** featured examples labeled "✨ Featured example —
hand-verified"; arbitrary mock-mode queries **never fabricate summaries** — they
return retrieved sources + "Live summaries need an LLM key — here are the
sources we found." (Verified over HTTP: `mode: mock_sources`, no summary key,
zero non-English text invented.) Gibberish queries get `low_confidence: true`
+ "We couldn't find strong sources for this."

### FATAL 4 — Fake document in index → FIXED (see Judge 1 FATAL 3)

### FATAL 5 — No demo video script → FIXED
`demo/VIDEO_SCRIPT.md`: 90-second storyboard — timed shots, exact clicks, full
voiceover, on-screen callouts, 7-item do-NOT list, and a scripted 15-second
adversarial "different moment" (the app honestly declining a query it can't
source). Written to the fixed UI; shot list needs one pass against the running
app before recording day.

### FATAL 6 — Mock banner poisoned first impressions → FIXED
Banner shrunk and moved to the footer; featured examples make it unnecessary
during the demo take.

### FATAL 7 — Originality optics / the "different" moment → FIXED (product + script)
The trust moment is now *felt*, not listed: click any 📄 citation → side panel
shows the exact source chunk (`GET /api/chunk?file=&page=`, path-traversal
blocked — verified 404; page-as-int-or-list handled). Plus the honest-decline
path scripted in the video.

---

## New docs
- `SUBMISSION.md` — CAC form draft (header: "DRAFT — the student reviews and
  edits before submitting"). (a) opens with the literal first clause; (b) who
  it's for; (c) how built (honest about featured-example vs live-key modes);
  (d) originality. Stat verified for the hook: **64.2%** of Fremont residents
  age 5+ speak a language other than English at home — U.S. Census Bureau
  QuickFacts 2020–2024 (resolves the earlier 64% vs 62% conflict; phrased
  exactly as the Census defines it). Data USA PUMA sourcing for the six-language
  set (Chinese 19.6%, Hindi 10.1%, Spanish 9.08%).
- `demo/VIDEO_SCRIPT.md`, `EVAL_REPORT.md` — see above.

## Coordinator's regression results (all green, run 2026-10-13)
| Check | Result |
|---|---|
| `python eval.py` self-tests | 11/11 pass |
| `python tests/test_retrieval_golden.py` | 9/9 pass |
| `pytest tests/` | 3 passed |
| `demo.py` (es query) | verdict PASS, validity 1.00 |
| Flask `/api/golden` | 4 cards, correct titles |
| Flask `/api/golden/<id>?language=hi/pa` | real Devanagari/Gurmukhi, featured label |
| Flask `/api/chunk` | exact source text; traversal → 404 |
| Flask `/api/ask` mock (Hindi nonsense) | honest `mock_sources`, no fabricated summary |
| Home page | "prompt chain" × 0 |
| Repo key scan | no API keys |
| `requirements.txt` | pinned |

## What is still NOT fixed (do not claim these)
1. **Retrieval ranking quality** — measured and flagged, not improved. Free-form
   non-English queries fail outright (Hindi 0.149 vs English 0.702 on the same concept);
   the UI now says "ask in English, then read the summary in your language."
2. **No real model output ever graded** — no key; golden claims are curated.
3. **Translation fluency / reading level** — untested.
4. **Paraphrase evasion of advisory detection** — inherent to substring matching.
5. **Live-LLM path** (`CIVICVOICE_LLM_API_KEY`) — never exercised end-to-end.
6. Video script needs one pass against the running app before recording.

## Cold judging round — 2026-10-13 (3 fresh judges, no prior knowledge)
All three judges said YES (wins CA-14): technical 7/7/8, impact 7/7/7, rival 7/7/8.
Verified flaws found and fixed in this round:
- Eval VERDICT was invisible on screen in the demo (panel showed "—"). Fixed: new
  `/api/eval-summary` endpoint + "Featured examples check: 90/90 claims grounded,
  0 advisory flags → PASS" rendered in the verification panel from the real eval_log.json.
- Video script's "different moment" refusal take used a query that doesn't trigger
  the low-confidence path (corpus too broad now; everything scores > 0.30). Fixed:
  the take now demonstrates the real demo-mode honesty — "Live summaries need an LLM
  key — here are the sources we found" instead of a fabricated summary.
- Free-form non-English retrieval failure was undocumented. Fixed: README + UI now
  state retrieval is English-only; six-language support is for the featured summaries.

## Corpus expansion — 2026-10-13 (Abhinav directive: rules/announcements/services)
- Added 7 HTML-derived sources (20 chunks): Fremont Rent Review Program + process,
  Source of Income Discrimination ordinance + FAQ, Emergency Preparedness hub +
  earthquake/wildfire guides, CERT program, 8 city press releases (Mar 2025–Aug 2026),
  Alameda County SSA CalFresh + CalWORKs/Medi-Cal + Fremont office.
- Corpus: 1,238 → **1,258 chunks**, 42 → **49 files**. fremont.gov blocks script
  fetching (bot protection); pages hand-extracted via browser, transcribed to
  `data/parsed/html-*.jsonl`, SHA-256 pinned in SOURCE_MANIFEST.json like PDFs.
- Provenance labeled honestly in manifest: CalFresh via Jan-2025 archived copy,
  CalWORKs/Medi-Cal via 211 Alameda County (agency site unreachable); press releases
  marked "refresh monthly or it rots."
- Retrieval probes on new content: rent rule 0.754, CalFresh 0.658, earthquake 0.824,
  police-chief release 0.815 — all hit the right source.
- Full suite re-run on 1,258-chunk corpus: eval.py 11/11, retrieval golden 9/9,
  pytest 3/3, eval_log regenerated 90/90 PASS.

## Final cold judging round — 2026-10-13 (2 fresh judges, expanded corpus + plain UI)
- Technical: 7/7/8 → YES. "Engineering, not a prompt chain." Planted-fixture
  rejection re-verified; 15/15 citations resolve; new rent-rules content sharpens
  problem fit (rent query 0.806). All 5 flaws already disclosed limitations.
- Impact: 8/7/7 → YES. "The demo of the day I'd remember tomorrow." One fix
  applied: eval summary line moved out of the collapsed tech-details panel so
  "90/90 PASS" is visible without clicking.
- Running total: 7 independent judging passes (2 re-review, 3 cold, 2 final),
  7 YES, 0 NO.
