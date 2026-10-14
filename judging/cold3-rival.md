# Cold Judging Run 3 of 3 — Rival's Review

**Persona:** sharp high-school hackathon winner (two regional wins), judging a rival's CAC entry cold. Never seen this project before. Looking for the holes.

**Method:** read app.py, eval.py, summarizer.py, llm_client.py, retriever.py (skim), advisory.py; ran the app live on port 5123; hit /api/golden, /api/golden/<id>, /api/chunk, /api/ask; ran pytest + eval self-tests; tested Hindi retrieval and advisory-guard evasion empirically. Did NOT read ~/workspace/civicvoice/judging/.

## Scores

**(a) Quality of the idea: 7/10** — Real, specific problem (Fremont's 64.2% non-English-at-home households, sourced to Census QuickFacts) with a real audience, and "every claim cited + accuracy harness" is a genuine differentiator against the sea of AI-summarizer entries. Docked: RAG-with-citations is a known pattern, not an invention; and the "6 languages" promise overreaches — search/retrieval is English-only (verified below), so the multilingual claim covers 5 pre-written cards, not the product.

**(b) Implementation: 7/10** — Working app, real 42-file / 1,238-chunk corpus, honest "hand-verified" labeling, defensive error handling, clean UX. Docked hard for two things: the eval VERDICT — the project's central technical claim — never appears on screen in the no-key demo (metrics stay "—"; they only populate in the live path), and free-form non-English queries return garbage sources. Coverage is 5 curated cards plus a source browser.

**(c) Coding excellence: 8/10** — Genuinely strong: unicode-aware eval with an explicit cross-lingual honesty policy, manifest-guarded corpus, metadata-aware retrieval boost, schema-validated summarizer with advisory post-hoc check, JSON error paths everywhere, tests green (3 passed, 11/11 self-tests). Docked: the live LLM path is dead code in practice (never exercised with a real key), and advisory detection is naive substring matching.

## Ranked fatal flaws (all verified empirically, no vibes)

**1. The eval harness — the core differentiator — is invisible in the demo.** (Severity: high, presentation)
Verified: templates/index.html only populates `mValidity`/`mGrounding`/`mVerdict` inside the `live_summary` branch, which requires `CIVICVOICE_LLM_API_KEY`. With no key (the state any judge sees), the "How we check our work" panel shows "—" for every metric, and featured golden cards never touch `evaluate()`. The pitch's strongest claim ("verified accuracy") has zero on-screen proof. A judge hears about the harness but never sees it work.

**2. Retrieval is English-only; non-English search fails.** (Severity: high, functional)
Verified: `retrieve('स्कूल बॉन्ड', k=3)` (Hindi for "school bonds") returned top score **0.149** — below the 0.30 low-confidence floor — on irrelevant docs (a Newark agenda, Prop 45, a budget doc). The English control `retrieve('school bonds')` scored **0.702** on exactly the right voter-guide section. Root cause: all-MiniLM-L6-v2 is an English-only embedding model. A Hindi/Punjabi/Chinese-speaking resident typing in their own language gets weak, irrelevant sources. The "6 languages" label on the picker does not extend to the ask box — even with an LLM key, the retriever would feed the model garbage chunks.

**3. The live AI pipeline has never run — the demo is 5 hand-written Q&A cards.** (Severity: high, substance)
Verified: `MOCK_MODE` is true (no key in env); `MockLLM.complete()` returns generic English placeholders; the golden entries are hand-written translations (honestly labeled "curated featured example, hand-verified"). `summarize()`'s real path, `evaluate()` on real model output, and translation fluency are all untested. If a judge asks "did the AI generate this summary?", the honest answer is no. The retrieve→summarize→evaluate loop — the thing being pitched — is unproven end to end.

**4. Advisory guard is trivially evaded by paraphrase.** (Severity: medium, safety)
Verified: `contains_advisory("You might consider supporting this measure.")` → `[]`; `"Many voters are backing this proposition."` → `[]`. Direct phrasing ("You should vote yes") is caught, but any competent LLM paraphrase sails through. The "never tells you how to vote" guarantee rests on substring matching against 115 patterns — and it has never been tested against real model output, which is the only place it matters.

**5. Keyword-overlap grounding is a weak truth signal.** (Severity: medium, technical)
Verified by code reading: per-claim threshold is 0.15 overlap; a claim sharing 15% of keywords with the cited chunk counts as "grounded" even if it misattributes (e.g., opponents' rhetoric framed as fact — the code's own cross-lingual policy admits overlap "proves the CONTENT is in the source, not that the translation is faithful"). For non-English claims, scoring runs against an English `claim_en` shadow, so translation faithfulness is never checked at all.

**6. Coverage is 5 questions.** (Severity: low-medium, scope)
Verified: `/api/golden` serves exactly 5 entries; without a key, any other query returns `mode: "mock_sources"` — sources only, no summary. The "app" as demoed is 5 curated cards plus a source browser. Fine for a demo, thin as a product.

## Acknowledged strengths (rival's grudging credit)

- The eval harness is real engineering, not theater: unicode tokenization, CJK bigram fallback, explicit cross-lingual honesty policy, 11/11 self-tests green. I tried to break it and couldn't on its own terms.
- Citation drill-down works: I verified a Prop 1 Hindi claim's citation resolves via `/api/chunk` to source text containing the $11.25B figure. The verifiability loop is functional.
- Honesty architecture is genuinely rare: no fabricated summaries, "hand-verified" labels, footer discloses demo mode. Most student AI projects fake this; this one doesn't.
- Corpus is real: 42 parsed government PDFs, 1,238 chunks, manifest-guarded.

## Verdict: YES — it wins CA-14

Three live attack lines exist (show me the AI; type in Hindi; where's the PASS badge), and any judge who pokes for 5 minutes will find them. But judging is relative: against a typical district field, this is a polished, honest, working product on a real local problem with a real corpus and functional citation verification. The flaws are gaps between the pitch and the demo, not deception — and the honesty about those gaps is itself the strongest signal. A sharper rival with a live multilingual loop could take it; as it stands, this clears the bar.
