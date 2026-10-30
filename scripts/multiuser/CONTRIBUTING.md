# Sharing these changes and proposing upstream pull requests

This is an experimental Linux multiuser setup. It runs one loopback server and
one watcher in each graphical login, names new buckets by username and hostname,
and adds a user selector to Activity. All local users can read the shared API.
It does not provide per-user authorization or track background process runtime.

## Reproducible source export

From the activitywatch repository root:

```sh
python3 scripts/multiuser/export_sources.py
```

The result is `dist/activitywatch-multiuser-sources.zip`. It contains patches,
the full changed source files, a repository/revision manifest, this guide and
a patch validation/application script. Only explicitly selected source paths
are exported. Local databases, configuration, API keys, binaries, virtualenvs,
lockfile changes and unrelated package/version edits are excluded.

Recipients should unpack the ZIP, clone the upstream repositories at the
manifest revisions, then run:

```sh
python3 apply.py /path/to/activitywatch --check
python3 apply.py /path/to/activitywatch
```

`apply.py` verifies every repository revision and checks every patch before
applying any of them. Use a fresh checkout with initialized recursive submodules.
It does not fetch dependencies or build binaries. Build using the repository's
normal instructions; the Linux multiuser installer additionally requires a built
bundle in `dist/activitywatch` and GNOME's Focused Window D-Bus extension.

## Suggested upstream submissions

Submit independent fixes first:

1. **ActivityWatch/aw-server** — current upstream already closes request-thread
   SQLite connections. Do not submit our equivalent local fix as a duplicate PR.
   This was verified against the GitHub default branch on 2026-10-30.
2. **2e3s/awatcher** — retry unavailable watcher backends instead of ending the
   process and stopping working idle tracking. This has its own patch.
3. **ActivityWatch/activitywatch** — rebuild awatcher during packaging instead
   of copying a potentially stale executable. This has its own patch.

Discuss the multiuser design with maintainers before presenting it as a finished
feature. It spans ActivityWatch/aw-webui, the three Python watchers,
2e3s/awatcher and the bundle's Linux deployment scripts. The patches preserve
existing data but create new buckets; username naming is currently unconditional.
For an upstream-ready feature, agree on an opt-in configuration or structured
username metadata, migration/default-selection behavior, and which tools should
support user filtering. The UI currently supports Activity only.

Known limitations to resolve and test:

- Session switching is not explicitly detected. Idle reporting depends on the
  desktop backend; inactive sessions are not immediately forced to AFK.
- Username inference uses bucket IDs and hostname metadata. Cross-user query
  selection is not an authorization boundary.
- Default selection picks the first sorted known username, not the current
  viewer's OS account. Other pages have not gained user selection.
- A clean installation and multiple GNOME logins need end-to-end testing.
- The Rust tests could not run offline because a dev dependency was unavailable;
  the release build succeeded. Web UI type checking, build and affected tests
  passed locally. Do not describe this as CI verification of the full feature.

## Publishing forks

Each modified submodule is its own Git repository. Commit and push its changes
to a feature branch in a fork of that repository, then create a pull request to
its upstream. Start with `fix: close SQLite connections after requests` for the
server fix and a separate `feat:` branch for multiuser work.

Only after submodule commits are publicly accessible should a bundle fork point
to those commits. For a cloneable fork, configure its `.gitmodules` URLs to the
forks that contain unmerged commits. Publish the root commit last. Never publish
submodule pointers to commits that exist only on the author's computer.

The export does not create commits or publish repositories. Existing project
licenses and notices still apply; they are not replaced by this guide.
