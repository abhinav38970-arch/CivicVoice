# JUDGE 1 — Technical Skeptic: CivicVoice Code Review

**Persona:** CS professor. Prior: "this looks like a prompt chain, not engineering."
**Entry:** CivicVoice — multilingual (en/hi/pa/zh/es/fa) plain-language summaries of public civic
documents (CA voter guides, Fremont council agendas), every claim cited to source file + page,
plus an evaluation harness (citation validity, grounding, advisory-language detection).
**Repo reviewed:** `~/workspace/civicvoice/` — all 8 Python files, both prompt templates,
`templates/index.html`, `README.md`, `requirements.txt`. `demo.py` and `eval.py` executed;
adversarial probes run against `eval.grounding_score` and `retriever.retrieve`.
**District:** CA-14. **Deadline:** Oct 26, 2026.

---

## Scores (official 2026 CAC criteria)

### (a) Quality of the idea — 7/10
The idea is genuinely good: civic documents are unreadable to most residents, non-English
households are the majority in much of CA-14, and claim-level citations plus a visible
accuracy harness is a real differentiator against "AI summarizer" entries. It is not, however,
technically original — retrieval-augmented summarization with citations is a well-trodden
pattern, and the multilingual angle is a product choice, not an invention. Strong problem,
familiar solution shape. The idea can win; the implementation as it stands cannot carry it.

### (b) Implementation of the idea (UX/design) — 5/10
A working Flask app: query box, 6-language picker, claims rendered with citations, a
prominent VERDICT badge, an honesty banner in mock mode, JSON error handling. Serviceable.
But the core value proposition is *verifiability*, and the UI gives the user no way to
verify: clicking a citation does not show the cited source text, so a judge cannot check
whether a claim matches its page. Single-shot Q&A only — no document browsing, no
comparison view, no reading-level indicator despite the "8th-grade" prompt claim. And in
the configuration the judges will actually run (no API key), the "Hindi" summary on screen
is English placeholder text wearing a Hindi label. That is a demo that misrepresents the
product unless the banner is read carefully.

### (c) Demonstrated excellence of coding and programming skills — 4/10
There is real engineering here, and I will credit it: `parser.py` (399 lines — PyMuPDF
primary with pdfplumber fallback, two-column reading-order recovery, header/footer
stripping, heading-based chunking with word budgets, scanned-page flagging instead of
silent drops) is substantive document engineering, not a prompt chain. `llm_client.py`
has a clean three-transport fallback (openai → httpx → urllib), env-var configuration,
and a deterministic mock. `summarizer.py` validates schema strictly, retries once on
bad JSON, and enforces a post-hoc advisory ban. `eval.py`'s self-tests pass.

But the load-bearing claims of the project collapse under reading:

1. **The eval harness cannot evaluate the product's own core languages** (proven below).
2. **The verification loop is circular** — it has never evaluated a real summary.
3. **Fake data sits in the live corpus** and outranks real documents.
4. **Retrieval quality is unmeasured and visibly weak.**
5. No pinned dependencies, no test suite — only `__main__` self-tests.

Good scaffolding; the load-bearing walls are missing. A professor reading this code does
not conclude "prompt chain" — they conclude "unfinished engineering with untested claims,"
which loses the same way.

---

## Fatal flaws (ranked, most lethal first)

### FATAL 1 — The grounding metric is Latin-script-only; the eval FAILs exactly the languages the app exists for
`eval.py` line: `WORD_RE = re.compile(r"[a-z0-9]+")`. Keyword extraction matches ASCII
alphanumerics only. Any claim written in Devanagari, Gurmukhi, Han characters, or
Perso-Arabic script with no ASCII digits produces an **empty keyword set**, hits the
`if not claim_kw: continue` branch, scores **0.0 grounding**, and forces verdict **FAIL**.

Empirically confirmed on this machine (realistic translated claims, chunk text in English
as the product's corpus is):
- Hindi (Devanagari, no digits): `grounding_score = 0.0`
- Chinese (no digits): `grounding_score = 0.0`
- Farsi (no digits): `grounding_score = 0.0`
- English control: `1.0`

The demo only ever shows PASS because `MockLLM` emits **English placeholder text**
regardless of the requested language. The moment a real LLM key is plugged in and a real
Hindi/Punjabi/Chinese summary comes back, the project's own "accuracy harness" — the
centerpiece of its anti-"prompt-chain" defense — will FAIL it. Five of the six supported
languages are affected. This is not a subtle bug; it is the project's thesis statement
being false. Any technical judge who reads `eval.py` (306 lines, they will) finds this in
under ten minutes.

### FATAL 2 — The verification story is circular: the harness has never judged a real summary
`MockLLM.complete()` cites the first retrieved chunk's own `source_file`/`page` metadata.
`citation_validity` then checks those citations against the same retrieved chunks. Result:
**1.00 by construction, every run, forever.** Grounding on the mock's generic English
placeholders scored **0.50** — exactly on the FAIL boundary (`< 0.5` fails) — in the
project's own demo runs. So the "VERDICT: PASS" in every screenshot and demo is a
tautology: the mock grades its own homework. The CAC rules explicitly allow judges to
request the app and source to "verify it works as claimed." As claimed, the eval proves
accuracy. In reality, no real model output has ever passed through `evaluate()`. Until a
real key runs real translations through this pipeline and the scores are recorded, the
eval harness is theater, and presenting it as proof of accuracy in the demo video is a
claim the code cannot support.

### FATAL 3 — Synthetic lorem-ipsum fixture is live in the retrieval corpus and outranks real documents
`data/parsed/fremont-council-2026-07-11-agenda.jsonl` (3 chunks) is the documented
synthetic test fixture ("lorem ipsum", "Test Staff Recommendation"). The README honestly
discloses this — but the file is still indexed, and disclosure in docs does not fix the
demo. Live probe on this machine:

```
query: "city council closed session labor negotiations"
 1. 'CHARTER ADVISORY COMMITTEE Q & A' (...) score=0.398
 2. 'B. Test – Lorem ipsum dolor sit amet, consectetur adipiscing'
     (fremont-council-2026-07-11-agenda.pdf, p.[2, 3]) score=0.378   <-- FAKE
 3. 'CONFERENCE WITH LABOR NEGOTIATOR:' (20250318_CC_Minutes__CLOSED_SESSION.pdf) score=0.365
```

A judge typing any council-related query has a real chance of being shown lorem ipsum as
a retrieved source — one screenshot of that in deliberation and the entry is dead. The
fix is one line; the fact that it shipped in the "complete" build signals no one ran the
demo on a council query before declaring victory.

### FATAL 4 — Retrieval quality is unmeasured, and what I measured is weak
Same probe as above: for the query "city council closed session labor negotiations," the
two documents *literally titled* "Closed Session Notice — Labor Negotiations"
(`20250304_...pdf`, `20250617_...pdf`) did not make the top 5. An unrelated charter
advisory Q&A (0.398) and the lorem-ipsum fixture (0.378) beat the genuinely relevant
"CONFERENCE WITH LABOR NEGOTIATOR" minutes (0.365). Top scores of 0.29–0.40 cosine are
mediocre. There is no retrieval test set, no recall@k measurement, no score floor (a
nonsense query still returns 5 chunks with a straight face), no reranking. The pipeline's
first stage — the one everything downstream depends on — is the least validated part of
the system. A judge who tries three queries will feel this before they read a line of code.

### FATAL 5 — "Six languages" is an untested claim, not an implementation
No real translation has ever been generated (no API key exists in this project). No
fluency check, no reading-level verification of the "8th-grade" prompt requirement, no
evidence the model honors the target-language instruction. The Hindi/Punjabi advisory
patterns are admitted in-code to be thin ("transliterated Hindi/Punjabi thin,
Devanagari/Gurmukhi minimal"). Criterion (b) scores *implementation* — five-sixths of the
language surface is currently a picker widget that changes a label on English text.

### FATAL 6 — Advisory-language detection is two inconsistent regex lists; paraphrase walks through
`summarizer.py` has `BANNED_ADVISORY_PHRASES` (14 phrases); `eval.py` has
`ADVISORY_PATTERNS` (a different, larger per-language set). Two sources of truth that
disagree. Both are substring matches: "you might consider supporting this measure,"
"it would be wise to vote against," or any novel phrasing passes silently. The guard has
never fired on a real model path because no real model has ever run. As defense-in-depth
it is fine; as a *demonstrated* safety property it is unproven.

### (Non-fatal, noted) Reproducibility and test discipline
`requirements.txt` has **zero version pins** (`sentence-transformers`, `flask`, ...).
A judge running `pip install` in November gets different versions than the builder tested.
There is no `tests/` directory and no CI — only `__main__` self-tests. `parser.py` is the
strongest file in the repo and the least demonstrated: no sample of its two-column
recovery or header/footer stripping appears in the demo.

---

## Fix list (concrete, in priority order)

1. **`eval.py` — make grounding script-aware (fixes FATAL 1).** Replace `WORD_RE =
   re.compile(r"[a-z0-9]+")` tokenization with Unicode-aware token sets:
   `re.findall(r"\w+", text.lower(), re.UNICODE)` for spaced scripts, plus a
   character-bigram fallback when the token count is < 3 (covers CJK, where "words"
   are single characters). Keep the English stopword list for Latin tokens only.
   Then **prove it**: add Devanagari, Chinese, and Farsi cases to the `__main__`
   self-test (a grounded claim in each script must score ≥ 0.5; an ungrounded one
   must score low). Re-run `python eval.py` and keep the output.

2. **Quarantine the synthetic fixture (fixes FATAL 3).** Delete
   `data/raw/fremont-council-2026-07-11-agenda.pdf` and
   `data/parsed/fremont-council-2026-07-11-agenda.jsonl` (or move both to
   `data/quarantine/`), add an `EXCLUDE_FILES` set in `retriever.load_chunks()`,
   rebuild the index (`python retriever.py --rebuild`), and re-run the council
   probe query to confirm no lorem ipsum in results. Five-minute fix; do it first.

3. **Break the circularity with a real model (fixes FATAL 2 and FATAL 5).** Obtain an
   LLM API key, run `demo.py` on at least 3 real queries × all 6 languages, and
   record every output plus its eval scores in a new `EVALLOG.md`. Fix whatever
   fails (it will fail — see FATAL 1). The submission's accuracy claims must rest
   on this log, not on mock runs. If no key is available before submission, the
   demo video must state plainly that translations are unevaluated — but understand
   this guts the entry's central defense.

4. **Retrieval: measure it, then improve it (fixes FATAL 4).** Create
   `tests/test_retrieval.py` with ~10 hand-written queries and their known-relevant
   chunk IDs (from the real corpus); assert recall@5. Add a minimum-score floor in
   `retrieve()` (e.g., warn/flag when top score < 0.30 instead of presenting weak
   matches as answers). Consider a lightweight keyword-boost hybrid if recall is
   poor. Re-run the "labor negotiations" probe as the regression test.

5. **Unify the advisory lists (fixes FATAL 6).** Move `ADVISORY_PATTERNS` into one
   module (e.g., `advisory.py`) imported by both `summarizer.py` and `eval.py`;
   extend hi/pa transliteration coverage; document the paraphrase limitation honestly
   in `README.md` rather than implying detection is robust.

6. **`app.py`/UI — make verifiability tangible (lifts criterion b).** Clicking a
   citation must display the cited chunk: source file, page, section title, and the
   actual chunk text, so a judge can check the claim against its source. This
   single feature is the product's thesis made clickable; without it the "every
   claim cited" story is cosmetic.

7. **Pin dependencies and add a test suite.** `pip freeze` the working venv into
   `requirements.txt`. Move the `__main__` self-tests into `tests/` runnable via
   `pytest` (eval multilingual cases + retrieval golden set + summarizer schema
   validation).

8. **Demo video (1–3 min) discipline.** Lead with the eval panel on a *real*
   key-backed run; show the citation drill-down (fix 6) on one claim; never show
   English placeholder text under a non-English language label. If mock mode is
   shown at all, the banner must be legible on camera.

---

## Overall verdict: as it stands, does this win CA-14? **No.**

The idea is a 7/10 and could win this district. The code as it stands would not survive
a careful judge. The single most disqualifying fact: the evaluation harness — the
entry's chosen defense against "it's just a prompt chain" — **provably fails summaries
in the very languages the app exists to produce**, and every PASS it has ever printed
came from a mock grading its own homework. Add a live lorem-ipsum landmine in the
retrieval corpus, unmeasured retrieval that buries the relevant documents, and five
unexercised languages, and a technical judge needs about fifteen minutes with this repo
to vote no. None of this is fatal to the *project* — fixes 1–4 are days of work, not
weeks — but as of today the entry is a strong idea wrapped around untested claims, and
untested claims are what lose competitions.
