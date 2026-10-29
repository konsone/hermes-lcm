# My-OS integration changes

Local commits carried on top of `wzgrx/hermes-lcm`. Newest first.

## Unreleased

| Change | Origin | Why |
|---|---|---|
| `perf(recall)`: warm the chunk-vector pages at engine start | local, from a measured cold-start gap | after the matrix/IN-list fix the scan costs ~1.2 s warm but 10–15 s cold, so the FIRST recall after every gateway start still blew the 8 s budget (`timeout: true`, verbatim arm absent) while every later one was fine. A daemon thread reads the identity's vectors once on its own read-only connection (58 200 rows in 815 ms, keyset scan, no joins). Verified live: run the helper by hand, then `lcm_recall` → `coverage.chunk: full`, no timeout. Opt out with `LCM_PREWARM_CHUNK_VECTORS=0`; skipped when the corpus is under 2 000 vectors and bounded by a 120 s deadline |
| `perf(recall)`: float32 chunk matrix built from blobs + IN-list batches | local, from a measured bottleneck | the exact full-corpus chunk scan cost 11–17 s on the live 58k-chunk corpus; with the 8 s recall budget it could never finish, so `lcm_recall` returned `timeout: true` and the verbatim arm contributed nothing. 96% of the time was the batch loader: one Python list per vector (`frombuffer` now) and a per-batch CREATE TEMP + executemany + join (IN-list now). Measured on a DB copy: `_scan_ranked` 5 829 → 1 480 ms, whole `lcm_recall` 8 001 ms (timeout) → 3 304–4 759 ms with `coverage: full` and all three arms contributing. Exactness preserved — the vectors and the cosine are unchanged |
| `fix(store)`: `cached_statements=0` on shared SQLite connections | port of `the3asic/hermes-lcm` `8502bc5`, adapted | CPython #118172: threads sharing one connection (check_same_thread=False) can reuse a cached prepared statement while another binds/steps it. Measured here: the ported test returns truncated rows (`('worker-1-query-80', 10)` where 8/14 are missing) **3/3 before**, **5/5 pass after** |
| `fix(summary)`: dispatch-boundary deadline + order-insensitive spend backoff | ports of `the3asic/hermes-lcm` `17a8172` and `6c0533a`, adapted | the loop-level deadline check ran before circuit/spend decisions that can consume the remaining window; concurrent guard reservations timestamp before the lock and could append out of order, anchoring the backoff at the wrong call |

**Corrected 2026-10-29:** `8502bc5` was rejected on 2026-10-19 with the note
"no statement cache in our store". That claim was wrong — the connections are
opened with the sqlite3 default cache. The race reproduced immediately against
our own `MessageStore` and `SummaryDAG` (see the row above), so the patch is now
carried. Lesson: a rejection reason that is a factual claim about our code needs
a probe, not a reading.

Rejected after inspection (defect absent in rc.3): `ed7cec4` and `13fc460` (our
guard reserves at dispatch; no pending-reservation mechanism), `969ad26` (rc.3
already rechecks sources and publishes the frontier atomically, `e927404`),
`1dd7435` (rc.3 ships `repair_external_content_fts`, `34a93e0`).

## myos-2026.10.19 (base `19bc4ff`, v1.0.0-rc.3)

| Change | Origin | Why |
|---|---|---|
| `fix(recall)`: reserve recall time for usable semantic corpora | port of `the3asic/hermes-lcm` `15723dc`, adapted | the FTS arm consumed the whole recall budget before the semantic arm ran; observed 24 times live |
| `docs(skill)`: live diagnostics lessons | local | embedding coverage, backfill lease, dead inflight markers, standalone-script env, compaction cost distribution, safe update procedure |
| `docs`: fork policy | local | branch model, update cadence, acceptance rules |

### Not yet accepted

Reviewed on 2026-10-19, not applied yet — each needs an isolated test:

- `1dd7435` (the3asic) — atomic repair of drifted FTS trigger bodies
- `969ad26` (the3asic) — atomic summary frontier publication
- `17a8172` / `8c372fd` (the3asic) — summary deadline checked at dispatch
- `ed7cec4` / `6c0533a` / `13fc460` (the3asic) — summary spend accounting at dispatch, backoff anchor
- `db2b1f6` (tuly) — background workers run in the caller's context
- `6a688ba` (tuly) — opt-in threshold-only automatic summaries

Rejected as already covered by the base or not applicable: `4609946`,
`a13e709`, `cb231ba` (upstream — our tree already has the substance), `f44b725`
(profile scoping — single-profile install), `9629132` (base already reads the
Hermes compression threshold).
