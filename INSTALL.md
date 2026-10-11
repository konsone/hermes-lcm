# Managed installation — maintained Hermes-LCM fork

The maintained deployment is `wzgrx/hermes-lcm` main. Keep development checkouts
separate from `$HERMES_HOME/plugins/hermes-lcm`. Use the durable `hermes` launcher
and Hermes PM for runtime dependencies; do not pip-install into a serving runtime.

```bash
hermes plugins install wzgrx/hermes-lcm --enable --force
hermes pm install
hermes plugins doctor hermes-lcm --ci
```

Installation/reinstallation is interactive. Review source, scan findings, declared
capabilities and Python requirements before approving. `--enable` is not dependency
consent. Preserve existing `context.engine: lcm`, provider settings, thresholds,
custom grants and profile-specific configuration.

## Reviewed updates on current official Hermes

1. Review upstream changes and the maintained fork diff. Run tests and require
   successful CI for the exact selected main SHA; record the old and reviewed SHAs.
2. Confirm Gateway idle immediately before stopping it gracefully. Stop any other
   writers to the same LCM database. Back up the database with SQLite's backup API;
   record plugin install metadata, configuration and PM generation facts privately.
3. Confirm the remote main still equals the reviewed SHA, then update through PM:

```bash
hermes gateway stop
hermes plugins update --help
hermes plugins update hermes-lcm
hermes pm install
hermes plugins doctor hermes-lcm --ci
```

Current official `plugins update` has neither `--force` nor `--expected-revision`.
Do not add an old core overlay to restore those flags. `--force` in the initial
installation example belongs to **install**, not **update**. Updates may request
new dependency/capability consent. Inspect scanner findings before approving;
never disable scanning globally. If update has no confirmation path for reviewed
CAUTION findings, retain the backup and use the official interactive same-source
`plugins install wzgrx/hermes-lcm --enable --force`, then recheck configuration,
provenance and worktree registrations. The two commands have different semantics.

4. Verify the installed SHA equals the reviewed SHA **before starting Gateway**.
   Remote checks are not an atomic pin: if main moved during publication, keep
   Gateway stopped and review/restore the selected snapshot instead of starting
   unexpected code. Verify `pinned: false` and source in installer metadata.
5. Run read-only SQLite `quick_check`, plugin diagnostics and, when Card is enabled,
   its current `verify`/`status` commands. Start Gateway once, then verify loaded
   plugin version, connection and fresh logs. Service health is not a real chat test.

`./scripts/update.sh` delegates a managed checkout to this PM workflow. A separate
non-serving development checkout may use its legacy Git pull/link workflow.
Adopt a self-cloned install through `hermes plugins adopt hermes-lcm` only when
install provenance is missing. Preserve Git worktree registrations and user files.

## Card 1.5.x coexistence

Read the installed Card's INSTALL.md before changing Hermes core. Current Card
owns reversible source injections and plugin compatibility code. Do not replay
retired core overlays or commit Card-generated hooks into official Hermes main.
An LCM-only update does not require upgrading Card or rewriting its hooks. For a
core upgrade follow Card's uninstall/update/PM/verify/install sequence separately.

## Pins, packaging and rollback

A `--ref` pin can survive same-source reinstallation. To unpin, preserve checkout,
config/grants and metadata, use managed removal and interactive install from main,
restore custom settings through Hermes APIs, and verify provenance. Never edit
installer metadata to pretend a pin has disappeared.

Root `pyproject.toml` is intentionally a virtual PM dependency project. Its
placeholder version is not the plugin version, which is declared in `plugin.yaml`.
Do not remove that metadata or pip-install the tool-only directory.

Version 1.0.0-rc.3 adds a nullable reasoning column without rewriting historical
messages. Preserve backups and prior PM generations. For rollback, keep all
writers stopped, restore the recorded code/config/dependency generation through
managed tooling and validate before restart. If restoring data, use the consistent
pre-upgrade database snapshot and quarantine the failed database with its own
WAL/SHM together; never combine different snapshot generations. Do not replace a
newer database merely to roll back code without considering intervening messages.
