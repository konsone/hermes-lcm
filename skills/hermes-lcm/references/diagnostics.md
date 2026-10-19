# Diagnostics

Use read-only product tools before changing configuration or running an apply path.

## Fast path

1. `hermes plugins`: confirm `hermes-lcm` is enabled and the selected context engine is `lcm`.
2. Send one normal message if the session has not been bound since restart.
3. `lcm_status`: inspect runtime identity, database path, context pressure, summary/store counts, filters, and lifecycle state.
4. `lcm_inspect`: inspect current-session lineage, frontiers, fresh tail, externalized-ref readability, and skip/no-op reasons without retrieving content.
5. `lcm_doctor`: run database, FTS, lifecycle, configuration, and context-pressure diagnostics.

If optional slash commands are enabled, `/lcm status` and `/lcm doctor` expose the corresponding operator views.

## Safe mutation order

For cleanup, repair, source normalization, or rotate:

1. run the read-only preview;
2. inspect exact candidates and paths;
3. create/confirm a backup;
4. obtain user authorization for the specific apply operation;
5. run one bounded apply and verify integrity afterward.

Cleanup apply is separately feature-gated. Never infer permission to enable it from a diagnosis request.

## Update procedure (live maintenance, 2026-09)

1. Backup `lcm.db` first (SQLite backup API, never cp on a live WAL DB).
2. Update the clone: currently a FORK (`wzgrx/hermes-lcm`, rc.2, carries the WAL contour guard + the POSIX lockfix equivalent + FTS fairness); upstream is abandoned — do not pull from upstream.
3. Deploy/restart via Dokploy, verify `lcm_status` (`plugin_git_commit` must match the fork HEAD).
- Pitfall: a compose deploy with NO parsed-config change is a silent no-op — send a label change only after `compose.update` actually landed it, and verify the gateway process start time moved before trusting a green deploy (see hermes-agent-update).
- Pitfall: a standalone backfill script does NOT inherit gateway LCM_* env — set defaults explicitly (embeddings enabled/provider/model/base_url) in the script, else refusal 'embeddings are disabled'.
- Pitfall: a timed-out/killed backfill run holds the backfill lease for its TTL (default 600 s) — the next attempt is refused 'another embedding backfill holds the lease'; wait out the TTL or override `LCM_EMBEDDING_BACKFILL_LEASE_TTL_S`.
- Pitfall: cron `--script` accepts only a file under `/opt/data/scripts/` (relative name), not `/opt/data/work/`.
- After a catch-up: verify `MAX(embedded_at)` moved to today, active chunk meta == vectors count (100%), inflight empty; dead inflight markers (chunk gone) delete by the checklist bullet in SKILL.md.

## Common states

- Unbound status after restart: send a normal message, then check again.
- Database exists but stays empty: verify plugin enablement, `context.engine`, profile, database path, and ignore/stateless patterns.
- Weak exact recall: verify source rows exist, query construction/scope is correct, summary health is sound, and embedding coverage/provenance matches the requested mode.
- Conflicting summary and raw evidence: prefer the newer exact raw evidence and inspect lineage.
- Repeated automatic preflight after a would-grow/no-progress verdict: inspect `lcm_status.host_rejection_backoff_seconds` and `host_rejection_reason`. Ordinary model-backed preflight shares the session-scoped five-minute gate; overflow recovery, critical pressure and deterministic cleanup remain eligible. A lowered `LCM_AUTOMATIC_FOREGROUND_MAX_SECONDS` begins at compression entry, including preparation, but remains best-effort around individual provider/filesystem calls. Compare `last_compaction_duration_ms` and sweep stop reason rather than treating the ceiling as a hard wall-clock guarantee.
- Large durable store but no leaf passes or `raw_backlog` debt: compare `lcm_status.store.post_frontier` (or `/lcm status` `store_post_frontier_*`) with `lcm_inspect`'s assembled middle and fresh tail. The post-frontier count is a read-only **upper bound**, including protected fresh-tail rows and potentially already represented source rows; missing/zero token estimates are counted separately. If the lifecycle frontier does not match the foreground session, the metric is unavailable rather than borrowing another session's cursor. The bounded [#585](https://github.com/stephenschoettler/hermes-lcm/issues/585) hidden-prefix path runs when pressure reaches threshold: verify D0 source IDs and the frontier advance after each pass. If debt stays without a pass, inspect sidecar readability, active-to-store suffix alignment, tool-group boundaries, and the 16,384-row / 4-million-character / 5,000-active-message limits. Keep raw rows and summary lineage intact while diagnosing; an empty debt field alone is not proof that durable backlog is drained.
- Path B/context-engine schema log: expected on hosts where plugin-registry handlers do not receive active messages; context-engine schemas and dispatch remain the healthy route.
