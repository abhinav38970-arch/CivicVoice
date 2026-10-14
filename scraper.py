#!/usr/bin/env python3
"""CivicVoice Phase 1 scraper — download public government PDFs.

Usage:
    python scraper.py                  # download the curated SAMPLE_URLS
    python scraper.py URL [URL ...]    # download explicit URLs
    python scraper.py --urls-file urls.txt
    python scraper.py --year 2025      # samples whose filename contains the year

Options:
    --outdir DIR      destination dir (default: data/raw/ next to this script)
    --force           re-download even if the file already exists

Behavior:
    - Skips files that already exist (by filename) unless --force.
    - Polite User-Agent, 30s timeout, up to 2 retries on transient errors.
    - Verifies each download starts with the %PDF magic bytes and is >50KB;
      duds are deleted and reported as failures.
    - Logs every outcome to stdout; failures are clearly marked FAILED.
No LLM calls, no API keys. Only public government PDFs.
"""

import argparse
import os
import re
import sys
import time
from urllib.parse import urlparse

import requests

USER_AGENT = (
    "CivicVoice-Scraper/1.0 (Congressional App Challenge research project; "
    "contact: civicvoice project) python-requests"
)
TIMEOUT = 30
RETRIES = 2
MIN_SIZE_BYTES = 50 * 1024  # 50 KB

# Curated Phase-1 samples: descriptive filename -> public PDF URL.
# See URLS.md for how these URL patterns were found.
SAMPLE_URLS = {
    # --- Fremont City Council (fremont.gov agenda center) ---
    # NOTE (2026-10-12): fremont.gov blocks automated downloads with Akamai
    # bot-mitigation 403s from this network. These URLs are correct and will
    # download from an unblocked network or via a real browser; see URLS.md.
    "fremont-council-2025-03-04-special-closed-agenda.pdf":
        "https://www.fremont.gov/home/showpublisheddocument/17472/638766000171030000",
    "fremont-council-2025-06-17-special-closed-agenda.pdf":
        "https://www.fremont.gov/home/showpublisheddocument?id=18363",
    "fremont-council-2026-06-30-state-of-city-agenda.pdf":
        "https://www.fremont.gov/home/showpublisheddocument/20790/639179809815670000",
    "fremont-council-2025-03-18-special-minutes.pdf":
        "https://www.fremont.gov/home/showpublisheddocument/18089/638822171000430000",
    "fremont-council-2025-midyear-priority-report.pdf":
        "https://www.fremont.gov/home/showpublisheddocument/18864/638929163980739256",
    # --- Fremont committees (same document system) ---
    "fremont-charter-committee-2026-04-06-agenda.pdf":
        "https://www.fremont.gov/home/showpublisheddocument/20164",
    "fremont-fusd-liaison-committee-2025-09-22-agenda.pdf":
        "https://www.fremont.gov/home/showpublisheddocument?id=18933",
    # NOTE (2026-10-12): the third-party mirror below served a SYNTHETIC
    # lorem-ipsum test fixture ("fremont-council-2026-07-11-agenda.pdf"),
    # which was quarantined out of the corpus and index. Do NOT re-add it.
    # "fremont-council-2026-07-11-agenda.pdf":
    #     "https://archive.theboringparts.com/agenda/fremont/169028.pdf",
    # --- CA Secretary of State official Voter Information Guides ---
    "ca-voter-guide-2024-general.pdf":
        "https://vig.cdn.sos.ca.gov/2024/general/pdf/complete-vig.pdf",
    "ca-voter-guide-2022-general.pdf":
        "https://vig.cdn.sos.ca.gov/2022/general/pdf/complete-vig.pdf",
    # Added 2026-10-13 (scrape expansion): the current election + historical depth.
    "ca-voter-guide-2026-general.pdf":
        "https://vig.cdn.sos.ca.gov/2026/general/pdf/complete-vig.pdf",
    "ca-voter-guide-2026-primary.pdf":
        "https://vig.cdn.sos.ca.gov/2026/primary/pdf/complete-vig.pdf",
    "ca-voter-guide-2020-general.pdf":
        "https://vig.cdn.sos.ca.gov/2020/general/pdf/complete-vig.pdf",
    # --- Union City, CA (unioncity.primegov.com portal; added 2026-10-13) ---
    "union-city-council-2025-09-09-special-agenda.pdf":
        "https://unioncity.primegov.com/Public/CompiledDocument?meetingTemplateId=4085&compileOutputType=1",
    "union-city-bart-mural-project-staff-report.pdf":
        "https://unioncity.primegov.com/api/compilemeetingattachmenthistory/historyattachment/?historyId=d40f4db5-6eff-4c55-87b1-8372b4b2f7ea",
    "union-city-council-2026-meeting-schedule-resolution.pdf":
        "https://unioncity.primegov.com/api/compilemeetingattachmenthistory/historyattachment/?historyId=ee07927a-d344-4d39-8739-cda4f2293b48",
    "union-city-council-2026-07-28-item-4-3-staff-report.pdf":
        "https://unioncity.primegov.com/api/compilemeetingattachmenthistory/historyattachment/?historyId=6aa2c3d8-fb09-48d5-bf6a-28a134cd2c9c",
    "union-city-senior-commission-2026-03-17-minutes.pdf":
        "https://unioncity.primegov.com/api/compilemeetingattachmenthistory/historyattachment/?historyId=b0fde8a8-4528-48d6-a1ef-f9b6f67c8c21",
    "union-city-it-strategic-roadmap-2026-update.pdf":
        "https://unioncity.primegov.com/api/compilemeetingattachmenthistory/historyattachment/?historyId=cb78a5eb-8a36-4c0f-8354-42f14a2b338a",
    # NOTE: Alameda County BOS agendas (6 files, added 2026-10-13) come from the
    # county's Granicus DocumentViewer (alamedacounty.granicus.com); their
    # per-meeting URLs were not captured verbatim — re-discover via the portal.
}


def slugify_filename(url: str, fallback_index: int) -> str:
    """Derive a safe .pdf filename from a URL when no explicit name is given."""
    path = urlparse(url).path.rstrip("/")
    base = os.path.basename(path) or f"download-{fallback_index}"
    base = re.sub(r"[^A-Za-z0-9._-]+", "-", base).strip("-")
    if not base.lower().endswith(".pdf"):
        base += ".pdf"
    return base


def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT})
    return s


def download_pdf(session: requests.Session, url: str, dest: str) -> bool:
    """Download one URL to dest. Returns True on verified success."""
    for attempt in range(RETRIES + 1):
        try:
            resp = session.get(url, timeout=TIMEOUT, allow_redirects=True)
            resp.raise_for_status()
            body = resp.content
        except requests.RequestException as e:
            if attempt < RETRIES:
                print(f"  retry {attempt + 1}/{RETRIES} for {url} ({e})",
                      flush=True)
                time.sleep(2 * (attempt + 1))
                continue
            print(f"FAILED  {url}\n        error: {e}", flush=True)
            return False

        # Verify it is really a PDF and non-trivial.
        if not body.startswith(b"%PDF"):
            if os.path.exists(dest):
                os.remove(dest)
            print(f"FAILED  {url}\n        error: not a PDF (bad magic bytes)",
                  flush=True)
            return False
        if len(body) < MIN_SIZE_BYTES:
            if os.path.exists(dest):
                os.remove(dest)
            print(f"FAILED  {url}\n        error: too small "
                  f"({len(body)} bytes < {MIN_SIZE_BYTES})", flush=True)
            return False

        with open(dest, "wb") as f:
            f.write(body)
        print(f"OK      {dest}  ({len(body) / 1024:.0f} KB)", flush=True)
        return True
    return False  # unreachable


def main() -> int:
    ap = argparse.ArgumentParser(description="Download public government PDFs.")
    ap.add_argument("urls", nargs="*", help="explicit PDF URLs to download")
    ap.add_argument("--urls-file", help="text file with one URL per line")
    ap.add_argument("--year", help="download sample files matching this year")
    ap.add_argument("--outdir", default=None, help="destination directory")
    ap.add_argument("--force", action="store_true",
                    help="re-download existing files")
    args = ap.parse_args()

    outdir = args.outdir or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data", "raw")
    os.makedirs(outdir, exist_ok=True)

    targets = []  # list of (filename, url)
    if args.urls:
        for i, u in enumerate(args.urls):
            targets.append((slugify_filename(u, i), u))
    elif args.urls_file:
        with open(args.urls_file) as f:
            for i, line in enumerate(f):
                u = line.strip()
                if u and not u.startswith("#"):
                    targets.append((slugify_filename(u, i), u))
    else:
        items = SAMPLE_URLS.items()
        if args.year:
            items = [(n, u) for n, u in items if args.year in n]
            if not items:
                print(f"No sample files match year {args.year}.", flush=True)
                return 1
        targets = list(items)

    ok, failed, skipped = 0, 0, 0
    session = make_session()
    for name, url in targets:
        dest = os.path.join(outdir, name)
        if os.path.exists(dest) and not args.force:
            print(f"SKIP    {dest} (already downloaded)", flush=True)
            skipped += 1
            continue
        if download_pdf(session, url, dest):
            ok += 1
        else:
            failed += 1
        time.sleep(2.5)  # be polite between requests (2-3s policy)

    print(f"\nDone: {ok} downloaded, {skipped} skipped, {failed} failed.",
          flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
