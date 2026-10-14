# CivicVoice — Demo Video Script (90 seconds)

**Purpose:** CAC 2026 submission video (1–3 min requirement). Runtime target: **90 seconds.**
**Verified against the built UI (2026-10-13):** language picker first → featured
example cards → cited summaries in 6 languages → 📄 citation side panel →
"How we check our work" panel → ✨ Featured example golden responses
(hand-written, hand-verified — never presented as live model output).
Re-confirm every click on the running app before recording.

## The one sourced stat (used at 0–15s)

> **64.2% of Fremont residents age 5 and older speak a language other than English at home.**
> U.S. Census Bureau QuickFacts, Fremont city, California (2020–2024 American Community Survey 5-year estimates).
> Source: https://www.census.gov/quickfacts/fact/table/fremontcitycalifornia,CA/BZA110223
>
> (This resolves the 64% vs 62% conflict in earlier drafts: the verified figure is **64.2%**.
> Phrase it exactly as above — "residents age 5+", not "households.")

Background stat (for SUBMISSION.md, not spoken in the video): in the Data USA PUMA covering
Fremont's southeast, 68.3% of households report speaking a non-English language at home as
their primary shared language; the top three are Chinese (incl. Mandarin/Cantonese),
Hindi, and Spanish — the reason the six languages are en/hi/pa/zh/es/fa.
Source: https://DataUSA.io/profile/geo/alameda-county-south-fremont-city-southeast-puma-ca

## Shot list + voiceover (all 90 seconds)

> Formatting convention: **🎥 On screen** = exact action/click. **🎙️ Voiceover** = spoken line.
> **⌨️ Callout** = on-screen text overlay to add in editing (must be legible at 1080p).

### SHOT 1 — 0:00–0:15 · The hook (face to camera)

🎥 Face to camera. In Abhinav's hand (or on a desk prop): a printed California Voter
Information Guide — dense, small print. He sets it down / taps it.

🎙️ "This is the California Voter Information Guide. It's dense legal English, written
at a level most residents can't parse. And in my city, Fremont, 64.2% of residents
speak a language other than English at home — so for most of my neighbors, this might
as well not exist."

⌨️ Callout (lower third, hold 4s):
"64.2% of Fremont residents age 5+ speak a language other than English at home
— U.S. Census Bureau QuickFacts, 2020–2024"

🎥 Cut to: laptop screen, browser open to CivicVoice at http://127.0.0.1:5000 (or the
deployed URL). The language picker is the FIRST thing on the page.

### SHOT 2 — 0:15–0:45 · The magic (one click, her language)

🎥 Screen recording, cursor visible. **Exact clicks:**
1. Click the language picker → select **हिन्दी (Hindi)**.
2. Click the featured card **"🗳️ Prop 1: housing bond (Nov 2026)"** — the current
   election's lead measure (✨ Featured example). (Alternate: "🗳️ What's on the
   ballot?" — the 2024 Prop 2 card. Prefer the Nov 2026 card: the election is
   three weeks away.)
3. Summary renders: 3 plain-language claims in real Devanagari script, each claim
   carrying a **📄 citation** (source file + page).

🎙️ "So I built CivicVoice. You pick your language first — say Hindi — and tap one card.
That's it. No question to write, no settings to figure out. You get a plain-language
summary of what's on the ballot — in Hindi — and every single sentence is cited to the
exact page it came from."

⌨️ Callout: "✨ Featured example — hand-verified golden response"
⌨️ Zoom-in cutaway (2s): the summary clearly shows Devanagari text — real non-English
script fills the frame, not a label.

*(Note for the editor: the on-screen Hindi copy is the hand-verified golden response
from the eval log — Worker B's deliverable. This script does not invent that wording.)*

### SHOT 3 — 0:45–1:15 · The trust (citation drill-down + the guard)

🎥 **Exact clicks:**
1. Hover/click the first claim's **📄 citation** → side panel slides in showing the
   EXACT source chunk: file name, page number, section title, and the full chunk text.
2. Scroll briefly in the side panel to show it's real source text, not a snippet.
3. Close panel. Scroll down to the **"How we check our work"** panel; glance at it for
   2 seconds (technical metrics stay collapsed — the headline speaks human).

🎙️ "But most AI summarizers invent facts. So here's the part that matters: every claim
opens the exact source page it came from — you can check it yourself. And by design,
CivicVoice *describes* the measure. It never tells you how to vote."

⌨️ Callout: "Every sentence traced to its source."
⌨️ Callout on the guard moment: "Describes — never advises."

### SHOT 4 — 1:15–1:30 · The builder (face to camera) + ask

🎥 Face to camera. The laptop behind/beside him still shows the Hindi summary.

🎙️ "I live in Fremont, in California's 14th district, and I built this because my
neighbors shouldn't need perfect English to understand what's on their ballot. I'm
Abhinav — and this is CivicVoice."

⌨️ End card (4s): "CivicVoice — Civic documents in your language. Every claim cited,
never advisory. Built by Abhinav Upadhyay, CA-14."

---

## The "different moment" (honesty take — record as an alternate take)

Record this as a second 15-second take; it can replace Shot 3's panel glance or run as
a mid-video beat if the main cut has room. It is the single most persuasive shot in the
video (Judge 2, fix #7: "Nothing persuades like a refusal").

🎥 **Exact clicks:**
1. Language picker → **English** (keep it simple).
2. "Ask your own question" box → type any free-form question, e.g.
   **"fremont property tax rate change 2026"**.
3. Click Ask. In demo mode (no LLM key) the app responds with its honest state:
   **"Live summaries need an LLM key — here are the sources we found."**
   It shows the real retrieved sources and refuses to fabricate a summary.

🎙️ "And it never invents an answer — without a live model, it shows its sources and says so plainly."

⌨️ Callout: "It refuses to invent facts."

**Why this works:** most AI demos would hallucinate a fluent summary here. CivicVoice
shows its sources and admits what it can't do. That honesty IS the product story.

**Pre-flight requirement for this take:** confirm on camera that the free-form query
returns the "Live summaries need an LLM key" state (not a fabricated summary). Never
fake the refusal — it is the app's real designed behavior in demo mode.

## Full continuous voiceover (read-aloud copy)

> "This is the California Voter Information Guide. It's dense legal English, written
> at a level most residents can't parse. And in my city, Fremont, 64.2% of residents
> speak a language other than English at home — so for most of my neighbors, this
> might as well not exist.
>
> So I built CivicVoice. You pick your language first — say Hindi — and tap one card.
> That's it. No question to write, no settings to figure out. You get a plain-language
> summary of what's on the ballot — in Hindi — and every single sentence is cited to the
> exact page it came from.
>
> But most AI summarizers invent facts. So here's the part that matters: every claim
> opens the exact source page it came from — you can check it yourself. And by design,
> CivicVoice describes the measure. It never tells you how to vote.
>
> I live in Fremont, in California's 14th district, and I built this because my
> neighbors shouldn't need perfect English to understand what's on their ballot. I'm
> Abhinav — and this is CivicVoice."

*(Abhinav: this is a draft — rewrite any line in your own words before recording. Keep
the 64.2% stat wording and the "describes, never tells you how to vote" line intact.)*

## Do NOT list

1. **Never show English placeholder text under a non-English language label.** Every
   non-English shot must show the real golden (hand-verified) response or real-key
   output. If a golden response isn't ready for a language, don't show that language.
2. **The "Demo mode — mock summaries" banner must be legible on camera if it appears.**
   Better: record only golden/real-key paths so no banner is on screen at all. Do not
   crop or blur a banner to hide it — that's misrepresentation.
3. **Voiceover + face, never an unnarrated screen recording.** Abhinav's face opens and
   closes the video; his voice runs under every screen shot.
4. Never claim the app covers documents it doesn't — on camera, only query the corpus
   that exists (CA Voter Information Guides + Fremont council documents). Keep the
   footer demo note ("featured examples are hand-verified; live summaries need an LLM
   key") legible in at least one wide shot — never crop or hide it.
5. Never present the "different moment" refusal as a live model run if it is the
   app's designed decline path — it IS the designed decline path; say exactly that.
6. Don't read the stat callout off the screen — say it, then let the callout reinforce it.
7. Keep the end card under 4 seconds and end on his name + district: judges remember
   the builder, not the tagline.
