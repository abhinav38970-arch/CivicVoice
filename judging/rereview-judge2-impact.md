# Re-review: Judge 2 (impact/presentation) — CivicVoice, 2026-10-13

Second look after the fix pass. Last night: (a) 6, (b) 4, (c) 7 → NO.
Method: read README.md, SUBMISSION.md, demo/VIDEO_SCRIPT.md; booted the app
(`python app.py --port 5010`) and used it as a Fremont resident would —
golden cards in all 6 languages, citation drill-down, free-form query path,
homepage first impression. Judged against the official CAC criteria.

## Per-fix verification

### Kill 1: "Zero non-English words anywhere" → FIXED
- Pulled the Prop 1 (Nov 2026) golden card in Hindi, Chinese, Punjabi, Farsi,
  Spanish, English. All real script, all saying the same real things
  ($11.25B housing bonds, $5.1B multifamily rental, $1.25B veterans home
  loans). Hindi Devanagari and Chinese Han confirmed character-level; Gurmukhi
  and Perso-Arabic confirmed as real script with consistent numbers.
- Every claim carries a real citation (`ca-voter-guide-2026-general.pdf`,
  pp. 13/16). `/api/chunk?file=...&page=13` returns the actual voter-guide
  source text — the $500–600M annual repayment figure is really there.
- Ran the project's own `advisory.py` guard over every golden claim in every
  language: 0 flags. Descriptive, never advisory. Verified, not assumed.

### Kill 2: "Developer tool in an app costume" → FIXED
- Homepage first impression: "Your city council and ballot, explained in your
  language." Language picker is first on the page (6 languages, native names).
  Featured cards are real cards with ✨ "Featured example — hand-verified"
  labels — honest about what they are.
- The 30-second resident test passes: pick language → tap one card → cited
  summary. No question to write, no settings.
- Free-form query with no LLM key (the video's "different moment"): returns
  `mode: "mock_sources"`, message "Live summaries need an LLM key — here are
  the sources we found," plus real retrieved sources. No fabricated claims.
  This is the single most persuasive behavior in the product and it works.
- "How we check our work" panel exists; demo-mode footer note is legible.
  The page never argues with an imaginary critic anymore.

### Kill 3: "Synthetic fixture in the index" → FIXED (UI-side confirmation)
- Zero occurrences of "lorem" in served HTML or any API response. Nothing
  placeholder-flavored appears anywhere a judge or camera can see.
  (Deep technical confirmation is Judge 1's lane.)

### Kill 4 (new): video script → FIXED
- `demo/VIDEO_SCRIPT.md` is a shootable 90 seconds: 4 timed shots with exact
  clicks I verified against the running app (language picker first, Prop 1
  card, citation side panel, "How we check our work" glance all exist where
  the script says they are).
- Leads with Prop 1 from the *current* November 2026 ballot — the right call
  three weeks before the election. The Do-NOT list is genuinely protective
  (never crop the demo-mode banner, never fake the refusal, rewrite voiceover
  in his own words).
- Would it persuade me? The arc — stat hook → one-tap magic in Hindi →
  citation drill-down → "describes, never tells you how to vote" → his face
  and name — is the strongest 90-second structure this entry has had.

## New flaws found (none fatal, all fixable before Oct 26)

1. **Stale numbers in the docs.** README.md and SUBMISSION.md both say "344
   chunks across 9 files" and README says "4 hand-verified featured examples."
   Reality: 1,238 chunks, 42 files, 5 golden cards. A judge who reads the
   README gets wrong numbers — a 10-minute fix, but it must happen before
   submission because wrong counts read as sloppiness or fabrication.
2. **eval_log.json says "903 chunks."** Same drift, one line. The log's method
   is honest about what it measured; the count note is just stale.
3. **The video is still unfilmed.** Everything above verifies the script is
   shootable — but the persuasion now lives or dies on his delivery. The
   pre-flight check on the adversarial query is non-optional.

## Re-scores

- **(a) Idea: 7/10** (was 6). The idea didn't change; its *visibility* did.
  The differentiators — citations as the interaction, the visible harness,
  the refusal — are now the product a judge touches, not engineering buried
  under a demo. Still a summarizer at its core, which caps it, but the
  verifiability loop is a genuine wedge and the current-election framing
  makes it timely rather than generic.
- **(b) Implementation: 8/10** (was 4). This is the transformation. Real
  product surface: language-first, one-tap cards, working citation
  drill-down, honest mock mode, legible demo banner. Docked two points for
  the stale doc counts (a judge-facing embarrassment if uncorrected) and
  because I did not verify mobile layout with my own eyes.
- **(c) Coding: 7/10** (unchanged). From the API surface: clean JSON schemas,
  proper 4xx paths, no key leakage, no placeholder text escaping anywhere.
  No new evidence to move it; deep code re-audit is Judge 1's lane.

## Verdict: YES — it can win CA-14 now

Last night it was "a winning backend looking for its product — forgettable
by dinner." Tonight the product exists: a resident picks her language, taps
one card, gets a cited summary of the *current* ballot in her script, and can
open the exact source page behind every sentence. The refusal behavior is the
kind of moment judges remember the next morning. The binding constraints are
no longer in the code — they're his: fix the stale counts (10 minutes), film
the video well (the script is ready), plug in an LLM key if he can before
submission. If he does those three things, this is a winning entry.
