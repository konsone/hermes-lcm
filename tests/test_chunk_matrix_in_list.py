"""The float32 chunk matrix path must equal the per-row decoder, and the
IN-list batch must equal the temp-table batch.

Regression for the full-corpus exact scan: the stored float32 wire format is
read straight into a NumPy matrix instead of one Python list per row, and a
bounded batch binds its ids as parameters instead of staging them in a temp
table (~12 ms vs ~80 ms per 2000-id batch on the live 58k-chunk corpus).
"""
from __future__ import annotations

import sqlite3

import numpy as np

import hermes_lcm.vector_store as vector_store_module
from hermes_lcm.vector_store import EmbeddingIdentity, VectorStore

MODEL = "voyage-context-4"
PROVIDER = "voyage"
DIM = 8


def _seed_messages(db_path, count=6):
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


def _identity():
    return EmbeddingIdentity.canonical(
        PROVIDER, MODEL, "", DIM, "float32", "little", "chunk"
    )


def _unit(seed):
    rng = np.random.default_rng(seed)
    v = rng.standard_normal(DIM).astype(np.float32)
    return (v / np.linalg.norm(v)).tolist()


def _build(tmp_path, count=6):
    db_path = tmp_path / "lcm.db"
    _seed_messages(db_path, count)
    vs = VectorStore(db_path)
    vs.register_profile(MODEL, PROVIDER, DIM, task="chunk")
    identity = _identity()
    vectors = {}
    for i in range(count):
        vec = _unit(i + 1)
        vectors[f"{i}:0"] = vec
        vs.record_chunk_embedding(
            f"{i}:0", MODEL, vec, store_id=i, chunk_index=0,
            char_start=0, char_end=1, token_estimate=1, identity=identity,
        )
    return vs, identity, vectors


def test_float32_matrix_matches_per_row_decoder(tmp_path):
    vs, identity, vectors = _build(tmp_path)
    try:
        ids = list(vectors)
        query = np.asarray(vectors[ids[2]], dtype=np.float32)

        rowids_a, ids_a, kinds_a, matrix = vs._load_chunk_matrix(
            np, identity.identity_hash, DIM, ids, "float32"
        )
        rowids_b, ids_b, kinds_b, decoded = vs._load_chunk_vectors_for_ids(
            identity.identity_hash, DIM, ids, "float32"
        )

        # Same rows; the batch order itself is not part of the contract (the scan
        # ranks by score), so compare per chunk id rather than by position.
        assert sorted(ids_a) == sorted(ids_b)
        assert sorted(rowids_a) == sorted(rowids_b)
        assert set(kinds_a) == set(kinds_b) == {"chunk"}
        assert matrix.shape == (len(ids), DIM)
        assert matrix.dtype == np.float32
        by_id = {cid: row for cid, row in zip(ids_a, matrix)}
        reference = {cid: row for cid, row in zip(ids_b, decoded)}
        for cid in ids:
            np.testing.assert_array_equal(by_id[cid], np.asarray(reference[cid], dtype=np.float32))
        score_a = {cid: float(by_id[cid] @ query) for cid in ids}
        score_b = {cid: float(np.asarray(reference[cid], dtype=np.float32) @ query) for cid in ids}
        for cid in ids:
            assert abs(score_a[cid] - score_b[cid]) < 1e-6
    finally:
        vs.close()


def test_mis_sized_blob_is_skipped_not_misread(tmp_path):
    vs, identity, vectors = _build(tmp_path, count=3)
    try:
        ids = list(vectors)
        with vs._conn:
            vs._conn.execute(
                "UPDATE lcm_chunk_vectors SET vec = ? WHERE chunk_id = ? AND identity_hash = ?",
                (b"\x00\x00", ids[1], identity.identity_hash),
            )
        rowids, out_ids, kinds, matrix = vs._load_chunk_matrix(
            np, identity.identity_hash, DIM, ids, "float32"
        )
        assert ids[1] not in out_ids
        assert len(out_ids) == len(ids) - 1
        assert matrix.shape == (len(ids) - 1, DIM)
    finally:
        vs.close()


def test_in_list_batch_matches_temp_table_batch(tmp_path, monkeypatch):
    vs, identity, vectors = _build(tmp_path, count=5)
    try:
        ids = list(vectors)
        in_list = vs._fetch_chunk_rows_for_ids(identity.identity_hash, ids)

        # Force the temp-table branch by lowering the IN-list cap below the batch.
        monkeypatch.setattr(vector_store_module, "_IN_LIST_ID_MAX", 1)
        temp_table = vs._fetch_chunk_rows_for_ids(identity.identity_hash, ids)

        assert {r["chunk_id"] for r in in_list} == {r["chunk_id"] for r in temp_table}
        by_id_in = {r["chunk_id"]: bytes(r["vec"]) for r in in_list}
        by_id_tmp = {r["chunk_id"]: bytes(r["vec"]) for r in temp_table}
        assert by_id_in == by_id_tmp
    finally:
        vs.close()
