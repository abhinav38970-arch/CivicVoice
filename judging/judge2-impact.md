# JUDGE 2 — Impact & Presentation Verdict: CivicVoice (CA-14)

**Role:** congressional-staffer / non-technical judge. Thirty student demos watched today. Judged ONLY against the official 2026 CAC criteria:
a. Quality of the idea (creativity, originality)
b. Implementation of the idea (UX, design)
c. Demonstrated excellence of coding and programming skills

**Method:** read README.md, app.py, templates/index.html, static/style.css; ran the Flask app; hit `/api/ask` with two real queries (Hindi ballot query, Punjabi council query); inspected `data/parsed/` contents. Everything below is from what I actually saw, not what the docs claim.

---

## Scores

### (a) Quality of the idea — 6/10
The problem is real and specific: CA-14 (Fremont) is one of the most linguistically diverse districts in the country, and civic documents are genuinely unreadable to large parts of the community. "Everyone feels involved and understands the language" is a good pitch sentence. But "AI summarizes documents in other languages" is the single most common student-AI-project archetype of the last two years — I have seen this demo, with different fonts, many times. The genuine differentiators (claim-level citations, the eval harness, descriptive-never-advisory by design) are *engineering* differentiators: real, but invisible to a non-technical judge in 90 seconds unless the demo makes them visceral. As presented, this pattern-matches to "multilingual summarizer #47."

### (b) Implementation (UX/design) — 4/10
This is where it bleeds. What I experienced: a form with **Query**, **Topic (optional)**, **Language**, **Sources: 3/5/8**, and an Ask button. Those are developer affordances, not a resident's tool. A Punjabi-speaking grandmother does not know what "k sources" means, does not know what to type into an empty box (cold start — nothing tells her what's inside the 347 chunks), and cannot distinguish "query" from "topic." The language picker is the cruelest part: it promises six languages and delivers **zero non-English words** — the mock returns English boilerplate literally reading *"This is a mock summary in Hindi about…"*. The claims themselves are vacuous even as English ("The document's section contains the official text, which readers can consult on the cited page" — that is a pointer, not a summary). The Verification panel, meant to be the moat, speaks metrics to a non-technical judge ("Grounding score 0.50" next to a PASS badge looks like a rigged test) and its subhead — *"why this is more than a prompt chain"* — argues with an imaginary critic instead of telling the user why to trust it. It works as software. It fails as a product a real Fremont resident could use.

### (c) Coding excellence — 7/10
The strongest pillar, and it's genuinely good for a student entry: clean Flask app, input validation with proper JSON 400s, errors surfaced as JSON never trace pages, honest automatic MockLLM fallback, vendored embedding model so the pipeline runs offline, an eval harness with self-tests, a real 347-chunk parsed corpus behind it. The code I read is careful and the API behaved exactly as documented under my own testing, including error paths. Docked points only because the most impressive engineering (the eval/advisory-guard design) currently serves placeholder content — excellence of code in service of a demo that can't show its value.

---

## FATAL FLAWS (ranked, most lethal first)

1. **The demo cannot show the product's core promise.** Not one word of Hindi, Punjabi, Chinese, Spanish, or Farsi exists anywhere in the system. The entire pitch is "understands the language"; the entire demo is English boilerplate. A judge watching the 1–3 minute video sees an English search box returning English filler with a language dropdown that changes nothing. *Nothing else on this list matters until this is fixed — this alone loses the competition.*

2. **It's a developer tool wearing an app costume.** Query + topic + k-sources; no browsing, no curated entry points ("What's on the ballot," "This week's council agenda"), total cold start. The people this is supposedly for could not operate it. The demo video therefore cannot show a human story, because the product has no human entry point.

3. **The Verification panel destroys its own credibility.** "Grounding score: 0.50" displayed next to "VERDICT: PASS" — any judge who asks what 0.50 means hears "it barely passed its own test." And the subhead "why this is more than a prompt chain" is defensive insider language; a staffer who's watched 30 demos reads it as protesting too much. Trust UI must speak human, not metrics.

4. **A fake document is still in the retrieval index.** `fremont-council-2026-07-11-agenda.pdf` — the synthetic lorem-ipsum fixture — is parsed and indexed. The rules explicitly allow judges to run the app themselves. One adversarial (or unlucky) query surfacing fake council business = instant, unrecoverable credibility death.

5. **No demo video script exists.** There is no script, no storyboard, no arc anywhere in the repo. Without one, the video will be an uns narrated screen recording of a form — and I will have forgotten it by demo #31.

6. **The mock banner poisons first impressions.** "Demo mode — mock summaries (connect an LLM key for live translations)" sits directly under the tagline. It's honest, but it tells the judge "this isn't real" before they've seen a single thing work.

7. **Originality optics.** In a stack of AI entries, the burden is on this one to feel different in the first 30 seconds. Right now the first 30 seconds feel identical to every AI summarizer demo. The differentiator must be a *felt moment*, not a features list.

---

## FIX LIST (concrete, in flaw order)

1. **Get real non-English output on screen before the video — non-negotiable.** Either do one real-key session and record it, or (more robust) pre-bake 2–3 golden demo responses: generate full cited summaries in Hindi + Punjabi + Spanish for the exact demo queries with a real model, verify every citation by hand, and cache them so the demo path serves the golden response for those queries. The video must show real Devanagari/Gurmukhi/Spanish text. This is an afternoon of work, not a rebuild.
2. **Rebuild the front page around a resident, not the pipeline.** Language picker FIRST and persist it. Below it, one-click curated cards — "🗳️ What's on the ballot" and "🏛️ This week's council agenda" — that fire pre-set queries and render full cited summaries. Demote the raw query box to "Ask your own question," merge or kill the "topic" field, and hide k-sources behind an "advanced" disclosure (or drop it entirely).
3. **Rewrite the Verification panel in human language.** Headline: "Every sentence traced to its source." Body: tap any 📄 citation to see the exact page it came from. Move the raw metrics (citation validity, grounding, flags) into a collapsed "for the technically curious" section. Delete the words "prompt chain" from the product UI forever — never let the product sound defensive.
4. **Quarantine the fixture TODAY.** Delete `fremont-council-2026-07-11-agenda.pdf` from `data/raw/` and its `.jsonl` from `data/parsed/`, rebuild the embedding index, and add a filename blocklist (or a `FIXTURE` marker check) so it can never re-enter the corpus. Verify with a retrieval query afterward.
5. **Write the 90-second video script and storyboard it before recording:**
   - 0–15s: the human problem — a Fremont grandmother, the voter guide she can't read, the CA-14 multilingual reality (one real stat, sourced).
   - 15–45s: the magic — one click, in HER language, on screen, real script visible.
   - 45–75s: the trust — tap a citation → lands on the exact source page; "it describes, it never tells you how to vote" (say the advisory-guard out loud, plainly).
   - 75–90s: the builder, one line on why he built it, the ask.
   Voiceover + face. Never an unnarrated screen recording.
6. **Fix the banner for the demo take.** Best: the golden-response fix (#1) makes the banner unnecessary during recording. Minimum: restyle it smaller and move it to the footer during the video build.
7. **Manufacture the "different" moment.** In the first 30 seconds of the video AND above the fold on the page: "Most AI summarizers invent facts. CivicVoice refuses to say anything it can't point to." Then *prove* it: demo an adversarial query where the app declines or the eval FAILs something live. Nothing persuades like a refusal — a PASS badge is cheap, a caught failure is proof.

---

## Overall verdict: NO — as it stands, this does not win CA-14.

The idea is real, the audience is specific, and the engineering is genuinely strong — this is a winning *backend* looking for its product. But a judge experiences an entry, not a repo: and the entry as it stands is an English-language pipeline demo that cannot demonstrate its own core promise, wrapped in a developer UI, with a fake document still in the index and no video script. That is not a winning entry; in a room of thirty demos it is forgettable by dinner. The good news: every fatal flaw above is fixable before October 26, and the most important one — real multilingual output on screen — is an afternoon's work, not a rebuild. If the fixes land, this becomes genuinely competitive: specific audience, real problem, and a verifiable engineering story no other summarizer entry will have.
