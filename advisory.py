"""CivicVoice advisory-language patterns — SINGLE SOURCE OF TRUTH.

Imported by:
  - summarizer.py : post-hoc ban (ValueError if a generated claim matches)
  - eval.py        : advisory_flags() scanning of every claim

CivicVoice must NEVER advise how to vote. Matching is case-insensitive
substring matching on each claim. Patterns are literal substrings (not
regexes).

COVERAGE HONESTY (do not over-claim in docs):
  * Substring matching only catches phrasings we enumerated. A paraphrase
    ("you might consider supporting this measure", "it would be wise to
    vote against") walks through silently. This is a keyword backstop, not
    a demonstrated safety property.
  * Non-English coverage is per-language spot lists of the most direct
    voting-advice phrasings (equivalents of "vote yes/no", "you should
    support/oppose"). It is not a lexicon of every way to advise a vote in
    Hindi, Punjabi, Spanish, Chinese, or Farsi.

  get_patterns(lang) -> list of lowercase literal substrings.
"""

ADVISORY_PATTERNS = {
    # English
    "en": [
        "vote yes",
        "vote no",
        "vote for",
        "vote against",
        "you should",
        "you must",
        "we recommend",
        "i recommend",
        "it is best to",
        "support this",
        "oppose this",
        "support prop",
        "oppose prop",
        "don't vote",
        "do not vote",
        "cast your vote for",
        "back this measure",
        "reject this measure",
        "should vote",
        "ought to",
        "vote in favor of",
    ],
    # Spanish
    "es": [
        "vota sí",
        "vota si",
        "vota no",
        "vota por",
        "vota en contra",
        "vota a favor",
        "voten a favor",
        "deberías",
        "deberias",
        "deberías votar",
        "deberían votar",
        "deberías apoyar",
        "deberías oponerte",
        "deberías rechazar",
        "te recomiendo",
        "te recomendamos",
        "apoya esta",
        "apoyen la medida",
        "apoya la medida",
        "oponente a esta",
        "oponete a esta",
        "rechaza esta",
        "rechacen la medida",
        "rechaza la medida",
    ],
    # Hindi (Devanagari + common transliterations)
    "hi": [
        "हाँ में वोट",
        "हां में वोट",
        "ना में वोट",
        "के लिए वोट",
        "के खिलाफ वोट",
        "के पक्ष में वोट दें",
        "के खिलाफ वोट दें",
        "हाँ को वोट दें",
        "हां को वोट दें",
        "ना को वोट दें",
        "आपको समर्थन करना चाहिए",
        "आपको विरोध करना चाहिए",
        "हम अनुशंसा करते हैं",
        "haan mein vote",
        "na mein vote",
        "ko vote karein",
        "haan me vote",
        "na me vote",
        "haan ko vote dein",
        "na ko vote dein",
    ],
    # Punjabi (Gurmukhi + common transliterations)
    "pa": [
        "ਹਾਂ ਵਿੱਚ ਵੋਟ",
        "ਨਾਂ ਵਿੱਚ ਵੋਟ",
        "ਲਈ ਵੋਟ",
        "ਦੇ ਖਿਲਾਫ਼ ਵੋਟ",
        "ਦੇ ਹੱਕ ਵਿੱਚ ਵੋਟ ਦਿਓ",
        "ਦੇ ਖਿਲਾਫ ਵੋਟ ਦਿਓ",
        "ਹਾਂ ਨੂੰ ਵੋਟ ਦਿਓ",
        "ਨਾਂ ਨੂੰ ਵੋਟ ਦਿਓ",
        "ਤੁਹਾਨੂੰ ਸਮਰਥਨ ਕਰਨਾ ਚਾਹੀਦਾ ਹੈ",
        "ਤੁਹਾਨੂੰ ਵਿਰੋਧ ਕਰਨਾ ਚਾਹੀਦਾ ਹੈ",
        "ਹਾਂ ਨੂੰ ਵੋਟ ਦਿਉ",
        "haan vich vote",
        "na vich vote",
        "haan nu vote dio",
        "na nu vote dio",
    ],
    # Simplified/Traditional Chinese
    "zh": [
        "投赞成票",
        "投反对票",
        "应该投票",
        "應該投票",
        "投票支持",
        "投票反对",
        "投票反對",
        "建议投",
        "建議投",
        "你应该",
        "你應該",
        "你应该支持",
        "你應該支持",
        "你应该反对",
        "你應該反對",
        "支持这项提案",
        "支持這項提案",
        "反对这项提案",
        "反對這項提案",
        "建议大家投",
        "建議大家投",
    ],
    # Persian (Farsi)
    "fa": [
        "رأی مثبت",
        "رأی منفی",
        "رأی مثبت دهید",
        "رأی منفی دهید",
        "باید رأی",
        "به آن رأی دهید",
        "از آن حمایت کنید",
        "با آن مخالفت کنید",
        "شما باید حمایت کنید",
        "شما باید مخالفت کنید",
        "به این طرح رأی مثبت دهید",
        "به این طرح رأی منفی دهید",
        "از این طرح حمایت کنید",
        "با این طرح مخالفت کنید",
    ],
}

# Deprecated alias: summarizer.py previously enforced a smaller English-only
# list under this name. Kept so any external import of the old symbol keeps
# working; new code should use ADVISORY_PATTERNS.
BANNED_ADVISORY_PHRASES = tuple(ADVISORY_PATTERNS["en"])


def get_patterns(lang: str) -> list:
    """Patterns for one language code (en/hi/pa/zh/es/fa)."""
    return list(ADVISORY_PATTERNS.get(lang, []))


def all_patterns() -> dict:
    """The full per-language pattern map."""
    return {lang: list(pats) for lang, pats in ADVISORY_PATTERNS.items()}


def contains_advisory(text: str) -> list:
    """Return [(lang, pattern), ...] for every pattern matched in text."""
    lowered = text.lower()
    hits = []
    for lang, patterns in ADVISORY_PATTERNS.items():
        for pattern in patterns:
            if pattern.lower() in lowered:
                hits.append((lang, pattern))
    return hits


if __name__ == "__main__":
    # Quick smoke checks (substring, case-insensitive)
    assert contains_advisory("You should vote yes on Prop 5."), "en"
    assert contains_advisory("के पक्ष में वोट दें।"), "hi"
    assert contains_advisory("ਦੇ ਹੱਕ ਵਿੱਚ ਵੋਟ ਦਿਓ"), "pa"
    assert contains_advisory("你应该支持这项提案"), "zh"
    assert contains_advisory("deberías apoyar esta medida"), "es"
    assert contains_advisory("شما باید حمایت کنید"), "fa"
    assert not contains_advisory("The bond would fund school repairs."), "false positive"
    total = sum(len(v) for v in ADVISORY_PATTERNS.values())
    print(f"advisory.py OK: {len(ADVISORY_PATTERNS)} languages, {total} patterns; "
          "all smoke checks passed")
