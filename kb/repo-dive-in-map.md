# Repo Dive-In Map

Compact source map for understanding `brr` without re-reading every
module at once. This page points to the source and tests that define
current behavior; deeper rationale lives in the linked subject hubs,
decisions, designs, and research pages.

## Reading Contract

Use this page as a navigator, not as an alternate implementation
reference. For any behavior-sensitive change, read the linked source
file and its tests before editing.

The durable reading pattern is:

```text
product surface -> file protocol -> task + branch + env state ->
runner/prompt contract -> daemon orchestration -> gates -> kb tooling
```

The runtime path is:

```text
gate -> event -> conversation -> task -> env -> runner -> response -> gate
```

## Current Snapshot

- Public CLI commands are `init`, `run`, `auth`, `bind`, `setup`, `up`,
  and `down`; removed diagnostic commands are covered by
  [CLI tests](../tests/test_cli.py).
- Built-in daemon gates are `telegram`, `slack`, and `github`
  (`daemon._BUILTIN_GATES`). CLI gate commands load modules by name
  through [`gates.import_gate`](../src/brr/gates/__init__.py).
- Events and responses are markdown files with restricted
  frontmatter parsing from [`protocol.py`](../src/brr/protocol.py);
  no PyYAML or runtime dependency is involved.
- `Task.from_event` builds tasks mechanically. There is no LLM triage
  step and no response frontmatter contract; see
  [`decision-remove-triage.md`](decision-remove-triage.md).
- User-facing environment policy is `environment=<auto|host|worktree|docker>`.
  Legacy `env` and `default_env` still work as aliases. `auto` picks
  Docker only when `docker.image` is configured, otherwise `worktree`;
  `host` is explicit only.
- Built-in environment backends are `host`, `worktree`, and `docker`.
  The task resolver accepts future names syntactically, but
  [`envs.get_env`](../src/brr/envs/__init__.py) rejects unavailable
  backends with the supported list.
- Branch intent is deterministic daemon state. Structured event fields
  (`branch_target`, `target_branch`, `base_branch`, legacy `branch`)
  create a [`BranchPlan`](../src/brr/branching.py). The worker agent
  still owns runtime `git switch` / commit choices inside the worktree.
- Event-named branches seed from `<remote>/<target>` when that remote
  tracking ref exists, so PR/comment work starts from forge-visible
  state even if the host's local branch diverged. `branch.fallback=current`
  remains host-branch self-development mode and does not prefer remote.
- Before branch planning, the daemon calls
  [`sync.refresh_before_task`](../src/brr/sync.py): one fetch plus
  best-effort ff-only refresh of the default branch and any structured
  event branch. Sync failures never block execution.
- The daemon uses a bounded `ThreadPoolExecutor` (`max_workers=2` by
  default). Shared runtime state is partitioned per event, task, or
  branch; only auto-land fast-forward and push take per-branch locks.
- Progress is emitted as [`UpdatePacket`](../src/brr/updates.py)
  records, folded by [`run_progress.py`](../src/brr/run_progress.py),
  and rendered by gates that expose `render_update`. Telegram and
  Slack edit chat cards; GitHub creates or edits a progress comment on
  the originating issue or PR.
- The kb is durable project memory. Deterministic checks live in
  [`kb_preflight.py`](../src/brr/kb_preflight.py); graph stats live in
  [`kb_health.py`](../src/brr/kb_health.py); the cross-tool schema
  lives in [`AGENTS.md`](../AGENTS.md) and
  [`decision-kb-shape.md`](decision-kb-shape.md).

## Fast Reading Path

Read in this order for the shortest useful model:

1. [README](../README.md) for user-facing shape and install/run
   commands.
2. [Gate protocol](../src/brr/gates/README.md) for the file boundary
   between gates and the daemon.
3. [Protocol source](../src/brr/protocol.py) with
   [protocol tests](../tests/test_protocol.py).
4. [Task source](../src/brr/task.py),
   [branching source](../src/brr/branching.py), and their tests:
   [task](../tests/test_task.py), [branching](../tests/test_branching.py).
5. [Conversation source](../src/brr/conversations.py),
   [updates](../src/brr/updates.py), and
   [run progress](../src/brr/run_progress.py), with
   [conversation tests](../tests/test_conversations.py) and
   [run-progress tests](../tests/test_run_progress.py).
6. [Runner](../src/brr/runner.py) and
   [prompts](../src/brr/prompts.py), with
   [runner tests](../tests/test_runner.py) and
   [prompt tests](../tests/test_prompts.py).
7. [Environment backends](../src/brr/envs/__init__.py), with
   [env tests](../tests/test_envs.py) and
   [Dockerfile tests](../tests/test_dockerfile.py).
8. [Daemon](../src/brr/daemon.py),
   [sync](../src/brr/sync.py),
   [forges](../src/brr/forges.py), and
   [dev reload](../src/brr/dev_reload.py), with the daemon, sync,
   forge, heartbeat, concurrency, and dev-reload tests.
9. [Bundled execution map](../src/brr/docs/execution-map.md) to
   re-read the system top-down after seeing the parts.

## Source Map

### Package Skin

Start here when changing public entry points:

- [`pyproject.toml`](../pyproject.toml) defines package metadata,
  console script, and dev dependency on pytest.
- [`src/brr/__main__.py`](../src/brr/__main__.py) delegates
  `python -m brr` to the CLI.
- [`src/brr/cli.py`](../src/brr/cli.py) is the thin dispatch layer.
- [`src/brr/AGENTS.md`](../src/brr/AGENTS.md) is the canonical
  playbook template; root [`AGENTS.md`](../AGENTS.md) is the repo copy.

Tests: [CLI tests](../tests/test_cli.py),
[docs tests](../tests/test_docs.py).

### File Protocol And Config

Read these before touching event/task persistence:

- [`protocol.py`](../src/brr/protocol.py) owns markdown frontmatter
  parsing/writing, event creation, pending/done scans, response reads,
  and status updates.
- [`config.py`](../src/brr/config.py) owns the flat `.brr/config`
  key-value format.
- [`gitops.py`](../src/brr/gitops.py) wraps the git observations and
  mutations shared by branch, worktree, daemon, sync, and forge code.
- [`worktree.py`](../src/brr/worktree.py) creates/removes task
  worktrees and answers branch/commit/dirty-state questions.

Tests: [protocol](../tests/test_protocol.py),
[config](../tests/test_config.py),
[git/worktree](../tests/test_gitops.py).

### Task, Branch, And Conversation State

- [`task.py`](../src/brr/task.py) defines `Task`, mechanical
  `Task.from_event`, and `resolve_env`.
- [`branching.py`](../src/brr/branching.py) defines `BranchPlan`,
  structured event branch keys, fallback policy, remote-preferring
  event branch seeds, and task metadata rendering.
- [`conversations.py`](../src/brr/conversations.py) stores one
  append-only jsonl per event pipeline under
  `.brr/conversations/<safe-key>/<event-id>.jsonl`.
- [`updates.py`](../src/brr/updates.py) defines stable lifecycle packet
  types and dispatches packets to console plus gate renderers.
- [`run_progress.py`](../src/brr/run_progress.py) projects
  conversation records into gate/operator views.
- [`run_context.py`](../src/brr/run_context.py) writes the per-task
  recovery document under `.brr/runs/<task-id>/context.md`.

Tests: [task](../tests/test_task.py),
[branching](../tests/test_branching.py),
[conversation](../tests/test_conversations.py),
[daemon conversation](../tests/test_daemon_conversations.py),
[run progress](../tests/test_run_progress.py),
[daemon progress packets](../tests/test_daemon_progress_packets.py).

### Runner And Prompt Contract

- [`runner.py`](../src/brr/runner.py) owns runner profile detection,
  command construction, subprocess execution, trace writing, and the
  direct `brr run` path.
- [`prompts.py`](../src/brr/prompts.py) owns bundled prompt loading,
  `.brr/prompts/<name>.md` overrides, AGENTS.md injection, recent
  conversation rendering, and builders for setup/run/daemon/kb
  maintenance prompts.
- [`src/brr/prompts/run.md`](../src/brr/prompts/run.md) is the
  daemon task prompt template. Its Task Context Bundle is the hot
  path for brr-launched workers.
- [`src/brr/prompts/kb-maintenance.md`](../src/brr/prompts/kb-maintenance.md)
  is the thin kb redundancy pass. It defers the rules to AGENTS.md.

The runner contract is stdout-as-response. `RunnerResult.validation_ok`
combines subprocess success, required artifact presence, and non-empty
stdout when a response path is expected. Daemon retries trigger on
empty stdout.

Tests: [runner](../tests/test_runner.py),
[prompts](../tests/test_prompts.py).

### Environments

[`envs/__init__.py`](../src/brr/envs/__init__.py) contains the
`EnvBackend` protocol and built-ins:

- `HostEnv` runs in the main checkout and finalizes as a no-op.
- `WorktreeEnv` creates `.brr/worktrees/<task-id>` on `brr/<task-id>`
  from the resolved seed ref, then either fast-forwards an explicit
  auto-land target or preserves/pushes the branch.
- `DockerEnv` uses worktree semantics plus `docker run`. It requires
  the Docker CLI and `docker.image`, bind-mounts the repo, runs as the
  host UID, sets `HOME=/brr-home`, forwards configured credentials,
  injects git `safe.directory=*`, and preserves containers on error
  for salvage.

Outcome-aware cleanup is shared: clean success removes scratch when
there are no uncommitted files; `error`, `conflict`, or dirty state
keeps the worktree/container metadata visible.

Tests: [env](../tests/test_envs.py),
[Dockerfile](../tests/test_dockerfile.py).
User docs: [envs](../src/brr/docs/envs.md).

### Daemon Spine

[`daemon.py`](../src/brr/daemon.py) owns the event-to-response
lifecycle:

1. Load config, PID state, gates, and optional dev-reload watcher.
2. Poll configured gates and inbox events.
3. Derive conversation key and per-worker emitter.
4. Run `sync.refresh_before_task`.
5. Resolve `BranchPlan`.
6. Append event/task records and progress packets.
7. Build `Task` and prepare the selected environment.
8. Write run context and build daemon prompt.
9. Invoke runner with heartbeat packets and empty-stdout retries.
10. Run kb preflight/health and, when needed, the kb-maintenance pass.
11. Finalize environment.
12. Push the final branch when publishable and attach forge view URLs
    to `push_done` packets when derivable.

Related modules:

- [`sync.py`](../src/brr/sync.py) performs pre-task fetch + ff-only
  refresh and returns a non-raising `SyncResult`.
- [`forges.py`](../src/brr/forges.py) turns remote URLs into branch
  view URLs for GitHub, GitLab, Bitbucket, Gitea/Forgejo, or configured
  forge overrides.
- [`dev_reload.py`](../src/brr/dev_reload.py) implements opt-in
  quiescent daemon re-exec for brr self-development.

Tests: [daemon](../tests/test_daemon.py),
[daemon heartbeat](../tests/test_daemon_heartbeat.py),
[daemon concurrency](../tests/test_daemon_concurrency.py),
[sync](../tests/test_sync.py),
[forges](../tests/test_forges.py),
[dev reload](../tests/test_dev_reload.py).

### Gates And Operator Views

Core gate surface:

- [`gates/__init__.py`](../src/brr/gates/__init__.py) provides
  event/response helpers and dynamic built-in imports.
- [`gates/telegram.py`](../src/brr/gates/telegram.py) polls Telegram,
  creates events, delivers responses, and edits live progress cards.
- [`gates/slack.py`](../src/brr/gates/slack.py) does the same for
  Slack channels/threads.
- [`gates/github.py`](../src/brr/gates/github.py) polls GitHub using
  stdlib `urllib`, supports label, mention, and any-activity triggers,
  posts responses as issue/PR comments, passes PR head branches as
  `branch_target`, and maintains a progress comment through
  `render_update`.

Gate renderers consume `run_progress`; they should not reconstruct
task state directly from raw conversation rows. Gate-side failures are
swallowed after the packet has been persisted, so progress rendering
cannot break task execution.

Tests: [Telegram gate](../tests/test_telegram_gate.py),
[Telegram render-update](../tests/test_telegram_render_update.py),
[Slack render-update](../tests/test_slack_render_update.py),
[GitHub gate](../tests/test_github_gate.py),
[gate setup](../tests/test_gate_setup.py).

### Bundled Docs And KB Tooling

Bundled tool documentation lives in [`src/brr/docs/`](../src/brr/docs/)
and ships with the package:

- [brr internals](../src/brr/docs/brr-internals.md)
- [active task](../src/brr/docs/active-task.md)
- [conversations](../src/brr/docs/conversations.md)
- [envs](../src/brr/docs/envs.md)
- [execution map](../src/brr/docs/execution-map.md)

Repo-specific durable knowledge lives in `kb/`:

- [`kb_preflight.py`](../src/brr/kb_preflight.py) checks index
  coverage, broken links, missing status markers, oversized pages,
  revision-heavy pages, hub coverage, and proposal scaffolding.
- [`kb_health.py`](../src/brr/kb_health.py) reports graph stats:
  page counts by kind, largest pages, peer in-degree, peer orphans,
  and log size.
- [`kb/log.md`](log.md) is the curated chronological narrative.
- Subject hubs and decision/design/research pages describe current
  state and rationale.

Tests: [kb preflight](../tests/test_kb_preflight.py),
[kb health](../tests/test_kb_health.py).

## Core Entities

| Entity | Source | Durable location | Current rule |
| --- | --- | --- | --- |
| Event | [`protocol.py`](../src/brr/protocol.py) | `.brr/inbox/<event-id>.md` | Gate-created markdown with frontmatter and body. |
| Task | [`task.py`](../src/brr/task.py) | `.brr/tasks/<task-id>.md` | Built mechanically from event + config; concrete backend stored as `env`. |
| BranchPlan | [`branching.py`](../src/brr/branching.py) | Task metadata | Names `seed_ref`, optional `auto_land_branch`, source, host branch, and expected old oid. |
| RunContext | [`run_context.py`](../src/brr/run_context.py) | `.brr/runs/<task-id>/context.md` | Recovery detail for agents; Task Context Bundle remains the daemon hot path. |
| Conversation log | [`conversations.py`](../src/brr/conversations.py) | `.brr/conversations/<key>/<event-id>.jsonl` | Runtime history, not durable project knowledge. |
| UpdatePacket | [`updates.py`](../src/brr/updates.py) | Conversation update rows | Stable lifecycle packet vocabulary for console and gate renderers. |
| RunProgressView | [`run_progress.py`](../src/brr/run_progress.py) | Derived on demand | Projection of update records for cards/comments/diagnostics. |
| EnvBackend | [`envs/__init__.py`](../src/brr/envs/__init__.py) | Task metadata + scratch dirs | Three-phase `prepare -> invoke -> finalize`. |
| Gate module | [`gates/`](../src/brr/gates/) | `.brr/gates/...` runtime state | Transport adapter: create events, deliver responses, optionally render progress. |

## Runtime Invariants

### Runtime State Is Under `.brr/`

`.brr/` is gitignored runtime state: inbox, responses, tasks, runs,
conversations, traces, gate state, prompt/doc overrides, config, and
worktrees. Do not commit it.

### Durable Knowledge Is Under `kb/`

The kb records current state, decisions, research, and curated history.
Subject/design/decision pages should read as synthesis, not a running
diff. Chronology belongs in [`kb/log.md`](log.md).

### Task Construction Is Mechanical

The daemon does not ask an LLM how to classify incoming work. It builds
one task per event and performs one runner invocation per attempt.
`decision-remove-triage.md` explains the removed triage surface.

### Environment Policy Is Deterministic

`resolve_env` maps `auto` to Docker when configured, otherwise
`worktree`; explicit `host`, `worktree`, and `docker` policies are
honored as written. Future environment names can appear in config or
events, but unavailable backends fail at `get_env`.

### Branching Splits Daemon Safety From Agent Choice

The daemon resolves where to start and whether an auto-land
fast-forward is allowed. The agent can still stay on `brr/<task-id>` or
switch to another branch inside the worktree. `WorktreeEnv.finalize`
observes the final git state instead of trusting a frozen task field.

### Freshness Is Best-Effort

`sync.refresh_before_task` never raises into task execution. Fetch,
ff-only success, skipped branches, and errors surface through
`SyncResult` and the `synced` packet. Event branch plans prefer the
remote tracking ref when available; host-current fallback remains local
by design.

### Runner Success Has Three Layers

`RunnerResult.validation_ok` means subprocess exit zero, required
artifacts exist, and stdout is non-empty when a response path is
expected. brr writes the response file from stdout.

### Progress Is A Projection

Conversation update rows are the source of truth. Gate cards/comments
come from `run_progress.project_task`, not from gate-local parsing of
daemon internals. Adding lifecycle UX means adding/handling packet
types, then extending the projection.

### Concurrency Is Partitioned

Every worker owns its event pipeline: one conversation jsonl, one task
branch, one worktree, one trace area, and one gate progress-state file.
The only shared git refs are auto-land targets and pushed branches, both
guarded by per-branch locks.

### KB Maintenance Is A Safety Net

After a successful task, the daemon scans kb structure and graph shape.
The LLM maintenance pass runs only when preflight has findings or the
task touched kb/AGENTS.md. Leftover kb edits become a single maintenance
commit scoped to kb and playbook files.

## Rationale Trail

Start with subject hubs when entering an area:

- [the kb itself](subject-kb.md)
- [daemon and process lifecycle](subject-daemon.md)
- [tasks and branching](subject-tasks-branching.md)
- [environments](subject-envs.md)
- [fleet and overlays](subject-fleet-overlays.md)

Read these decisions for the major simplifications:

- [Remove triage](decision-remove-triage.md)
- [Drop streams](decision-drop-streams.md)
- [kb shape](decision-kb-shape.md)
- [Bundled docs location](decision-bundled-docs.md)

Read these designs for current contracts:

- [Env protocol](design-env-interface.md)
- [Daemon branch intent](design-daemon-landing-branch.md)
- [Git layer rework](design-git-layer-rework.md)
- [Developer daemon reload](design-daemon-dev-reload.md)
- [Concurrent execution](design-concurrent-execution.md)

Plans and research worth knowing:

- [State-first kb maintenance](plan-kb-state-first-maintenance.md)
- [Agent orientation layering](plan-agent-orientation-layering.md)
- [Concurrent worktrees](plan-concurrent-worktrees.md) is superseded by
  concurrent execution but still useful for abandoned merge-coordinator
  reasoning.
- [Branch modes](plan-branch-modes.md) is shipped with revisions.
- [Overlays](plan-overlays.md) and [fleet pondering](notes-pondering-fleet.md)
  are paused.
- [Cursor orientation ergonomics](research-cursor-orientation-ergonomics-2026-05-16.md)
  and its [follow-up](research-cursor-orientation-ergonomics-followup-2026-05-16.md)
  explain why this page stays compact.
- [Runner orientation ergonomics](research-runner-orientation-ergonomics-2026-05-16.md)
  covers daemon-launched context shape.
- [Test suite grooming](research-test-suite-grooming-2026-05-16.md)
  maps shared test scaffolding in [`tests/_helpers.py`](../tests/_helpers.py).
- [Branch plan simplification](research-branch-plan-simplification-2026-05-12.md)
  explains the current seed/auto-land contract.
- [brr vs gh-aw](research-brr-vs-gh-aw.md) is the external workflow
  comparison.

## Maintenance Triggers

Update this page when any of these change:

- public CLI commands
- event/task/conversation file formats
- supported built-in gates or gate hooks
- environment backends or environment resolution
- branch-plan fields, structured branch keys, or fallback policy
- daemon sync, finalization, push, forge, or concurrency behavior
- lifecycle packet types or run-progress projection fields
- runner response/artifact validation
- bundled docs vs kb ownership
- kb preflight/health invariants
- source/test files that become the best reading path for an area
