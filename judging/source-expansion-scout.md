# Source Expansion Scout — CivicVoice corpus growth
**Date:** 2026-10-13 | **Scout only — nothing downloaded or ingested**

Current corpus: 1,238 chunks / 42 files (CA voter guides, Fremont/Newark/Union City council docs, Alameda County agendas, Fremont FY26-27 budget). All PDF-derived. Abhinav's directive: add (a) Fremont city-site content — rules, ordinances, announcements, services — and (b) other government sites a Fremont resident would use.

## Ranked candidate sources

### Tier 1 — "What are the rules" (highest value; fills the biggest gap in the corpus)

**1. Fremont Municipal Code (full text) — codelibrary.amlegal.com**
- URL: `https://codelibrary.amlegal.com/codes/fremont/latest/overview` (code library root; per-title pages beneath)
- Content: every city ordinance organized by subject (rent review Ch. 9.60, ADUs, zoning, noise, parking, business licensing…). This is THE "what are the rules in Fremont" source.
- Format: HTML, one page per code section. Continuously updated as council amends the code.
- Size: large — hundreds of sections; a full ingest is maybe 2–4k chunks, dwarfing the current corpus. Recommend selective ingest: Titles 9 (public peace/morals), 18 (planning/zoning), plus rent review Ch. 9.60 and ADU sections first.
- Update frequency: rolling (amended after council votes).
- Usefulness: ★★★★★. Directly answers "what are the rules" — the exact question class the app currently cannot answer.
- Caveat: direct fetch returned HTTP 403 (bot protection). Ingest may need polite headers/rate-limiting, or fall back to the city's published code PDFs. Verify fetchability before committing.

**2. Rent Review Program — fremont.gov**
- URL: `https://www.fremont.gov/government/departments/housing/rent-review-program`
- Content: the rules — rent increase >5% in 12 months triggers tenant's right to review/hearing; process (consultation → mediation → board hearing, free, nonbinding recommendation).
- Format: HTML. Stable evergreen content.
- Size: small (~5–10 chunks with the sub-pages).
- Update frequency: rare (only when ordinance changes).
- Usefulness: ★★★★★. Fremont is majority-renter in large apartment tracts; rent questions are the #1 "rules" query class. Also pairs with the existing corpus (council rent-control report already ingested).

**3. Source of Income Discrimination ordinance — fremont.gov**
- URL: `https://www.fremont.gov/government/departments/housing/rent-review-program/source-of-income-discrimination`
- Content: 2019 amendment — landlords can't discriminate on Section 8 / lawful income sources; FAQ; contact line.
- Format: HTML. Stable.
- Size: tiny (~3–5 chunks).
- Usefulness: ★★★★☆. Concrete tenant right, FAQ format chunks beautifully.

### Tier 2 — "What's announced" (freshness; keeps the app current)

**4. City press releases — fremont.gov**
- URL: `https://fremont.gov/about/news-media/press-releases`
- Content: official announcements (2026 examples: police chief appointment, CALEA accreditation, homelessness count, real-time information center).
- Format: HTML index + per-release pages. New items ~monthly.
- Size: small per release (1–3 chunks each); ingest the last 12 months, then monthly refresh.
- Update frequency: monthly-ish.
- Usefulness: ★★★★☆. This is the "what's announced" feed. Staleness risk is the main cost — needs a refresh cadence or it rots.

**5. Human Services public notices (CDBG) — fremont.gov**
- URL: e.g. `https://www.fremont.gov/home/showpublisheddocument/20962/639210229873270000` (public comment periods, funding amendments)
- Content: 30-day comment periods, hearing dates, funding changes — actionable civic participation info.
- Format: mix of HTML notices and DocumentCenter PDFs (the PDF path already works via parser.py).
- Update frequency: several per year.
- Usefulness: ★★★☆☆. High civic value but episodic.

### Tier 3 — "What help exists" (services)

**6. Tenants / Fair Housing page — fremont.gov**
- URL: `https://www.fremont.gov/government/departments/housing/tenants`
- Content: counseling on deposits, repairs, evictions, discrimination complaints; hours, phone, address.
- Format: HTML. Stable.
- Size: small (~5 chunks).
- Usefulness: ★★★★☆. Actionable help info; pairs with the rent-review tier.

**7. Emergency Preparedness hub — fremont.gov**
- URL: `https://fremont.gov/residents/emergency-preparedness`
- Content: earthquake / wildfire / storm / tsunami / heat / power outage / evacuation guidance; alerts signup; volunteer programs.
- Format: HTML hub + sub-pages. Evergreen, reviewed periodically.
- Size: medium (~20–40 chunks across sub-pages).
- Usefulness: ★★★★☆. Fremont sits on the Hayward Fault; earthquake/wildfire guidance is genuinely high-stakes local content.

**8. CERT program page — fremont.gov**
- URL: `https://fremont.gov/government/departments/fire/safety-preparedness/cert`
- Content: free resident disaster training; next training early 2027; contact.
- Format: HTML. Stable.
- Size: tiny (~3 chunks).
- Usefulness: ★★★☆☆. Niche but concrete.

**9. Alameda County Social Services Agency**
- URL: `https://www.alamedacountysocialservices.org/` (office/contact pages)
- Content: CalFresh / Medi-Cal / CalWORKs / General Assistance; **Fremont office: 39155 Liberty St., Suite C330, 510-795-2428** — a Fremont resident's actual service point.
- Format: HTML. Stable program descriptions; office info changes rarely.
- Size: small (~10–15 chunks for the key program + contact pages).
- Usefulness: ★★★★☆. "What help exists" for benefits — the most-asked government question class after rules.

**10. Alameda County Newcomers resource directory**
- URL: `https://newcomerswelcome.acgov.org/resource-directory/`
- Content: categorized directory of county services (health, benefits, language access, employment) with office locations and phone numbers.
- Format: HTML directory. Updated periodically.
- Size: medium (~30–50 chunks if each listing becomes a chunk).
- Usefulness: ★★★☆☆. Broad but shallow; best as a referral layer, not deep content. Overlaps with #9 — ingest #9 first, this only if cheap.

### Tier 4 — State (supplementary)

**11. ca.gov / BenefitsCal**
- URLs: `https://www.ca.gov/` service finders; `https://www.benefitscal.com/`
- Content: state-level services (DMV, Covered California, EDD).
- Format: HTML; much of it is interactive tools, not documents.
- Size/update: varies.
- Usefulness: ★★☆☆☆. Deprioritize: interactive tools don't chunk well, and the app's wedge is *local* Fremont/CA-14 content. Only revisit if the local corpus is exhausted.

**Not recommended:** citizenportal.ai (third-party summaries of council meetings — not a government source, paywalled), Tri-City Voice news (not government), FUSD Simbli portal (JS-walled; parked already).

## Ingest proposal: HTML → the existing JSONL chunk format

The retriever expects `data/parsed/*.jsonl` where each line is:
`{"source_file", "page" (int or [start,end]), "section_title", "text"}`
and `retriever.load_chunks()` enforces the SHA-256 allowlist in `data/SOURCE_MANIFEST.json`. The manifest entries are `{filename, sha256, description}` — format-agnostic. HTML-derived JSONL fits with **zero changes** to the retriever, the manifest guard, or `/api/chunk`.

**Proposed pipeline** (`html_ingest.py`, new script next to `parser.py`):
1. **Fetch** a curated URL list (hand-maintained in the script, like the current raw/ workflow — no crawler; every source is a deliberate choice, which keeps the manifest's anti-junk property).
2. **Extract main content** with `trafilatura` (preferred: aggressive boilerplate removal, handles CivicPlus-style city sites well) or `readability-lxml` + BeautifulSoup fallback. Strip nav/header/footer/sidebars at extraction time.
3. **Section-split** on headings (`h1`–`h3`); each section becomes one chunk with `section_title` = heading path, `text` = section body, merged to the same 200–1500 word budget parser.py uses.
4. **`page` = section index (int).** This is the key compatibility trick: `/api/chunk?file=<name>&page=<n>` and the citation drill-down work unchanged — "page 3" just means "section 3 of the page" for HTML sources. Display copy can say "section" where it matters.
5. **Filename convention:** `html-<slug>.jsonl`, e.g. `html-fremont-rent-review-program.jsonl`, `html-fremont-municipal-code-ch9.60.jsonl`. Never use a `.pdf`-suffixed name (the `.pdf`→`.jsonl` mapping in `_safe_parsed_path` is only for PDF originals).
6. **Manifest:** script prints the SHA-256 of each output file plus a suggested `description` line; the operator appends the entry to `SOURCE_MANIFEST.json`. Same trust model as PDFs.
7. **Refresh:** re-run per source on its cadence (code: quarterly; press releases: monthly); the manifest entry's sha256 is regenerated each refresh — treat refresh as a new manifest edit, reviewed before commit.

**Pitfalls and how to handle them:**
- **Boilerplate** (nav, footer, "contact us" repeated on every city page): trafilatura removes most; add a post-pass that drops chunks whose text is >80% identical to another chunk from the same site (near-dupe filter).
- **JS-rendered pages:** fremont.gov is CivicPlus (server-rendered HTML — fine). amlegal returned 403 to the text fetcher: verify with real browser headers + rate limiting before counting the municipal code as ingestible; fallback is the city's published code PDFs via the existing parser.
- **Thin/duplicated pages:** many city pages are 2–3 sentences plus links. Set a minimum: skip sections under ~40 words unless they're high-signal (a phone number + address + hours block is worth keeping even when short — flag as `contact` section).
- **Staleness:** press releases and notices rot. Every HTML manifest entry should carry a `fetched` date in its description (e.g. "fetched 2026-10-13; refresh monthly") so staleness is visible in the manifest itself.
- **Scope discipline:** the manifest guard's real value is that junk can't enter silently. Keep the URL list hand-curated in the script — no recursive crawling, ever.

## Suggested ingest order (value per effort)
1. Rent Review Program + Source-of-Income pages (tiny, highest rules value)
2. Tenants/Fair Housing page (tiny, pairs with #1)
3. Emergency Preparedness hub (medium, high-stakes local)
4. Municipal code selective titles (large; verify amlegal fetch first — this is the single biggest corpus win)
5. Press releases, last 12 months (freshness layer; needs refresh cadence)
6. Alameda County SSA program + Fremont office pages
7. CDBG notices, CERT, newcomers directory (as cheap follow-ups)
