# BLOCKED_URLS.md — real documents that need a live-browser pull

Generated 2026-10-13. Every URL below is a VERIFIED REAL official government document
(verified via text-fetch or search-engine content). Automated download fails because
the site's bot mitigation (Akamai) 403s python-requests from this network; each was
tried ≤2 times. A live browser (real Chrome) is NOT blocked — pull each PDF, save
with the suggested filename into `data/raw/`, then run `python parser.py` and add
the new JSONL to `data/SOURCE_MANIFEST.json` (sha256).

## Fremont, CA — fremont.gov (11 URLs, all 403 AkamaiGHost)

| Suggested filename | URL |
|---|---|
| fremont-edac-2026-09-10-agenda.pdf | https://www.fremont.gov/home/showpublisheddocument/21124/639238525887330000 |
| fremont-council-2026-07-07-charter-public-comment.pdf | https://www.fremont.gov/home/showpublisheddocument/20824/639190263948570000 |
| fremont-cdbg-2026-07-31-public-notice.pdf | https://www.fremont.gov/home/showpublisheddocument/20962/639210229873270000 |
| fremont-council-handbook.pdf | https://www.fremont.gov/home/showpublisheddocument/16416/638646809454000000 |
| fremont-cdbg-2026-27-annual-action-plan.pdf | https://www.fremont.gov/home/showpublisheddocument/20192/639111543011678179 |
| fremont-charter-committee-2026-03-23-minutes.pdf | https://www.fremont.gov/home/showpublisheddocument/20132/639105501608500000 |
| fremont-sotc-2026-06-30-address.pdf | https://www.fremont.gov/home/showpublisheddocument/20804/639184590300770000 |
| fremont-charter-committee-2026-04-16-correspondence.pdf | https://www.fremont.gov/home/showpublisheddocument/20288/639122889591470000 |
| fremont-fy2026-27-adopted-budget.pdf | https://www.fremont.gov/home/showdocument?id=21162&t=639241258046568824 |
| fremont-fy2026-27-proposed-budget-presentation.pdf | https://www.fremont.gov/home/showpublisheddocument/20494 |
| fremont-newsletter-2026-spring.pdf | https://www.fremont.gov/home/showpublisheddocument/20104/639102327541730000 |

More available at https://www.fremont.gov/government/agenda-center (full council
agendas/packets + minutes, planning commission). Prefer full packets.

## Newark, CA — newarkca.gov (7 URLs, all 403 Akamai)

| Suggested filename | URL |
|---|---|
| newark-council-biennial-budget-2026-28.pdf | https://www.newarkca.gov/home/showpublisheddocument/12542/639216212636200000 |
| newark-council-recent-agenda.pdf | https://www.newarkca.gov/home/showpublisheddocument/12588/639232713026530000 |
| newark-council-2026-03-26-minutes.pdf | https://www.newarkca.gov/home/showpublisheddocument/12179/639131487149270000 |
| newark-council-2026-03-12-minutes.pdf | https://www.newarkca.gov/home/showpublisheddocument/12095/639107671677230000 |
| newark-planning-commission-2026-05-26-agenda.pdf | https://www.newarkca.gov/home/showpublisheddocument/12263/639149784297600000 |
| newark-nov-2026-election-notice.pdf | https://www.newarkca.gov/home/showpublisheddocument/12488/639199134082300000 |
| newark-master-fee-schedule-hearing-notice.pdf | https://www.newarkca.gov/home/showpublisheddocument/12436/639190455560570000 |

Meeting list (packet links Sept 2025–Sept 2026): https://www.newarkca.gov/departments/council-meetings-agendas-minutes

## Fremont Unified School District — board agendas (JS-rendered, needs live browser)

- FUSD board page: https://fremontunified.org/about/board/ → "Board Agenda and Policy Platform"
- GAMUT/Simbli meeting listing: https://simbli.eboardsolutions.com/SB_Meetings/SB_MeetingListing.aspx?S=36031613
  (meetings 10/14/2026, 09/09/2026, 08/26/2026, 07/29/2026, 06/24/2026, 06/10/2026,
  05/27/2026, 05/13/2026, 04/15/2026, 03/25/2026, 03/11/2026, 02/25/2026,
  02/11/2026, 01/28/2026, 01/14/2026, 12/10/2025, 11/19/2025, 10/22/2025,
  10/08/2025, 09/24/2025, 09/10/2025, 08/27/2025, 07/30/2025, retreat 01/31/2026)
- Agenda item text and attachment PDFs (`/Meetings/Attachment.aspx?S=36031613&AID=...`)
  are JS-rendered — enumerate per-meeting attachments in a JS-capable browser.

## Alameda County Nov 2026 Voter Information Guide (not found via public search)

- Official election page: https://acvote.alamedacountyca.gov/election-information/elections?id=260
- The county VIG is likely printed per ballot type and may live behind the
  My Voter Profile lookup (acvote.org/mvp, needs a voter address) or a JS-loaded
  documents section. In a live browser: check the election page's documents section,
  or run the mvp lookup with a Fremont address and grab one Fremont ballot-type
  VIG PDF as representative.
