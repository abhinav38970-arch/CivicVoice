# CivicVoice — Demo Video Script (90 seconds)

**Purpose:** CAC 2026 submission video (1–3 min requirement). Runtime target: **90 seconds.**
**Verified against the built UI (2026-10-14):** language gatekeeper (zero English) →
6-language UI flip → featured cards with Summary / If it passes / If it fails →
📄 citation side panel → 🔊 listen button → notices feed → 311 tap-to-report →
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

## Shot list + voiceover (all 90 seconds)

> Formatting convention: **🎥 On screen** = exact action/click. **🎙️ Voiceover** = spoken line.
> **⌨️ Callout** = on-screen text overlay to add in editing (must be legible at 1080p).

### SHOT 1 — 0:00–0:12 · The hook (face to camera)

🎥 Face to camera. In Abhinav's hand (or on a desk prop): a printed California Voter
Information Guide — dense, small print. He sets it down / taps it.

🎙️ "This is the California Voter Information Guide. It's dense legal English. And in my
city, Fremont, 64.2% of residents speak a language other than English at home — so for
most of my neighbors, this might as well not exist."

⌨️ Callout (lower third, hold 4s):
"64.2% of Fremont residents age 5+ speak a language other than English at home
— U.S. Census Bureau QuickFacts, 2020–2024"

### SHOT 2 — 0:12–0:35 · The gatekeeper (zero English)

🎥 Screen recording, fresh browser profile (clear localStorage first so the gatekeeper
shows). The FIRST screen: six big buttons in native scripts — English, Español,
हिन्दी, ਪੰਜਾਬੀ, 中文, فارسی — and nothing else. No English explanatory copy.

**Exact clicks:**
1. Click **हिन्दी**.
2. The whole page flips to Hindi — headings, buttons, placeholders, footer.
3. Click the featured card **"🗳️ Prop 1: housing bond (Nov 2026)"**.

🎙️ "So I built CivicVoice. The first screen doesn't even speak English — you tap your
language, and the entire app flips. Tap one card, and you get what's on the ballot in
Hindi: a summary, what happens if it passes, what happens if it fails."

⌨️ Callout: "Zero English until you choose"
⌨️ Zoom-in cutaway (2s): the pass/fail sections render in real Devanagari script —
real non-English script fills the frame, not a label.

### SHOT 3 — 0:35–0:55 · The trust (citation drill-down + listen)

🎥 **Exact clicks:**
1. Click the first claim's **📄 citation** → side panel slides in showing the EXACT
   source chunk: file name, page number, section title, full chunk text.
2. Close panel. Click the **🔊 Listen** button — the summary reads aloud in Hindi
   (record the audio; it's the browser's real voice, no API key).

🎙️ "Every sentence opens the exact source page it came from — check it yourself. It
reads aloud for anyone who'd rather listen. And by design, CivicVoice *describes* the
measure. It never tells you how to vote."

⌨️ Callout: "Every sentence traced to its source."
⌨️ Callout on the guard moment: "Describes — never advises."

### SHOT 4 — 0:55–1:15 · The neighborhood (311 + notices)

🎥 **Exact clicks:**
1. Scroll to **"Report a neighborhood issue"** (Hindi UI). Tap the pothole icon,
   type one line (or use the mic), click "Use my location" — do NOT grant location in
   the recording; instead show the generated report text and the Copy button.
2. Quick scroll past the **notices feed** — 8 official City of Fremont announcements
   with dates.

🎙️ "It also helps with the rest of civic life — report a pothole in your own language,
get a ready-to-send report for the city, and see local notices. And it's honest about
what it can't do: it never pretends to file the report for you."

⌨️ Callout: "Honest about what it can't do"

### SHOT 5 — 1:15–1:30 · The builder (face to camera) + ask

🎥 Face to camera. The laptop behind/beside him shows the Hindi summary.

🎙️ "I live in Fremont, in California's 14th district, and I built this because my
neighbors shouldn't need perfect English to understand their ballot. I'm Abhinav —
and this is CivicVoice."

⌨️ End card (4s): "CivicVoice — Civic documents in your language. Every claim cited,
never advisory. Built by Abhinav Upadhyay, CA-14."

---

## The "different moment" (honesty take — record as an alternate take)

Record this as a second 15-second take; it can replace Shot 4's notices beat if the
main cut runs long. The single most persuasive shot in the video: "Nothing persuades
like a refusal."

🎥 **Exact clicks:**
1. Language picker → **English** (keep it simple).
2. "Ask your own question" box → type any free-form question, e.g.
   **"fremont property tax rate change 2026"**.
3. Click Ask. In demo mode (no LLM key) the app responds with its honest state:
   **"Live summaries need an LLM key — here are the sources we found."**
   It shows the real retrieved sources and refuses to fabricate a summary.

🎙️ "And it never invents an answer — without a live model, it shows its sources and says so plainly."

⌨️ Callout: "It refuses to invent facts."

**Pre-flight requirement for this take:** confirm on camera that the free-form query
returns the "Live summaries need an LLM key" state (not a fabricated summary). Never
fake the refusal — it is the app's real designed behavior in demo mode.

## Full continuous voiceover (read-aloud copy)

> "This is the California Voter Information Guide. It's dense legal English. And in my
> city, Fremont, 64.2% of residents speak a language other than English at home — so
> for most of my neighbors, this might as well not exist.
>
> So I built CivicVoice. The first screen doesn't even speak English — you tap your
> language, and the entire app flips. Tap one card, and you get what's on the ballot
> in Hindi: a summary, what happens if it passes, what happens if it fails.
>
> Every sentence opens the exact source page it came from — check it yourself. It
> reads aloud for anyone who'd rather listen. And by design, CivicVoice describes
> the measure. It never tells you how to vote.
>
> It also helps with the rest of civic life — report a pothole in your own language,
> get a ready-to-send report for the city, and see local notices. And it's honest
> about what it can't do: it never pretends to file the report for you.
>
> I live in Fremont, in California's 14th district, and I built this because my
> neighbors shouldn't need perfect English to understand their ballot. I'm Abhinav —
> and this is CivicVoice."

*(Abhinav: this is a draft — rewrite any line in your own words before recording. Keep
the 64.2% stat wording and the "describes, never tells you how to vote" line intact.)*

## Do NOT list

1. **Never show English placeholder text under a non-English language label.** Every
   non-English shot must show the real golden (hand-verified) response or real-key
   output. If a golden response isn't ready for a language, don't show that language.
2. **The "Demo mode" footer note must be legible on camera in at least one wide shot.**
   Do not crop or blur it to hide it — that's misrepresentation.
3. **Voiceover + face, never an unnarrated screen recording.** Abhinav's face opens and
   closes the video; his voice runs under every screen shot.
4. Never claim the app covers documents it doesn't — on camera, only query the corpus
   that exists (CA Voter Information Guides + Fremont council documents + city press
   releases).
5. Never present the "different moment" refusal as a live model run — it IS the
   designed decline path; say exactly that.
6. Don't read the stat callout off the screen — say it, then let the callout reinforce it.
7. Keep the end card under 4 seconds and end on his name + district: judges remember
   the builder, not the tagline.
8. Do not grant browser location permission on camera — describe the GPS step without
   capturing real coordinates.
