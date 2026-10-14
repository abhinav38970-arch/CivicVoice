# SCRAPE_REPORT.md — corpus expansion, 2026-10-13

Three document-hunter workers ran in parallel to massively expand the CivicVoice
corpus of REAL public government documents. All downloads used the repo's
`scraper.py` (polite UA, 2.5s spacing, %PDF magic + 50KB verification).

## Before / after

| | Files | Chunks |
|---|---|---|
| Before | 9 (2 CA VIGs + 7 Fremont docs) | 344 |
| Added | 15 | 559 |
| **After** | **24** | **903** |

Corpus is allowlisted in `data/SOURCE_MANIFEST.json` (24 entries, sha256-pinned);
`retriever.load_chunks()` skips anything not listed — the permanent guard against
synthetic fixtures.

## Files added (all text-verified real, spot-checked)

**CA Secretary of State — Voter Information Guides (3)**
- `ca-voter-guide-2026-general.pdf` — 176 pp, 7.1 MB — **Nov 3, 2026 general (the current election)**, Weber-certified → 227 chunks
- `ca-voter-guide-2026-primary.pdf` — 64 pp, 35.9 MB — Jun 2, 2026 primary → 50 chunks
- `ca-voter-guide-2020-general.pdf` — 112 pp, 1.4 MB — Nov 3, 2020 general, Padilla-certified → 177 chunks

**Alameda County Board of Supervisors (6)** — agendas via alamedacounty.granicus.com
DocumentViewer: Jan 13 (31 pp, 27 chunks), Jan 27, Feb 10 planning, Mar 5 planning,
Apr 7, Jun 16, 2026 → 96 chunks total. No Sept/Oct 2026 agendas were publicly
indexed at scrape time.

**Union City (6)** — via unioncity.primegov.com portal: Sep 9, 2025 special council
agenda; BART mural project staff report; 2026 council meeting schedule resolution;
Jul 28, 2026 item 4.3 staff report; Senior Citizens Commission minutes Mar 17, 2026;
IT Strategic Roadmap 2022–2027 year-4 update (11 pp, 1 scanned page flagged, 10/11
pages extracted) → 9 chunks total.

## Blocked — needs a live-browser pull

`data/BLOCKED_URLS.md` has the full list (18 verified-real URLs + 2 portal guides):
- **fremont.gov: 11 URLs** — all 403 (Akamai bot mitigation), incl. FY 2026/27 adopted
  budget, proposed budget presentation, charter committee minutes, CDBG action plan.
- **newarkca.gov: 7 URLs** — all 403 (same Akamai wall): council minutes, biennial
  budget, planning commission agenda, Nov 2026 election notice.
- **FUSD board agendas** — found the GAMUT/Simbli portal
  (`simbli.eboardsolutions.com/...S=36031613`, 20+ meetings listed Oct 2025–Oct 2026)
  but attachments are JS-rendered; needs a JS-capable browser.
- **Alameda County Nov 2026 Voter Information Guide** — not publicly indexed; likely
  behind the county's My Voter Profile lookup or a JS documents section
  (see `data/BLOCKED_URLS.md` for the exact lead).

## Parser anomalies

- One scanned-only page: `union-city-it-strategic-roadmap-2026-update.pdf` p.10
  (flagged by parser, remaining 10 pages extracted normally).
- One sub-50KB real doc deleted by the scraper's size floor (Union City Aug 2026
  recess resolution draft, 15 KB — real but tiny; URL preserved in the hunter's
  notes for a browser retry if wanted).
- No placeholder/lorem-ipsum/test content found anywhere. Zero-tolerance rule held.

## Verification after integration

- `parser.py`: 24/24 files parsed, 903 chunks total.
- Manifest: 24 entries, sha256-pinned (updated 2026-10-13).
- Index rebuilt: 903 chunks embedded (`data/index/`).
- `pytest tests/`: **3 passed**.
- `tests/test_retrieval_golden.py`: **9/9 passed** (incl. fixture-quarantine and
  low-confidence cases).
- Sanity retrieval "2026 general election ballot measures" → 2026 general VIG
  top hit (0.565), 2024 VIG second (0.528).

## New URLs in scraper.py

`SAMPLE_URLS` now includes the three new VIG URLs and the six Union City portal
URLs (Alameda BOS per-meeting URLs were not captured verbatim — re-discover via
the Granicus DocumentViewer; noted in scraper.py).
