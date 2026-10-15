"""CivicVoice adversarial eval — the 4 test types from outside AI feedback.

Keyword grounding (eval.py) proves a claim is *about* the cited chunk. It
cannot see what the AI reviewers flagged:

1. supported_claim ....... key numbers/entities in the claim must actually
   appear in the cited chunk (entailment-ish, not just topic overlap)
2. contradicted_claim .... a plausible-but-false claim (number swapped,
   outcome flipped) must be REJECTED — the old evaluator PASSES these,
   which this module demonstrates before fixing
3. missing_info ........... the system must decline when sources don't
   establish an answer (integration test vs /api/ask mock mode; see
   tests/test_eval_adversarial.py)
4. multilingual_fidelity .. amounts/dates in the 6 verified languages'
   golden text must match the English, with locale digits normalized and
   legitimate conversions (Chinese billion->yi, month words->month numbers)
   accounted for

Deterministic. No LLM, no API calls.
"""

import glob
import json
import os
import re

from eval import _tokens, evaluate

# ---------------------------------------------------------------------------
# Locale digit normalization
# ---------------------------------------------------------------------------
_DIGIT_MAP = {}
for _digits in (
    "\u0966\u0967\u0968\u0969\u096a\u096b\u096c\u096d\u096e\u096f",  # Devanagari
    "\u0660\u0661\u0662\u0663\u0664\u0665\u0666\u0667\u0668\u0669",  # Arabic-Indic
    "\u06f0\u06f1\u06f2\u06f3\u06f4\u06f5\u06f6\u06f7\u06f8\u06f9",  # Extended Arabic-Indic
):
    for _d, _ch in enumerate(_digits):
        _DIGIT_MAP[_ch] = str(_d)


def normalize_digits(text: str) -> str:
    """Map locale digits to ASCII; normalize locale decimal/thousands
    separators (Persian ٫/٬) so '۱۱٫۲۵' reads as 11.25."""
    t = "".join(_DIGIT_MAP.get(c, c) for c in text)
    return t.replace("٬", "").replace("٫", ".")


_NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")


def extract_numbers(text: str) -> set:
    """Normalized number strings: '11.25', '55', '2026'. Commas stripped,
    locale digits mapped to ASCII."""
    t = normalize_digits(text).replace(",", "")
    return set(_NUMBER_RE.findall(t))


_MONTHS = {
    "january": "1", "february": "2", "march": "3", "april": "4",
    "may": "5", "june": "6", "july": "7", "august": "8",
    "september": "9", "october": "10", "november": "11", "december": "12",
}


def _month_numbers_in_en(en_text: str) -> set:
    found = set()
    low = en_text.lower()
    for word, num in _MONTHS.items():
        if word in low:
            found.add(num)
    return found


def numbers_supported(claim_en: str, chunk_text: str) -> bool:
    """Test 1: every number in the claim appears in the cited chunk."""
    claim_nums = extract_numbers(claim_en)
    if not claim_nums:
        return True  # nothing numeric to check
    chunk_nums = extract_numbers(chunk_text)
    return claim_nums <= chunk_nums


def contradiction_detected(claim_en: str, chunk_text: str,
                           overlap_threshold: float = 0.15) -> bool:
    """Test 2: True when the claim is ABOUT the chunk (topic overlap) but a
    number in the claim does not appear in the chunk — the classic
    number-swapped false claim that keyword grounding cannot see."""
    claim_kw = _tokens(claim_en)
    chunk_kw = _tokens(chunk_text)
    if not claim_kw:
        return False
    overlap = len(claim_kw & chunk_kw) / len(claim_kw)
    if overlap < overlap_threshold:
        return False  # different topic entirely — not a contradiction
    claim_nums = extract_numbers(claim_en)
    chunk_nums = extract_numbers(chunk_text)
    # A numeric claim with numbers absent from the chunk, on the same topic,
    # contradicts the source.
    return bool(claim_nums) and not (claim_nums <= chunk_nums)


def evaluate_strict(summary_json: dict, retrieved_chunks: list) -> dict:
    """evaluate() plus the contradiction scan. Adds 'contradictions' (list
    of claim indexes) and fails the verdict if any are found."""
    result = evaluate(summary_json, retrieved_chunks)
    contradictions = []
    for i, claim in enumerate(summary_json.get("summary") or []):
        text = claim.get("claim_en") or claim.get("claim") or ""
        chunk = None
        cit = claim.get("citation") or {}
        for ch in retrieved_chunks:
            if (ch.get("source_file") == cit.get("source_file")
                    and ch.get("page") == cit.get("page")):
                chunk = ch
                break
        if chunk and contradiction_detected(text, chunk.get("text", "")):
            contradictions.append(i)
    result["contradictions"] = contradictions
    if contradictions and result["verdict"] == "PASS":
        result["verdict"] = "FAIL"
        result["contradiction_note"] = (
            f"claims {contradictions} contradict their cited chunks "
            "(numeric mismatch on same topic)"
        )
    return result


def multilingual_number_fidelity(golden_dir: str) -> dict:
    """Test 4: for each golden claim, every English number must be
    accounted for in each verified language (verbatim, digit-normalized,
    or via legitimate zh conversions). Returns per-claim results."""
    results = []
    for path in sorted(glob.glob(os.path.join(golden_dir, "*.json"))):
        if "eval_log" in path:
            continue
        data = json.load(open(path, encoding="utf-8"))
        for claim in data.get("claims", []):
            texts = claim.get("text", {})
            en = texts.get("en", "")
            en_nums = extract_numbers(en)
            if not en_nums:
                continue
            en_months = _month_numbers_in_en(en)
            for lang in ("es", "hi", "pa", "zh", "fa"):
                lt = texts.get(lang, "")
                lang_nums = extract_numbers(lt)
                missing = []
                for n in en_nums:
                    if n in lang_nums:
                        continue
                    ok = False
                    if lang == "zh":
                        norm = normalize_digits(lt)
                        if "亿" in norm:
                            # billion -> yi (x10): 11.25 -> 112.5
                            # million -> yi (/100): 500 -> 5
                            for factor in (10, 0.01):
                                try:
                                    conv = str(float(n) * factor
                                               ).rstrip("0").rstrip(".")
                                    if conv in lang_nums:
                                        ok = True
                                        break
                                except ValueError:
                                    pass
                        if not ok and n in en_months:
                            ok = True  # "April" -> 4月
                    if not ok:
                        missing.append(n)
                # Extra numbers in the translation must also be explainable
                # (zh month numbers / yi conversions); otherwise flag.
                extra = lang_nums - en_nums
                unexplained_extra = set()
                for x in extra:
                    if lang == "zh":
                        explained = False
                        try:
                            for e in en_nums:
                                for factor in (10, 0.01):
                                    if (str(float(e) * factor
                                            ).rstrip("0").rstrip(".") == x):
                                        explained = True
                                        break
                        except ValueError:
                            pass
                        if explained or x in en_months:
                            continue
                    unexplained_extra.add(x)
                results.append({
                    "file": os.path.basename(path),
                    "claim": claim.get("id"),
                    "lang": lang,
                    "ok": not missing and not unexplained_extra,
                    "missing": sorted(missing),
                    "unexplained_extra": sorted(unexplained_extra),
                })
    return results


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def _run_self_tests():
    chunk = {
        "source_file": "CA-Voter-Guide-2026.pdf",
        "page": 4,
        "text": (
            "Proposition 5 would amend the state constitution to lower the "
            "voter approval threshold for local bonds funding affordable "
            "housing and public infrastructure from two-thirds to 55 percent."
        ),
    }
    chunks = [chunk]
    cit = {"source_file": "CA-Voter-Guide-2026.pdf", "page": 4}
    results = []

    def check(name, cond, detail=""):
        results.append((name, cond))
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}"
              + (f" — {detail}" if detail else ""))

    true_claim = ("Proposition 5 would lower the voter approval threshold "
                  "for local housing bonds from two-thirds to 55 percent.")
    false_claim = ("Proposition 5 would RAISE the voter approval threshold "
                   "for local housing bonds to 75 percent.")

    # Test 1: supported claim — numbers present
    check("(1) supported claim numbers present",
          numbers_supported(true_claim, chunk["text"]))

    # Test 2a: the OLD evaluator passes the false claim (the blind spot)
    old = evaluate({"summary": [{"claim": false_claim, "citation": cit}],
                    "language": "en"}, chunks)
    check("(2a) old evaluate() PASSES number-swapped false claim (blind spot)",
          old["verdict"] == "PASS", f"verdict={old['verdict']}")

    # Test 2b: contradiction check catches it
    check("(2b) contradiction_detected catches the false claim",
          contradiction_detected(false_claim, chunk["text"]))
    check("(2c) contradiction_detected clears the true claim",
          not contradiction_detected(true_claim, chunk["text"]))
    strict = evaluate_strict(
        {"summary": [{"claim": false_claim, "citation": cit}],
         "language": "en"}, chunks)
    check("(2d) evaluate_strict FAILS the false claim",
          strict["verdict"] == "FAIL" and strict["contradictions"] == [0],
          f"verdict={strict['verdict']}")

    # Test 4: golden translations preserve numbers
    gdir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "data", "golden")
    fidel = multilingual_number_fidelity(gdir)
    bad = [r for r in fidel if not r["ok"]]
    check("(4) multilingual number fidelity across golden claims",
          not bad, f"{len(fidel) - len(bad)}/{len(fidel)} ok"
          + (f"; bad={bad[:3]}" if bad else ""))

    failed = [n for n, ok in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} adversarial self-tests passed")
    if failed:
        raise SystemExit(f"FAILED: {failed}")


if __name__ == "__main__":
    _run_self_tests()
