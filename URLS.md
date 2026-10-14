# CivicVoice Phase 1 — URL patterns & source notes

How each document source was found, how its PDF links are structured, and
what is blocked. Written 2026-10-12. All URLs below were verified via web
search result pages or direct fetch on that date.

## 1. Fremont City Council agendas (fremont.gov)

- **Agenda Center (human entry point):** https://fremont.gov/government/agenda-center
- **CivicPlus FlexAgendaCenter module:** https://www.fremont.gov/Home/Components/FlexAgendaCenter/AgendaCenter/2877327/608
  - The meeting listing on this page is JavaScript-rendered; a plain text fetch
    shows no document links. Phase 2 bulk enumeration will need a JS-capable
    browser (or the CivicPlus agenda search UI) to collect document IDs.
- **Direct PDF pattern (verified with 8 real examples):**
  - `https://www.fremont.gov/home/showpublisheddocument/{docID}/{version}`
  - `https://www.fremont.gov/home/showpublisheddocument?id={docID}` (older variant)
  - Examples: docID 17472 (2025-03-04 special closed-session agenda),
    18363 (2025-06-17 special closed-session agenda), 20790 (2026-06-30 State
    of the City agenda), 18089/18079 (2025 special-meeting minutes),
    18864 (2025 mid-year council priority progress report), 20164 (2026-04-06
    Charter Advisory Committee agenda), 18933 (2025-09-22 City/FUSD liaison agenda).

### BLOCKED — Akamai bot mitigation (2026-10-12)

Every `fremont.gov/home/showpublisheddocument` request from automated clients
returns **HTTP 403 from AkamaiGHost**, on both `www.fremont.gov` and
`fremont.gov`, even with a full browser User-Agent + Referer. This is a
bot-management block, not a header or URL problem — do not retry aggressively
or try to circumvent it. The 7 fremont.gov URLs are already curated in
`scraper.py` SAMPLE_URLS with target filenames; re-running the scraper from
an unblocked network — or downloading via a real (live) browser session and
dropping the files into `data/raw/` with the listed names — will complete the
set. The documents are public records; only the automated path is blocked.

## 2. Third-party public mirror: archive.theboringparts.com

- **Pattern:** `https://archive.theboringparts.com/agenda/fremont/{numericID}.pdf`
- Verified example: https://archive.theboringparts.com/agenda/fremont/169028.pdf
  = "Fremont City Council Agenda and Report, Saturday, July 11, 2026"
  (3300 Capitol Avenue, Fremont CA; Mayor Raj Salwan) — 7 pages, 149 KB.
  Downloaded and verified 2026-10-12.
- This archive mirrors many CA cities (`/agenda/{city-slug}/{id}.pdf`, e.g.
  `/agenda/lodi.gov/`, `/agenda/rz-ci.porterville.ca.us/`). Numeric IDs are
  sequential across all cities and cannot be guessed — new Fremont entries
  must be discovered via web search. Only one Fremont CA PDF was indexed at
  the time of research.

## 3. Ballot pamphlets — CA Secretary of State Voter Information Guides

- **Index page:** https://www.sos.ca.gov/elections/voting-resources/voter-information-guides
  (lists every statewide election back to 1996; each links to its archive page)
- **HTML archive:** `https://vigarchive.sos.ca.gov/{YYYY}/{general|primary}/`
  (verified: `https://vigarchive.sos.ca.gov/2024/general/`)
- **Complete-guide PDF pattern:** `https://vig.cdn.sos.ca.gov/{YYYY}/general/pdf/complete-vig.pdf`
  - Verified 2026-10-12 (both downloaded, %PDF magic + size checked):
    - https://vig.cdn.sos.ca.gov/2024/general/pdf/complete-vig.pdf (144 pages, ~4.8 MB)
    - https://vig.cdn.sos.ca.gov/2022/general/pdf/complete-vig.pdf (128 pages, ~11.5 MB)
  - Per-section PDFs live alongside it (e.g. `front-cover.pdf`,
    `secretary-message.pdf`, `letter-from-sos.pdf`, `back-cover.pdf`,
    `info-about-candidate-statements.pdf`). Only the two `complete-vig.pdf`
    URLs above are verified; assume the pattern holds for other years but
    re-verify before bulk use.
- These are the STATE guides (statewide propositions + candidate info). The
  county Voter Information Guide (which carries Fremont/Alameda County local
  measures) was not researched — see §5.

## 4. Fremont Unified school board agendas (optional; researched, not downloaded)

- **Board page:** https://fremontunified.org/about/board/ — the "Board Agenda
  and Policy Platform" link there goes to the district's GAMUT Meetings site
  (effective for meetings on/after 2025-07-30).
- **GAMUT Meetings (Simbli/eBoardSolutions), verified site ID:** `S=36031613`
  - Meeting page pattern: `https://simbli.eboardsolutions.com/SB_Meetings/ViewMeeting.aspx?S=36031613&MID={mid}`
  - Verified example: https://simbli.eboardsolutions.com/SB_Meetings/ViewMeeting.aspx?S=36031613&MID=49144
    ("Regular Meeting of the Board of Education | 01/28/2026").
  - (Note: `S=36030796` found in an old Google Form belongs to Washington
    Unified SD in West Sacramento — NOT Fremont. Do not use it.)
  - Agenda item detail/attachments load dynamically; no direct PDF attachment
    URLs were discoverable via text fetch. Phase 2 needs a JS-capable browser
    to enumerate meetings and pull attachment PDFs.

## 5. Open items for Phase 2

- **Alameda County Registrar of Voters** county voter-information guides /
  local-measure pamphlets (2022, 2024): not researched in Phase 1 — the
  publications page and direct PDF links still need discovery.
- **fremont.gov bulk download route:** pick one of (a) live-browser download
  of the 7 curated showpublisheddocument URLs, (b) unblocked egress re-run of
  `scraper.py`, or (c) more `archive.theboringparts.com/agenda/fremont/`
  entries via search.
- **Regular council agenda PACKETS** (full staff-report packets, the richest
  source) were not individually indexed by search; enumerate via the
  FlexAgendaCenter UI in a browser.
