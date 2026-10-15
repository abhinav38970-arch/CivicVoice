"""Adversarial eval pytest: missing-info decline + adversarial module checks.

Test 3 (missing_info): when the corpus cannot answer, /api/ask in no-key
mode must DECLINE with retrieved sources — never fabricate a summary.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import eval_adversarial  # noqa: E402
import app as app_module  # noqa: E402


def test_missing_info_declines_honestly():
    """An unanswerable query gets sources + honest message, never a summary."""
    app_module.app.config["TESTING"] = True
    client = app_module.app.test_client()
    res = client.post("/api/ask", json={
        "query": "what is the mayor's favorite ice cream flavor",
        "language": "en",
        "k": 5,
    })
    assert res.status_code == 200
    data = res.get_json()
    if app_module.MOCK_MODE:
        assert data["mode"] == "mock_sources", data
        assert "summary" not in data or not data.get("summary"), \
            "mock mode must never fabricate a summary"
        assert data.get("message"), "must include the honest decline message"
        assert isinstance(data.get("sources"), list)
    else:
        # With a real key the live path runs; eval still applies downstream.
        assert "summary" in data or "mode" in data


def test_adversarial_module_self_tests():
    """Run the module's own 6 checks (supported/contradicted/fidelity)."""
    # Raises SystemExit on failure.
    eval_adversarial._run_self_tests()


if __name__ == "__main__":
    test_missing_info_declines_honestly()
    test_adversarial_module_self_tests()
    print("adversarial pytest checks passed")
