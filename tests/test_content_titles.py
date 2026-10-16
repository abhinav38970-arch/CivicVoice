"""Content-title i18n pytest: hand-translated news/ballot titles.

Asserts data/i18n/content_titles.json covers every notice id and every
golden entry id (with claims) in all 5 verified non-English languages
(es/hi/pa/zh/fa), that topic translations exist for ballot ids, and that
/api/notices, /api/golden and /api/golden/<id> expose title_i18n/topic_i18n.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import app as app_module  # noqa: E402

LANGS = ("es", "hi", "pa", "zh", "fa")
BALLOT_IDS = (
    "charter-advisory",
    "closed-session-labor",
    "midyear-winter-relief",
    "prop1-2026-housing-bond",
    "prop2-school-bonds",
)


def _titles():
    return app_module._get_content_titles()


def test_data_file_covers_all_notices():
    titles = _titles()
    for n in app_module._load_notices():
        nid = n["id"]
        assert nid in titles, f"notice id missing from content_titles.json: {nid}"
        got = set((titles[nid].get("title") or {}))
        assert set(LANGS) <= got, f"{nid} title missing langs: {set(LANGS) - got}"
        for lang in LANGS:
            assert titles[nid]["title"][lang].strip(), f"{nid} {lang} title empty"


def test_data_file_covers_all_golden_entries():
    titles = _titles()
    for e in app_module._get_golden_entries():
        if not e.get("claims"):
            continue
        eid = e["id"]
        assert eid in titles, f"golden id missing from content_titles.json: {eid}"
        got = set((titles[eid].get("title") or {}))
        assert set(LANGS) <= got, f"{eid} title missing langs: {set(LANGS) - got}"
        for lang in LANGS:
            assert titles[eid]["title"][lang].strip(), f"{eid} {lang} title empty"


def test_ballot_ids_have_topic_translations():
    titles = _titles()
    for eid in BALLOT_IDS:
        assert eid in titles, f"ballot id missing: {eid}"
        got = set((titles[eid].get("topic") or {}))
        assert set(LANGS) <= got, f"{eid} topic missing langs: {set(LANGS) - got}"
        for lang in LANGS:
            assert titles[eid]["topic"][lang].strip(), f"{eid} {lang} topic empty"


def test_api_responses_include_title_i18n():
    app_module.app.config["TESTING"] = True
    client = app_module.app.test_client()

    notices = client.get("/api/notices").get_json()
    assert notices, "no notices returned"
    for n in notices:
        ti = n.get("title_i18n") or {}
        assert set(LANGS) <= set(ti), f"notice {n['id']} missing title_i18n langs"

    cards = client.get("/api/golden").get_json()
    assert cards, "no golden cards returned"
    for c in cards:
        ti = c.get("title_i18n") or {}
        assert set(LANGS) <= set(ti), f"card {c['id']} missing title_i18n langs"

    for c in cards:
        data = client.get(f"/api/golden/{c['id']}?language=hi").get_json()
        ti = data.get("title_i18n") or {}
        assert set(LANGS) <= set(ti), f"entry {c['id']} missing title_i18n langs"
        if c["id"] in BALLOT_IDS:
            pi = data.get("topic_i18n") or {}
            assert set(LANGS) <= set(pi), f"entry {c['id']} missing topic_i18n langs"


def test_extended_language_falls_back_to_english():
    """Languages without hand translations (vi/tl/ko/ar/ja/ru) get {} → client
    falls back to the English title exactly as before."""
    app_module.app.config["TESTING"] = True
    client = app_module.app.test_client()
    notices = client.get("/api/notices").get_json()
    for n in notices:
        assert "vi" not in (n.get("title_i18n") or {}), n["id"]
    cards = client.get("/api/golden").get_json()
    for c in cards:
        assert "vi" not in (c.get("title_i18n") or {}), c["id"]
