# Design: env protocol, durability contract, and decentralised merging

Status: accepted on 2026-05-06

This page is the design spec for environments: the shipped
`EnvBackend` Protocol, the durability contract, the per-env mechanics,
the designed plugin model, and the decentralised merge framing. Current
rollout status (which envs ship, which don't, what the salvage rule
looks like) lives one level up in [`subject-envs.md`](subject-envs.md);
start there if you want the synthesis. Strategic context for the fleet
axis is in [`deck-brr-fleet-steering.md`](deck-brr-fleet-steering.md),
and open items adjacent to envs (overlays, brnrd, cross-platform
supervisor, third-party plugin candidates) live in
[`notes-pondering-fleet.md`](notes-pondering-fleet.md).

## Scope

The design covers a single three-phase abstraction (`prepare → invoke
→ finalize`) for the built-in env family (`host`, `worktree`, and
`docker` shipped; `ssh` and `devcontainer` designed but not wired), an
explicit durability contract the daemon enforces from the host, the
decentralised branch-and-PR merge model that replaced an earlier
merge-coordinator sketch, and a dual plugin point — Python entry
points under `brr.envs` and drop-in script envs in
`~/.config/brr/envs/` or `.brr/envs/` — that remains a design target
rather than current resolver behavior. Concurrent execution, overlays,
`brnrd`, and env-specific secret handling beyond what gates already do
are explicitly out of scope and live in their own designs / notes.

---

## The EnvBackend Protocol

```python
# src/brr/envs/__init__.py

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

@dataclass
class RunContext:
    """Per-task handle returned by Env.prepare()."""
    name: str
    cwd: Path                  # where the runner should be invoked
    repo_root: Path            # the host repo (always)
    runtime_dir: Path          # host's .brr/ (read-only mount in remote envs)
    response_path_host: Path   # where the daemon records the response
    response_path_env: Path    # path shown to the runner in its prompt
    branch_name: str | None = None
    branch_plan: branching.BranchPlan | None = None
    env_state: dict[str, Any] = field(default_factory=dict)

class EnvBackend(Protocol):
    name: str                  # "host" | "worktree" | "docker" | …

    def prepare(
        self, task: Task, repo_root: Path, cfg: dict[str, Any], *,
        branch_plan: branching.BranchPlan, response_path: Path,
    ) -> RunContext: ...

    def invoke(
        self, ctx: RunContext, runner_name: str,
        invocation: runner.RunnerInvocation, cfg: dict[str, Any], *,
        trace: bool = False,
    ) -> runner.RunnerResult: ...

    def finalize(self, ctx: RunContext, task: Task, tasks_dir: Path) -> Task: ...
```

`invoke` keeps returning `RunnerResult` so the existing trace / retry
plumbing in `runner.invoke_runner` is reused unchanged. Envs are
typically thin wrappers around `runner.invoke_runner` plus
prepare/finalize logic. Backend validation happens in `prepare()`;
finalization records branch, scratch, and conflict outcomes on the
returned `Task` / `task.meta`.

### Response path split

`response_path_env` is what the runner sees in its prompt ("write your
response to …"). `response_path_host` is where the daemon later verifies
the response landed. For envs that share a filesystem with the host,
they're the same path; for remote envs, `finalize` is responsible for
the transfer.

| Env            | `response_path_env`                            | `response_path_host`                           | Equal? |
|----------------|------------------------------------------------|------------------------------------------------|--------|
| `host`         | `repo_root/.brr/responses/<id>.md`             | same                                           | yes    |
| `worktree`     | `repo_root/.brr/responses/<id>.md`             | same (worktree shares `.brr/`)                 | yes    |
| `docker`       | `repo_root/.brr/responses/<id>.md` (same absolute path bind-mounted into the container) | same | yes |
| planned `ssh`  | `<scratch>/<task-id>/.brr/responses/<id>.md`   | `repo_root/.brr/responses/<id>.md`             | **no** — `finalize` would copy it back |
| planned `devcontainer` | `/workspaces/<repo>/.brr/responses/<id>.md` | `repo_root/.brr/responses/<id>.md`          | yes, if mounted at a stable workspace path |
| planned plugin envs | env's choice                              | `repo_root/.brr/responses/<id>.md`             | plugin-dependent |

The daemon only ever checks `response_path_host`. `response_path_env`
is a hint to `prompt` construction; how it's translated into the
runner's prompt is each env's concern.

### Registry & plugin point

Current resolver behavior is built-in only:

1. Built-in Python class in `src/brr/envs/`.
2. Otherwise → `UnsupportedEnvironmentError`.

```python
# src/brr/envs/__init__.py
_BUILTINS: dict[str, type[EnvBackend]] = {
    "docker": DockerEnv,
    "host": HostEnv,
    "worktree": WorktreeEnv,
}

def get_env(name: str) -> EnvBackend:
    env_name = (name or "worktree").strip()
    backend = _BUILTINS.get(env_name)
    if backend is None:
        raise UnsupportedEnvironmentError(...)
    return backend()
```

The accepted extension point is still the same protocol with a wider
resolution order: per-repo script env, user-wide script env, then Python
entry point under `brr.envs`. That extension is not wired into the
current resolver; `get_env("firecracker")`, `get_env("ssh")`, and
`get_env("devcontainer")` fail today.

#### Python plugins

Designed for typed, reusable, shareable envs. Ship as a separate pip
package:

```toml
# someone-else/pyproject.toml
[project.entry-points."brr.envs"]
firecracker = "myorg_brr_envs.firecracker:FirecrackerEnv"
```

`brr` keeps zero runtime deps; plugins bring their own. See
`notes-pondering-fleet.md` §10 for the list of plugin candidates.

#### Script envs (drop-in, zero install)

Designed for "bash script on my machine, point brr at it" ergonomics.
A script env is a directory whose name *is* the env name. Two planned
layouts:

```
.brr/envs/myenv/
├── prepare           # executable
├── invoke            # executable
├── finalize          # executable
└── validate          # optional; executable
```

or a single executable dispatching by first argv:

```
.brr/envs/myenv             # executable; $1 ∈ {validate, prepare, invoke, finalize}
```

Protocol is **JSON-in on stdin, JSON-out on stdout**, with fields
mirroring the Python protocol (`RunContext`, `RunnerResult`, and the
task/status metadata returned from `finalize`). `stderr` is propagated
unchanged to the trace.

Minimal bash stub for the `invoke` step of a script env:

```bash
#!/usr/bin/env bash
set -euo pipefail
# stdin: {"ctx": {...}, "prompt": "...", "cfg": {...}}
# stdout: {"stdout": "...", "stderr": "...", "returncode": 0, "validation_ok": true}
input=$(cat)
cwd=$(jq -r '.ctx.cwd' <<<"$input")
prompt=$(jq -r '.prompt' <<<"$input")
cd "$cwd"
out=$(some-runner --print "$prompt" 2> >(cat >&2))
rc=$?
jq -nc --arg out "$out" --argjson rc "$rc" \
  '{stdout: $out, stderr: "", returncode: $rc, validation_ok: ($rc == 0)}'
```

The planned `ScriptEnvAdapter` shells out to these four executables and
marshals JSON. It is the bridge that keeps protocol parity between
Python and script envs once the plugin path is implemented.

For the future `brr env init` scaffolding helper, see the "Env
scaffolding" section further down.

---

## The durability contract

> Every task that runs in a non-`host` env runs in an **ephemeral**
> location. Containers exit. Worktrees are removed. Planned remote envs
> follow the same rule by copying durable outputs back before teardown.
> **The only outputs that survive are git refs and the response file.**
> Everything else is lost on `finalize()` unless the salvage rule keeps
> scratch around for inspection.

Concrete rules every `EnvBackend.finalize()` must satisfy:

| Output                                      | Where it ends up on the host          | Required when                            |
|---------------------------------------------|----------------------------------------|------------------------------------------|
| Git commits on `ctx.branch_name` or the branch the agent switched to | reachable in host's `.git` | branch-producing envs |
| Response file `<event-id>.md`               | `repo_root/.brr/responses/<id>.md`     | runner exits 0 with non-empty stdout     |
| Trace artefacts                             | `repo_root/.brr/traces/<kind>/…/`      | always written; removed on clean `status=done`, kept on `error`/`conflict` |
| Env-private scratch teardown                | n/a — removed from env's territory     | clean `status=done` with no uncommitted files |

Anything an agent writes outside of a commit, the response file, or a
trace, is **not durable** and the framework makes no guarantee about it.
This is documented in `prompts/run.md` and `docs/brr-internals.md`.

**Salvage rule.** Env scratch state (worktrees, containers, and future
remote/devcontainer scratch) is torn down only when the task finished
cleanly with nothing left uncommitted in the worktree. On `error` /
`conflict`, or when the worktree has untracked/unstaged files, scratch
is preserved so the user can inspect or salvage work. Persisted task
metadata surfaces the preserved location via `task.meta`.

### Enforcement

The daemon doesn't guess. Runner validation happens before finalization:
the runner subprocess must exit 0 and, for daemon tasks, print a
non-empty final stdout response that brr writes to
`response_path_host`. After that, `daemon._run_worker()` marks the task
done and asks the env to finalize branch landing and scratch cleanup:

```python
if result.validation_ok:
    task.update_status("done", tasks_dir)
    with _branch_lock(branch_plan.auto_land_branch):
        task = env_backend.finalize(env_ctx, task, tasks_dir)
else:
    task.update_status("error", tasks_dir)
    with _branch_lock(branch_plan.auto_land_branch):
        task = env_backend.finalize(env_ctx, task, tasks_dir)
```

Finalize is responsible for the env-specific observable work:
fast-forward a safe auto-land target, preserve branch/scratch metadata
on conflicts or failures, and remove scratch only when the salvage rule
allows it.

---

## Shipped and Designed Envs

Only `host`, `worktree`, and `docker` are wired in `_BUILTINS` today.
`ssh` and `devcontainer` below are accepted design targets, not
available backends.

### `host`

- **prepare** → `RunContext(cwd=repo_root, branch_name=None, …)`
- **invoke** → `runner.invoke_runner(...)` directly.
- **finalize** → no-op; work happened directly in the host repo.

This is the explicit main-checkout path, refactored into the protocol.

### `worktree`

- **prepare** → `git worktree add .brr/worktrees/<task-id> <branch>` (creating the branch if needed); cwd points at the worktree.
- **invoke** → unchanged.
- **finalize** →
  - If the task branch has commits and `branch_plan.auto_land_branch`
    is set, attempt `git merge --ff-only` via
    `gitops.fast_forward_branch`. On conflict → mark task `conflict`
    and preserve the branch.
  - If there is no auto-land target, preserve the branch for human
    routing.
  - If the agent switched branches, preserve the runtime branch choice.
  - **Worktree teardown rule:** outcome-aware. Remove the worktree on
    clean `status=done` with nothing uncommitted. Preserve on
    `status ∈ {error, conflict}` or when the worktree has
    uncommitted/untracked files, so the user can inspect or salvage.
  - Response file is already on the host (worktree shares `.git` and `.brr/`).

This is the default isolated execution path for code-modifying work.

#### Why worktree stays a flat env in v1

A decomposed model ("working-copy strategy" × "isolation strategy")
would arguably be cleaner: you could compose e.g. `docker-worktree` for
a fresh checkout inside a container, or `ssh-worktree` for a remote
worktree. Theoretically correct, but it doubles the taxonomy users have
to reason about and forces every env to answer both axes up front.

v1 keeps `worktree` flat because the common intent behind it is
concrete and narrow: **give the agent a fresh folder without polluting
the main checkout** — which flat `worktree` covers cleanly on its own.
Compose-oriented envs (`docker-worktree` etc.) become warranted only
when there's a real request for two axes at once; at that point the
compose axis moves into a follow-up, not v1.

### `docker`

> **Implementation status (2026-05-06):** `prepare`/`invoke`/`finalize`
> shipped per this design. Credential wiring (env-var pass-through for
> known runner keys, `~/.{claude,codex,gemini}` bind mounts when present,
> and `safe.directory='*'` injection so git works against the
> bind-mounted repo) added on top of the original spec to remove the
> "your image must bake in tokens" hidden requirement. The bundled
> first-party Dockerfile now builds a practical runner image with the
> three runner CLIs plus baseline dev tools (`python`/`pip`, SSH client,
> `git`, `rg`, `curl`/`wget`, `jq`, `rsync`, zip tools, and native build
> tooling). Still pending: publishing that image and auto-resolving blank
> `docker.image=`. User-facing docs live in `src/brr/docs/envs.md`.

- **prepare**:
  - Image: `docker.image` in `.brr/config`. The bundled Dockerfile is
    the local first-party path for a runner image, but this is still
    required until brr publishes a default image and can safely resolve
    blank `docker.image=`. brr wires credentials at run time (env-var
    pass-through plus host login-dir bind mounts), so the image no
    longer needs an API key baked in.
  - Bind-mount `repo_root` at the same absolute path inside the container
    (read-write), so the prompt's host paths remain valid in the env.
  - Network: configurable (`docker.network`, default `bridge`).
  - **Branch handling:** Docker tasks first create the same
    `.brr/worktrees/<task-id>` checkout that `worktree` uses and run
    Docker with that as the working directory. This keeps branch work
    from switching or dirtying the host's main checkout while keeping
    commits visible through the shared `.git`.
- **invoke** → `docker run --name brr-<task-id>-<attempt> -v <repo>:<repo> -w <run-root> <image> <runner-cmd>`. The cmd line is built from the existing runner profile machinery. Note: **no `--rm`** — cleanup is `finalize`'s job so we can preserve the container for salvage and support retry diagnostics.
- **finalize** → branch handling identical to worktree finalize. Container teardown matches the worktree salvage rule: `docker rm -f <container>` on clean `status=done`; preserve on `status ∈ {error, conflict}` or when the worktree has uncommitted/untracked files.

For users who want **stronger isolation** (no shared `.git`), the
designed follow-up is a sub-mode `docker.isolation=clone`: `prepare`
clones the repo into a container-private volume, `finalize` does a
`git fetch` from that volume back to the host. Default stays the
bind-mount path because it's simpler and faster.

### `ssh`

Designed, not shipped.

- **prepare**:
  - Remote spec: `ssh.host`, `ssh.scratch` (default `~/.brr/scratch`).
  - `ssh remote 'mkdir -p <scratch>/<task-id>'`
  - `rsync -a --delete <repo_root>/ remote:<scratch>/<task-id>/`
  - `ctx.cwd` is local but `env_state["remote_path"]` is set; invoke proxies through ssh.
- **invoke**: `ssh remote 'cd <scratch>/<task-id> && <runner-cmd>'`. Stdout/stderr piped back; trace is host-side as usual.
- **finalize**:
  - Pull the branch back: `ssh remote 'cd <scratch>/<task-id> && git bundle create /tmp/<task-id>.bundle <branch>'` then `scp` the bundle and `git fetch` it locally to `<branch>`. Bundles handle disconnected transfer cleanly; no need to expose the host's repo over ssh-back.
  - Pull the response file: `scp remote:<scratch>/<task-id>/.brr/responses/<event-id>.md repo_root/.brr/responses/`
  - Pull traces always: `rsync remote:<scratch>/<task-id>/.brr/traces/ repo_root/.brr/traces/`
  - Tear down: `ssh remote 'rm -rf <scratch>/<task-id>'` on clean `status=done`. Preserve the remote scratch dir on `status ∈ {error, conflict}` for salvage, matching the worktree/docker rule.

ssh is the most procedural env. It's also the proof that the contract
generalises: anything that can hold a git repo + write a markdown file
+ run a binary can be a brr environment.

### `devcontainer`

Designed, not shipped.

For repos that already ship a `.devcontainer/devcontainer.json`. Reuses
the user's existing container recipe rather than asking them to
maintain a parallel `docker.image` for brr.

- **validate** → `devcontainer` CLI on PATH + `<repo_root>/.devcontainer/devcontainer.json` present. Raise if either is missing.
- **prepare**:
  - `devcontainer up --workspace-folder <repo_root>` — starts the container (no-op if already up).
  - Record the container id / workspace folder in `ctx.env_state`.
  - `ctx.cwd = repo_root` on the host side; the devcontainer CLI handles the in-container path.
  - Same bind-mount story as `docker`: the repo is mounted in the container, so commits on `ctx.branch_name` are visible to the host immediately. `response_path_env` resolves to the in-container path; `response_path_host` stays the host's `.brr/responses/<id>.md`.
- **invoke** → `devcontainer exec --workspace-folder <repo_root> -- <runner-cmd>`. Runner profile machinery unchanged.
- **finalize** → branch handling identical to worktree/docker finalize. Container teardown: `devcontainer down` on clean `status=done`; preserve on `status ∈ {error, conflict}`. Mirrors the worktree salvage rule.

When implemented, env setup should fail before invocation if the
`devcontainer` CLI or `.devcontainer/devcontainer.json` is missing.

---

## Decentralised "coordinator"

Replacing the central merge coordinator we kept deferring.

### The model

> Every isolated, branch-producing task starts on a task branch.
> Merging is opt-in per branch strategy. Conflicts are not a
> coordinator's problem — they are a human's problem (or the next agent
> run's problem).

| `branch:` strategy   | What `finalize` does for the branch                                        |
|----------------------|----------------------------------------------------------------------------|
| `current`            | nothing (no branch)                                                        |
| `auto` / `task`      | best-effort `git merge --ff-only`; on conflict → status=`conflict`, branch kept |
| `<name>` / `new:<x>` | nothing (human or PR tooling owns the merge)                               |

That's the whole "coordinator": `branching.BranchPlan` carries the
seed ref and optional auto-land target, and
`WorktreeEnv._land_or_preserve()` / `DockerEnv.finalize()` either
fast-forward the resolved target with `gitops.fast_forward_branch()` or
preserve the branch when no safe target exists.

### Concurrency note

Concurrent workers use a per-branch `threading.Lock()` around
finalization. Only tasks targeting the same auto-land branch contend;
different branches finalize independently. Branches commute well in
git, and conflicts that can't ff-merge get parked as `conflict` status
without blocking other tasks.

### Why this is enough

- **Host / read-only tasks** → no task branch, no merge. Nothing to coordinate.
- **Research tasks** → `branch: auto`, single new file in `kb/`. ff-merge succeeds 99% of the time.
- **Refactor tasks** → `branch: auto` or named; if auto fails, `conflict` status surfaces it; if named, it's a PR.
- **Long-lived feature work** → named branch; brr never tries to merge.

CRDT-flavoured framing is real here: branches in git already have a
well-defined merge operation; brr just orchestrates `git merge` calls
and falls back to "leave it for a human" when the operation isn't
trivially defined. No bespoke conflict resolution.

---

## Daemon Integration

`daemon._run_worker()` stays env-agnostic after it resolves the task:
it calls `envs.get_env(task.env)`, passes the resolved `BranchPlan` and
response path into `prepare()`, writes the run-context file from the
returned `RunContext`, invokes the runner through `EnvBackend.invoke()`,
then finalizes under the per-branch lock. `finalize()` reads
`task.status` and applies the same outcome-aware salvage rule on both
success and failure: tear scratch down only after a clean `done`, and
preserve worktree/container state when the task errors, conflicts, or
leaves uncommitted files behind.

---

## Env selection

There is no LLM triage step. The daemon picks the env mechanically
from `.brr/config` and event metadata: `environment=auto` resolves to
`docker` when a Docker image is configured, otherwise `worktree`;
`host` is explicit only. `Task.resolve_env()` accepts syntactically
valid future env names, but `envs.get_env()` can run only `host`,
`worktree`, and `docker` today. See
[`decision-remove-triage.md`](decision-remove-triage.md) for why this
shape replaced the earlier LLM triage idea.

---

## Configuration surface

Current `.brr/config` keys for shipped envs:

```ini
environment=auto               # docker when configured, otherwise worktree
env=                           # legacy alias
default_env=                   # legacy alias
docker.image=<runner-image>    # required if env=docker is picked
docker.network=bridge
docker.env=KEY1,KEY2           # extra env-var names to pass through
docker.mount_credentials=true  # mount known runner login dirs
```

Absent `environment` / `env` / `default_env` resolves to `auto`.
`DockerEnv.prepare()` raises before invocation when Docker is selected
without the Docker CLI or `docker.image`.

---

## Test shape (per env)

Each env gets the same test shape so the protocol stays observable
from outside:

1. `prepare` returns a usable `RunContext` (dirs exist, branch exists
   if requested; `response_path_env` vs `response_path_host` agrees
   with the table above).
2. `invoke` is called with a stub runner (existing
   `runner.invoke_runner` mocking pattern); stdout/stderr propagate.
3. `finalize` returns the updated `Task` with branch/scratch metadata:
   landed branch, preserved branch, conflict state, or preserved
   container names as applicable.
4. Daemon-level integration: a fake event end-to-end through the env,
   asserting durability artefacts on the host and cleanup of the
   env-private state.

The salvage rule has dedicated coverage on top of that: a task whose
worker errors out leaves the worktree / container scratch intact, and
`task.meta` points at the preserved location. Future script-env,
entry-point, ssh, and devcontainer implementations should add
registry-precedence and integration-gated coverage when they land.

---

## Reference docs

User-facing reference lives in
[`src/brr/docs/envs.md`](../src/brr/docs/envs.md) (when to pick each
env, configuration keys, troubleshooting). The execution map
([`src/brr/docs/execution-map.md`](../src/brr/docs/execution-map.md))
and the internals doc
([`src/brr/docs/brr-internals.md`](../src/brr/docs/brr-internals.md))
point at the same protocol from above.

---

## Env scaffolding (future `brr env init`)

**Not in v1.** Sketched here so the designed script/python plugin path
has a forward once the resolver supports non-built-in envs.

Proposed shape:

```
brr env init <name> --kind=script [--dir=.brr/envs/<name>]
  → Seeds a new script-env directory with:
      prepare, invoke, finalize, validate   (executable bash stubs)
      README.md                              (the protocol reminder)
  → Default target: .brr/envs/<name>/ (per-repo). Use --dir=~/.config/brr/envs/<name> for user-wide.
  → Stubs print the expected JSON shape on stdout and exit 0, so the env is
    runnable before you edit anything once script env dispatch exists.

brr env init <name> --kind=python --pkg=<package>
  → Scaffolds a minimal pyproject.toml + src/<package>/<name>.py with:
      * a class stub implementing the EnvBackend protocol
      * [project.entry-points."brr.envs"] pointing at the class
      * pytest stub mirroring the built-in env test shape
  → Leaves packaging/publishing to the user.
```

Why not v1: the runtime plugin/script dispatcher has not shipped, and
scaffolding it first would commit brr to a specific format before real
third-party envs prove what they need.

Prior art to steal from when this lands: how `brr eject` copies
bundled prompts (see `cli.cmd_eject`) — same pattern, different
source directory.

---

## Boundary

These adjacent concerns sit outside the design on purpose and have
their own homes:

- Concurrent execution — see
  [`design-concurrent-execution.md`](design-concurrent-execution.md);
  env finalization now serialises only on the target branch lock.
- Overlays — see [`plan-overlays.md`](plan-overlays.md).
- `brnrd` — separate project, see
  [`notes-pondering-fleet.md`](notes-pondering-fleet.md).
- Compose-oriented envs like `docker-worktree` — see "Why worktree
  stays a flat env in v1" above.
- First-party plugins (Daytona, Firecracker, E2B) — expected to ship
  outside core if pursued, see
  [`notes-pondering-fleet.md`](notes-pondering-fleet.md) §10.
- Auto-`git push` policy on auto/task branches — the daemon publishes
  branches when a remote is configured; explicit per-branch push
  policy is a follow-up captured alongside the branch-intent design.

## Lineage

Accepted on 2026-05-06 with `host` / `worktree` / `docker` shipped;
the branch-intent rewrite on 2026-05-11 moved finalization to
`branching.BranchPlan`, `gitops.fast_forward_branch`, and
`WorktreeEnv._land_or_preserve` / `DockerEnv.finalize`; the
2026-05-17 source check keeps the page explicit that `ssh`,
`devcontainer`, and plugin/script envs are still design targets rather
than wired runtime backends.
