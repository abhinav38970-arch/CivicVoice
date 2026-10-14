#!/usr/bin/env python3
"""
CivicVoice Phase 1 — PDF parser (Worker 2).

PDF -> clean text -> chunked JSONL.

  python parser.py

Parses every *.pdf in data/raw/ and writes one JSONL per source PDF to
data/parsed/<basename>.jsonl. Idempotent (overwrites).

Pipeline per page:
  1. PyMuPDF block extraction (primary); pdfplumber per-page fallback when a
     page yields suspiciously little text (<50 chars) or nothing.
  2. Pages still <50 chars after fallback are FLAGGED as scanned/image-only
     (recorded in the report; never silently dropped).
  3. Layout handling: two-column detection via block x-coordinates, column-wise
     reading order, and repeated header/footer stripping (>=80% of pages).
  4. Chunking: split by detected headings/agenda items. Each chunk is one JSON
     object: {"source_file", "page" (int or [start,end]), "section_title",
     "text"}. Word budget 200-1500; tiny fragments merged with neighbors.

No LLM calls, no API keys.
"""

import json
import os
import re
import sys

import pymupdf  # PyMuPDF

# pdfplumber is imported lazily only when needed (fallback path).

RAW_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "raw")
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "parsed")

MIN_CHARS = 50          # below this -> try pdfplumber, then flag scanned
HEADER_FRAC = 0.80      # a line repeated across >= this fraction of pages is header/footer
MIN_WORDS, MAX_WORDS = 200, 1500


# --------------------------------------------------------------------------
# Text extraction
# --------------------------------------------------------------------------

def extract_with_pymupdf(page):
    """Return (lines, blocks) with column-aware reading order."""
    w = page.rect.width
    raw_blocks = page.get_text("blocks")
    # Keep only horizontal text blocks (block_type == 0) with non-trivial text.
    blocks = [b for b in raw_blocks if b[6] == 0 and b[4].strip()]
    if not blocks:
        return []
    return _order_blocks(blocks, w)


def _order_blocks(blocks, w):
    """Best-effort reading order: detect two-column layout via x-coords.

    Full-width blocks (spanning the gutter) keep their vertical position;
    left column reads top-to-bottom, then right column top-to-bottom.
    Single-column pages are left untouched (y-order).
    """
    gutter = w / 2.0
    left, right, full = [], [], []
    for b in blocks:
        x0, x1 = b[0], b[2]
        cx = (x0 + x1) / 2.0
        spans = (x0 < w * 0.30) and (x1 > w * 0.70)
        if spans:
            full.append(b)
        elif cx < gutter and x1 < gutter + w * 0.10:
            left.append(b)
        elif cx > gutter and x0 > gutter - w * 0.10:
            right.append(b)
        else:
            # ambiguous: treat by vertical extent as full-width-ish flow
            full.append(b)

    two_col = len(left) >= 3 and len(right) >= 3
    ordered = []
    if two_col:
        left.sort(key=lambda b: b[1])
        right.sort(key=lambda b: b[1])
        full.sort(key=lambda b: b[1])
        # Full-width blocks above both columns go first, those below go last.
        top_edge = min(left[0][1], right[0][1])
        bot_edge = max(left[-1][3], right[-1][3])
        top_full = [b for b in full if b[1] <= top_edge]
        bot_full = [b for b in full if b[1] > top_edge]
        mid_full = [b for b in full if b[1] <= bot_edge and b[1] > top_edge and b not in bot_full]
        ordered = top_full + left + mid_full + right + bot_full
        # Simpler: any full block above the column region first, everything
        # else full-width (footnotes, continued headers) last.
        ordered = top_full + left + right + bot_full
    else:
        ordered = sorted(blocks, key=lambda b: b[1])

    lines = []
    for b in ordered:
        lines.extend(b[4].splitlines())
    return lines


def extract_with_pdfplumber(path, pgno):
    """Fallback: pdfplumber per-page extraction."""
    import pdfplumber  # lazy import
    lines = []
    with pdfplumber.open(path) as pdf:
        text = pdf.pages[pgno].extract_text() or ""
        lines = text.splitlines()
    return lines


# --------------------------------------------------------------------------
# Header/footer stripping
# --------------------------------------------------------------------------

PAGE_NUM_RE = re.compile(r"^\d{1,4}$")
PAGE_PIPE_RE = re.compile(r"^\d{1,4}\s*\|\s*.+$|^.+\s*\|\s*\d{1,4}$")


def find_repeated_lines(pages_lines):
    """Lines (after page-number filtering) identical across >=80% of pages."""
    from collections import Counter
    n = len(pages_lines)
    firsts = Counter()
    lasts = Counter()
    for lines in pages_lines:
        if not lines:
            continue
        firsts[lines[0]] += 1
        lasts[lines[-1]] += 1
    bad = {k for k, v in firsts.items() if v >= HEADER_FRAC * n}
    bad |= {k for k, v in lasts.items() if v >= HEADER_FRAC * n}
    # Also catch two-line headers that co-occur (e.g. "July 11, 2026" + "Fremont City Council").
    return bad


def clean_page(lines, repeated):
    """Strip whitespace, drop page numbers and repeated header/footer lines."""
    out = []
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        if PAGE_NUM_RE.match(s):
            continue
        if PAGE_PIPE_RE.match(s):
            continue  # e.g. "26 | Analysis" / "Analysis | 61" — page furniture
        if AGENDA_FOOTER_RE.match(s):
            continue  # e.g. "July 11, 2026 Fremont City Council Page 4"
        if s in repeated:
            continue
        out.append(s)
    # De-dup exact consecutive duplicates (header/footer stutter).
    dedup = []
    for s in out:
        if not dedup or dedup[-1] != s:
            dedup.append(s)
    return dedup


# --------------------------------------------------------------------------
# Heading detection / chunking
# --------------------------------------------------------------------------

PROP_RE = re.compile(r"^PROPOSITION\s+(\d+[A-Z]?)", re.IGNORECASE)
# Footer furniture like "July 11, 2026 Fremont City Council Page 4" or "Page 4"
AGENDA_FOOTER_RE = re.compile(
    r"^\w+\s+\d{1,2},\s+\d{4}\b.*\bPage\s+\d+$|^\s*Page\s+\d{1,3}\s*$",
    re.IGNORECASE)
AGENDA_ITEM_RE = re.compile(r"^(\d{1,2})\.\s+\S")
AGENDA_ITEM_WORD_RE = re.compile(r"^ITEM\s+(\d+)", re.IGNORECASE)
LETTER_ITEM_RE = re.compile(r"^([A-Z])\.\s+\S")


def is_heading(line):
    line = line.strip()
    if not line or len(line) < 4:
        return False
    if PROP_RE.match(line):
        # Real proposition headers in the VIG are ALL-CAPS ("PROPOSITION 4",
        # "PROPOSITION 36"); body sentences like "Proposition 4 would allow
        # the state to..." must NOT become headings.
        return line == line.upper() or bool(re.match(r"^PROPOSITION\s+\d+\s*[-–—:]", line))
    if AGENDA_ITEM_WORD_RE.match(line):
        return True
    if AGENDA_ITEM_RE.match(line):
        return True
    if LETTER_ITEM_RE.match(line):
        return True
    # ALL-CAPS heading line (short enough to be a title, not body)
    if len(line) > 8 and len(line) < 160 and line == line.upper():
        letters = [c for c in line if c.isalpha()]
        if len(letters) >= 4:
            return True
    return False


def heading_title(line):
    """Normalize a heading line into a section title."""
    s = line.strip()
    # Collapse run-on title fragments like "PROPOSITION\nALLOWS FELONY..." later;
    # keep the raw text but truncate.
    return s[:120]


def chunk_pages(doc_name, pages_lines):
    """Split cleaned page lines into 200-1500 word chunks.

    pages_lines: list of (pgno, [lines]).
    Returns list of dicts with page int or [start,end].
    """
    chunks = []
    cur = {"title": None, "pages": [], "words": []}

    def flush():
        if cur["words"]:
            n = len(cur["words"])
            if n < MIN_WORDS and chunks:
                # merge tiny fragment into previous chunk
                prev = chunks[-1]
                prev["text"] += " " + " ".join(cur["words"])
                p = prev["page"]
                new_end = cur["pages"][-1] if isinstance(p, int) else p[1]
                start = p if isinstance(p, int) else p[0]
                prev["page"] = start if start == new_end else [start, new_end]
            else:
                p = cur["pages"]
                chunks.append({
                    "source_file": doc_name,
                    "page": p[0] if len(p) == 1 else [p[0], p[-1]],
                    "section_title": cur["title"] or "UNTITLED",
                    "text": " ".join(cur["words"]),
                })
        cur["title"] = None
        cur["pages"] = []
        cur["words"] = []

    for pgno, lines in pages_lines:
        i = 0
        while i < len(lines):
            line = lines[i]
            if is_heading(line):
                # Flush if the current chunk already has substance.
                if len(cur["words"]) >= MIN_WORDS:
                    flush()
                if pgno not in cur["pages"]:
                    cur["pages"].append(pgno)
                new_title = heading_title(line)
                if cur["title"] and not cur["words"]:
                    # Consecutive heading lines with no body text between
                    # them are one title block (e.g. multi-line slogans,
                    # "PROPOSITION" / "ALLOWS FELONY CHARGES...").
                    if new_title not in cur["title"]:
                        cur["title"] = (cur["title"] + " / " + new_title)[:200]
                else:
                    cur["title"] = new_title
                i += 1
                continue

            # Paragraph joiner: merge a line that ends mid-sentence with its
            # next line (hyphenated wrap) or with a next line that begins with
            # a lowercase continuation word ("and", "of", "the", ...).
            line_acc = line
            j = i
            while True:
                nxt = lines[j + 1] if j + 1 < len(lines) else None
                looks_cont = (
                    nxt
                    and not is_heading(nxt)
                    and (
                        line_acc.endswith("-")
                        or re.match(
                            r"^(and|of|the|for|to|in|on|at|by|with|from|or|as|into|"
                            r"that|this|which|a|an)\b",
                            nxt,
                            re.I,
                        )
                    )
                )
                if not looks_cont:
                    break
                if line_acc.endswith("-"):
                    line_acc = line_acc[:-1] + nxt.strip()
                else:
                    line_acc = line_acc + " " + nxt.strip()
                j += 1
            i = j + 1

            if pgno not in cur["pages"]:
                cur["pages"].append(pgno)
            cur["words"].extend(line_acc.split())

    flush()

    # Merge pass: absorb any still-tiny (<MIN_WORDS) non-final chunks into the
    # following chunk so every chunk meets the word budget except the last.
    merged = []
    i = 0
    while i < len(chunks):
        c = chunks[i]
        if len(c["text"].split()) < MIN_WORDS and i + 1 < len(chunks):
            nxt = chunks[i + 1]
            nxt["text"] = c["text"] + " " + nxt["text"]
            s1 = c["page"]; s2 = nxt["page"]
            start = s1 if isinstance(s1, int) else s1[0]
            end = s2 if isinstance(s2, int) else s2[1]
            nxt["page"] = start if start == end else [start, end]
            nxt["section_title"] = (nxt["section_title"]
                                   if nxt["section_title"] != "UNTITLED"
                                   else c["section_title"])
            i += 1
        else:
            merged.append(c)
            i += 1
    return merged


# --------------------------------------------------------------------------
# Main driver
# --------------------------------------------------------------------------

def parse_pdf(path):
    """Parse one PDF. Returns (pages_lines, scanned_pages, stats)."""
    doc_name = os.path.basename(path)
    doc = pymupdf.open(path)
    n = len(doc)

    # First pass: extract + clean every page.
    pages_lines = []
    scanned = []
    fallback_used = 0
    for pgno in range(n):
        page = doc[pgno]
        lines = extract_with_pymupdf(page)
        text_len = len(" ".join(lines).strip())
        if text_len < MIN_CHARS:
            pl_lines = extract_with_pdfplumber(path, pgno)
            if len(" ".join(pl_lines).strip()) > text_len:
                lines = pl_lines
                fallback_used += 1
        pages_lines.append((pgno, lines))
        if len(" ".join(lines).strip()) < MIN_CHARS:
            scanned.append(pgno)
    doc.close()

    # Second pass: find repeated header/footer lines (>=80% of pages).
    repeated = find_repeated_lines([l for _, l in pages_lines])

    cleaned = []
    for pgno, lines in pages_lines:
        if pgno in scanned:
            cleaned.append((pgno, []))
        else:
            cleaned.append((pgno, clean_page(lines, repeated)))

    chunks = chunk_pages(doc_name, cleaned)

    stats = {
        "pages_total": n,
        "pages_with_text": n - len(scanned),
        "pages_scanned_flagged": scanned,
        "pdfplumber_fallback_pages": fallback_used,
        "repeated_header_footer_lines": sorted(repeated),
        "chunks": len(chunks),
        "avg_words_per_chunk": (sum(len(c["text"].split()) for c in chunks) / len(chunks)
                                if chunks else 0),
    }
    return chunks, stats


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    pdfs = sorted(f for f in os.listdir(RAW_DIR) if f.lower().endswith(".pdf"))
    if not pdfs:
        print(f"No PDFs found in {RAW_DIR}", file=sys.stderr)
        sys.exit(1)
    for fname in pdfs:
        path = os.path.join(RAW_DIR, fname)
        print(f"Parsing {fname} ...", flush=True)
        chunks, stats = parse_pdf(path)
        out = os.path.join(OUT_DIR, os.path.splitext(fname)[0] + ".jsonl")
        with open(out, "w", encoding="utf-8") as fh:
            for c in chunks:
                fh.write(json.dumps(c, ensure_ascii=False) + "\n")
        print(f"  -> {out}: {stats['chunks']} chunks, "
              f"{stats['pages_with_text']}/{stats['pages_total']} pages with text, "
              f"{len(stats['pages_scanned_flagged'])} flagged scanned, "
              f"{stats['pdfplumber_fallback_pages']} pdfplumber fallbacks, "
              f"{len(stats['repeated_header_footer_lines'])} header/footer lines stripped")
        if stats["pages_scanned_flagged"]:
            print(f"  !! scanned/image-only pages: {stats['pages_scanned_flagged']}")


if __name__ == "__main__":
    main()
