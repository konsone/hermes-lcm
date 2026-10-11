# Configuration and activation

Hermes-LCM is a general Hermes plugin and a context engine. Both identities must be active:

```yaml
plugins:
  enabled:
    - hermes-lcm

context:
  engine: lcm
```

Restart Hermes after changing plugin or context-engine configuration. Verify with `hermes plugins`, then use `lcm_status` after a normal message has bound the session.

## Installation

An existing checkout can install profile-aware plugin and skill links:

```bash
./scripts/install.sh
HERMES_PROFILE=myprofile ./scripts/install.sh
```

The installer exposes both:

- `plugins/hermes-lcm` for plugin loading;
- `skills/hermes-lcm` for normal skill discovery.

It refuses conflicting paths rather than overwriting an existing install.

## High-impact controls

Use `docs/operator-guide.md` as the complete current source. Start with:

- `LCM_CONTEXT_THRESHOLD`: when normal context pressure triggers compaction;
- `LCM_FRESH_TAIL_COUNT`: newest messages kept raw;
- `LCM_LEAF_CHUNK_TOKENS`: maximum raw material per leaf compaction group;
- `LCM_DATABASE_PATH`: profile-local SQLite path when the default is unsuitable;
- `LCM_IGNORE_SESSION_PATTERNS` and `LCM_STATELESS_SESSION_PATTERNS`: storage ownership boundaries;
- summary/embedding provider settings only after confirming credentials, cost, and data handling.

Optional slash commands are disabled by default with `LCM_ENABLE_SLASH_COMMAND=false`. Destructive cleanup apply is separately guarded. Do not enable mutation surfaces merely to diagnose a problem.

Change one tuning variable at a time, then re-check `lcm_status`, context pressure, summary health, latency, and actual answer quality.

## Profile-scoped settings (1.0.0-rc.3+)

On current Hermes, LCM reads `LCM_*` through the active profile secret scope and
YAML through the task-local Hermes home. This includes external cron workers
whose process environment has been stripped. A routed-profile miss falls back
to that profile's YAML/defaults, not the launch profile's environment. A missing
required scope is an error to diagnose, not a reason to copy global settings.
Older Hermes versions without these APIs retain environment/home fallback.

Reasoning sidecars count in conservative local token estimates and survive raw
store reloads. Provider-specific echo/sanitization is still handled by Hermes.
Existing stored rows are not backfilled. Reasoning is excluded from full-text
evidence search and respects existing opt-in sensitive-pattern redaction.
For upgrades and database rollback, follow the repository's `INSTALL.md`.
