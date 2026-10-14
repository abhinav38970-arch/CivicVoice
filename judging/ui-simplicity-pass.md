# UI Simplicity Pass — 2026-10-13

Directive from Abhinav: make the UI simple and plain — government-service plain,
not startup landing page. Functionality untouched.

## What changed (templates/index.html)

- Removed all emoji from headings, badges, chips, and citation buttons
  (🗳️ 🌐 ✨ 💬 🔍 📄). Citation buttons now read `file · page N`.
- Hero: deleted the badge row ("6 languages / Every claim cited / Never voting advice");
  the hero-sub paragraph already carries that information plainly.
- Title tag: "CivicVoice — Your government, in your language" → "CivicVoice —
  Plain-language summaries of civic documents".
- Shortened card sub-copy: "Tap a card — each summary is hand-written…" →
  "Each summary is hand-written and hand-verified against the source documents."
- Trust panel item 1: "Tap any 📄 citation" → "Tap any citation".
- Featured badge / card chip: "✨ … hand-verified" → plain "hand-verified" text.

Every honest label kept verbatim: "hand-written and hand-verified", "ask in English,
then read the summary in your language", the demo-mode footer note, the "never voting
advice" footer, the eval-summary honesty note ("Hand-verified examples, not live model
output"), and the translation-missing fallback.

## What changed (static/style.css)

- Deleted the gradient hero banner and its decorative watermark emoji; hero is now a
  plain heading + paragraph with a bottom rule.
- Deleted all box-shadows, the shimmer skeleton animation (skeletons are static gray
  blocks now), and hover lift/translate effects (hover = border color only).
- Deleted the CA-14 pill and hero badges; district renders as plain small-caps text.
- Radius 16px → 6px; gold accent treatments (featured badge, chip, drawer text box)
  → plain borders; drawer animation removed (static panel).
- Kept: spinner + button spinner (functional loading states), numbered claim circles
  (claim↔citation correspondence), warn-colored honest-note and foot-note (honesty
  signals), all responsive breakpoints and the mobile bottom-sheet drawer.

## Verification (live app, .venv, 2026-10-13)

- `GET /` → 200. Page contains zero emoji, zero `linear-gradient` in HTML; served
  CSS contains zero `linear-gradient` / `box-shadow` / `shimmer` references.
- `GET /api/golden` → 5 cards: charter-advisory, closed-session-labor,
  midyear-winter-relief, prop1-2026-housing-bond, prop2-school-bonds.
- `GET /api/eval-summary` → 90/90 claims grounded, 0 advisory flags, verdict PASS,
  6 languages.
- `GET /api/golden/prop1-2026-housing-bond?language=hi` → real Devanagari claim,
  cited to ca-voter-guide-2026-general.pdf p. 13.
- `GET /api/chunk` → exact source text served (drawer path intact).
- `POST /api/ask` (mock) → `mock_sources` with the honest "Live summaries need an
  LLM key" message.

## Deliberately not changed

- Language picker, featured cards, ask box, citation drawer, verification panel,
  eval-summary line, mobile layout, loading states — all work as before.
- No functionality was removed or added; this pass was presentation-only.
