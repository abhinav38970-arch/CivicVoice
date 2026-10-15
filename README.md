# CivicVoice

**CivicVoice is a web app that turns public civic documents — California voter guides,
Fremont city-council agendas — into plain-language summaries in six languages, with
every sentence cited to its source page.** It opens on a language gatekeeper (zero
English until you choose), reads summaries aloud, takes voice input, shows local
notices, and builds copy-ready neighborhood issue reports. Congressional App Challenge
2026, CA-14.

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
                          app.py ──▶ UI: gatekeeper → cards + notices + 311
                                     + TTS/STT (Web Speech API, no key)
                                     + claims + clickable 📄 citations
                                     + "How we check our work" panel
                          i18n.py ──▶ 59 UI strings × 6 languages (flip 100% of chrome)
```

### Feature notes (all client-side honest, no external APIs)

- **Language gatekeeper:** first screen is six native-script buttons and essentially
  zero English; the choice persists in `localStorage` and `applyLanguage()` re-renders
  every heading, button, placeholder, and the source drawer. Farsi sets `lang="fa"`
  (RTL-ready styling via the `lang` attribute).
- **Ballot pass/fail impacts:** featured ballot cards group claims into Summary /
  If it passes / If it fails. Impact claims exist only where the official voter guide
  supports them (Prop 1, Prop 2), are descriptive (never "vote yes/no"), and are
  evaluated like every other claim (114/114 grounded, 0 advisory flags).
- **Local notices:** `/api/notices` serves the 8 City of Fremont press releases in the
  corpus with title + date; tapping one opens the exact source chunk. Labeled as dated
  records, never "live alerts".
- **311 tap-to-report (honest):** pick pothole / illegal dumping / broken streetlight,
  describe it in your language (typed or voice), optionally attach GPS, and the app
  builds a copy-ready structured report and hands off to fremont.gov. **CivicVoice
  never submits anything to the city** — there is no verified Fremont submission API,
  and the UI says so.
- **Speech:** summaries read aloud via `speechSynthesis` and voice input via
  `SpeechRecognition`, both in the chosen language's BCP-47 locale. No key, no
  network. The mic button hides itself where the API is unsupported.

## How verification works

Every claim carries a `(source_file, page)` citation. Clicking 📄 opens the exact
source chunk — file, page, section, full text — so anyone can check each sentence
against the document it came from. The eval harness (`eval.py`) scores every response
on citation validity, keyword grounding (Unicode-aware: Devanagari, Gurmukhi, Han,
Perso-Arabic), and advisory-language flags, with a PASS/FAIL verdict. Weak retrieval
(`low_confidence`) makes the app decline to answer rather than invent one.

## Multilingual retrieval upgrade (branch `multilingual-retrieval`)

The old embedding model (all-MiniLM-L6-v2) is English-oriented: Hindi queries
scored ~0.15 on wrong docs while English scored 0.70 on the right doc
(full benchmark in EVAL_REPORT.md). The fix swaps to
`intfloat/multilingual-e5-base` with `query: `/`passage: ` prefixes.

The build machine couldn't download the 1.1GB model (throttled pipe), so
finish the swap on a Mac with normal internet:

```bash
git checkout multilingual-retrieval
source .venv/bin/activate
python retriever.py --rebuild   # downloads the model once (~1.1GB), re-embeds 1,258 chunks
python demo/retrieval_benchmark.py --tag after
python -m pytest tests/ -q
```

Then paste the `after` table into EVAL_REPORT.md. If R@5 on hi/es/zh/fa jumps
(Claude's estimate: +15-20 points minimum), merge the branch to master.

## Honest limitations

- No LLM key exists in this repo: the harness has graded mock placeholders and
  hand-written, hand-verified golden claims — **never real model output**.
- Retrieval was English-only in practice under the old embedding model
  (all-MiniLM-L6-v2) — e.g. the Hindi query 'स्कूल बॉन्ड' scored 0.149
  on irrelevant docs while the English equivalent scored 0.702 on the right doc.
  Fixed on branch `multilingual-retrieval` (pending Mac verification); free-form
  questions should be asked in English until the swap is verified.
- Advisory detection is substring matching; paraphrased voting advice walks through.
- Non-English grounding validates content via English source text, not translation
  quality. Translation fluency and reading level are untested.
- UI translations in `i18n.py` (including all pass/fail impact claims) are drafts —
  not native-speaker reviewed. The eval harness confirms the *content* is grounded in
  official sources; it does not judge fluency.
- Retrieval is measured, not solved: some council queries score 0.29–0.40.
- The notices feed is 8 dated press releases (Mar 2025–Aug 2026), not a live alert
  system; the corpus needs a monthly refresh to stay current.
- The 311 flow builds a report for the resident to copy — it does not file anything
  with the city, and says so on screen.
- Full accounting: `EVAL_REPORT.md`. Fix history: `FIXES.md`.

## Project structure

```
app.py / templates/ / static/   demo web app (Flask, no build step)
i18n.py                       59 UI strings × 6 languages + speech locales
retriever.py                    local-embedding retrieval (retrieve(query, k))
summarizer.py / llm_client.py   citation-grounded summarizer, OpenAI-compatible
eval.py / advisory.py           accuracy harness + advisory-language patterns
scraper.py / parser.py          PDF download + text extraction pipeline
prompts/                        editable system/user prompts
data/parsed/                    1,258 chunks (49 files, SHA-256 manifest-guarded)
data/golden/                    5 hand-verified featured examples × 6 languages
                                (114 claims incl. pass/fail impacts, eval PASS)
tests/                          retrieval golden tests (pytest)
demo/VIDEO_SCRIPT.md            90-second demo storyboard
SUBMISSION.md                   CAC submission draft (student reviews before filing)
```

*Built by Abhinav Upadhyay, CA-14. Repo stays key-free: keys come from the environment only.*

## v3 — accounts, 12 languages, personal dashboard (2026-10-14)

- **Landing:** warm welcome + horizontal scroll picker with 12 Bay Area languages
  (English, Español, हिन्दी, ਪੰਜਾਬੀ, 中文, فارسی, Tiếng Việt, Tagalog, 한국어,
  العربية, 日本語, Русский), then a login / create-account portal.
- **Accounts:** SQLite (`data/users.db`, gitignored), werkzeug password hashing,
  Flask sessions. Each user gets a personal dashboard.
- **Dashboard tabs:** 📰 Council news · 🗳️ Ballot information · 🔧 City tasks
  (311 report flow, reports saved per account) · 💬 Ask about city laws
  (typed or spoken questions + PDF/txt document upload).
- **Bilingual display:** interface and claims render in the user's language with
  the English version in smaller text beneath.
- **Machine translation + premium TTS:** `translate.py` / `tts_service.py` are
  key-driven seams. Set `CIVICVOICE_TRANSLATE_KEY` and `CIVICVOICE_TTS_KEY`
  (Google provider by default) and `/api/translate` + `/api/tts` go live; with
  no keys they return 503 and the UI falls back honestly (browser TTS, English
  text with a "not connected" notice). Nothing is ever faked.
- The 6 verified languages keep hand-written UI strings + golden content; the 6
  extended languages get English fallback + live machine translation when keys
  are connected.
