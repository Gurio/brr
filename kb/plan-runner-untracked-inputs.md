# Plan: explicit runner access to untracked host inputs

Status: active

This page records the 2026-05-17 revisit of whether daemon runners
should see untracked files from the host checkout. Current environment
shape is summarised in [`subject-envs.md`](subject-envs.md); the
durability and salvage contracts live in
[`design-env-interface.md`](design-env-interface.md).

## Current behaviour

`host` still ships. It is an explicit environment (`environment=host`)
implemented by `HostEnv`, and it runs the runner in the main checkout
with the daemon process environment inherited. That means host tasks see
the user's untracked and ignored repo files exactly like any local shell
would. `host` is not auto-picked; `environment=auto` chooses Docker
when configured, otherwise a git worktree.

`worktree` and `docker` are intentionally not host-checkout views.
`WorktreeEnv.prepare` creates `.brr/worktrees/<task-id>/` with
`git worktree add` from the resolved seed ref, so the runner's working
tree contains tracked repository state from that ref, not pre-existing
untracked or ignored files from the main checkout. Docker reuses that
worktree and runs the container with the worktree as cwd.

Credential access is already a separate lane from repo file access:
`host` and `worktree` runners inherit the daemon's process environment;
Docker forwards the known runner API-key variables plus names listed in
`docker.env`, and mounts known runner login directories unless
`docker.mount_credentials=false`.

## Problem

The current choices are all-or-nothing:

- stay isolated with `worktree` / `docker`, but lose easy access to
  local artifacts such as generated logs, one-off reports, or ignored
  build output;
- switch to `host`, which sees everything but gives up branch/worktree
  isolation and can dirty the user's main checkout.

Making every untracked file visible by default would solve the symptom
but cut across brr's core contracts. It would leak secrets such as
`.env`, private keys, and local credentials; it would make task inputs
depend on large ignored directories like `.venv`, `node_modules`, or
build caches; and if copied into the task worktree directly, those
inputs would show up as untracked leftovers and trigger the salvage
rule on otherwise clean successful runs.

## Proposal

Keep the default as **no ambient untracked-file access**. Add an
explicit, prompt-visible task input mechanism for the cases where the
operator wants local artifacts available to an isolated runner.

First slice:

- Add a flat config / event field, tentatively `runner.inputs=...`,
  containing comma-separated repo-relative files or directories.
- Merge config-level inputs with event-level `inputs` metadata so gates
  can attach task-specific artifacts without changing repo config.
- Reject absolute paths, `..`, `.git`, and `.brr` by default. Missing
  configured inputs should fail env preparation with a clear error; an
  optional input marker can be added later if a concrete workflow needs
  it.
- During env prepare, snapshot each input under
  `.brr/inputs/<task-id>/<repo-relative-path>` and record the copied
  paths in `RunContext.env_state` / `task.meta`.
- Add a Task Context Bundle section listing each source path and its
  runner-visible copy, with read-only wording. This makes the access
  auditable in the exact prompt the agent receives.
- Treat `.brr/inputs/<task-id>/` as env scratch: remove it on clean
  `done`, preserve it on `error` / `conflict` alongside the worktree
  and traces.

This gives worktree and Docker tasks the same semantics: a bounded
snapshot of explicitly named host files, not an ambient view of the
host checkout. Because the copies live under `.brr/inputs/`, they do
not dirty the task worktree and do not become accidental commit
material.

Second slice, only if snapshot input is not enough:

- Add Docker-specific read-only mounts for live logs or artifacts that
  change while the task runs.
- Keep this separate from the first slice because portable read-only
  bind mounts are not available for the plain worktree env, and because
  live host views have a larger nondeterminism surface than snapshots.

## Secrets stance

Do not use broad untracked-file access as the primary secret path.
Environment variables and runner credential mounts are the safer,
already-shipped mechanisms. For Docker, `docker.env=KEY1,KEY2` is the
current opt-in extension point for additional variables. If users keep
API keys in a repo-local `.env`, brr should steer them toward exporting
the needed variables into the daemon process or adding a narrow Docker
env passthrough, not toward automatically copying `.env` into every
runner task.

## Implementation notes

- The parser can live near env preparation, using only stdlib
  `pathlib` / `shutil`. It should preserve directory structure under
  `.brr/inputs/<task-id>/`.
- The run context file and Task Context Bundle should both carry the
  input map so recovery and chat-delivered prompts agree.
- Tests should cover `worktree` and `docker` prepare, rejection of
  unsafe paths, prompt rendering of the input map, and cleanup /
  preservation behavior on finalize.
- User docs should keep the simple rule: use `host` for trusted tasks
  that need the whole local checkout; use `runner.inputs` for specific
  artifacts; use env vars / credential mounts for secrets.
