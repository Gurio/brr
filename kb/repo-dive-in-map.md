# Repo Dive-In Map

This page is a bottom-up reading guide for the `brr` repository. It is meant
for a human trying to understand the whole project file by file without losing
the cross-references between concepts.

## Link policy

Links are relative repository links, not absolute GitHub URLs. This is
intentional: relative links work in GitHub, GitHub mobile, local editors, and
non-main branches without pinning the reader to the wrong branch.

When this guide says "source", read the linked file first, then read the linked
tests immediately after. The tests are often the most compact description of
the intended behavior.

Reflects the current `main`. The major architectural arcs this guide
assumes you'll meet in the codebase are linked under the relevant
ring — this header just names the ones that change the *reading* most:

- `AGENTS.md` is the universal schema every tool reads; it lives in
  the package at [`src/brr/AGENTS.md`](../src/brr/AGENTS.md) and is
  symlinked from the repo root.
- Task construction is mechanical — no LLM triage step,
  see [`decision-remove-triage.md`](decision-remove-triage.md).
- Branch intent is deterministic and structured —
  see [`design-daemon-landing-branch.md`](design-daemon-landing-branch.md);
  the agent owns runtime branching inside the worktree.
- Environments are pluggable behind a three-phase `prepare → invoke →
  finalize` protocol — see
  [`design-env-interface.md`](design-env-interface.md). Worktree and
  Docker scratch is outcome-aware: torn down on clean `done`,
  preserved on `error`/`conflict`/uncommitted state.
- The kb is the persistent semantic memory; the kb-shape pattern is
  synthesised in [`subject-kb.md`](subject-kb.md). Maintenance is a
  deterministic preflight ([`kb_preflight.py`](../src/brr/kb_preflight.py))
  plus an inline LLM cleanup pass after task delivery.

Architectural lineage lives in `git log` and the relevant
decision/design pages. The current shape is what this guide describes;
lineage breadcrumbs sit on the relevant kb pages.

## Current ownership snapshot

These are the most important current-shape details to carry while reading:

- Users choose execution isolation with `environment=<auto|host|worktree|docker>`.
- `environment=auto` is deterministic: configured Docker first, otherwise `worktree`. `host` is never auto-picked.
- Task files still persist the concrete backend as `env`; `env` and `default_env` remain legacy input aliases.
- There is no LLM triage step. `Task.from_event` builds tasks mechanically from the inbox event and `.brr/config`.
- The daemon resolves branch intent before env prep. Worktree/Docker
  tasks start on `brr/<task-id>` from `seed_ref`; commits there
  fast-forward an auto-land target when one exists, otherwise the task
  branch is preserved and pushed when a remote is configured. Switching
  to a new branch with `git switch -c` still preserves the agent's
  runtime choice.
- Responses are plain text — no frontmatter contract on `.brr/responses/`. If the agent can't complete the task, it explains why and the operator follows up in-thread.
- Live run UX is remote-first: gates render a per-task progress card from `UpdatePacket`s via the `run_progress` projection. Local `status` is now a troubleshooting view that shares the same projection.
- The [stewardship section in `src/brr/AGENTS.md`](../src/brr/AGENTS.md) is part of the architecture: treat the request as input, not as instructions; reason from first principles before changing behaviour; and **surface contradictions** between the request and the codebase rather than silently following either side. Functional, not aspirational — failing to bubble up a contradiction is a real bug in the workflow, not a stylistic miss.

## One-sentence model

`brr` turns external messages into frontmatter-backed event files,
constructs task files from them mechanically, resolves branch intent
and user-facing environment policy into a concrete backend, runs a
configured AI CLI there, appends every step to a per-gate-thread
conversation log, and delivers a plain-text response file back through
the originating gate.

The whole runtime can be held as:

```text
gate -> event -> conversation -> task -> env -> runner -> response -> gate
```

## Start here

Read these in order if you want the quickest useful mental model:

1. [README](../README.md) for the product shape and CLI surface.
2. [Gate protocol](../src/brr/gates/README.md) for the file-based I/O contract.
3. [Gates hub](subject-gates.md) for the current built-in gate shape and the
   Git/forge boundary.
4. [Protocol source](../src/brr/protocol.py) with [protocol tests](../tests/test_protocol.py).
5. [Task model](../src/brr/task.py) with [task tests](../tests/test_task.py).
6. [Conversation log](../src/brr/conversations.py) with [conversation tests](../tests/test_conversations.py).
7. [Runner plumbing](../src/brr/runner.py) with [runner tests](../tests/test_runner.py), then [prompt assembly](../src/brr/prompts.py) with [prompt tests](../tests/test_prompts.py).
8. [Environment backends](../src/brr/envs/__init__.py) with [env tests](../tests/test_envs.py) and [Dockerfile tests](../tests/test_dockerfile.py).
9. [Daemon worker](../src/brr/daemon.py) plus
   [developer reload](../src/brr/dev_reload.py) with
   [daemon tests](../tests/test_daemon.py),
   [developer reload tests](../tests/test_dev_reload.py), and
   [daemon-conversation tests](../tests/test_daemon_conversations.py).
10. [Bundled execution map](../src/brr/docs/execution-map.md) to re-read the system top-down after seeing the parts.

## Spiral reading route

### Ring 0: package skin

Purpose: know how execution enters the package before studying internals.

Read:

- [pyproject.toml](../pyproject.toml)
- [README](../README.md)
- [`src/brr/AGENTS.md`](../src/brr/AGENTS.md)
- [`src/brr/__init__.py`](../src/brr/__init__.py)
- [`src/brr/__main__.py`](../src/brr/__main__.py)
- [`src/brr/cli.py`](../src/brr/cli.py)

Keep in mind:

- The console script is `brr = brr.cli:main`.
- `python -m brr` delegates to the same CLI.
- The public CLI is intentionally small: `init`, `run`, `auth`, `bind`, `up`, `down`.
- Rich status/inspection helpers exist in [status.py](../src/brr/status.py), but the current CLI tests assert that older public diagnostic commands are not registered.
- [`src/brr/AGENTS.md`](../src/brr/AGENTS.md) is the **universal schema** every tool follows (brr daemon, Cursor, Codex CLI, Claude Code) — its contract on commits, kb shape, lifecycle markers, and delivery is shared. The stewardship section names a workflow rule with teeth: surface contradictions between the request and the codebase, don't blindly follow either.

Tests:

- [CLI tests](../tests/test_cli.py)

### Ring 1: filesystem atoms

Purpose: understand the primitive file and git contracts. These are the atoms
that all higher-level modules assume.

Read:

- [`src/brr/protocol.py`](../src/brr/protocol.py)
- [`src/brr/config.py`](../src/brr/config.py)
- [`src/brr/gitops.py`](../src/brr/gitops.py)
- [`src/brr/worktree.py`](../src/brr/worktree.py)

Keep in mind:

- Events are markdown files in `.brr/inbox/`.
- Responses are markdown files in `.brr/responses/`.
- Both use a restricted YAML-like frontmatter parser, not PyYAML.
- `.brr/config` is a flat key-value file.
- `gitops.shared_brr_dir()` is critical: in a linked worktree it resolves the shared runtime directory in the main checkout.
- Worktrees live under `.brr/worktrees/<task-id>`.

Tests:

- [protocol tests](../tests/test_protocol.py)
- [config tests](../tests/test_config.py)
- [git/worktree tests](../tests/test_gitops.py)

### Ring 2: state objects

Purpose: learn the durable runtime entities before reading orchestration.

Read:

- [`src/brr/task.py`](../src/brr/task.py)
- [`src/brr/conversations.py`](../src/brr/conversations.py)
- [`src/brr/updates.py`](../src/brr/updates.py)
- [`src/brr/run_progress.py`](../src/brr/run_progress.py)
- [`src/brr/run_context.py`](../src/brr/run_context.py)

Keep in mind:

- `Task` is the central work unit constructed mechanically from an event. It carries the originating event, concrete environment backend, status, source, conversation key, and freeform metadata (worktree path, branch name, response path, etc.). Branching is decided by the agent inside the worktree at runtime.
- A conversation is just a per-gate-thread append-only ndjson log of events, tasks, artifacts, and lifecycle update packets. It has no manifest, title, or intent; see [decision-drop-streams.md](decision-drop-streams.md).
- `UpdatePacket` is lifecycle telemetry routed to a conversation log and, optionally, gate `render_update` hooks. The packet vocabulary covers env prep, attempts, retries, finalize, push, and Docker container births/preservations.
- `RunProgressView` (in `run_progress.py`) folds conversation records into a compact per-task projection that both gates and local diagnostics render. Adding new lifecycle UX should extend this projection, not reinvent rendering per gate.
- `run_context.py` writes a per-task context file under `.brr/runs/<task-id>/context.md` so an agent can recover orientation without poking around runtime state.

Tests:

- [task tests](../tests/test_task.py)
- [conversation tests](../tests/test_conversations.py)
- [run-progress tests](../tests/test_run_progress.py)
- [daemon-conversation tests](../tests/test_daemon_conversations.py)
- [daemon-progress-packet tests](../tests/test_daemon_progress_packets.py)
- [status-troubleshooting tests](../tests/test_status_troubleshooting.py)

### Ring 3: execution contract

Purpose: understand how `brr` delegates actual work to an external AI runner,
and how the chosen environment shapes that runner invocation.

Read:

- [`src/brr/runner.py`](../src/brr/runner.py) — subprocess plumbing
- [`src/brr/prompts.py`](../src/brr/prompts.py) — prompt assembly, Task Context Bundle, conversation injection
- [`src/brr/envs/__init__.py`](../src/brr/envs/__init__.py)
- [`src/brr/prompts/runners.md`](../src/brr/prompts/runners.md)
- [`src/brr/prompts/run.md`](../src/brr/prompts/run.md)
- [`src/brr/prompts/kb-maintenance.md`](../src/brr/prompts/kb-maintenance.md) — thin redundancy pass; pointer at AGENTS.md → "Knowledge base shape"
- [`src/brr/kb_preflight.py`](../src/brr/kb_preflight.py) — deterministic kb consistency scanner that feeds the maintenance prompt

Keep in mind:

- `RunnerInvocation` describes one external AI CLI call.
- `RunnerResult.validation_ok` combines three layers: subprocess exit, the optional `required_artifacts` check (used by `adopt` for AGENTS.md / kb files), and the `has_response` check that fires only when the invocation specifies a `response_path`.
- The runner contract is "stdout is the response": `claude --print`, `codex exec`, and `gemini -p --yolo` all print only the final agent message to stdout. `invoke_runner` captures stdout and writes it to the task response file itself, so no per-runner output flag is needed.
- Daemon retry triggers on empty stdout, not a missing file.
- `RunContext` splits host-visible and environment-visible response paths so Docker invocations can resolve mount-aware paths even though brr (not the runner) writes the file.
- The user-facing policy key is `environment=<auto|host|worktree|docker>` in `.brr/config`; legacy `env` and `default_env` are still accepted.
- Task files still store the concrete backend as `env`.
- Current built-in backends on this branch are `host`, `worktree`, and `docker`. Design notes also discuss future `ssh` and `devcontainer` backends.
- The Docker env auto-wires credentials so users don't have to bake them into images: known runner env vars (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, `GOOGLE_API_KEY`) pass through, host login dirs (`~/.claude`, `~/.claude.json`, `~/.codex`, `~/.gemini`, `~/.gitconfig`) bind-mount into `/brr-home/<basename>` when present, and `safe.directory='*'` is injected via `GIT_CONFIG_*` env vars so git works against the bind-mounted repo regardless of UID. The container itself runs as the host UID (`-u "$(id -u):$(id -g)"`) with `HOME=/brr-home`, so writes inside the bind-mounted repo stay host-owned. Toggles: `docker.env=KEY1,KEY2` and `docker.mount_credentials=false`. The bundled [`envs.md`](../src/brr/docs/envs.md) is the user-facing reference.

Tests:

- [runner tests](../tests/test_runner.py)
- [prompt tests](../tests/test_prompts.py)
- [env tests](../tests/test_envs.py)
- [Dockerfile tests](../tests/test_dockerfile.py)
- [kb-preflight tests](../tests/test_kb_preflight.py)

### Ring 4: orchestration spine

Purpose: read the actual event-to-response loop after the lower layers make
sense.

Read:

- [`src/brr/daemon.py`](../src/brr/daemon.py)
- [`src/brr/dev_reload.py`](../src/brr/dev_reload.py)
- [daemon tests](../tests/test_daemon.py)
- [developer reload tests](../tests/test_dev_reload.py)
- [daemon-conversation tests](../tests/test_daemon_conversations.py)

Read `_run_worker()` in passes rather than all at once:

1. Resolve the incoming event to a conversation key (gate-thread fingerprint).
2. Append the event arrival and emit `event_received`.
3. Build the `Task` from the event with `Task.from_event`; emit `task_created`.
4. Resolve the environment policy into a concrete backend.
5. Prepare the environment (worktree creation included); emit `env_prepared`.
6. Write the run context file (with the recent conversation block).
7. Build the daemon prompt via [`prompts.build_daemon_prompt`](../src/brr/prompts.py) — preamble, recent conversation block, Task Context Bundle, delivery contract.
8. Invoke the runner, with retries when the runner prints no final reply on stdout.
9. Capture the plain-text response file (written from stdout).
10. Run [`kb_preflight.scan`](../src/brr/kb_preflight.py); if it has findings or `kb/` was touched, run the kb-maintenance LLM pass with findings injected. Otherwise skip — the pass is a safety net.
11. Finalize the environment — `WorktreeEnv.finalize` reads the worktree's git state to decide between fast-forward landing and branch preservation.
12. Update task status and append matching update packets to the conversation log.

Keep in mind:

- The daemon is serial in v1: it processes one pending event at a time.
- Gate threads run beside it, but task execution itself is not a worker pool yet.
- There is exactly one runner invocation per attempt — no separate triage call.
- The agent owns branching: brr only decides whether to fast-forward back or preserve the branch as-is.
- Worktree/Docker tasks isolate the working directory while sharing the runtime `.brr/`.

### Ring 5: edges and operator views

Purpose: understand how messages enter/leave the core, how live progress is
rendered into remote channels, and how humans inspect runtime state when
something looks wrong.

Read:

- [`src/brr/gates/__init__.py`](../src/brr/gates/__init__.py)
- [`src/brr/gates/telegram.py`](../src/brr/gates/telegram.py)
- [`src/brr/gates/slack.py`](../src/brr/gates/slack.py)
- [`src/brr/gates/git.py`](../src/brr/gates/git.py)
- [`src/brr/status.py`](../src/brr/status.py)
- [`src/brr/docs/__init__.py`](../src/brr/docs/__init__.py)
- [`src/brr/docs/brr-internals.md`](../src/brr/docs/brr-internals.md)
- [`src/brr/docs/conversations.md`](../src/brr/docs/conversations.md)
- [`src/brr/docs/active-task.md`](../src/brr/docs/active-task.md)
- [`src/brr/docs/envs.md`](../src/brr/docs/envs.md)
- [`src/brr/docs/execution-map.md`](../src/brr/docs/execution-map.md)

Keep in mind:

- Gates are transport adapters. They should not know about daemon internals.
- Gates create event files and deliver response files.
- `updates.emit()` can call optional gate `render_update()` hooks, but gate-side failures are swallowed.
- Telegram and Slack gates render a live per-task progress card via `render_update`: send-on-`task_created`, edit-on-progress through `editMessageText`/`chat.update`, fallback to a fresh send when the original message is gone. State lives at `.brr/gates/telegram_progress.json` and `.brr/gates/slack_progress.json`.
- The Git gate is enabled by default as a conservative task-file source and is a deliberate no-op for live rendering — Git is not a great surface for live progress; commits and PRs remain its primary delivery.
- `status.py` is a troubleshooting helper, not the primary UX. It uses the same `RunProgressView` projection to keep local and remote views consistent.
- Bundled docs live in `src/brr/docs/`; per-repo overrides live in `.brr/docs/`.
- Project-specific durable knowledge lives in `kb/`, not `.brr/`.

Tests:

- [Telegram gate tests](../tests/test_telegram_gate.py)
- [gate setup tests](../tests/test_gate_setup.py)
- [Telegram render-update tests](../tests/test_telegram_render_update.py)
- [Slack render-update tests](../tests/test_slack_render_update.py)
- [status-troubleshooting tests](../tests/test_status_troubleshooting.py)
- [docs tests](../tests/test_docs.py)

## Main entities

| Entity | Source | Persistence | Current shape | Read with |
| ------ | ------ | ----------- | ------------- | --------- |
| Event | [`protocol.py`](../src/brr/protocol.py) | `.brr/inbox/<event-id>.md` | Frontmatter-backed inbox item with `id`, `source`, `status`, gate metadata such as `telegram_chat_id`, `slack_channel`, or `git_file`, and body text. Gates create events; the daemon claims them. | [protocol tests](../tests/test_protocol.py), [gate tests](../tests/test_telegram_gate.py) |
| Task | [`task.py`](../src/brr/task.py) | `.brr/tasks/<task-id>.md` | Mechanical unit of work created from an event and `.brr/config`. It stores the concrete `env`, source, conversation key, status, body, and freeform runtime metadata. `environment` is the preferred config key; `env` and `default_env` are legacy aliases. | [task tests](../tests/test_task.py), [daemon tests](../tests/test_daemon.py) |
| Conversation log | [`conversations.py`](../src/brr/conversations.py) | `.brr/conversations/<safe-key>.ndjson` | Append-only per-gate-thread history. Keys are gate fingerprints such as `telegram:<chat>:<topic>`, `slack:<channel>:<thread_ts>`, or `git:<file>`. There is no manifest, title, or intent; lines of work that need durable naming belong in `kb/`. | [conversation tests](../tests/test_conversations.py), [conversations doc](../src/brr/docs/conversations.md) |
| Update packet | [`updates.py`](../src/brr/updates.py) | Conversation records with `kind=update` | Lifecycle telemetry emitted by the daemon and push path. Gates may render packets through `render_update`; `run_progress.py` folds them into the user-visible task card. `PACKET_TYPES` is the canonical vocabulary. | [daemon-conversation tests](../tests/test_daemon_conversations.py), [daemon-progress-packet tests](../tests/test_daemon_progress_packets.py) |
| Run progress view | [`run_progress.py`](../src/brr/run_progress.py) | Derived, not persisted | Projection of conversation records into task phase, state, branch/base display, environment, attempts, details, artifacts, containers, response path, and forge view URL. New live UX should extend packets and this projection first. | [run-progress tests](../tests/test_run_progress.py), [Telegram render-update tests](../tests/test_telegram_render_update.py), [Slack render-update tests](../tests/test_slack_render_update.py) |
| Runner invocation/result | [`runner.py`](../src/brr/runner.py) | Optional `.brr/traces/<kind>/<label>-<timestamp>/` | Subprocess execution plus trace capture. `validation_ok` combines exit status, expected artifacts, and non-empty stdout when a response path is requested. Daemon responses are written from captured stdout by brr. | [runner tests](../tests/test_runner.py) |
| Run context | [`run_context.py`](../src/brr/run_context.py), [`envs/__init__.py`](../src/brr/envs/__init__.py) | `.brr/runs/<task-id>/context.md` | Recovery document and prompt input for the selected env, including host/env response paths, repo/runtime roots, branch plan, and env state. Branch landing facts live on `branch_plan` and task metadata, not on a per-task narrative file. | [daemon tests](../tests/test_daemon.py) |
| Env backend | [`envs/__init__.py`](../src/brr/envs/__init__.py) | Worktree/Docker state under `.brr/` | Three-phase backend protocol: `prepare`, `invoke`, `finalize`. Built-ins are host, worktree, and docker; the env design covers future SSH/devcontainer shapes. | [env tests](../tests/test_envs.py), [env design](design-env-interface.md) |
| Gate module | [`gates/`](../src/brr/gates/) | `.brr/gates/<gate>.json` plus inbox/response files | Transport adapters implement `is_configured` and `run_loop`; setup hooks are optional. Telegram/Slack render live progress, while Git is a default task-file source and skips live rendering. | [gate protocol](../src/brr/gates/README.md), [gates hub](subject-gates.md) |

## Module cross-reference map

| Area | Primary files | Direction |
| ---- | ------------- | --------- |
| CLI and adoption | [`__main__.py`](../src/brr/__main__.py), [`cli.py`](../src/brr/cli.py), [`adopt.py`](../src/brr/adopt.py) | `cli.py` routes `init` to adoption, `run` to runner execution, `up`/`down` to the daemon, and gate setup commands through `gates.import_gate()`. Read with [CLI tests](../tests/test_cli.py), [adopt tests](../tests/test_adopt.py), and [integration tests](../tests/test_integration.py). |
| Filesystem protocol | [`protocol.py`](../src/brr/protocol.py), [`config.py`](../src/brr/config.py), [`gitops.py`](../src/brr/gitops.py), [`worktree.py`](../src/brr/worktree.py) | These are the low-level file and git contracts. Gates and daemon code should use them rather than hand-parsing runtime files. |
| Task and conversation state | [`task.py`](../src/brr/task.py), [`conversations.py`](../src/brr/conversations.py), [`updates.py`](../src/brr/updates.py), [`run_progress.py`](../src/brr/run_progress.py) | `Task` says what is executing, conversation logs say what happened in a gate thread, packets say what just changed, and `RunProgressView` is the rendering projection. |
| Runner and prompts | [`runner.py`](../src/brr/runner.py), [`prompts.py`](../src/brr/prompts.py), [`kb_preflight.py`](../src/brr/kb_preflight.py), [`src/brr/prompts/`](../src/brr/prompts/) | `runner.py` owns subprocess execution and traces. `prompts.py` owns bundled prompt loading, the Task Context Bundle, recent conversation/log injection, and kb-maintenance prompts. `kb_preflight.py` is the deterministic scanner that decides when the LLM redundancy pass has concrete findings. |
| Environments | [`envs/__init__.py`](../src/brr/envs/__init__.py), [`branching.py`](../src/brr/branching.py), [`gitops.py`](../src/brr/gitops.py), [`worktree.py`](../src/brr/worktree.py) | Host runs in-place; worktree creates a fresh `brr/<task-id>` branch from the resolved seed ref; Docker wraps worktree execution in `docker run`, forwards known runner credentials, uses the host UID, and injects git `safe.directory`. `environment=auto` selects configured Docker, otherwise worktree. |
| Daemon | [`daemon.py`](../src/brr/daemon.py), [`dev_reload.py`](../src/brr/dev_reload.py) | Main lifecycle spine: PID file, gate startup, inbox scan, task construction, branch intent, env prepare/invoke/finalize, retry/response validation, kb preflight, branch-aware push, progress packets, and optional quiescent re-exec for brr self-development. Read [subject-daemon.md](subject-daemon.md) before editing it. |
| Gates and operator views | [`gates/__init__.py`](../src/brr/gates/__init__.py), [`gates/git.py`](../src/brr/gates/git.py), [`gates/telegram.py`](../src/brr/gates/telegram.py), [`gates/slack.py`](../src/brr/gates/slack.py), [`status.py`](../src/brr/status.py) | Gates translate external surfaces to the file protocol and optional progress cards. Local status is a troubleshooting view over the same run-progress projection. Read [subject-gates.md](subject-gates.md) for the Git/forge boundary. |

## Runtime invariants

| Invariant | Current rule |
| --------- | ------------ |
| `.brr/` | Gitignored runtime state: inbox, responses, tasks, runs, conversations, traces, reviews, worktrees, gate state, prompt/doc overrides, and config. Do not treat it as durable project knowledge. |
| `kb/` | Committed project knowledge. Update it when repo structure, decisions, or durable operational knowledge changes. |
| `src/brr/docs/` | Bundled package docs, with per-repo overrides in `.brr/docs/<topic>.md`; see [decision-bundled-docs.md](decision-bundled-docs.md). |
| Runner success | `RunnerResult.validation_ok` requires subprocess success, expected artifacts, and non-empty stdout when a response path is requested. brr writes daemon responses from captured stdout. |
| Task construction | `Task.from_event` builds tasks mechanically from inbox events and `.brr/config`; there is no triage invocation. See [decision-remove-triage.md](decision-remove-triage.md). |
| Branching | Worktree/Docker runs start on `brr/<task-id>` from the resolved seed ref. The agent may commit there or switch to another branch; `WorktreeEnv.finalize` reads git state and either fast-forwards an explicit auto-land target or preserves the branch. |
| Environment | `environment=<auto|host|worktree|docker>` is the user-facing isolation knob. `auto` selects configured Docker, otherwise worktree. Runtime branch facts live in task metadata and `BranchPlan`, not a `Task.branch` field. |
| Responses | `.brr/responses/<event-id>.md` is plain final stdout. If work cannot complete, the response explains the blocker in text and the operator follows up through the gate. |
| Conversations | Conversation logs are runtime routing history, not semantic memory. They have no manifest/title/intent; durable named work belongs in `kb/`. See [decision-drop-streams.md](decision-drop-streams.md). |
| Progress | `RunProgressView` is derived from conversation update packets. Gates and local status should render this projection instead of building parallel state. |
| KB consistency | `kb_preflight.scan` reports deterministic graph findings; the LLM pass is a thin AGENTS.md-guided redundancy check when findings exist or `kb/` changed. Add deterministic invariants to `kb_preflight.py` first. |
| Local status | `status.py` is troubleshooting, not the primary product UX; remote gate cards are the normal progress surface. |

## Tests as a second reading path

If source-first reading feels too abstract, follow the same dependency
growth through tests: [protocol](../tests/test_protocol.py),
[task](../tests/test_task.py), [conversations](../tests/test_conversations.py),
[run progress](../tests/test_run_progress.py), [runner](../tests/test_runner.py),
[prompts](../tests/test_prompts.py), [git/worktree](../tests/test_gitops.py),
[envs](../tests/test_envs.py), [Dockerfile](../tests/test_dockerfile.py),
[kb preflight](../tests/test_kb_preflight.py), [daemon](../tests/test_daemon.py),
[daemon conversations](../tests/test_daemon_conversations.py),
[daemon progress packets](../tests/test_daemon_progress_packets.py),
[gates](../tests/test_telegram_gate.py), [gate setup](../tests/test_gate_setup.py),
[Telegram updates](../tests/test_telegram_render_update.py),
[Slack updates](../tests/test_slack_render_update.py),
[status](../tests/test_status_troubleshooting.py), [adopt](../tests/test_adopt.py),
[integration](../tests/test_integration.py), [CLI](../tests/test_cli.py), and
[docs](../tests/test_docs.py).

## Design history to read after source

The source says what is implemented; the index and subject hubs tell you
which decision/design pages are live context. Start with [subject-kb.md](subject-kb.md),
[subject-daemon.md](subject-daemon.md), [subject-gates.md](subject-gates.md),
[subject-envs.md](subject-envs.md), and [subject-tasks-branching.md](subject-tasks-branching.md).

Then read the decisions that still explain current constraints:
[decision-remove-triage.md](decision-remove-triage.md),
[decision-drop-streams.md](decision-drop-streams.md),
[decision-kb-shape.md](decision-kb-shape.md), and
[decision-bundled-docs.md](decision-bundled-docs.md). For active or
accepted designs, use [design-git-gate.md](design-git-gate.md),
[design-daemon-dev-reload.md](design-daemon-dev-reload.md),
[design-daemon-landing-branch.md](design-daemon-landing-branch.md), and
[design-env-interface.md](design-env-interface.md).

Strategic and research context lives in
[deck-brr-fleet-steering.md](deck-brr-fleet-steering.md),
[plan-overlays.md](plan-overlays.md),
[notes-pondering-fleet.md](notes-pondering-fleet.md),
[research-runner-context-ergonomics-2026-05-09.md](research-runner-context-ergonomics-2026-05-09.md),
and [research-brr-vs-gh-aw.md](research-brr-vs-gh-aw.md). Bundled user
docs live under [`src/brr/docs/`](../src/brr/docs/).

## Practical navigator notes

Use these heuristics while reading:

- If a file talks about event files, jump to [protocol.py](../src/brr/protocol.py).
- If a file talks about environment/status, jump to [task.py](../src/brr/task.py).
- If a file talks about branching, jump to [worktree.py](../src/brr/worktree.py) and `WorktreeEnv` in [envs/__init__.py](../src/brr/envs/__init__.py) — the agent owns branching at runtime.
- If a file talks about thread continuity or per-thread history, jump to [conversations.py](../src/brr/conversations.py).
- If a file talks about lifecycle packets or `render_update`, jump to [updates.py](../src/brr/updates.py).
- If a file talks about live progress phases, attempt counts, or rendering a per-task card, jump to [run_progress.py](../src/brr/run_progress.py).
- If a file talks about prompt assembly (Task Context Bundle, `kb/log.md` injection, AGENTS.md bundling), jump to [prompts.py](../src/brr/prompts.py). If it talks about subprocess execution, runner detection, or trace persistence, jump to [runner.py](../src/brr/runner.py).
- If a file talks about daemon process lifecycle, PID files,
  drain-and-stop behavior, or development reload, start with
  [subject-daemon.md](subject-daemon.md) and then jump to
  [daemon.py](../src/brr/daemon.py) and
  [dev_reload.py](../src/brr/dev_reload.py).
- If a file talks about kb consistency, orphan pages, broken cross-links, or "should this kb-maintenance pass run?", jump to [kb_preflight.py](../src/brr/kb_preflight.py) and `_maybe_kb_maintenance` in [daemon.py](../src/brr/daemon.py). The maintenance contract itself lives in [AGENTS.md → "Knowledge base shape"](../src/brr/AGENTS.md), not in the brr daemon.
- If a file talks about cwd, worktrees, Docker, response path translation, or runner credential wiring (env passthrough, login-dir mounts, git safe.directory), jump to [envs/__init__.py](../src/brr/envs/__init__.py).
- If a file talks about transport, auth, polling, or delivery, jump to [gates](../src/brr/gates/).
- If a file feels like "everything at once", you are probably in [daemon.py](../src/brr/daemon.py). Read it in lifecycle passes, not top-to-bottom once.

## Maintenance rule for this guide

Update this page when any of these change:

- public CLI commands
- event/task/conversation file formats
- environment backends
- daemon lifecycle
- runner artifact contract
- gate hook surface
- bundled docs vs KB ownership
- kb consistency contract (preflight findings, kb-maintenance trigger, AGENTS.md kb schema)
- module boundaries that affect "where do I jump?" routing (e.g. the runner / prompts split, kb_preflight)
- subject hubs added or retired
- test files that become the best behavioral reference for a module
