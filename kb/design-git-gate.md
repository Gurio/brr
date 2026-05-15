# Design: git gate defaults and forge boundary

Status: active

This hangs off the gates hub, [`subject-gates.md`](subject-gates.md), and
the daemon lifecycle hub, [`subject-daemon.md`](subject-daemon.md).

## Current choice

The built-in Git gate is a default-on, credential-free task source. `brr init`
writes `.brr/gates/git.json`; the daemon also treats missing git state as the
default config. The gate watches `tasks/` on the repo's default branch and
turns new or modified files into inbox events with `source=git`,
`git_file=<path>`, and `git_commit=<oid-prefix>`.

The module name and state file now match the public gate name:

- Python module: `git.py`
- Current state file: `.brr/gates/git.json`
- Legacy state file: `.brr/gates/git_gate.json`, still read for migration

The default uses `git fetch` plus a diff against the last observed commit.
It does not `git pull` unless `use_pull=true` is configured, because the gate
should not mutate the host checkout merely by polling for work.

## Why this default is narrow

Running an AI runner on every pulled change is not a safe default. It has no
portable intent signal, can spend tokens because someone synchronized normal
code, and can self-trigger when brr pushes its own task branches unless the
filtering rules become complex. Watching all branches multiplies that problem
and forces an opinion about which branch should seed or receive the resulting
work.

Task files are the smallest useful generic Git primitive:

- They work through any Git remote, including GitHub web edit, GitLab,
  Gitea, Forgejo, Bitbucket, Obsidian git-sync, or a script.
- They carry human intent in the file body, so the runner has a real request
  rather than an ambiguous diff.
- They do not require credentials beyond whatever `git fetch` already uses.
- They preserve the existing gate/file-protocol boundary: the gate only
  creates an event; the daemon still owns task execution and branch handling.

This makes the Git gate useful by default without making ordinary repo syncs
expensive.

## Future source modes

The next credible Git-only mode is an explicit repository-change source, not a
replacement default. It should require configuration such as:

- `mode=changes`
- `branches=default` or an allowlist, with `all` as an opt-in
- `paths=` include/exclude filters
- a prompt template that explains what to do with a pulled change
- loop guards for brr-produced branches and commits

That mode should start with the default branch. "All branches" should be
reserved for repos that explicitly want broad automation and accept the token
cost.

`use_pull=true` can remain available, but fetch+diff should stay the default.
Pulling changes into the host checkout is an operational policy choice, while
fetching is just observation.

## Git versus forges

PRs, issues, review threads, labels, assignees, and comments are not Git
concepts. They are forge concepts. A generic Git gate cannot observe them
without provider APIs, provider auth, pagination, rate limits, webhook
verification, and provider-specific permission models.

brr should keep the layers separate:

- `git.py` handles generic Git refs and task files.
- `forges.py` keeps provider URL inference for branch-view links and other
  provider-neutral helpers.
- Provider-aware gates or hooks can be added later for GitHub, GitLab,
  Gitea/Forgejo, and Bitbucket when brr has a real auth and event model for
  them.

Trying to hide PR/issues behind a single "generic git" gate would make the
first implementation look portable while leaking provider-specific behavior
immediately. A normalized event shape can still exist above provider adapters,
but the adapters should be honest about their provider.
