"""Startup chunk-vector prewarm: reads the corpus once, best effort, read-only."""
from __future__ import annotations

import sqlite3

import numpy as np

from hermes_lcm.config import LCMConfig
from hermes_lcm.vector_store import (
    EmbeddingIdentity,
    VectorStore,
    prewarm_chunk_vector_cache,
)

MODEL = "voyage-context-4"
PROVIDER = "voyage"
DIM = 4


def _seed_messages(db_path, count):
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            store_id INTEGER PRIMARY KEY,
            session_id TEXT NOT NULL,
            source TEXT DEFAULT '',
            role TEXT NOT NULL,
            content TEXT,
            timestamp REAL NOT NULL
        )
        """
    )
    conn.executemany(
        "INSERT INTO messages(store_id, session_id, source, role, content, timestamp) "
        "VALUES(?, ?, ?, ?, ?, ?)",
        [(i, "s", "history", "user", "m", 100.0 + i) for i in range(count)],
    )
    conn.commit()
    conn.close()


def _build(tmp_path, count=5):
    db_path = tmp_path / "lcm.db"
    _seed_messages(db_path, count)
    vs = VectorStore(db_path)
    vs.register_profile(MODEL, PROVIDER, DIM, task="chunk")
    identity = EmbeddingIdentity.canonical(PROVIDER, MODEL, "", DIM, "float32", "little", "chunk")
    rng = np.random.default_rng(7)
    for i in range(count):
        vec = rng.standard_normal(DIM).astype(np.float32)
        vec = (vec / np.linalg.norm(vec)).tolist()
        vs.record_chunk_embedding(
            f"{i}:0", MODEL, vec, store_id=i, chunk_index=0,
            char_start=0, char_end=1, token_estimate=1, identity=identity,
        )
    return vs, db_path, identity


def test_prewarm_reads_whole_corpus(tmp_path):
    vs, db_path, identity = _build(tmp_path, count=5)
    try:
        result = prewarm_chunk_vector_cache(db_path, min_rows=1)
        assert result["identity"] == identity.identity_hash
        assert result["rows"] == 5
        assert result["skipped"] is None
        assert result["elapsed_ms"] >= 0
    finally:
        vs.close()


def test_prewarm_skips_small_corpus(tmp_path):
    vs, db_path, _ = _build(tmp_path, count=3)
    try:
        result = prewarm_chunk_vector_cache(db_path, min_rows=2000)
        assert result["rows"] == 0
        assert result["skipped"].startswith("corpus_too_small")
    finally:
        vs.close()


def test_prewarm_respects_expired_deadline(tmp_path):
    vs, db_path, _ = _build(tmp_path, count=4)
    try:
        result = prewarm_chunk_vector_cache(db_path, min_rows=1, deadline=0.0)
        assert result["skipped"] == "deadline"
        assert result["rows"] == 0
    finally:
        vs.close()


def test_prewarm_works_while_store_connection_is_open(tmp_path):
    """Read-only reader must not contend with the live shared connection."""
    vs, db_path, _ = _build(tmp_path, count=4)
    try:
        result = prewarm_chunk_vector_cache(db_path, min_rows=1)
        assert result["rows"] == 4
        # the store is still usable afterwards
        hit = vs._conn.execute("SELECT COUNT(*) FROM lcm_chunk_vectors").fetchone()[0]
        assert hit == 4
    finally:
        vs.close()


def test_prewarm_without_profile_is_skipped(tmp_path):
    db_path = tmp_path / "empty.db"
    _seed_messages(db_path, 1)
    vs = VectorStore(db_path)
    try:
        result = prewarm_chunk_vector_cache(db_path, min_rows=1)
        assert result["skipped"] == "no_active_chunk_profile"
        assert result["rows"] == 0
    finally:
        vs.close()
