# My-OS integration changes

Local commits carried on top of `wzgrx/hermes-lcm`. Newest first.

## myos-2026.10.19 (base `19bc4ff`, v1.0.0-rc.3)

| Change | Origin | Why |
|---|---|---|
| `fix(recall)`: reserve recall time for usable semantic corpora | port of `the3asic/hermes-lcm` `15723dc`, adapted | the FTS arm consumed the whole recall budget before the semantic arm ran; observed 24 times live |
| `docs(skill)`: live diagnostics lessons | local | embedding coverage, backfill lease, dead inflight markers, standalone-script env, compaction cost distribution, safe update procedure |
| `docs`: fork policy | local | branch model, update cadence, acceptance rules |

### Not yet accepted

Reviewed on 2026-10-19, not applied yet — each needs an isolated test:

- `8502bc5` (the3asic) — avoid concurrent SQLite statement cache reuse
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
