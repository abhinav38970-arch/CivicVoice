"""CivicVoice retrieval golden tests.

Each case: a real query + the source file(s) that MUST appear in the top-k.
Facts come from the live corpus (data/parsed/), enforced by
data/SOURCE_MANIFEST.json — the quarantined lorem-ipsum fixture is gone.

Run with pytest:
    .venv/bin/python -m pytest tests/test_retrieval_golden.py -v
Or plain python:
    .venv/bin/python tests/test_retrieval_golden.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from retriever import retrieve  # noqa: E402

# (query, expected source files that must appear in top-k, k)
CASES = [
    (
        "city council closed session labor negotiations",
        ["20250318_CC_Minutes__CLOSED_SESSION.pdf"],
        5,
    ),
    (
        "Proposition 2 school bonds $10 billion",
        ["ca-voter-guide-2024-general.pdf"],
        5,
    ),
    (
        "homelessness safe parking program winter relief",
        ["2025_MidYear_Progress_Report.pdf"],
        5,
    ),
    (
        "charter advisory committee government form",
        ["20260406_Charter_Advisory_Committee_Meeting_Agenda_packet.pdf"],
        5,
    ),
    (
        "FUSD liaison committee meeting",
        ["20250922_COFFUSD_Liaison_Committee_Meeting_Agenda_rev2.pdf"],
        5,
    ),
    (
        "state of the city special meeting notice",
        ["20260630_SOTC_Special_Meeting_Notice.pdf"],
        5,
    ),
    (
        "what did voters decide on Prop 32 minimum wage",
        ["ca-voter-guide-2024-general.pdf"],
        5,
    ),
]

BANNED_FILES = ("fremont-council-2026-07-11-agenda.pdf",)  # quarantined fixture


def _check_case(query, expected_files, k):
    results = retrieve(query, k=k)
    got = [r["source_file"] for r in results]
    for expected in expected_files:
        assert expected in got, (
            f"query {query!r}: expected {expected} in top-{k}, got {got}"
        )
    for banned in BANNED_FILES:
        assert banned not in got, (
            f"query {query!r}: quarantined fixture {banned} leaked into results"
        )
    return results


def test_retrieval_golden_cases():
    for query, expected_files, k in CASES:
        _check_case(query, expected_files, k)


def test_quarantined_fixture_never_retrieved():
    results = retrieve("fremont city council agenda july 2026 lorem ipsum", k=10)
    got = [r["source_file"] for r in results]
    for banned in BANNED_FILES:
        assert banned not in got, f"quarantined fixture {banned} leaked: {got}"


def test_low_confidence_signal():
    # A nonsense query should not be presented as a confident match.
    results = retrieve("zqxw jklmnb purple elephant thermodynamics", k=5)
    assert results, "expected results list even for nonsense query"
    assert results[0]["low_confidence"] is True, (
        f"expected low_confidence=True for nonsense query, "
        f"top score={results[0]['score']:.3f}"
    )
    assert "low_confidence" in results[0], "low_confidence key missing"
    # A strong query must NOT be flagged.
    strong = retrieve("Proposition 2 school bonds $10 billion", k=5)
    assert strong[0]["low_confidence"] is False


def main():
    passed, failed = 0, 0
    for i, (query, expected_files, k) in enumerate(CASES, 1):
        try:
            results = _check_case(query, expected_files, k)
            top = results[0]
            print(f"  [PASS] case {i}: {query[:55]!r} -> "
                  f"{top['source_file'][:45]} (score={top['score']:.3f})")
            passed += 1
        except AssertionError as e:
            print(f"  [FAIL] case {i}: {e}")
            failed += 1
    for name, fn in (("fixture-quarantine", test_quarantined_fixture_never_retrieved),
                     ("low-confidence", test_low_confidence_signal)):
        try:
            fn()
            print(f"  [PASS] {name}")
            passed += 1
        except AssertionError as e:
            print(f"  [FAIL] {name}: {e}")
            failed += 1
    print(f"\n{passed}/{passed + failed} retrieval golden tests passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
