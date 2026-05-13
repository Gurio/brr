# Subject: fleet and overlays

Hub page for the paused work that would scale brr from one repo to a
user-visible fleet: overlays for cross-repo steering, a future `brnrd`
operator for fleet coordination, and the environment axis that has
partly landed in brr core.

The current state is intentionally conservative. The environment axis is
the only active strand and is synthesized in
[`subject-envs.md`](subject-envs.md). Overlay and fleet-manager work is
paused until the overlay shape research gate is resolved.

## Current shape

The fleet framing has three axes:

| Axis | Question | Current state |
| ---- | -------- | ------------- |
| Environments | Where does a task run? | Active in brr core through the `Env` protocol; host/worktree/Docker ship today, while ssh/devcontainer remain designed-but-pending. |
| Overlays | How does a user steer many repos without editing each repo? | Blocked behind env completion and a research page choosing the minimum overlay shape. |
| `brnrd` / fleet operator | How does a user see and command many brr repos as a set? | Future separate project; brr should expose repo-local facts and keep its own per-repo boundary honest. |

The deck, plan, and notes are receipts for that framing, not current
implementation specs. Their lifecycle markers matter:

- [`deck-brr-fleet-steering.md`](deck-brr-fleet-steering.md) is a
  roadmap deck. It introduced the three-axis separation but still
  contains details overtaken by later decisions such as no triage,
  no workstreams, and no per-task kb log files.
- [`plan-overlays.md`](plan-overlays.md) is blocked. It should not be
  implemented until `kb/research-overlay-shape.md` exists and chooses
  the overlay primitive.
- [`notes-pondering-fleet.md`](notes-pondering-fleet.md) is paused
  capture-only thinking. Material promoted into the overlays plan stays
  there as the actionable receipt.

## Overlay boundary

The current unresolved question is whether overlays should be a single
user-level markdown file appended to prompts, a multi-file prompt lookup
chain, or some smaller first slice. The plan currently carries both
credible options because they optimize for different things:

- a single file keeps the user concept small and behaves like a personal
  `AGENTS.md`;
- a multi-file lookup chain can replace specific bundled prompts and
  supports profiles, but creates more policy surface.

Implementation is intentionally blocked until research evaluates real
flows and picks one. Per-repo `.brr/prompts/<name>.md` remains the
escape hatch either way.

## Fleet-manager boundary

`brr` is per-repo. It should know how to run one task in one repository,
record local state, and expose enough status for a human or future tool
to inspect it.

`brnrd`, if built, is per-user or per-fleet. It would decide which repos
to ask, aggregate status, and carry its own memory and user channel.
That belongs outside brr core. brr-side groundwork should stay small:
machine-readable local status, a reliable repo registry if needed, and
stable file/gate contracts.

## Read next

1. [`subject-envs.md`](subject-envs.md) and
   [`design-env-interface.md`](design-env-interface.md) for the active
   axis that already changed brr core.
2. [`plan-overlays.md`](plan-overlays.md) for the blocked overlay plan
   and the research gate that must land before implementation.
3. [`deck-brr-fleet-steering.md`](deck-brr-fleet-steering.md) for the
   strategic framing, read as roadmap rather than spec.
4. [`notes-pondering-fleet.md`](notes-pondering-fleet.md) for paused
   capture-only questions around overlays, repo registry, `brnrd`,
   supervisors, and decentralized merge.
