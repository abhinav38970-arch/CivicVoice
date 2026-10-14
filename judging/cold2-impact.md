# COLD JUDGING RUN 2 — Impact / Memorability Review

**Reviewer persona:** congressional staffer, 30 demos deep, tired. Cold review — no prior
exposure to this project. Read README.md, SUBMISSION.md, demo/VIDEO_SCRIPT.md, then ran
`python app.py` and used the app as a Fremont resident would. Did NOT read
~/workspace/civicvoice/judging/ (per instructions).

**Date:** 2026-10-13.

## What I actually did

- Booted the app (homepage 200), listed 5 golden featured cards.
- Pulled the Prop 1 (Nov 2026) card in Hindi, Chinese, Punjabi, Farsi: all real script,
  real claims ($11.25B bond, $500–600M/yr repayment, veterans program), real citations
  (ca-voter-guide-2026-general.pdf pp. 13/16).
- Clicked a citation via `/api/chunk?file=ca-voter-guide-2026-general.pdf&page=13`:
  returned the actual source text ("Authorized new borrowing $11.25 billion… Annual
  cost to pay off bond $500 million to $600 million… 25 years"). The claim is genuinely
  supported. The citation loop is REAL, not decorative.
- Free-form queries in mock mode: returns `mock_sources` with "Live summaries need an
  LLM key — here are the sources we found." Never fabricates a summary. Honest.
- Adversarial queries: "fremont property tax rate change 2026" → 0.634, returns budget
  sources (no decline). "best tacos in fremont open late" → 0.471 (no decline).
  "quantum computing qubits entanglement" → 0.147, low_confidence: True (decline fires).
  "shakespeare hamlet soliloquy analysis" → 0.156, decline fires.
- Error paths: empty query → 400, bad language → 400, `../../etc/passwd` traversal → 404.
- Homepage HTML: hero "Your city council and ballot, explained in your language.",
  language picker with native names (हिन्दी, ਪੰਜਾਬੀ, 中文, Español, فارسی), "How we
  check our work" panel present, demo-mode footer note present. No lorem ipsum anywhere.

## Scores

**(a) Quality of the idea: 7/10.** The problem is real, specific, and quantified with a
sourced stat (64.2% of Fremont residents 5+ speak a non-English language at home —
cited to Census QuickFacts; I did not re-verify the number myself). The wedge is the
verifiability loop (every sentence cited, clickable to source, visible accuracy checks,
designed refusal) — not "AI summarizer," and I could feel the difference using it.
Docked: the outer shape (multilingual summarizer of public docs) is a recognizable
student-AI archetype; the originality lives in the trust architecture, which takes a
minute to perceive.

**(b) Implementation: 7/10.** The 90-second resident flow works: pick language → tap card
→ read a real Hindi summary → click 📄 → see the source page. Clean visual design,
honest empty/error states, no dead ends found, no fabrication anywhere. Docked hard for
two things: (1) without an LLM key the "app" is 5 hand-written cards — the live
pipeline (retrieval → model → eval) has never produced a real summary, and the docs
admit this; what I'd see on camera is curated content, not the system working. (2) The
video script's most persuasive planned shot — the refusal — cannot be staged with the
script's own example query ("fremont property tax rate change 2026" scores 0.634 and
returns sources); the decline path only fires for wildly off-topic queries. The script
does include a pre-flight requirement, but the centerpiece take is fragile.

**(c) Demonstrated excellence of coding: 7/10.** From black-box testing: proper JSON
API with clean 400/404 error paths, path-traversal protection on the chunk endpoint,
manifest-guarded corpus per docs, honest mode separation (mock never masquerades as
live). Competent, professional, defensive. Docked: I tested behavior, not the
internals — and the load-bearing live path (real model output through the real eval)
is untested by anyone, which caps how excellent I can call the demonstrated code.

## Ranked fatal flaws (all verified by using the app)

1. **The product being demoed is 5 hand-written cards, not the pipeline.** Everything on
   screen is golden content; the actual engineering (summarizer + eval on live model
   output) has never run. The docs are radically honest about this — which builds
   credibility — but a judge asking "show me it working on something you didn't
   pre-write" gets sources, not a summary. This is the single biggest gap between the
   submission's claims and a living tool. (Mitigation exists: plug in a key.)
2. **The refusal demo is hard to stage.** The script's hand-picked adversarial query
   does not trigger the decline path (verified: 0.634, returns sources). Only absurd
   queries ("quantum computing") trigger it. The "it refuses to invent facts" moment —
   billed as the most persuasive shot — needs a better query or it dies in pre-flight.
3. **Minor:** free-form "Ask" box is the most prominent interactive element after the
   cards, but in demo mode it's a source-finder, not a summarizer — a resident typing a
   real question gets a "need a key" message. Not dishonest, but the hero interaction
   of the page doesn't do the hero thing without a key.

## Verdict: YES — this wins CA-14.

Against 30 generic demos, this is the one I'd remember tomorrow morning: the Hindi
summary of a measure on the ballot three weeks from now, the click that opens the
actual voter-guide page behind the sentence, and — rarest of all — a student AI project
that labels its demo content instead of faking liveness. The honesty architecture IS
the differentiator, and it's the kind of thing a congressional office can showcase
without worrying about being embarrassed later. Binding constraints are the builder's:
film the video well (fix the refusal take's query in pre-flight), and plug in a key if
possible so the live pipeline exists before a judge asks to see it.
