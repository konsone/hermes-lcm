# Fork policy — `konsone/hermes-lcm`

This repository is a **curated integration branch**, not a rewrite. It tracks
[`wzgrx/hermes-lcm`](https://github.com/wzgrx/hermes-lcm) and carries a small,
reviewed set of local commits on top.

## Branches

| Branch | Purpose | Rules |
|---|---|---|
| `wzgrx` | tracking branch, mirrors `wzgrx/hermes-lcm` | fast-forward only, never commit here |
| `myos` | integration branch: `wzgrx` + local commits | the only branch deployed to My-OS |

Production runs a **tag** on `myos` (`myos-YYYY.MM.DD`), never a moving branch.

## Remotes

| Remote | URL | Use |
|---|---|---|
| `origin` | `konsone/hermes-lcm` | push local commits and tags |
| `wzgrx` | `wzgrx/hermes-lcm` | base for updates |
| `the3asic` | `the3asic/hermes-lcm` | source of individual patches only |
| `tuly` | `tuly-space/hermes-lcm` | source of individual patches only |
| `upstream` | `stephenschoettler/hermes-lcm` | archived reference; not a base |

`the3asic`, `tuly` and `upstream` diverged from the same rc.1 commit as our
base. **Never merge them.** Port single commits with a stated reason and a
test.

## Update procedure (about every 1–2 months)

```bash
cd /opt/data/plugins/hermes-lcm
git fetch --all --tags --prune
git checkout wzgrx && git merge --ff-only wzgrx/main
git checkout myos && git rebase wzgrx
# resolve conflicts in favour of wzgrx behaviour unless a local commit
# explicitly documents otherwise
python -m pytest tests/ -q            # full suite on a clean copy, not the live DB
git tag myos-$(date +%Y.%m.%d)
git push origin myos --tags
```

Then deploy through Dokploy (label change → recreate), and verify in phase B:

1. `plugin.yaml` version matches the new base.
2. Boot log has `Plugin 'hermes-lcm' registered context engine: lcm` and no
   `load timed out`.
3. `lcm_status.runtime_identity.plugin_git_commit` equals the deployed tag.
4. `store_id` grows after the first turn; `lcm.db` integrity is `ok`.

## Accepting a foreign commit

A patch from another fork is accepted only when all of these hold:

1. **Named defect or measured need** — not "it looks useful". Write the
   failure mode or the measurement into the commit body.
2. **Small and separable** — one logical change; no drive-by refactors.
3. **Test included** — the patch ships or gains a regression test that fails
   before and passes after.
4. **No schema or storage migration** without a backup plan for `lcm.db`.
5. **Full suite green** on a clean copy (pre-existing failures listed and
   compared against the base).
6. **Rollback is one line** — revert the commit; the plugin dir is restored
   from the previous tag.

Accepted patches and their upstream commit ids are listed in `CHANGELOG.myos.md`.

## What does not belong here

- Rewrites of the compaction or storage model.
- Features with no current consumer (build them when a trigger appears).
- Profile multiplexing changes (the My-OS install is single-profile).
- Vendor-specific embeddings adapters until a deployment actually needs one;
  the supported providers already cover local and cloud paths.

## Rollback

```bash
git checkout myos-<previous-tag>
# restart through Dokploy
```

Database rollback is separate: use the SQLite backup API (`backup/`), never
`cp` on a live WAL database.
