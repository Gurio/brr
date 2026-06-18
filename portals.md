# Portals — the control protocol, looked-up not memorized

The seam between me and the human runs through control dotfiles in the
per-event outbox dir (`.brr/outbox/<event-id>/`) — these are the
**portals** (inbound / outbound / parked). I keep forgetting the exact
names mid-task, so they live here to glance at, not to memorize. The
shipped manual is `brr docs portals`; this is my own short version.
(Lineage: was the G4 "cheatsheet" `cockpit.md`; renamed 2026-06-18 when
the maintainer retired the "cockpit" noun — see
`kb/design-portal-grammar.md`.)

## Outbox dir — `.brr/outbox/<event-id>/`
- **A `*.md` file** → one chat message, delivered in order, mid-thought.
  Stage as `*.tmp` and rename for atomic write.
- **Frontmatter `event: <id>`** → reply to a *different* pending event
  inline; marks it handled so it won't wake again.
- **Frontmatter `gate: <name>`** (e.g. `gate: telegram`) → send to a
  destination with no waiting event (ping a chat, scheduled-thought
  output). `gate: forge` wants `head`/`base`/`title`; body = PR body.
- **`.card`** → a `note:` line under the daemon's live progress card
  (outbound desired-state portal — reconciled in place, not appended).
  This is my live surface back to the human. Compose it as a matter of course
  so the human sees *me*, not just daemon scaffolding. Rewrite to update;
  empty/delete to withdraw. Control file — never delivered as a message.
- **`.keepalive`** → first line ISO-8601 ("busy until T") or `+30m`.
  Holds the single-flight slot past the budget. Rewrite to extend.
- **`inbox.json`** → daemon-owned live inbox view; re-read at plan
  boundaries to decide continue / fold-in / leave-for-own-wake. Don't edit.

## Dwelling — the dominion (`.brr/dominion/`, branch `brr-home`)
- `playbook.md` — standing orientation (self-injected full each wake).
- `self-inject` — `<mode> <path>` per line; what rides into each wake.
- `pitfalls.md` — trigger-indexed failure memory; surfaced when a
  trigger appears in the task.
- `schedule.md` — self-woken thoughts (`at:` once / `every:` repeat).
- `thread-of-record.md` — durable cross-channel project narrative (slot
  the bundle points at; create when there's narrative worth carrying).
- **Commit what I mean to keep** — the diff is the receipt the next wake
  reads from. brr best-effort pushes brr-home; a *diverged* remote is
  mine to fetch/merge/push.

## Reflexes worth keeping
- Worktree, not host checkout: edit under `.brr/worktrees/<task-id>/`,
  never `/home/gurio/src/misc/brr/src/...` (that's host `main`).
- Refer to files by **basename** in replies — the human reads remotely;
  worktree/absolute paths don't render on their end.
