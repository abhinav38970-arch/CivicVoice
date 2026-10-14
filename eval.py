"""CivicVoice eval harness — citation validity, grounding, advisory-language detection.

Deterministic. No LLM, no API calls.

Usage:
    from eval import evaluate
    result = evaluate(summary_json, retrieved_chunks)

Self-test:
    python eval.py
"""

import re

from advisory import contains_advisory

# ============================================================================
# GROUNDING POLICY (cross-lingual honesty)
#
# Keyword overlap can only validate claims against chunk text written in the
# SAME script. A Devanagari/Hindi, Gurmukhi/Punjabi, Han/Chinese, or
# Perso-Arabic/Farsi claim will essentially never keyword-overlap English
# chunk text — and overlap with the English claim would prove nothing about
# the translation's accuracy anyway.
#
# Policy:
#   * A claim dict may carry "claim_en" — the English source text the
#     non-English claim was translated from.
#   * If a claim's script differs from the cited chunk's script, grounding is
#     computed against claim_en when present (this validates that the
#     *content* exists in the source, NOT that the translation is faithful).
#   * Without claim_en, the claim is marked "cross_lingual_unevaluated" and
#     EXCLUDED from the FAIL threshold: the verdict then rests on
#     citation_validity == 1.0 and zero advisory flags.
#
# We never imply that keyword overlap validates a translation.
# ============================================================================

# English stopword list for grounding overlap. Kept minimal on purpose —
# dropping too much inflates overlap scores. Applies to pure-Latin tokens
# only; it is not applied to Devanagari/Gurmukhi/Han/Perso-Arabic tokens.
STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "then", "else", "when",
    "at", "by", "for", "with", "about", "into", "through", "during",
    "before", "after", "above", "below", "to", "from", "up", "down",
    "in", "out", "on", "off", "over", "under", "again", "further",
    "once", "here", "there", "when", "where", "why", "how", "all",
    "any", "both", "each", "few", "more", "most", "other", "some",
    "such", "no", "nor", "not", "only", "own", "same", "so", "than",
    "too", "very", "can", "will", "just", "should", "now", "is",
    "are", "was", "were", "be", "been", "being", "have", "has",
    "had", "having", "do", "does", "did", "doing", "would", "could",
    "ought", "i", "me", "my", "myself", "we", "our", "ours",
    "ourselves", "you", "your", "yours", "yourself", "yourselves",
    "he", "him", "his", "himself", "she", "her", "hers", "herself",
    "it", "its", "itself", "they", "them", "their", "theirs",
    "themselves", "what", "which", "who", "whom", "this", "that",
    "these", "those", "am",
}

_LATIN_TOKEN_RE = re.compile(r"[a-z0-9_]+")


def _tokens(text: str) -> set:
    """Unicode-aware keyword tokens.

    re.findall(r"\\w+", ..., re.UNICODE) tokenizes spaced scripts
    (Devanagari, Gurmukhi, Perso-Arabic, Latin) into word tokens. When the
    token count is < 3 — the CJK case, where "words" are single characters
    and one long token results — character bigrams are added so overlap can
    still be measured. English stopwords are dropped only for pure-Latin
    tokens.
    """
    toks = re.findall(r"\w+", text.lower(), re.UNICODE)
    kept = [
        t for t in toks
        if not (_LATIN_TOKEN_RE.fullmatch(t) and t in STOPWORDS)
    ]
    out = set(kept)
    if len(kept) < 3:
        for t in toks:
            chars = list(t)
            for a, b in zip(chars, chars[1:]):
                out.add(a + b)
    return out


def _has_nonlatin_wordchar(text: str) -> bool:
    return any(ord(c) > 127 and (c.isalnum() or c == "_") for c in text)


def _is_cross_lingual(claim_text: str, chunk_text: str) -> bool:
    """True when the claim uses a non-Latin script but the chunk does not."""
    return _has_nonlatin_wordchar(claim_text) and not _has_nonlatin_wordchar(chunk_text)


def _citation_matches(citation: dict, chunk: dict) -> bool:
    cited_page = citation.get("page")
    chunk_page = chunk.get("page")
    if citation.get("source_file") != chunk.get("source_file"):
        return False
    cited_pages = cited_page if isinstance(cited_page, list) else [cited_page]
    chunk_pages = chunk_page if isinstance(chunk_page, list) else [chunk_page]
    return any(p in chunk_pages for p in cited_pages)


def _find_chunk(citation: dict, retrieved_chunks: list) -> dict | None:
    for chunk in retrieved_chunks:
        if _citation_matches(citation, chunk):
            return chunk
    return None


def citation_validity(claims: list, retrieved_chunks: list) -> float:
    """Fraction of claims whose citation matches at least one retrieved chunk."""
    if not claims:
        return 0.0
    valid = 0
    for claim in claims:
        citation = claim.get("citation") or {}
        if _find_chunk(citation, retrieved_chunks) is not None:
            valid += 1
    return valid / len(claims)


def grounding_detail(claims: list, retrieved_chunks: list,
                     threshold: float = 0.15) -> dict:
    """Per-claim grounding analysis.

    Returns {"per_claim": [...], "score": float, "evaluated": int,
             "grounded": int}. Each per-claim entry has "index", "overlap",
    "status", and "note". Statuses:

      grounded                 — same-script overlap reached threshold
      ungrounded               — overlap below threshold (claim not in source)
      cross_lingual_unevaluated— non-Latin claim vs Latin chunk, no claim_en
                                 supplied; EXCLUDED from the FAIL threshold
      no_citation_match        — citation matched no retrieved chunk
      empty_claim              — no keywords extractable from claim

    score = grounded / evaluated (claims actually scored). When nothing was
    evaluable, score is 1.0 by convention — the verdict then rests on
    citation validity and advisory flags (see evaluate()).
    """
    per_claim = []
    grounded = 0
    evaluated = 0
    for i, claim in enumerate(claims):
        claim_text = claim.get("claim", "") or ""
        chunk = _find_chunk(claim.get("citation") or {}, retrieved_chunks)
        if chunk is None:
            per_claim.append({
                "index": i, "overlap": 0.0, "status": "no_citation_match",
                "note": "citation did not match any retrieved chunk",
            })
            continue
        chunk_text = chunk.get("text", "") or ""
        scoring_text = claim_text
        note = None
        if _is_cross_lingual(claim_text, chunk_text):
            claim_en = claim.get("claim_en")
            if claim_en:
                scoring_text = claim_en
                note = ("cross-lingual claim scored via claim_en (English "
                        "source text); overlap proves the CONTENT is in the "
                        "source, not that the translation is faithful")
            else:
                per_claim.append({
                    "index": i, "overlap": None,
                    "status": "cross_lingual_unevaluated",
                    "note": ("no claim_en supplied; keyword overlap against "
                             "English chunk text is meaningless — excluded "
                             "from the FAIL threshold"),
                })
                continue
        claim_kw = _tokens(scoring_text)
        if not claim_kw:
            per_claim.append({
                "index": i, "overlap": 0.0, "status": "empty_claim",
                "note": "no keywords extractable from claim",
            })
            continue
        chunk_kw = _tokens(chunk_text)
        overlap = len(claim_kw & chunk_kw) / len(claim_kw)
        evaluated += 1
        if overlap >= threshold:
            grounded += 1
            status = "grounded"
        else:
            status = "ungrounded"
        per_claim.append({
            "index": i, "overlap": round(overlap, 4),
            "status": status, "note": note,
        })
    score = (grounded / evaluated) if evaluated else 1.0
    return {
        "per_claim": per_claim,
        "score": round(score, 4),
        "evaluated": evaluated,
        "grounded": grounded,
    }


def grounding_score(claims: list, retrieved_chunks: list,
                    threshold: float = 0.15) -> float:
    """Backward-compatible float: fraction of EVALUATED claims grounded."""
    return grounding_detail(claims, retrieved_chunks, threshold)["score"]


def advisory_flags(claims: list) -> list:
    """Scan every claim for voting-advice language across all target languages."""
    flags = []
    for i, claim in enumerate(claims):
        text = claim.get("claim", "") or ""
        for lang, pattern in contains_advisory(text):
            flags.append(
                f"advisory language '{pattern}' (lang {lang}) found in claim {i}"
            )
    return flags


def evaluate(summary_json: dict, retrieved_chunks: list) -> dict:
    """Run the full eval. Returns citation_validity, grounding_score,
    advisory_flags, verdict, and the per-claim grounding_detail.

    FAIL iff: any advisory flag, citation_validity < 1.0, or the grounding
    score over EVALUATED claims < 0.5. Claims marked
    cross_lingual_unevaluated are excluded from the grounding threshold —
    they cannot force a FAIL by themselves.
    """
    claims = summary_json.get("summary") or []
    validity = citation_validity(claims, retrieved_chunks)
    detail = grounding_detail(claims, retrieved_chunks)
    flags = advisory_flags(claims)
    grounding_fail = detail["evaluated"] > 0 and detail["score"] < 0.5
    verdict = "FAIL" if (flags or validity < 1.0 or grounding_fail) else "PASS"
    return {
        "citation_validity": round(validity, 4),
        "grounding_score": detail["score"],
        "advisory_flags": flags,
        "verdict": verdict,
        "grounding_detail": detail,
    }


# ============================================================================
# Self-test
# ============================================================================
def _run_self_tests():
    chunks = [
        {
            "source_file": "CA-Voter-Guide-2026.pdf",
            "page": 4,
            "section_title": "Proposition 5",
            "text": (
                "Proposition 5 would amend the state constitution to lower the "
                "voter approval threshold for local bonds funding affordable "
                "housing and public infrastructure from two-thirds to 55 percent. "
                "The Legislative Analyst estimates this change would make it "
                "easier for cities and counties to approve housing bonds."
            ),
        },
        {
            "source_file": "CA-Voter-Guide-2026.pdf",
            "page": [10, 11],
            "section_title": "Proposition 6",
            "text": (
                "Proposition 6 proposes removing the gas tax adjustment indexed "
                "to inflation. Supporters argue it lowers fuel costs for "
                "drivers; opponents argue it reduces transportation funding "
                "for road repairs and transit projects across the state."
            ),
        },
        # Same-script Chinese chunk: proves the char-bigram fallback path.
        {
            "source_file": "CA-Voter-Guide-2026.pdf",
            "page": 12,
            "section_title": "Proposition 5 (Chinese)",
            "text": (
                "第5号提案将把地方住房债券的选民批准门槛从三分之二降低到55%。支持者认为这会帮助城市。"
            ),
        },
    ]
    en_citation = {"source_file": "CA-Voter-Guide-2026.pdf", "page": 4}
    zh_citation = {"source_file": "CA-Voter-Guide-2026.pdf", "page": 12}

    results = []

    def check(name, cond, detail=""):
        results.append((name, cond, detail))
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}"
              + (f" — {detail}" if detail else ""))

    # (a) Clean summary — expect PASS
    clean = {
        "summary": [
            {
                "claim": (
                    "Proposition 5 would lower the voter approval threshold for "
                    "local housing bonds from two-thirds to 55 percent."
                ),
                "citation": en_citation,
            },
            {
                "claim": (
                    "Proposition 6 opponents say removing the gas tax adjustment "
                    "would reduce funding for road repairs and transit projects."
                ),
                "citation": {"source_file": "CA-Voter-Guide-2026.pdf", "page": 11},
            },
        ],
        "language": "en",
    }
    r = evaluate(clean, chunks)
    check("(a) clean summary verdict PASS", r["verdict"] == "PASS", str(r))

    # (b) One bogus citation (page 9999) — expect FAIL on validity
    bogus = {
        "summary": [
            {
                "claim": (
                    "Proposition 5 would lower the voter approval threshold for "
                    "local housing bonds from two-thirds to 55 percent."
                ),
                "citation": en_citation,
            },
            {
                "claim": (
                    "Proposition 6 opponents say removing the gas tax adjustment "
                    "would reduce funding for road repairs and transit projects."
                ),
                "citation": {"source_file": "CA-Voter-Guide-2026.pdf", "page": 9999},
            },
        ],
        "language": "en",
    }
    r = evaluate(bogus, chunks)
    check("(b) bogus citation verdict FAIL", r["verdict"] == "FAIL", str(r))

    # (c) Advisory language — expect FAIL with advisory flag
    advisory = {
        "summary": [
            {
                "claim": (
                    "Proposition 5 would lower the voter approval threshold for "
                    "local housing bonds from two-thirds to 55 percent."
                ),
                "citation": en_citation,
            },
            {
                "claim": "You should vote yes on Prop 5.",
                "citation": en_citation,
            },
        ],
        "language": "en",
    }
    r = evaluate(advisory, chunks)
    check("(c) advisory language verdict FAIL + flag",
          r["verdict"] == "FAIL" and bool(r["advisory_flags"]),
          str(r["advisory_flags"]))

    # (d) Grounded non-English claims scored via claim_en: each >= 0.5
    claim_en = ("Proposition 5 would lower the voter approval threshold for "
                "local housing bonds from two-thirds to 55 percent.")
    multilingual = [
        ("hi", "प्रस्ताव 5 स्थानीय आवास बांडों के लिए मतदाता अनुमोदन सीमा "
               "को दो-तिहाई से घटाकर 55 प्रतिशत करेगा।"),
        ("pa", "ਪ੍ਰਸਤਾਵ 5 ਸਥਾਨਕ ਹਾਊਸਿੰਗ ਬਾਂਡਾਂ ਲਈ ਵੋਟਰ ਮਨਜ਼ੂਰੀ ਦੀ ਸੀਮਾ "
               "ਨੂੰ ਦੋ-ਤਿਹਾਈ ਤੋਂ ਘਟਾ ਕੇ 55 ਪ੍ਰਤੀਸ਼ਤ ਕਰੇਗਾ।"),
        ("zh", "第5号提案会将地方住房债券的选民批准门槛从三分之二降低到55%。"),
        ("fa", "پروپوزیشن ۵ آستانه تأیید رأی‌دهندگان برای اوراق قرضه "
               "مسکن محلی را از دو سوم به ۵۵ درصد کاهش می‌دهد."),
    ]
    for lang, text in multilingual:
        s = {"summary": [{"claim": text, "claim_en": claim_en,
                          "citation": en_citation}],
             "language": lang}
        res = evaluate(s, chunks)
        overlap = res["grounding_detail"]["per_claim"][0]["overlap"]
        check(f"(d) grounded {lang} claim overlap >= 0.5",
              overlap is not None and overlap >= 0.5, f"overlap={overlap}")

    # (e) Ungrounded multilingual claim (via claim_en) scores low
    ungrounded = {
        "summary": [{
            "claim": "यह फिल्म ऑस्कर जीतेगी।",  # "This film will win an Oscar."
            "claim_en": "This film will win an Oscar.",
            "citation": en_citation,
        }],
        "language": "hi",
    }
    r = evaluate(ungrounded, chunks)
    ov = r["grounding_detail"]["per_claim"][0]["overlap"]
    check("(e) ungrounded claim scores low + verdict FAIL",
          ov is not None and ov < 0.5 and r["verdict"] == "FAIL",
          f"overlap={ov}, verdict={r['verdict']}")

    # (f) Cross-lingual claim with NO claim_en must NOT force FAIL
    no_en = {
        "summary": [{
            "claim": "प्रस्ताव 5 स्थानीय आवास बांडों के लिए मतदाता अनुमोदन "
                     "सीमा को दो-तिहाई से घटाकर 55 प्रतिशत करेगा।",
            "citation": en_citation,
        }],
        "language": "hi",
    }
    r = evaluate(no_en, chunks)
    status = r["grounding_detail"]["per_claim"][0]["status"]
    check("(f) no-claim_en cross-lingual claim excluded, verdict PASS",
          status == "cross_lingual_unevaluated" and r["verdict"] == "PASS",
          f"status={status}, verdict={r['verdict']}")

    # (g) Same-script Chinese claim vs Chinese chunk (bigram fallback) >= 0.5
    zh_same = {
        "summary": [{
            "claim": "第5号提案降低了住房债券的批准门槛。",
            "citation": zh_citation,
        }],
        "language": "zh",
    }
    r = evaluate(zh_same, chunks)
    ov = r["grounding_detail"]["per_claim"][0]["overlap"]
    check("(g) same-script Chinese bigram overlap >= 0.5",
          ov is not None and ov >= 0.5, f"overlap={ov}")

    # (h) Mostly ungrounded (2 of 3 claims, score 1/3 < 0.5) → grounding FAIL
    mixed = {
        "summary": [
            {"claim": claim_en, "citation": en_citation},
            {"claim": "यह फिल्म ऑस्कर जीतेगी।",
             "claim_en": "This film will win an Oscar.",
             "citation": en_citation},
            {"claim": "这部电影会得奥斯卡奖。",
             "claim_en": "This movie will win an Oscar.",
             "citation": en_citation},
        ],
        "language": "hi",
    }
    r = evaluate(mixed, chunks)
    check("(h) mostly-ungrounded → verdict FAIL",
          r["verdict"] == "FAIL" and r["grounding_score"] < 0.5,
          f"grounding={r['grounding_score']}, verdict={r['verdict']}")

    failed = [n for n, ok, _ in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} self-tests passed")
    if failed:
        raise SystemExit(f"FAILED: {failed}")


if __name__ == "__main__":
    _run_self_tests()
