# CivicVoice — CAC 2026 Submission Draft

> **DRAFT — the student reviews and edits before submitting.** Deadline: Oct 26, 2026,
> 12:00 PM ET. Student plans to submit Oct 25. District: CA-14.

Notes for Abhinav before you submit:
- Every number below is real and sourced — do not add new statistics without a source URL.
- [NEEDS ABHINAV] No LLM key has ever been plugged in: if you run the app with a real
  key before submitting, re-run `demo.py` and `eval.py`, and update (c) + EVAL_REPORT.md
  with the real-model scores. Until then, never claim real-model accuracy.
- [NEEDS ABHINAV] Film the video per `demo/VIDEO_SCRIPT.md`, including the pre-flight
  check on the adversarial query. Rewrite the voiceover in your own words, but keep the
  64.2% stat wording and the "describes, never tells you how to vote" line intact.
- [NEEDS ABHINAV] Read every answer below aloud and rewrite anything that doesn't sound
  like you. Judges can tell.

---

## (a) What the app does

**CivicVoice is a web app that turns public civic documents into plain-language summaries
in six languages, with every sentence cited to its source page.** A resident picks their
language first (English, Hindi, Punjabi, Mandarin, Spanish, or Farsi), taps a featured
card — "🗳️ What's on the ballot?" or "🏛️ Council labor talks" — and gets a short,
plain-language summary of the relevant public documents. Every claim in the summary
carries a 📄 citation; clicking it opens a side panel showing the exact source chunk —
file, page, section, full text — so anyone can verify each sentence against the document
it came from. A "How we check our work" panel shows how every response was validated.
By design, CivicVoice *describes* civic documents and never tells anyone how to vote.

## (b) Who it's for

CivicVoice is for residents of Fremont and California's 14th congressional district who
navigate civic life in a language other than English. The need is concrete, not assumed:
**64.2% of Fremont residents age 5 and older speak a language other than English at home**
(U.S. Census Bureau QuickFacts, Fremont city, California, 2020–2024 American Community
Survey 5-year estimates —
https://www.census.gov/quickfacts/fact/table/fremontcitycalifornia,CA/BZA110223).
At the neighborhood level, the picture is even sharper: in the Census PUMA covering
Fremont's southeast, 68.3% of households report speaking a non-English language at home
as their primary shared language, led by Chinese (incl. Mandarin, Cantonese), Hindi, and
Spanish (Data USA, 2024 ACS —
https://DataUSA.io/profile/geo/alameda-county-south-fremont-city-southeast-puma-ca).
California's official voter guides and city council agendas are published in dense
English legal language. CivicVoice exists so the majority of these residents — the
grandmother who votes in Punjabi at the kitchen table, the parent parsing a ballot
measure in Mandarin — can understand what's on the ballot and what their council is
doing, in the language they actually read.

## (c) How it was built

The pipeline is four real stages, all running locally or on a standard Flask server —
no third-party civic API, no external data dependency:

1. **Document ingestion.** `scraper.py` downloads public government PDFs (California
   Voter Information Guides, City of Fremont council documents); `parser.py` converts
   them to text with reading-order recovery for two-column layouts, header/footer
   stripping, heading-based chunking, and scanned-page flagging instead of silent
   drops. The current corpus is 1,258 parsed chunks across 49 files, guarded by a
   SHA-256 source manifest so test fixtures can never enter the index.
2. **Retrieval.** `retriever.py` embeds every chunk with a locally vendored
   sentence-transformer model (`all-MiniLM-L6-v2`, no network round-trip at runtime)
   and retrieves the top-k chunks by cosine similarity for each query.
3. **Citation-grounded summarization.** `summarizer.py` sends the retrieved chunks to an
   LLM (any OpenAI-compatible endpoint via environment configuration) with a system
   prompt that requires every claim to carry a citation (source file + page), bans
   voting-advice language, and targets ~8th-grade plain language in the requested
   language. A post-hoc guard rejects any response containing banned advisory phrases.
4. **Evaluation harness.** `eval.py` scores every response on citation validity (each
   cited file/page exists in the retrieved chunks), grounding (claim↔source text
   overlap, Unicode-aware so it works in Devanagari, Gurmukhi, Han, and Perso-Arabic
   scripts), and advisory-language flags — with a PASS/FAIL verdict. Results are shown
   in the app's "How we check our work" panel (technical metrics collapsed by default).

Honest accounting of the demo: the featured cards serve **hand-written, hand-verified
golden responses** (every claim checked by a person against the cited page text, then
translated by hand — labeled "✨ Featured example", never presented as live model
output) so the demo never shows placeholder text under a non-English label. Free-form
queries run the live pipeline end to end when an API key is set; without a key the app
returns the retrieved sources with an honest message instead of fabricating a summary.
`EVAL_REPORT.md` documents every eval run the project has (mock + golden) — no
real-model runs exist yet, and nothing here claims otherwise.

## (d) What makes it original

Three things, and they compound:

1. **Clickable, claim-level citations as the product — not a footnote.** Most AI
   summarizers cite at the document level or not at all. CivicVoice puts a 📄 citation
   on every sentence and makes it open the exact source page, so verifiability is the
   interaction, not a claim about the interaction.
2. **A visible accuracy harness, built for the languages it serves.** The eval panel
   doesn't just assert accuracy — it shows citation validity, grounding, and
   advisory-flag checks for every response, with tokenization that actually handles
   Hindi, Punjabi, Mandarin, and Farsi script. The app is designed to refuse: when
   retrieval can't find strong sources, it says so instead of inventing an answer.
3. **Descriptive-never-advisory by design, in two layers.** The system prompt bans
   voting-advice language and the post-hoc guard rejects it — a deliberate guardrail
   for a civic tool, where the line between explaining and persuading is the whole
   trust question.

None of these is "an AI summarizer." Together they are a verifiability machine: the
app retrieves real documents, cites every sentence to its page, lets you open the
page, checks its own work in front of you, and refuses to answer when it can't find
sources. That loop — not the summary — is the product.

---

*Sources for the statistics used above:*
- *U.S. Census Bureau QuickFacts, Fremont city, California (2020–2024 ACS 5-year estimates):*
  *https://www.census.gov/quickfacts/fact/table/fremontcitycalifornia,CA/BZA110223*
- *Data USA, Alameda County (South)–Fremont City (Southeast) PUMA, CA (2024 ACS):*
  *https://DataUSA.io/profile/geo/alameda-county-south-fremont-city-southeast-puma-ca*
