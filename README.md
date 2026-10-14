# CivicVoice

**CivicVoice is a web app that turns public civic documents — California voter guides,
Fremont city-council agendas — into plain-language summaries in six languages, with
every sentence cited to its source page.** Congressional App Challenge 2026, CA-14.

## Who it's for

Residents of Fremont and CA-14 who navigate civic life in a language other than
English: **64.2% of Fremont residents age 5+ speak a language other than English at
home** (U.S. Census QuickFacts, 2020–2024 ACS). Voter guides and council agendas are
published in dense English legal language. CivicVoice *describes* what those documents
say — in English, Hindi, Punjabi, Mandarin, Spanish, or Farsi — and never tells anyone
how to vote.

## Run it (30 seconds)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # pulls torch (~200MB) via sentence-transformers
python app.py                     # open http://127.0.0.1:5000
```

No key needed: the app runs in demo mode on hand-verified featured examples, and says
so in the footer. With `CIVICVOICE_LLM_API_KEY` set (any OpenAI-compatible endpoint),
free-form queries run the live pipeline.

**Verify the install:** `python smoke_test.py` (or `python app.py --smoke`) boots the
real pipeline (retrieve → evaluate on a golden query) and exits 0/1 — ~30 seconds.
**Port taken?** `python app.py --port 5001` (or `CIVICVOICE_PORT=5001`) — a busy port
prints the fix, not a traceback. **Offline?** If the embedding model can't download,
every entry point explains what happened and what to do (go online once, or copy
`models/all-MiniLM-L6-v2/` from the project download) instead of a stack trace —
same for missing `data/parsed/`. `/tmp` too small for the torch wheel?
`TMPDIR=~/workspace/.pip-tmp pip install -r requirements.txt`.

## Architecture

```
  data/raw/*.pdf ──parser.py──▶ data/parsed/*.jsonl (1,258 chunks, manifest-guarded)
  curated gov web pages ──(hand-extracted 2026-10-13)──▶ data/parsed/html-*.jsonl ┘
                                        │
  query ──retriever.py (MiniLM-L6-v2, cosine top-k)──▶ chunks
                                        │
                                        ▼
                          ┌──summarizer.py──▶ LLM / MockLLM──▶ cited claims
                          │                        │
                          │                        ▼
                          │              advisory.py guard (115 patterns, 6 langs)
                          ▼
                     eval.py ──▶ citation validity / grounding / advisory flags
                                        │
                                        ▼
                          app.py ──▶ UI: claims + clickable 📄 citations
                                     + "How we check our work" panel
```

## How verification works

Every claim carries a `(source_file, page)` citation. Clicking 📄 opens the exact
source chunk — file, page, section, full text — so anyone can check each sentence
against the document it came from. The eval harness (`eval.py`) scores every response
on citation validity, keyword grounding (Unicode-aware: Devanagari, Gurmukhi, Han,
Perso-Arabic), and advisory-language flags, with a PASS/FAIL verdict. Weak retrieval
(`low_confidence`) makes the app decline to answer rather than invent one.

## Honest limitations

- No LLM key exists in this repo: the harness has graded mock placeholders and
  hand-written, hand-verified golden claims — **never real model output**.
- Retrieval is English-only in practice: the embedding model (all-MiniLM-L6-v2) does
  not handle non-English queries well — e.g. the Hindi query 'स्कूल बॉन्ड' scored 0.149
  on irrelevant docs while the English equivalent scored 0.702 on the right doc. Free-form
  questions should be asked in English; the six-language support is for the featured
  summaries, verified by eval.py against English source text.
- Advisory detection is substring matching; paraphrased voting advice walks through.
- Non-English grounding validates content via English source text, not translation
  quality. Translation fluency and reading level are untested.
- Retrieval is measured, not solved: some council queries score 0.29–0.40.
- Full accounting: `EVAL_REPORT.md`. Fix history: `FIXES.md`.

## Project structure

```
app.py / templates/ / static/   demo web app (Flask, no build step)
retriever.py                    local-embedding retrieval (retrieve(query, k))
summarizer.py / llm_client.py   citation-grounded summarizer, OpenAI-compatible
eval.py / advisory.py           accuracy harness + advisory-language patterns
scraper.py / parser.py          PDF download + text extraction pipeline
prompts/                        editable system/user prompts
data/parsed/                    1,258 chunks (49 files, SHA-256 manifest-guarded)
data/golden/                    5 hand-verified featured examples × 6 languages
tests/                          retrieval golden tests (pytest)
demo/VIDEO_SCRIPT.md            90-second demo storyboard
SUBMISSION.md                   CAC submission draft (student reviews before filing)
```

*Built by Abhinav Upadhyay, CA-14. Repo stays key-free: keys come from the environment only.*
