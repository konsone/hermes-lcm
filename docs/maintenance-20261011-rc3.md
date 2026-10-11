# Maintained fork review — 2026-10-11

## Reviewed upstream scope

- Original upstream main: `8d1b1e6d3d63f5fc7b209e8d7ec1dc9b814f2e54`.
  Already contained in the maintained fork; no newer merged main was required.
- Adapted open upstream [PR #666](https://github.com/stephenschoettler/hermes-lcm/pull/666),
  including all three reasoning/accounting/discovery commits. Retained existing
  maintained-fork ingest and timestamp-dedupe changes during integration.
- Addressed [issue #667](https://github.com/stephenschoettler/hermes-lcm/issues/667)
  with profile-scoped settings and task-local YAML home, plus legacy-host fallback.
- Reviewed #663 SQLite descriptor/lock handling: equivalent protection and tests
  already exist here. Reviewed #664 compression policy: existing maintained live
  cap/ratio/model-resolution behavior retained rather than replaced wholesale.
- Added opt-in sensitive-pattern protection for the newly persisted reasoning.
  No new model/provider calls, runtime dependency requirement or core patch.

## Verification

- Python 3.14.7 in the existing Hermes environment; isolated HOME/HERMES_HOME tests.
- Full release gate: PASS, including 503 focused tests, benchmark/stress smoke,
  release stress, compile, shell, dependency contract and whitespace gates.
- Full suite: **3608 passed, 8 skipped, 12 xfailed**.
- Same suite under 1024 file-descriptor limit: **3608 passed, 8 skipped, 12 xfailed**.
- Ruff: all checks passed. Contract 1.0.6 declares 11 external import boundaries.
- Real installed Hermes scope API check: routed YAML and ignore settings survive
  stripped process variables; foreign launch-profile values do not leak.
- Live-database-copy migration rehearsal: 323399 messages, 137 summary nodes and
  144 lifecycle records preserved; quick_check OK. Live database was not the test
  target. Schema remains v5 with one additional nullable reasoning column.

An initial full run exposed stale release/contract assertions, which were updated
with the release metadata. It also had one transient placeholder lifecycle failure;
that exact test and both final full-suite runs passed without relaxing assertions
or claiming a new fix for that transient. Initial logs are retained privately.

## Operations

Use INSTALL.md and current official Hermes commands. The installed Card is the
Claude-rewritten 1.5.2; do not revive older overlays, hook architectures or private
update flags. LCM-only publication preserves core/Card source. Gateway connection
and database diagnostics are deployment checks, not real-chat or 850k-token
compression acceptance. CI and deployed identity are verified separately.
