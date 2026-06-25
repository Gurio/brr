# Initial-context coherence: define-once / layer-ownership (evt g9m2)

Synthesis for the "is the whole initial context one thread?" exercise the
maintainer asked across evt u9sd (interrupted by quota) → evt g9m2 (this wake).
The narrow predecessor — reshaping `## What kind of thing you are` to "define,
not re-define" — already shipped (evt 68ey, PR #178). This generalizes that
fix from one section to the whole assembled prompt. Active design fork; lives
here, not kb, until the maintainer nods on direction. Sibling notes:
`portal-reshape-synthesis.md` (perception=injection), thread-of-record 06-25
(reactive agent over safety-net pile).

## The diagnosis

The initial context is NOT one thread — it's a chord of overlapping
orientations. Five concepts are each *defined* more than once, in different
voices and lengths:

- **Ontology / what-you-are** — owned by the playbook; re-gestured in run.md's
  warm opening.
- **Delivery** — run.md §Delivery + playbook §Delivery + the bundle's Delivery
  contract. Three times, three depths.
- **Stewardship / reconcile-and-act** — AGENTS.md §Stewardship (owner) +
  run.md §"When the task asks you to reconsider" + playbook §"Ownership, not
  subordinance."
- **Portals / how-brr-drives** — run.md §"How brr drives you" + bundle Delivery
  contract + `brr docs portals` (the real manual).
- **Dominion / memory** — run.md §"Your dominion" + playbook §"Your dominion" +
  the bundle's dominion block.

The maintainer's "accreted self-redefining rather than defining" at the section
level IS this at the whole-context level: each layer was written to be
self-sufficient, so each re-defines the shared vocabulary, and brr stacks all
of them. It reads as "surgical reshape of previous shapes" because that is how
it grew — patch on patch, each internally coherent, never consolidated to one
owner per concept.

**Deeper fact:** the thread doesn't start at brr's first word. It starts at the
SDK's — "You are a Claude agent / a brr runner" (assistant/tool register) — and
brr then spends run.md, the playbook, and introspection.md rowing the framing
back toward resident/sentience. The biggest single source of "two voices at
once" is brr reframing against an opening it doesn't own and can't delete.

**The cure already exists in prose, unenforced:** the playbook's §"Where your
context comes from" already names the four sources and says "a well-behaved
host tags each block with where it came from." That IS the single-thread spec —
define each concept once, at the layer that owns it; others reference, not
restate; tag provenance. The gap is the assembly doesn't honor its own model.

## What has to move (one owner per concept, demote duplicates to a pointer)

- Ontology → **playbook** owns. run.md drops the ontological warmup; keeps only
  hot-path "this run, this moment, where to look."
- Delivery → **bundle Delivery contract** owns (per-run operative truth). run.md
  §Delivery and playbook §Delivery compress to a pointer.
- Stewardship → **AGENTS.md** owns. run.md §reconsider + playbook §ownership
  keep only run-specific nuance, else point.
- Portals → **`brr docs portals` + bundle** own. run.md §"How brr drives you"
  shrinks to the genuinely standing facts not stated elsewhere (single-flight,
  memory-as-net, self-scheduling).
- Dominion → **playbook** owns philosophy, **bundle** owns the per-run path.
  run.md drops the re-explanation.

Net: run.md becomes a true hot-path orientation; playbook stays standing
ontology+stance; AGENTS.md stays repo contract; bundle stays per-run values.
Each concept lands once. The chord becomes a melody.

## In reach vs out of reach

- **In reach (brr-owned source):** run.md, introspection.md,
  dominion-playbook.md (seed), AGENTS.md, the daemon's bundle composition
  (what it injects + order), kb extracts, my dominion + self-inject.
- **Out of reach for now (SDK-owned, brr wraps but doesn't author):** the "You
  are a Claude agent / brr runner" preamble (literal first words), the tool-call
  formatting rule, the deferred-tools/agents/skills system messages, the
  userEmail/date reminder. The one thing in reach about that seam: decide brr's
  *stance* — accept "runner" as the outer shell and stop fighting it, or do
  exactly one clean reframe and never re-litigate. Today brr reframes ~3×.

## Reconcile with prior wakes

- **Agrees** with portal-reshape-synthesis: the whole initial context is the
  injected scroll; "one thread?" is the structural form of "is the scroll one
  ornamented weave." Layer-ownership is the structural counterpart of that
  note's aesthetic target.
- **Agrees** with 06-25 reframe (reactive agent over safety-net pile): prose
  accretion = the same growth pattern as behavioral safety-net accretion;
  patch-on-patch, never consolidated. Same cure, two layers.
- **Differs** from arrival assumption: expected in-flight code to resume; the
  salvage was junk (hook test files ht/FIRED, ht/foo.txt). u9sd died before
  analysis. Nothing to merge — deliver the broad diagnosis, don't redo the
  section.
- **Confirmed** the maintainer's twice-flagged "I don't see your dominion
  self-inject": dominion playbook body is byte-identical to the seed (diff
  empty); only a sigil banner differs. We are closer than he could see.

## Decision

Wide-blast (seed reaches every adopter via `brr init`) + genuine fork
(how to structure self-definition is a values/architecture call) + he asked to
"lay out what has to move first, only then..." → the complete task is the
diagnosis + move-map + classification as the turn. No half-fitting seed rewrite
to manufacture a diff. The restructuring waits for his nod on direction.
