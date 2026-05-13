# Repo Dive-In Map

This page is the bottom-up navigator for the `brr` repository. Use it
when you need to move from the product shape into source files, tests,
and the subject hubs that explain the current architecture.

Links are relative repository links so they work on GitHub, GitHub
mobile, local editors, and task branches. When this guide says "read",
read the source file and then the matching tests; the tests are often
the most compact behavior spec.

Compressed on 2026-05-13 from an exhaustive file-by-file tour into this
current-state navigator because subject hubs now carry the synthesis and
tests carry the fine-grained behavior.

## Current model

`brr` turns external messages into frontmatter-backed event files,
constructs task files mechanically, resolves branch intent and an
execution environment, runs a configured AI CLI, records every step in a
per-gate-thread conversation log, and delivers the runner's final stdout
back through the originating gate.

```text
gate -> event -> conversation -> task -> env -> runner -> response -> gate
```

Carry these invariants while reading:

- `AGENTS.md` is the universal agent playbook. The canonical copy lives
  at [`src/brr/AGENTS.md`](../src/brr/AGENTS.md) and is symlinked at
  the repo root.
- Task construction is mechanical. There is no LLM triage stage; see
  [`decision-remove-triage.md`](decision-remove-triage.md).
- Conversation logs are routing history, not workstream identity; see
  [`decision-drop-streams.md`](decision-drop-streams.md).
- Branch intent is deterministic setup context, while the agent owns
  runtime branching inside the prepared workspace; see
  [`subject-tasks-branching.md`](subject-tasks-branching.md) and
  [`design-daemon-landing-branch.md`](design-daemon-landing-branch.md).
- Execution isolation is selected through `environment=<auto|host|worktree|docker>`.
  `auto` picks configured Docker first, otherwise a worktree. `host`
  is explicit only.
- Environments implement the `prepare -> invoke -> finalize` protocol;
  see [`subject-envs.md`](subject-envs.md) and
  [`design-env-interface.md`](design-env-interface.md).
- The runner contract is stdout-as-response. `invoke_runner` captures
  stdout and writes `.brr/responses/<event-id>.md`; empty stdout is the
  retry/failure signal.
- Remote gate progress and local status both render from
  `RunProgressView`, derived from conversation update packets.
- `kb/` is durable project knowledge. `.brr/` is runtime state and is
  gitignored.

## Start Here

Read these in order for the fastest useful mental model:

1. [README](../README.md) for the product and CLI surface.
2. [Gate protocol](../src/brr/gates/README.md) for file-based ingress
   and delivery.
3. [Protocol source](../src/brr/protocol.py) with
   [protocol tests](../tests/test_protocol.py).
4. [Task model](../src/brr/task.py) with
   [task tests](../tests/test_task.py).
5. [Conversation log](../src/brr/conversations.py) with
   [conversation tests](../tests/test_conversations.py).
6. [Runner plumbing](../src/brr/runner.py) and
   [prompt assembly](../src/brr/prompts.py), with
   [runner tests](../tests/test_runner.py) and
   [prompt tests](../tests/test_prompts.py).
7. [Environment backends](../src/brr/envs/__init__.py) with
   [env tests](../tests/test_envs.py) and
   [Dockerfile tests](../tests/test_dockerfile.py).
8. [Daemon worker](../src/brr/daemon.py) plus
   [developer reload](../src/brr/dev_reload.py), with
   [daemon tests](../tests/test_daemon.py),
   [developer reload tests](../tests/test_dev_reload.py), and
   [daemon-conversation tests](../tests/test_daemon_conversations.py).
9. [Bundled execution map](../src/brr/docs/execution-map.md) to reread
   the system top-down after seeing the parts.

## Source Rings

### Ring 0: Package Skin

Read:

- [pyproject.toml](../pyproject.toml)
- [README](../README.md)
- [`src/brr/AGENTS.md`](../src/brr/AGENTS.md)
- [`src/brr/__init__.py`](../src/brr/__init__.py)
- [`src/brr/__main__.py`](../src/brr/__main__.py)
- [`src/brr/cli.py`](../src/brr/cli.py)
- [CLI tests](../tests/test_cli.py)

Keep in mind:

- The console script is `brr = brr.cli:main`.
- `python -m brr` delegates to the same CLI.
- The public CLI stays small: `init`, `run`, `auth`, `bind`, `up`,
  `down`, plus status/inspection helpers for troubleshooting.
- `src/brr/AGENTS.md` affects brr itself and every project that runs
  `brr init`.

### Ring 1: Filesystem Atoms

Read:

- [`protocol.py`](../src/brr/protocol.py)
- [`config.py`](../src/brr/config.py)
- [`gitops.py`](../src/brr/gitops.py)
- [`worktree.py`](../src/brr/worktree.py)
- [protocol tests](../tests/test_protocol.py)
- [config tests](../tests/test_config.py)
- [git/worktree tests](../tests/test_gitops.py)

Keep in mind:

- Events are markdown files in `.brr/inbox/`.
- Responses are markdown files in `.brr/responses/`.
- `.brr/config` is a flat key-value file.
- `gitops.shared_brr_dir()` resolves the shared runtime directory from
  linked worktrees.
- Worktrees live under `.brr/worktrees/<task-id>`.

### Ring 2: Durable State

Read:

- [`task.py`](../src/brr/task.py)
- [`conversations.py`](../src/brr/conversations.py)
- [`updates.py`](../src/brr/updates.py)
- [`run_progress.py`](../src/brr/run_progress.py)
- [`run_context.py`](../src/brr/run_context.py)
- [task tests](../tests/test_task.py)
- [conversation tests](../tests/test_conversations.py)
- [run-progress tests](../tests/test_run_progress.py)
- [daemon-conversation tests](../tests/test_daemon_conversations.py)
- [daemon-progress-packet tests](../tests/test_daemon_progress_packets.py)
- [status-troubleshooting tests](../tests/test_status_troubleshooting.py)

Keep in mind:

- `Task` is the central work unit built from an event and config.
- A conversation is an append-only ndjson log keyed by gate thread.
- `UpdatePacket` is lifecycle telemetry, persisted in the conversation
  log and optionally rendered by gates.
- `RunProgressView` is a projection from conversation records; it is
  not persisted state.
- `run_context.py` writes `.brr/runs/<task-id>/context.md` so a runner
  can orient itself without inspecting runtime internals.

### Ring 3: Execution Contract

Read:

- [`runner.py`](../src/brr/runner.py)
- [`prompts.py`](../src/brr/prompts.py)
- [`envs/__init__.py`](../src/brr/envs/__init__.py)
- [`prompts/runners.md`](../src/brr/prompts/runners.md)
- [`prompts/run.md`](../src/brr/prompts/run.md)
- [`prompts/kb-maintenance.md`](../src/brr/prompts/kb-maintenance.md)
- [`kb_preflight.py`](../src/brr/kb_preflight.py)
- [runner tests](../tests/test_runner.py)
- [prompt tests](../tests/test_prompts.py)
- [env tests](../tests/test_envs.py)
- [Dockerfile tests](../tests/test_dockerfile.py)
- [kb-preflight tests](../tests/test_kb_preflight.py)

Keep in mind:

- `RunnerInvocation` describes one external AI CLI call.
- `RunnerResult.validation_ok` combines subprocess success, required
  artifact checks, and non-empty stdout when a response path is set.
- `RunContext` carries both host-visible and environment-visible
  response paths so Docker can mount the repo correctly.
- Docker forwards known runner credentials, mounts common login dirs
  under `/brr-home`, runs as the host UID, and injects git
  `safe.directory='*'`.
- `kb_preflight.scan` is deterministic; the LLM maintenance prompt is
  only the synthesis-heavy redundancy pass.

### Ring 4: Orchestration Spine

Read:

- [`daemon.py`](../src/brr/daemon.py)
- [`dev_reload.py`](../src/brr/dev_reload.py)
- [daemon tests](../tests/test_daemon.py)
- [developer reload tests](../tests/test_dev_reload.py)
- [daemon-conversation tests](../tests/test_daemon_conversations.py)

Read `_run_worker()` in lifecycle passes:

1. resolve the event to a conversation key;
2. append event arrival and progress packets;
3. build and persist the mechanical task;
4. resolve branch intent and environment policy;
5. prepare the env and write run context;
6. assemble the daemon prompt;
7. invoke the runner, retrying on empty stdout;
8. run kb preflight and the optional maintenance pass;
9. finalize the env and record branch/worktree outcome;
10. mark the event terminal and push the branch that changed.

The daemon is serial in v1: one pending event, one active task, one
response, one finalize path.

### Ring 5: Edges and Operator Views

Read:

- [`gates/__init__.py`](../src/brr/gates/__init__.py)
- [`gates/telegram.py`](../src/brr/gates/telegram.py)
- [`gates/slack.py`](../src/brr/gates/slack.py)
- [`gates/git_gate.py`](../src/brr/gates/git_gate.py)
- [`status.py`](../src/brr/status.py)
- [`docs/__init__.py`](../src/brr/docs/__init__.py)
- [`docs/brr-internals.md`](../src/brr/docs/brr-internals.md)
- [`docs/conversations.md`](../src/brr/docs/conversations.md)
- [`docs/active-task.md`](../src/brr/docs/active-task.md)
- [`docs/envs.md`](../src/brr/docs/envs.md)
- [`docs/execution-map.md`](../src/brr/docs/execution-map.md)
- [Telegram gate tests](../tests/test_telegram_gate.py)
- [gate setup tests](../tests/test_gate_setup.py)
- [Telegram render-update tests](../tests/test_telegram_render_update.py)
- [Slack render-update tests](../tests/test_slack_render_update.py)
- [status-troubleshooting tests](../tests/test_status_troubleshooting.py)
- [docs tests](../tests/test_docs.py)

Keep in mind:

- Gates are transport adapters. They create events, render progress
  when they opt into `render_update`, and deliver responses.
- Telegram and Slack render per-task progress cards from
  `RunProgressView`; Git deliberately does not try to be a live UX.
- `status.py` is troubleshooting, not the primary progress surface.
- Bundled docs live in `src/brr/docs/`; durable project knowledge lives
  in `kb/`; runtime overrides live under `.brr/docs/`.

## Entity Map

| Entity | Source | Persistence | Read With |
| ------ | ------ | ----------- | --------- |
| Event | [`protocol.py`](../src/brr/protocol.py) | `.brr/inbox/<event-id>.md` | [protocol tests](../tests/test_protocol.py), gate tests |
| Task | [`task.py`](../src/brr/task.py) | `.brr/tasks/<task-id>.md` | [task tests](../tests/test_task.py), [daemon tests](../tests/test_daemon.py) |
| Conversation log | [`conversations.py`](../src/brr/conversations.py) | `.brr/conversations/<safe-key>.ndjson` | [conversation tests](../tests/test_conversations.py), [conversations doc](../src/brr/docs/conversations.md) |
| UpdatePacket | [`updates.py`](../src/brr/updates.py) | conversation `kind=update` records | daemon progress and gate render tests |
| RunProgressView | [`run_progress.py`](../src/brr/run_progress.py) | derived on demand | [run-progress tests](../tests/test_run_progress.py), gate render tests |
| RunnerInvocation / RunnerResult | [`runner.py`](../src/brr/runner.py) | optional `.brr/traces/` records | [runner tests](../tests/test_runner.py) |
| RunContext | [`run_context.py`](../src/brr/run_context.py), [`envs/__init__.py`](../src/brr/envs/__init__.py) | `.brr/runs/<task-id>/context.md` | daemon/env tests |
| EnvBackend | [`envs/__init__.py`](../src/brr/envs/__init__.py) | branch refs, response path, optional preserved scratch | [env tests](../tests/test_envs.py), [env design](design-env-interface.md) |
| Gate module | [`gates/`](../src/brr/gates/) | gate-specific runtime files under `.brr/gates/` | gate protocol and gate tests |

## Module Map

| Area | Primary Files | Notes |
| ---- | ------------- | ----- |
| Entry and commands | [`__main__.py`](../src/brr/__main__.py), [`cli.py`](../src/brr/cli.py) | `cli.py` dispatches to adoption, direct runs, daemon control, and gate setup. |
| Bootstrap | [`adopt.py`](../src/brr/adopt.py), [`config.py`](../src/brr/config.py), [`gitops.py`](../src/brr/gitops.py) | `brr init` writes repo setup and invokes the runner with required artifacts. |
| File protocol | [`protocol.py`](../src/brr/protocol.py) | Shared by gates, daemon, task parsing, runner profile parsing, and status recovery. |
| Task and conversations | [`task.py`](../src/brr/task.py), [`conversations.py`](../src/brr/conversations.py), [`updates.py`](../src/brr/updates.py), [`run_progress.py`](../src/brr/run_progress.py) | Keep "unit of work", "thread history", "packet", and "renderable view" separate. |
| Runner and prompts | [`runner.py`](../src/brr/runner.py), [`prompts.py`](../src/brr/prompts.py), [`kb_preflight.py`](../src/brr/kb_preflight.py) | Subprocess execution, prompt assembly, and deterministic kb scan are separate modules. |
| Environments | [`envs/__init__.py`](../src/brr/envs/__init__.py), [`branching.py`](../src/brr/branching.py), [`worktree.py`](../src/brr/worktree.py), [`gitops.py`](../src/brr/gitops.py) | Host, worktree, and Docker share the same env protocol and branch plan. |
| Daemon | [`daemon.py`](../src/brr/daemon.py), [`dev_reload.py`](../src/brr/dev_reload.py) | Main integration point: PID file, gates, inbox scan, task execution, kb maintenance, finalize, push, optional re-exec. |
| Gates and views | [`gates/`](../src/brr/gates/), [`status.py`](../src/brr/status.py), [`docs/`](../src/brr/docs/) | Gate progress and local status share `RunProgressView`; docs ship as package data. |

## Runtime Invariants

### `.brr/` Is Runtime State

Runtime files live in `.brr/` and are gitignored: inbox events,
responses, tasks, runs, conversations, traces, reviews, worktrees, gate
state, prompt overrides, doc overrides, and config.

### `kb/` Is Durable Project Knowledge

Repo-specific decisions, research, plans, subject hubs, and the curated
chronological log live in `kb/`. Do not put per-task scratch there.

### `src/brr/docs/` Is Bundled Tool Documentation

Bundled docs are package data and can be overridden per repo by
`.brr/docs/<topic>.md`. The decision is
[`decision-bundled-docs.md`](decision-bundled-docs.md).

### Runner Success Has Three Layers

`RunnerResult.validation_ok` means: subprocess exit zero, all required
artifacts present, and non-empty stdout when a response path is set.
Daemon runs use stdout as the response and retry on empty stdout.

### Tasks Are Mechanical

`Task.from_event` builds directly from the inbox event and config. There
is no triage prompt, `needs_context` status, or frontmatter contract on
response files.

### Agents Own Runtime Branching

Worktree and Docker tasks start on a fresh `brr/<task-id>` branch from
the resolved seed ref. The agent can stay there, switch branches, or
make no commit for read-only work. Finalization reads git state and
either fast-forwards an explicit auto-land target or preserves/pushes
the branch for human routing.

### Environments Are the Isolation Knob

Use `environment=auto`, `host`, `worktree`, or `docker`. The resolved
backend is stored as task `env`; runtime branch facts land in
`task.meta`.

### Conversations Are Not KB

Conversation logs are append-only runtime coordination. Durable lessons,
architecture, and decisions belong in `kb/`.

### Progress Is a Projection

`RunProgressView` is derived from conversation update packets. New live
UX should extend `updates.py` and `run_progress.py`, not build parallel
per-gate state machines.

### KB Consistency Is Preflight Plus Redundancy

`kb_preflight.scan` catches structural problems. The LLM cleanup pass
handles synthesis-heavy drift and only runs when findings exist or
`kb/` changed.

### Status Is Troubleshooting

Remote gates are the primary progress surface. `status.py` answers
"what is running and where do I inspect it?" after something needs
operator attention.

## Tests as a Second Reading Path

If source-first reading feels too abstract, read tests in dependency
order:

1. [protocol tests](../tests/test_protocol.py)
2. [task tests](../tests/test_task.py)
3. [conversation tests](../tests/test_conversations.py)
4. [run-progress tests](../tests/test_run_progress.py)
5. [runner tests](../tests/test_runner.py)
6. [prompt tests](../tests/test_prompts.py)
7. [git/worktree tests](../tests/test_gitops.py)
8. [env tests](../tests/test_envs.py)
9. [Dockerfile tests](../tests/test_dockerfile.py)
10. [kb-preflight tests](../tests/test_kb_preflight.py)
11. [daemon tests](../tests/test_daemon.py)
12. [daemon-conversation tests](../tests/test_daemon_conversations.py)
13. [daemon-progress-packet tests](../tests/test_daemon_progress_packets.py)
14. [gate tests](../tests/test_telegram_gate.py)
15. [gate setup tests](../tests/test_gate_setup.py)
16. [Telegram render-update tests](../tests/test_telegram_render_update.py)
17. [Slack render-update tests](../tests/test_slack_render_update.py)
18. [status-troubleshooting tests](../tests/test_status_troubleshooting.py)
19. [adopt tests](../tests/test_adopt.py)
20. [integration tests](../tests/test_integration.py)
21. [CLI tests](../tests/test_cli.py)
22. [docs tests](../tests/test_docs.py)

## Design Reading

Read source first, then these pages for why the current shape exists:

- [`subject-daemon.md`](subject-daemon.md) for the foreground process,
  gate/file-protocol boundary, worker lifecycle, local process control,
  and developer reload.
- [`subject-envs.md`](subject-envs.md) for the env protocol,
  durability contract, and salvage rule.
- [`subject-tasks-branching.md`](subject-tasks-branching.md) for
  task construction, branch intent, and landing behavior.
- [`subject-kb.md`](subject-kb.md) for the knowledge-base pattern.
- [`subject-fleet-overlays.md`](subject-fleet-overlays.md) for the
  paused fleet/overlay roadmap and how it relates to env work.
- [`decision-remove-triage.md`](decision-remove-triage.md),
  [`decision-drop-streams.md`](decision-drop-streams.md), and
  [`decision-kb-shape.md`](decision-kb-shape.md) for the simplification
  decisions that removed noisy abstractions.
- [`design-env-interface.md`](design-env-interface.md),
  [`design-daemon-landing-branch.md`](design-daemon-landing-branch.md),
  [`design-task-file-ingress.md`](design-task-file-ingress.md), and
  [`design-daemon-dev-reload.md`](design-daemon-dev-reload.md) for
  active or shipped design details.
- [`deck-brr-fleet-steering.md`](deck-brr-fleet-steering.md) and
  [`plan-overlays.md`](plan-overlays.md) for the strategic overlay and
  fleet direction, with lifecycle markers respected.
- [`research-runner-context-ergonomics-2026-05-09.md`](research-runner-context-ergonomics-2026-05-09.md),
  [`research-branch-plan-simplification-2026-05-12.md`](research-branch-plan-simplification-2026-05-12.md),
  and [`research-brr-vs-gh-aw.md`](research-brr-vs-gh-aw.md) for
  point-in-time research receipts.

## Practical Navigator Notes

- Event files: start with [`protocol.py`](../src/brr/protocol.py).
- Task state or environment resolution: start with
  [`task.py`](../src/brr/task.py).
- Branching: start with [`subject-tasks-branching.md`](subject-tasks-branching.md),
  then [`branching.py`](../src/brr/branching.py), [`worktree.py`](../src/brr/worktree.py),
  and `WorktreeEnv`.
- Thread continuity: start with
  [`conversations.py`](../src/brr/conversations.py).
- Lifecycle packets: start with [`updates.py`](../src/brr/updates.py).
- Progress rendering: start with
  [`run_progress.py`](../src/brr/run_progress.py).
- Prompt assembly: start with [`prompts.py`](../src/brr/prompts.py).
- Subprocess execution: start with [`runner.py`](../src/brr/runner.py).
- Daemon lifecycle or reload: start with
  [`subject-daemon.md`](subject-daemon.md), then
  [`daemon.py`](../src/brr/daemon.py) and
  [`dev_reload.py`](../src/brr/dev_reload.py).
- KB consistency: start with [`subject-kb.md`](subject-kb.md),
  [`kb_preflight.py`](../src/brr/kb_preflight.py), and
  [`prompts/kb-maintenance.md`](../src/brr/prompts/kb-maintenance.md).
- Transport, auth, polling, or delivery: start with
  [`gates/`](../src/brr/gates/).

## Maintenance Rule

Update this page when public CLI commands, file formats, env backends,
daemon lifecycle, runner contracts, gate hooks, bundled-doc ownership,
kb consistency rules, major module boundaries, subject hubs, or primary
behavioral tests change.
