# Design: task files as daemon ingress

Status: active

This proposal hangs off the current
[`tasks and branching`](subject-tasks-branching.md) hub and would amend
one narrow part of [`decision-remove-triage.md`](decision-remove-triage.md):
after removing LLM triage, brr kept both frontmatter-backed event files
and frontmatter-backed task files. The event file no longer earns enough
to justify being a separate runtime entity.

## Proposed model

Current one-sentence model in [`repo-dive-in-map.md`](repo-dive-in-map.md):

```text
gate -> event -> conversation -> task -> env -> runner -> response -> gate
```

Proposed model:

```text
gate -> task -> env -> runner -> response -> gate
              \-> conversation log
```

In prose: brr turns external messages directly into
frontmatter-backed task files, threads those tasks through a per-gate
conversation log, resolves branch intent and environment policy, runs a
configured AI CLI, writes a plain-text response keyed to the task, and
lets the originating gate deliver that response.

The conversation log is a sidecar projection surface, not a pipeline
stage. It still records incoming user messages, lifecycle update
packets, artifacts, and task rows so remote progress cards and recent
thread context keep working.

## Why collapse events into tasks

The event file currently has three jobs:

- queue/claim state for the daemon (`pending` / `processing` / terminal);
- gate delivery routing (`source`, Telegram / Slack / Git metadata);
- provenance for the original user message.

Task files already carry the unit of work, source, status, environment,
conversation key, response path, branch/runtime metadata, and copied gate
metadata. Conversation logs already preserve the user-message summary
for thread context. Response files can be keyed by task ID without
needing a second event ID. That leaves event files as a queue wrapper
around the real work item.

Collapsing the layers removes:

- duplicated lifecycle state (`event.status` plus `task.status`);
- event/task/response correlation code;
- the awkward "event file missing" path in task inspection after gates
  clean up inbox files;
- the public gate mental model where a "task" arrives as an "event" and
  is then converted back into a task before running.

## Shape

`.brr/tasks/<task-id>.md` becomes the ingress queue item. A pending task
created by a gate looks like:

```text
---
id: task-YYMMDD-HHMM-rand
source: telegram
status: pending
created: 2026-05-13T21:14:00Z
telegram_chat_id: 123
telegram_topic_id: 456
---
User request text.
```

The daemon claims pending tasks by changing `status` to `running`,
loads config, resolves the concrete env, and rewrites the task file with
runtime metadata. Gate-created tasks may carry optional structured
inputs such as `environment`, `target_branch`, or `conversation_key`;
the daemon is still the component that resolves those into concrete env
and branch-plan metadata.

Responses should move from `.brr/responses/<event-id>.md` to
`.brr/responses/<task-id>.md`. After successful delivery, a chat gate
marks the task with delivery metadata such as `delivered_at` instead of
deleting the task. Response retention can be policy-driven later; the
first version should keep response files so `brr inspect` has a stable
artifact path.

Conversation records can keep the current `kind: event` vocabulary for
one compatibility slice if that keeps the patch small, but the runtime
entity should be the task. A later naming cleanup can rename the record
kind and `event_received` packet to `message` / `task_received` if the
extra churn is worth it.

## Migration slice

1. Add task-ingress helpers in `task.py`: create a pending task from a
   gate message, list claimable tasks, claim a task, and mark a task
   delivered.
2. Teach the daemon to scan `.brr/tasks/` first and run an existing
   task without creating a second task. Keep a temporary legacy importer
   from `.brr/inbox/` so old scripts and in-flight gates do not break
   abruptly.
3. Switch Telegram, Slack, and Git gates to create pending task files
   directly and deliver by scanning done, undelivered tasks for their
   source.
4. Move response correlation to task ID. Keep `event_id` as an optional
   legacy field only for tasks imported from old inbox files.
5. Update bundled docs, README diagrams, the gate file protocol, the
   repo dive-in map, and `decision-remove-triage.md` once the code lands.
   The decision should get a lineage breadcrumb saying that event
   frontmatter was removed because task frontmatter now owns ingress.
6. After one compatibility window, remove `protocol.create_event`,
   `list_pending`, `list_done`, and event cleanup if no shipped gate or
   documented extension path still uses them.

## What not to collapse

Do not remove task files. They are the durable manifest for status,
runtime paths, branch outcomes, trace references, and gate routing.

Do not fold conversation logs into task files. Conversation logs answer
"what happened in this thread over time"; task files answer "what unit
of work is or was running." Mixing those would bring back the stream
identity problem removed in
[`decision-drop-streams.md`](decision-drop-streams.md).

Do not make gates resolve environment policy or branch plans. Gates
should stay transport adapters. They may write structured input fields,
but daemon-side config and deterministic resolvers still own the
runtime decisions.

## Trade-offs

The simplification changes the public gate protocol. Third-party scripts
that write `.brr/inbox/<event-id>.md` need either a compatibility window
or a clear breaking-change note.

Done tasks will accumulate unless gates mark delivery or a retention
policy cleans old runtime state. That is a better problem than deleting
the only ingress record: task files are gitignored raw runtime state,
and inspection is more valuable than pretending `.brr/responses/` is the
only artifact worth retaining.

The current update vocabulary uses event-oriented names. Renaming all of
that in the first patch would widen the change for little functional
gain. The important architectural cut is file ownership: gates should
write tasks, and the daemon should run tasks.

## Recommendation

Yes: collapse event files into task files. The event/task split was
useful when a triage stage transformed raw input into a richer work
unit. After triage was removed, that split became accidental
complexity. The smallest healthy change is to keep the task manifest,
keep conversations as a sidecar, and remove the inbox event file as the
primary queue entity.
