# COLD JUDGING — FINAL ROUND (Impact / Congressional Staffer Lens)

**Project:** CivicVoice — plain-language cited summaries of civic documents, CA-14
**Reviewer stance:** never seen this project before; did not read `judging/`. Read
README.md, SUBMISSION.md, demo/VIDEO_SCRIPT.md in full, then ran the app myself
(`python app.py --port 5099`) and used it as a Fremont resident would.

## What I did

- Booted the app clean on port 5099 (200 on `/`).
- Pulled all 5 featured cards; opened the Prop 1 housing-bond card in **Hindi** —
  real Devanagari script, 3 claims, each with a `(file, page)` citation.
- Clicked a citation: `/api/chunk?file=ca-voter-guide-2026-general.pdf&page=13`
  returned the exact source text — the claim's numbers ($11.25B bond,
  $500–600M/yr, 25 years) appear verbatim in the cited page. Verified, not vibes.
- Opened the winter-relief card in **Chinese** — real Han script, on the new
  city-website content (not just voter guides).
- Ran a free-form query ("fremont rent rules tenant protection 2026"): demo mode
  responded honestly — "Live summaries need an LLM key — here are the sources we
  found" — and the sources were real Fremont Rent Review Program content (5%
  threshold, $23/unit fee, RentReview@Fremont.gov).
- Ran a Hindi free-form query (स्कूल बॉन्ड): low_confidence=True, top score 0.149 —
  the app declined to answer strongly rather than invent one.
- Hit `/api/eval-summary`: 90/90 claims grounded, 0 advisory flags, verdict PASS,
  across all 6 languages, with an explicit "not live model output" note.
- Tried to break it: empty query → `{"error":"query is required"}`; bad language →
  400; `../../etc/passwd` traversal → 404; unknown card id → 404. All clean.

## Scores

**(a) Quality of the idea — 8/10.** This is the one demo of the day I'd remember
tomorrow morning. The problem is real, quantified, and sourced — 64.2% of Fremont
residents age 5+ speak a non-English language at home (Census QuickFacts, URL in the
docs) — and the timing is live ammunition: Prop 1 is on the November 2026 ballot
three weeks out, and the featured card is about it. The differentiator isn't
"summarizer"; it's that verifiability is the interaction — every sentence opens its
source page, the app shows how it checks its own work, and it refuses to invent
answers. Docked two: the outer shape (AI civic summarizer) is a familiar archetype,
and the six-language pitch overreaches given free-form retrieval is English-only.

**(b) Implementation — 7/10.** The 90-second resident flow works end to end:
language picker → card → real-script summary → click 📄 → real source page. The
verification panel shows a real PASS (90/90) from the real eval log. Error paths
are clean JSON, the demo-mode honesty is on screen everywhere, and the UI is plain
civic-service style — no decoration, no prompt-chain smell. Docked three: without
an LLM key the "app" is 5 hand-written cards, not a general tool; free-form
non-English queries fail (disclosed, but still a wall for the named audience);
the eval numbers live one click behind a collapsed panel.

**(c) Demonstrated excellence of coding — 7/10.** Judged by what survived use:
clean Flask API surface, proper 400/404s, traversal-proof chunk endpoint,
manifest-guarded corpus, honest mode separation, pinned requirements. Nothing I
touched crashed or leaked. Docked three: I didn't audit the pipeline at depth,
and the load-bearing path — real model output through summarize→evaluate — has
never run, so the harness is proven on its own mechanics only.

## Verified fatal flaws (ranked, all confirmed by using the app)

1. **The live product has never been demonstrated.** The pitch is
   retrieve→summarize→evaluate; what I could use was 5 hand-written cards plus
   honest source lists. Mock mode never fabricates — which is admirable — but it
   means the central AI behavior is entirely unproven. A judge asking "show me
   the AI" gets honesty, not a summary.
2. **Six languages is half a promise.** The featured cards are genuinely
   multilingual, but a Punjabi-speaking resident typing her own question hits a
   wall — non-English retrieval scores 0.149 and the app declines. The UI now says
   "ask in English," which is honest, but the hero pitch ("pick your language
   first") meets its limit immediately outside the 5 cards.
3. **The verification story is circular in the demo.** 90/90 PASS, 0 advisory
   flags — on hand-written, hand-verified claims. The log says so itself ("not
   live model output"). The eval harness has never checked a real answer, so the
   most persuasive number on screen is a rehearsal, not a performance.

## Verdict: YES — wins CA-14

Thirty demos deep, this is the one with a real problem, a real number, a live
election, citations that actually open, and the discipline to say what it can't do.
The flaws are pitch-vs-demo gaps, all disclosed in the open — and the disclosure
itself is the strongest signal in the room.
