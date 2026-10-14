# CivicVoice Phase 1 — Parse Report

Parser: `parser.py` (run: `cd ~/workspace/civicvoice && .venv/bin/python parser.py`).
Outputs: `data/parsed/<basename>.jsonl`. Run is idempotent (verified: re-run produces byte-identical files).

## ca-voter-guide-2024-general.pdf (CA SOS Voter Information Guide, Nov 2024)
- Pages total: 144 | pages parsed with text: 144 | flagged scanned/image-only: **0**
- Chunks: **181** | word range 201–1392 (avg ~485); every chunk within the 200–1500 budget
- Multi-column: **yes** — proposition/analysis/argument pages are two-column. Parser detects
  two-column layout per page from text-block x-coordinates and reads left column top-to-bottom
  before the right column; full-width title blocks are pinned above/below the columns.
  Reading order verified on 3 sample pages (Prop 36 analysis, Prop 4 LAO analysis, Prop 26/27
  arguments) — prose flows correctly.
- Headers stripped: standalone page numbers, "N | Section" / "Section | N" furniture
  (e.g. "26 | Analysis", "Text of Proposed Laws | 81"). No exact-duplicate header line met the
  ≥80%-of-pages threshold, so nothing else was stripped.
- Chunk boundaries: ALL-CAPS headings, "PROPOSITION N" headers (ALL-CAPS only — a body sentence
  like "Proposition 4 would allow the state to..." was initially misfiring and was fixed),
  "★ ARGUMENT IN FAVOR OF PROPOSITION N ★" star headings, agenda-style numbered items.
  Consecutive heading lines with no body text between them are merged into one title block
  (multi-line slogans like "YES ON PROP. 36: TOUGHER LAWS TO MAKE OUR / COMMUNITIES SAFER...").
- Known limitation: **table-heavy pages read in jumbled order.** The LAO "Figure 1" summary
  tables (e.g. Prop 4 bond categories/amounts) interleave cell fragments — cell text is all
  present but row/column alignment is lost. Prose sections on the same pages are fine.
- Note: source text layer contains typos baked into the PDF ("beneft", "wildfres", "fscal",
  "ofce") — preserved as-is, not "corrected".

## ca-voter-guide-2022-general.pdf (CA SOS VIG, Nov 2022)
- Pages total: 128 | pages parsed with text: 128 | flagged scanned/image-only: **0**
- Chunks: **149** | word range 201–1229 (avg ~510); all within budget
- Multi-column: **yes** — same two-column handling as 2024; verified on sampled argument
  and "ARGUMENTS / A NO vote... A YES vote..." pages.
- Headers stripped: same page-number/"N | Section" rules. Most chunks are "TEXT OF PROPOSED
  LAWS" (43 chunks) — the 2022 guide's back half is statute text with fewer sub-headings, so
  statute chunks run long (up to ~1229 words) but stay in budget.

## fremont-council-2026-07-11-agenda.pdf (Fremont City Council agenda, 7 pages)
- Pages total: 7 | pages parsed with text: 7 | flagged scanned/image-only: **0**
- Chunks: **3** | word range 231–565 (avg ~427)
- Multi-column: no (single-column throughout).
- Headers stripped: "July 11, 2026" (repeated ≥80% of pages) and per-page footers "Page 2"–"Page 7".
- Chunk boundaries: lettered/numbered agenda items ("B. Test – ...", "C. Roll Call",
  "2. Consent Calendar", "5. Scheduled Items", "8. Adjournment"). Cover page has no heading → 1 UNTITLED chunk.
- ⚠️ **This PDF is a synthetic/test fixture, not a real agenda**: it contains "B. Test –
  Lorem ipsum dolor sit amet, consectetur adipiscing elit" placeholder text and a "Test Staff
  Recommendation" line. Parsed faithfully, but downstream consumers should not treat its
  contents as real council business.

## Pipeline notes
- Extraction: PyMuPDF block extraction primary. pdfplumber per-page fallback engaged on
  **0 pages** (no page fell below the 50-char threshold). Scanned-page detection active but
  nothing flagged — all three PDFs are born-digital with full text layers.
- Paragraph joiner re-joins hyphenated line wraps and continuation lines starting with
  lowercase glue words ("and", "of", "the", ...) before chunking.
- Tiny fragments (<200 words) are merged into the following chunk; no chunk exceeds 1500 words.
- Spot-checks: 2–3 random chunks per file read back in full — all read in sane sentence order.
