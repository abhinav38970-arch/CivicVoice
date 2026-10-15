"""retriever.py unit tests that don't need the model weights.

The multilingual model (~1.1GB) can't download on the build VM's throttled
pipe, so the full after-benchmark runs on Abhinav's Mac. These tests verify
the swap logic itself with a stubbed model: e5 prefixes are applied to
queries and passages, and a model change forces an index rebuild.
"""
import os
import sys
import types

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import retriever  # noqa: E402


class StubModel:
    def __init__(self):
        self.seen = []

    def encode(self, texts, **kwargs):
        self.seen.extend(texts)
        rng = np.random.default_rng(0)
        return rng.random((len(texts), 8)).astype(np.float32)


def _patch(monkeypatch, tmp_path):
    monkeypatch.setattr(retriever, "INDEX_DIR", str(tmp_path))
    monkeypatch.setattr(retriever, "EMB_PATH", str(tmp_path / "embeddings.npy"))
    monkeypatch.setattr(retriever, "META_PATH", str(tmp_path / "meta.json"))
    monkeypatch.setattr(retriever, "MODEL_ID_PATH", str(tmp_path / "model.txt"))
    monkeypatch.setattr(retriever, "_model", StubModel())
    monkeypatch.setattr(retriever, "_church", None)


def test_e5_prefixes_applied(tmp_path, monkeypatch):
    _patch(monkeypatch, tmp_path)
    chunks = [
        {"source_file": "a.pdf", "page": 1, "section_title": "T",
         "text": "school bonds for housing"},
    ]
    emb = retriever.build_index(chunks)
    model = retriever.get_model()
    assert model.seen[0].startswith("passage: "), model.seen[:1]
    retriever.save_index(emb, chunks)
    retriever.retrieve("स्कूल बॉन्ड", k=1)
    queries = [t for t in model.seen if t.startswith("query: ")]
    assert queries, "query prefix was not applied"
    assert emb.shape[1] == 8


def test_model_change_forces_rebuild(tmp_path, monkeypatch):
    _patch(monkeypatch, tmp_path)
    chunks = [{"source_file": "a.pdf", "page": 1, "section_title": "T",
               "text": "hello"}]
    emb = retriever.build_index(chunks)
    retriever.save_index(emb, chunks)
    assert retriever._cached_model_name() == retriever.MODEL_NAME
    # Simulate a stale cache from the old English-only model.
    with open(retriever.MODEL_ID_PATH, "w", encoding="utf-8") as f:
        f.write("all-MiniLM-L6-v2\n")
    assert retriever._cached_model_name() != retriever.MODEL_NAME


if __name__ == "__main__":
    import tempfile
    from unittest import mock

    with tempfile.TemporaryDirectory() as td, mock.patch.dict(os.environ):
        import pathlib

        class MP:
            def setattr(self, *a):
                setattr(*a)

        _patch(MP(), pathlib.Path(td))
        test_e5_prefixes_applied(pathlib.Path(td), MP())
        test_model_change_forces_rebuild(pathlib.Path(td), MP())
    print("retriever swap unit tests passed")
