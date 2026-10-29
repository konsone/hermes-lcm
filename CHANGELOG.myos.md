# My-OS integration changes

Local commits carried on top of `wzgrx/hermes-lcm`. Newest first.

## Unreleased

| Change | Origin | Why |
|---|---|---|
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
