"""CivicVoice retrieval: embeds parsed document chunks with sentence-transformers
(intfloat/multilingual-e5-base) and persists a normalized cosine-similarity
index to data/index/.

The multilingual model replaced all-MiniLM-L6-v2 on 2026-10-15: MiniLM is
English-oriented and scored non-English queries near zero (Hindi R@5=0.16,
Farsi R@5=0.00 on the golden-claim benchmark). e5 needs "query: "/"passage: "
prefixes — see QUERY_PREFIX/PASSAGE_PREFIX.

Usage:
    python retriever.py            # build (or load cached) index, run 3-line test
    python retriever.py --rebuild  # force re-encoding of all chunks
"""
import argparse
import glob
import hashlib
import json
import os
import re
import sys

# httpx (used by huggingface_hub) crashes parsing bracketed IPv6 entries
# like "[::1]" in NO_PROXY (httpx.InvalidURL: Invalid port: ':1]'). Strip
# them; the runtime's egress proxy still applies to huggingface.co.
for _var in ("NO_PROXY", "no_proxy"):
    _v = os.environ.get(_var)
    if _v:
        os.environ[_var] = ",".join(
            e for e in _v.split(",") if not re.fullmatch(r"\[.*\]", e.strip())
        )

import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARSED_DIR = os.path.join(BASE_DIR, "data", "parsed")
INDEX_DIR = os.path.join(BASE_DIR, "data", "index")
EMB_PATH = os.path.join(INDEX_DIR, "embeddings.npy")
META_PATH = os.path.join(INDEX_DIR, "meta.json")
MODEL_NAME = "intfloat/multilingual-e5-base"
MODEL_DIR = os.path.join(BASE_DIR, "models", "multilingual-e5-base")
# e5 models are trained with task prefixes; queries and passages MUST carry
# them or retrieval quality collapses. (MiniLM, the previous model, used none.)
QUERY_PREFIX = "query: "
PASSAGE_PREFIX = "passage: "
MODEL_ID_PATH = os.path.join(INDEX_DIR, "model.txt")
MANIFEST_PATH = os.path.join(BASE_DIR, "data", "SOURCE_MANIFEST.json")
LOW_CONFIDENCE_THRESHOLD = 0.30  # top-score floor; below this, matches are weak
METADATA_BOOST_WEIGHT = 0.15  # max score add for query terms matching a chunk's
# section title / filename (human-authored topic labels the embeddings miss)


def _model_source():
    """Local snapshot when vendored (HF hub is unreachable through the
    runtime's egress proxy), otherwise the hub model id."""
    if os.path.isdir(MODEL_DIR):
        return MODEL_DIR
    return MODEL_NAME

_church = None  # module-level cache: (embeddings, chunks)
_model = None  # module-level cache: SentenceTransformer instance


def get_model():
    """Load the embedding model once per process.

    Raises RuntimeError with a human-readable explanation (never a raw
    traceback) when the model cannot be loaded — e.g. sentence-transformers
    not installed, or an offline machine with no cached/vendored model.
    """
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise RuntimeError(
                "CivicVoice needs the 'sentence-transformers' package, which is "
                "not installed.\n"
                "What to do: pip install -r requirements.txt"
            )
        source = _model_source()
        try:
            _model = SentenceTransformer(source)
        except Exception as e:  # noqa: BLE001 - translated below, never raw
            raise RuntimeError(
                "Could not load the embedding model 'intfloat/multilingual-e5-base' "
                f"(tried: {source}).\n"
                "This usually means this machine is offline and the model was "
                "never downloaded.\n"
                "What to do:\n"
                "  1. Connect to the internet and run any CivicVoice command "
                "once — the model (~1.1GB) downloads automatically from "
                "Hugging Face and is cached for offline use afterwards.\n"
                "  2. Or copy the 'models/multilingual-e5-base/' folder from the "
                "project download into this copy of the project.\n"
                f"Technical detail (for debugging): {type(e).__name__}: {e}"
            )
    return _model


def _load_manifest():
    """Return {filename: sha256} from data/SOURCE_MANIFEST.json, or {} if
    the manifest is missing (defensive: chunk loading proceeds but warns)."""
    try:
        with open(MANIFEST_PATH, encoding="utf-8") as f:
            manifest = json.load(f)
        return {
            s["filename"]: s.get("sha256", "")
            for s in manifest.get("sources", [])
            if s.get("filename")
        }
    except (OSError, json.JSONDecodeError, AttributeError) as e:
        print(f"WARNING: could not read source manifest {MANIFEST_PATH}: {e}; "
              "loading chunks without manifest enforcement.", file=sys.stderr)
        return {}


def _file_ok(path, allowed):
    """True iff the parsed file is in the manifest AND its sha256 matches.
    Loud warning otherwise (the file is skipped by the caller)."""
    name = os.path.basename(path)
    if name not in allowed:
        print(f"WARNING: SKIPPING {name}: not listed in data/SOURCE_MANIFEST.json "
              "(possible synthetic fixture — refusing to index it).", file=sys.stderr)
        return False
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    if h.hexdigest() != allowed[name]:
        print(f"WARNING: SKIPPING {name}: sha256 mismatch vs SOURCE_MANIFEST.json "
              "(file changed since manifest was generated).", file=sys.stderr)
        return False
    return True


def load_chunks():
    """Load chunks from data/parsed/*.jsonl, enforcing SOURCE_MANIFEST.json.

    Files missing from the manifest, or whose checksum changed, are SKIPPED
    with a loud warning so synthetic test fixtures can never enter the index.
    """
    allowed = _load_manifest()
    chunks = []
    skipped = 0
    for path in sorted(glob.glob(os.path.join(PARSED_DIR, "*.jsonl"))):
        if not _file_ok(path, allowed):
            skipped += 1
            continue
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                c = json.loads(line)
                chunks.append({
                    "source_file": c.get("source_file", ""),
                    "page": c.get("page", -1),
                    "section_title": c.get("section_title", ""),
                    "text": c.get("text", ""),
                })
    if skipped:
        print(f"Manifest enforcement: skipped {skipped} unlisted/modified file(s).",
              file=sys.stderr)
    return chunks


def build_index(chunks, model_name=MODEL_NAME):
    """Encode chunk texts (with the e5 passage prefix); return L2-normalized
    (N, D) embedding matrix."""
    model = get_model()
    texts = [PASSAGE_PREFIX + c["text"] for c in chunks]
    emb = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    norms = np.linalg.norm(emb, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return emb / norms


def save_index(embeddings, chunks):
    os.makedirs(INDEX_DIR, exist_ok=True)
    np.save(EMB_PATH, embeddings)
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False)
    with open(MODEL_ID_PATH, "w", encoding="utf-8") as f:
        f.write(MODEL_NAME + "\n")


def _cached_model_name():
    try:
        with open(MODEL_ID_PATH, encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return None


def load_index():
    embeddings = np.load(EMB_PATH)
    with open(META_PATH, encoding="utf-8") as f:
        chunks = json.load(f)
    return embeddings, chunks


def get_index(rebuild=False):
    """Return (embeddings, chunks), using the cached index when valid."""
    global _church
    if _church is not None and not rebuild:
        return _church
    chunks = load_chunks()
    if not chunks:
        raise RuntimeError(
            f"No usable document chunks found in {PARSED_DIR}.\n"
            "What to do:\n"
            "  1. Download public PDFs:  python scraper.py\n"
            "  2. Parse them:            python parser.py\n"
            "  3. Re-run your command.\n"
            "(Parsed files must also be listed in data/SOURCE_MANIFEST.json — "
            "see README 'Known gaps'.)"
        )
    if os.path.exists(EMB_PATH) and os.path.exists(META_PATH) and not rebuild:
        if _cached_model_name() != MODEL_NAME:
            print(f"Embedding model changed ({_cached_model_name()} -> "
                  f"{MODEL_NAME}); rebuilding index...")
        else:
            embeddings, cached = load_index()
            if len(cached) == len(chunks):
                _church = (embeddings, chunks)
                print(f"Loaded cached index: {len(chunks)} chunks from {INDEX_DIR}")
                return _church
            print("Chunk count changed; rebuilding index...")
    print(f"Building index for {len(chunks)} chunks ({MODEL_NAME})...")
    embeddings = build_index(chunks)
    save_index(embeddings, chunks)
    print(f"Index saved to {INDEX_DIR}")
    _church = (embeddings, chunks)
    return _church


def _metadata_boost(query, chunks):
    """Keyword overlap between the query and each chunk's human-authored
    metadata (section title + filename). Embeddings only see chunk text, so a
    chunk whose *label* names the topic (e.g. section "CONFERENCE WITH LABOR
    NEGOTIATOR:") would otherwise lose to longer generic documents. Returns a
    per-chunk boost in [0, METADATA_BOOST_WEIGHT]."""
    import re

    terms = [t for t in re.findall(r"\w+", query.lower(), flags=re.UNICODE) if len(t) > 2]
    if not terms:
        return np.zeros(len(chunks))
    boosts = np.zeros(len(chunks))
    for i, c in enumerate(chunks):
        meta = f"{c.get('section_title', '')} {c.get('source_file', '')}".lower()
        meta = re.sub(r"[_\-/]+", " ", meta)
        hits = sum(1 for t in terms if t in meta)
        boosts[i] = (hits / len(terms)) * METADATA_BOOST_WEIGHT
    return boosts


def retrieve(query, k=5, rebuild=False):
    """Return top-k chunks as [{source_file, page, section_title, text, score,
    low_confidence}]. When the top score is below LOW_CONFIDENCE_THRESHOLD the
    matches are weak; every result carries low_confidence=True so the UI can be
    honest about it instead of presenting weak matches as answers."""
    embeddings, chunks = get_index(rebuild=rebuild)
    model = get_model()
    q = model.encode([QUERY_PREFIX + query], convert_to_numpy=True)[0]
    q = q / (np.linalg.norm(q) or 1.0)
    scores = embeddings @ q  # cosine, since both sides normalized
    scores = scores + _metadata_boost(query, chunks)
    top = np.argsort(scores)[::-1][:k]
    low_conf = bool(top.size and float(scores[top[0]]) < LOW_CONFIDENCE_THRESHOLD)
    return [
        {
            "source_file": chunks[i]["source_file"],
            "page": chunks[i]["page"],
            "section_title": chunks[i]["section_title"],
            "text": chunks[i]["text"],
            "score": float(scores[i]),
            "low_confidence": low_conf,
        }
        for i in top
    ]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rebuild", action="store_true", help="force re-encoding")
    args = parser.parse_args()
    for r in retrieve("ballot measure school funding", k=3, rebuild=args.rebuild):
        print(f"{r['section_title']} | score={r['score']:.4f}")
