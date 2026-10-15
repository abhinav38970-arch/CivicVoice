"""False-claim injection demo — for the CAC demo video.

Shows, in plain human-readable steps:
  1. the TRUE source passage,
  2. a deliberately FALSE claim about it (number swapped),
  3. the OLD evaluator passing it (the blind spot), and
  4. the NEW contradiction check rejecting it.

Run:  .venv/bin/python demo/eval_false_claim_demo.py
Everything here uses a clearly labeled synthetic fixture — never present
the false claim as a real ballot result.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from eval import evaluate
from eval_adversarial import contradiction_detected, evaluate_strict

CHUNK = {
    "source_file": "CA-Voter-Guide-2026.pdf",
    "page": 4,
    "text": (
        "Proposition 5 would amend the state constitution to lower the voter "
        "approval threshold for local bonds funding affordable housing and "
        "public infrastructure from two-thirds to 55 percent."
    ),
}
CITATION = {"source_file": "CA-Voter-Guide-2026.pdf", "page": 4}

TRUE_CLAIM = ("Proposition 5 would lower the voter approval threshold for "
              "local housing bonds from two-thirds to 55 percent.")
# SYNTHETIC false claim, built only to test the evaluator:
FALSE_CLAIM = ("Proposition 5 would RAISE the voter approval threshold for "
               "local housing bonds to 75 percent.")


def main():
    print("=" * 70)
    print("CivicVoice evaluator demo — false-claim injection")
    print("(synthetic fixture; the false claim is deliberately wrong)")
    print("=" * 70)
    print("\n[1] TRUE source passage (p. 4):")
    print(f"    \"{CHUNK['text']}\"")
    print("\n[2] Injected FALSE claim:")
    print(f"    \"{FALSE_CLAIM}\"")

    print("\n[3] OLD evaluator (keyword grounding only):")
    old = evaluate({"summary": [{"claim": FALSE_CLAIM, "citation": CITATION}],
                    "language": "en"}, [CHUNK])
    print(f"    verdict = {old['verdict']}   <-- the blind spot: high word "
          "overlap, wrong numbers")

    print("\n[4] NEW contradiction check:")
    hit = contradiction_detected(FALSE_CLAIM, CHUNK["text"])
    print(f"    contradiction_detected = {hit}")
    strict = evaluate_strict(
        {"summary": [{"claim": FALSE_CLAIM, "citation": CITATION}],
         "language": "en"}, [CHUNK])
    print(f"    evaluate_strict verdict = {strict['verdict']}")
    print(f"    note: {strict.get('contradiction_note', '')}")

    print("\n[5] Sanity — the TRUE claim still passes:")
    strict_true = evaluate_strict(
        {"summary": [{"claim": TRUE_CLAIM, "citation": CITATION}],
         "language": "en"}, [CHUNK])
    print(f"    evaluate_strict verdict = {strict_true['verdict']}")
    print("\nDone. The mechanism fails safely: false claims are rejected, "
          "true claims pass.")


if __name__ == "__main__":
    main()
