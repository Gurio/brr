# Design: diffense — a kb-first PR review experience

Status: proposed, not yet accepted (drafted 2026-05-28)

diffense opens a new area for brr: the **review surface** an agent
produces so a human can review its work well. It is the human-side
counterpart to the GitHub gate's review-event handling
([`design-github-gate-vs-brnrd-app.md`](design-github-gate-vs-brnrd-app.md)
— gate-side, brr *reacts* to reviews); diffense is the side where brr
*produces* a surface humans can review well. No code ships in this
commit; this is the framing + design artifact that opens the
exploration. The cornerstones below are proposed, not accepted — the
`Status` line stays `proposed` until a substrate spike and a
hand-authored prototype pack confirm the shape against a real PR.

## Why a design page, not research-only or code

Four refinement passes converged on enough cornerstones that the
honest artifact is a design page with research-flavoured sections
inside, not a pure research note and not code:

- inspect-mode item-cards with always-vs-conditional axes;
- walkthrough cards as a first-class kind;
- uncertainty cards as a first-class kind for failure-mode honesty;
- two-axis lore (descriptive + possibility);
- usage-perspective demos grounded in tests;
- six discipline clamps (sharp / helpful / honest / non-prescriptive
  / emit-iff-honest / substrate-honest);
- a two-layer architecture (pack + substrate-with-multiple-targets);
- Textual proposed as the substrate for parallel CLI/web rendering;
- the PR body as the v0 surface;
- the project named `diffense`.

The dimensions still open (pack JSON schema, substrate validation,
aesthetic locking, project boundary) sit naturally inside a design
page as marked-open sections rather than blocking the framing. The
**Alternatives briefly considered** section preserves the research
dimension without spawning a separate page.

## Problem

KB-first reviews are unsupported by generic PR tools. Roughly half of
a brr PR's value lives in `kb/` diffs, and a kb diff reads poorly as a
raw unified diff but well as rendered Markdown — the forge's diff view
shows the *characters that changed*, not the *page as it now reads*.
Tests already encode user stories, but a test diff reads mechanically:
the reviewer has to reconstruct the user-facing behaviour from
fixtures and assertions.

The pain compounds because a good reviewer needs three things the diff
view never gives them: the surrounding mental model the change assumes,
an honest picture of *what becomes possible* after the change, and an
honest picture of *what the agent itself was uncertain about* while
making it. The current GitHub PR diff view is hostile to all three.

## Target audience

Solo developers through large teams. diffense optimises for reviewers
who **have, or aspire to have, full context** of the change — the
depth-first reading model is the audience filter, not team size. It is
deliberately *not* designed for skim-approvers: a reviewer who wants to
glance and thumbs-up is better served by a shallower tool, and that's
fine (see **Alternatives briefly considered**).

The kb-aware advantage extends to teams sharing a brr-managed repo just
as much as to solo dogfooding — anyone reviewing changes to a repo
whose knowledge lives in `kb/` benefits from a surface that renders the
kb graph rather than its character diff.

## Alternatives briefly considered (research dimension)

One-line treatment each; none of these is wrong, they optimise for a
different shape:

- **Plain PR body only, no inspect mode.** Leaves the touched-graph
  and lateral exploration on the table; fine as a v0 (it *is* the v0
  here), insufficient as the ceiling.
- **Forge-hosted artifact (PR comment / gist).** Hosting drift, no
  interactivity, ties the surface to GitHub semantics.
- **TUI-only viewer.** Power-user-friendly but locks out peers without
  brr installed.
- **Hosted-web-only viewer.** Requires brnrd / network; breaks
  dogfooding on a laptop with no connection.
- **A per-team review tool integrated with brr (Reviewable /
  Graphite shape).** These optimise for a different reviewer profile —
  skim-approval, threaded-comment management, merge-queue mechanics.
  diffense's depth-first, kb-aware shape **complements** rather than
  replaces them: a team can run Graphite for merge mechanics and reach
  for diffense when a change is context-heavy enough to warrant the
  deeper read. Trying to be both produces a worse version of each.

## Reframings the discussion converged on

Each reframing moved a noun from a heavyweight thing-to-build into a
projection over state brr already has:

- "Review document" → **"Review surface"**: a projection over existing
  structured state, not a separately-authored document.
- "Hosted on the forge" → **"Forge as data source"**.
- "Spiraling story" → **"Progressive disclosure with pre-loaded
  mental-model slots"**.
- "Linear PR scroll" → **"Navigable graph of inspection cards"**.
- "Tests as spec validation" → **"Tests as grounding evidence for
  honest user-perspective demos"**.
- "One renderer per surface" → **"One substrate, multiple rendering
  targets"**.
- "Agent always confident" → **"Agent uncertainty as first-class
  output, prominently surfaced"**.

## brr-specific inputs nobody else has

A generic PR tool sees a diff and a commit list. brr sees more, and
the pack is built from it:

- `gh pr view --json` + `gh pr diff` (the forge data source);
- the commit graph and commit messages;
- the per-conversation log in `.brr/conversations/`
  ([`src/brr/conversations.py`](../src/brr/conversations.py));
- the `kb/` graph itself — lifecycle markers, subject hubs, the
  decision / design / plan separation
  ([`subject-kb.md`](subject-kb.md));
- `brr kb pages` + `brr kb doc <page>` once the kb subcommand ships
  ([`plan-kb-subcommand.md`](plan-kb-subcommand.md));
- `kb/log.md`, the curated episodic narrative;
- the test suite, used as grounding evidence for usage demos;
- **the runner's own state during the run** — the basis for
  uncertainty cards, which nothing outside the runner can reconstruct.

## Architecture: pack as data, substrate-with-multiple-targets as renderers

Two layers, cleanly split so the data outlives any one renderer:

- **Pack** (data layer). JSON, language-agnostic. Nodes (item cards +
  walkthroughs + uncertainty cards), edges (relations between them),
  and metadata (PR id, conversation id, branch, base, generation
  time). Generated by the runner at publish time.
- **Substrate** (component layer). Python. Defines the information
  architecture — cards, navigation, search, view state. **Proposed:
  Textual** (validation pending; see below).

The pack is the contract; the substrate is one consumer of it. The
targets are renderers over the same pack:

| Target | Surface | Status |
| ------ | ------- | ------ |
| TUI (default) | `brr review <pr-url>` | proposed |
| Local web | `textual serve` — same UI, browser-rendered | proposed |
| Hosted web | HTMX view in the brnrd dashboard ([`plan-brnrd-dashboard-mvp.md`](plan-brnrd-dashboard-mvp.md)); different renderer, same pack; for peers without a brr checkout | future |
| Forge PR body | humanised Markdown projection of the pack | **v0** |
| Live agent | in-context Q&A; reads the pack as grounding context | future |

The PR-body projection is the only target this design commits to as
the near-term surface; everything else is proposed or future.

## Rendering substrate: Textual proposed, validation pending

**Why Textual.** It gives keyboard-driven navigation, CSS-flavoured
styling, reactive components, and — the load-bearing property — the
*same widget renders as a TUI and in a browser* via `textual serve`.
That is the mechanism behind "one substrate, multiple targets" for the
two local targets.

**What it does not give us cleanly.** Rich animated transitions, and
some interactive-graph affordances that would need extra work in the
web target only.

**Validation.** A small spike: render one hand-authored pack as a
Textual app, run it both as a TUI and via `textual serve`, and confirm
the card / navigation model survives both. Until that spike lands,
Textual is *proposed*, not chosen.

**If Textual doesn't pan out.** Fall back to parallel implementations
(a separate TUI and a separate web renderer over the shared pack) or to
an HTMX-only web target with no TUI. The pack-as-data split means this
fallback costs a renderer, not the model.

## Aesthetic stance: hacker-terminal-text-games leaning, held against a substrate-honest clamp

A *leaning*, not a lock. The substrate is a terminal, so the aesthetic
that fits is dense monospace, keyboard-driven navigation, a low-key
palette, and a terminal-game personality. The web target inherits it.

The **substrate-honest** clamp (see **Discipline**) keeps the aesthetic
from sliding into cosplay: a styling choice has to earn its space by
improving readability, navigation, or usefulness, held to the same
standard as a cosmetic stat. The aesthetic is validated alongside the
substrate spike, not locked ahead of it.

## Inspect mode: the diffense card model

### Three first-class card kinds

- **Item cards** — a typed unit of change: `code-fn-edit`,
  `code-fn-new`, `code-fn-delete`, `kb-page-edit`, `kb-page-new`,
  `kb-page-split`, `lifecycle-flip`, `test-add`, `dep-add`, and the
  like.
- **Walkthrough cards** — reference multiple item-card ids and tell a
  setup → action → outcome story spanning them. They coexist with
  per-item demos, earning their place only when the story needs
  framing a single item card can't carry.
- **Uncertainty cards** *(first-class)* — the agent's honest
  expression of confusion, assumption, dilemma, or out-of-scope flag
  during the run. See **Failure modes** below.

### Always-present axes (every card)

- **Identity** — file + symbol + line range, or kb page + section, or
  walkthrough id, or the uncertainty trigger.
- **Kind** — the discriminator above.
- **Descriptive lore** — factual. For `test-add` and walkthrough
  cards, the descriptive lore *is* the story; for uncertainty cards it
  is "what was unclear".
- **Kind-specific stat block** — see **Stats are load-bearing**.
- **Provenance** — which conversation message, which commit, which
  run-state moment produced this.

### Conditional axes (emitted iff honest and load-bearing)

- **Possibility lore** — what becomes possible / what constraint is
  lifted.
- **Before/after content**.
- **Lateral edges** — `calls` / `called-by` / `implements` /
  `referenced-by` / `shares-invariant` / `part-of-same-decision`; for
  walkthroughs, an *ordered* list of referenced item-ids; for
  uncertainty cards, related cards.
- **Usage-perspective demo** — textual at v0; GIFs deferred.
- **Exercising-tests link**.
- **Severity** *(uncertainty-only)* — `low` / `med` /
  `blocking-for-merge`.
- **Proposed-resolution** *(uncertainty-only)*.
- **Locked-abilities axis** — deferred future direction.

### Two-axis lore

Borrowed from the Souls / DMC menu framing: every card can carry two
kinds of lore. **Descriptive** lore states what the change *is*.
**Possibility** lore states what it *makes possible* — what constraint
is lifted, what new move is now available. Possibility lore is honest
and property-flavoured: it states a property that is actually true
after the change, never a recommendation about what to build next (the
non-prescriptive clamp).

### Tests as grounding evidence for usage demos

The agent extracts a user-flavoured shape from a test's
setup / action / assertion, using the test's *real* values. A
`test-add` card's descriptive lore *is* that humanised story.
Walkthroughs lean heaviest on integration tests, where the
setup → action → outcome arc already spans multiple units.

### Stats are load-bearing (per-kind)

Each kind carries a stat block that answers a real reviewer question:

| Kind | Stats |
| ---- | ----- |
| `code-fn-edit` | signature delta · callers in repo / updated / unchanged · complexity delta · new error paths · test-coverage delta |
| `kb-page-edit` | lifecycle-marker delta · inbound-link delta · sibling-page sync · successor-link validity |
| `test-add` | production code path exercised · assertion shape · fixture sharing |
| new-file | location justification · inbound-link wiring · sibling-pattern adherence |
| deletion | replacement · broken-ref flagging |
| uncertainty | severity · blast radius (which other cards it touches) |

## Worked-example cards

Five hand-authored illustrative mocks — *not* output from a real run.
They show the shape the runner would emit, grounded in recognisable
brr surfaces. The first is shown TUI-framed to hint at the substrate
aesthetic; the rest use a compact field form for brevity. Each emits
only the conditional axes that are honest and load-bearing for it —
the omissions are part of the demonstration.

**1. code-fn-rewrite** (full conditional axes):

```text
┌─ code-fn-edit · branching.resolve_publish_plan (src/brr/branching.py)
│ what    Adds a remote lease anchor so the publish step can
│         force-with-lease against a known OID instead of a second
│         resolver round-trip.
│ stats   sig Δ +1 field (expected_remote_oid) · callers 3 / 3 updated
│         / 0 stale · branches Δ +2 · new error paths 1 · cov Δ +2
│ opens   Callers can express "publish only if the remote tip is still
│         <oid>" as data, not control flow.
│ edges   called-by daemon.publish · shares-invariant WorktreeEnv.finalize
│ demo    > plan = resolve_publish_plan(event, repo)
│         > plan.expected_remote_oid  → 'a1b2c3d'
│ tests   test_branching::test_lease_anchor (exercises the new arm)
└─
```

**2. kb-page-edit-with-lifecycle-flip** (sibling edges; no usage demo —
absence is signal):

```text
kind         kb-page-edit + lifecycle-flip
identity     design-daemon-landing-branch.md (Status line + body)
descriptive  Flips the page to superseded and trims the body to a
             lineage breadcrumb; the publish kernel is now canonical.
stats        lifecycle Δ  active → superseded-by design-publish-kernel.md
             inbound-links Δ 0 · sibling-sync publish-kernel lineage ✓
             successor-link ✓ (resolves to an existing page)
edges        superseded-by → design-publish-kernel.md
             part-of-same-decision → design-publish-kernel.md
(no usage demo — a kb page has no runtime behaviour to exercise;
 the absence is the signal, not an omission)
```

**3. test-add** (descriptive *is* the story):

```text
kind         test-add
identity     tests/test_branching.py::test_lease_anchor
descriptive  When an event names a target branch whose remote tip moved
             under the agent mid-run, publish now force-with-leases
             against the recorded OID rather than clobbering the newer
             remote commit.
stats        exercises  daemon.publish (lease arm) + resolve_publish_plan
             asserts    the emitted push command string carries
                        --force-with-lease=<branch>:<oid>
             fixtures   reuses tmp_repo + fake_remote (shared)
edges        exercising-tests-for → branching.resolve_publish_plan
```

**4. walkthrough** (cross-cutting flow; ordered item refs):

```text
kind         walkthrough
identity     wt:review-event-round-trip
descriptive  How a reviewer's inline comment becomes a brr task and a
             threaded reply — the cross-cutting path no single item
             card carries.
refs (ordered)
  1. gate-poll-review-comments   (polling._poll_mention_review_comments)
  2. event-normalise             (parse._format_review_comment_body)
  3. task-construct              (github_kind = "pr-review-comment")
  4. response-post-in-thread     (delivery → /pulls/{n}/comments/replies)
setup        a reviewer leaves an inline diff comment mentioning @brr
action       the gate polls /pulls/comments, normalises, and the daemon
             constructs a task scoped to that hunk
outcome      brr replies in the same review thread, quote-prefaced
grounded-by  tests/test_github_gate.py (review-comment integration path)
```

**5. uncertainty — concern subkind** (the agent's honest WTF surfacing):

```text
kind         uncertainty · concern
identity     trigger: reading polling._poll_mention_review_comments
severity     med
descriptive  The seen-id cap (`sorted(seen)[-_SEEN_CAP:]`) silently
             forgets the oldest review-comment ids. On a busy PR this
             could re-surface an already-handled comment as new. I did
             not touch it — it was outside this task's scope.
proposed-resolution
             raise the cap, or switch from a bounded id-set to a
             time-window dedup keyed on comment timestamp. Flagging so
             you can decide whether to fix it here or file it.
edges        related → gate-poll-review-comments item card
blast-radius the gate's review-comment dedup only; no other card depends
             on this behaviour
```

Card 5 is the model working as intended: the change under review was
clean, but the agent noticed something *adjacent* that looked wrong and
said so, with a severity and a proposed resolution, rather than
emitting a surface that reads "everything is fine."

## Reading order: uncertainty cards first

A concrete rule for every renderer and for the PR-body projection:
**uncertainty cards land at the top of the reading order**, before
per-item cards and walkthroughs. They short-circuit the reviewer's
"what should I scrutinise hardest?" question and are the
highest-value first read.

Renderers may collapse the section when there are no uncertainty cards
— and that collapse preserves the absence-is-signal principle: "the
agent flagged no confusions" is itself meaningful information, not an
empty placeholder.

## Failure modes: agent uncertainty as first-class output

**Why this exists.** The rest of the card model implicitly assumes the
agent executed a well-scoped task successfully. Real PRs often come
from half-defined prompts the agent didn't fully understand; the agent
forms opinions and uncertainties during a run; suppressing them
produces a brittle, dishonest review surface. A pack that always reads
"everything is fine and clean" cannot be telling the truth.

**Four uncertainty subkinds:**

- **assumption** — "your prompt didn't specify X; I assumed Y; here's
  why; flag if wrong."
- **concern** — "Y seems wrong upstream but you didn't ask; I left it;
  flagging in case you want to fix it here." (Card 5 above.)
- **dilemma** — "I had to choose between A and B; chose A because of
  constraint Z; here's the path not taken."
- **out-of-scope-flag** — "the task implied Z but I didn't do it
  because it reads as out of scope; you may want to."

**Honesty applies to the agent's own state.** The honest clamp here
means the agent reports its *own* confusions truthfully, not just the
shape of the change. This is the failure-mode honesty the rest of the
surface can't provide.

**Runner-prompt implication.** The prompt step that produces the pack
instructs the agent to surface uncertainty cards explicitly, with
examples and severity guidance. No code in this commit; the
integration shape is named in **Where the runner / publish kernel wire
in**.

## Discipline: the six clamps

Every emitted element passes all six:

1. **Sharp.** A reviewer skims a card in 5–10 seconds; every element
   earns its space (a *form* constraint).
2. **Helpful.** Every element load-bears for a reviewer decision (a
   *function* constraint). Distinct from sharp: a card can be small and
   still useless — that passes sharp but fails helpful.
3. **Honest.** Every stat answers a real question; possibility lore
   states properties that are actually true; usage demos use real
   values; uncertainty cards report the agent's actual state.
4. **Non-prescriptive.** Cards describe; the reviewer composes the
   verdict. No "this is the cornerstone of strategy X."
5. **Emit-iff-honest.** Conditional axes appear only when there is real
   material behind them; absence is signal (Card 2's missing demo).
6. **Substrate-honest, not cosplay.** Aesthetic choices earn their
   space by improving readability / navigation / usefulness — the same
   bar as a cosmetic stat.

**The Occam's-razor reading-order test.** A reviewer should reach
"approve / dive deeper / ask a question" within seconds of landing on a
card. If they can't, the card is doing too much, or doing the wrong
thing.

The sharp-vs-helpful split is the one most worth holding explicitly:
trimming a card until it skims fast (sharp) does not guarantee each
surviving element earns a reviewer decision (helpful), and the reverse
holds too. Both clamps, independently.

## PR body as the v0 surface

A stable Markdown template projected from the pack — the first
surface diffense ships, well before any TUI or web target. v1 is the
inspect-mode surface; this is the meaningful improvement available now.
Each section is labelled by how it was produced (`LLM` = generated
prose, `mechanical` = derived from structured state):

```markdown
## ⚠ Uncertainty   <!-- only present when uncertainty cards exist -->
- **[concern · med]** seen-id cap may re-surface handled review
  comments on busy PRs — left as out of scope.   (LLM)

## Intent
One-paragraph statement of what this PR is for.   (LLM)

## Narrative
The setup → action → outcome arc across the change.   (LLM)

## Touched
- `src/brr/branching.py` — resolve_publish_plan gains a lease anchor
- `kb/design-daemon-landing-branch.md` — flipped to superseded
- `tests/test_branching.py` — +1 case (lease arm)   (mechanical)

## Reading order
1. Uncertainty (above)
2. branching.resolve_publish_plan
3. the test that exercises it   (mechanical)

## Deferred / open
- the seen-id cap concern, if not fixed here   (LLM)
```

The **Uncertainty** section sits at the top when present, per
**Reading order**, and is omitted entirely when there are no
uncertainty cards.

## Where the live agent fits

Future. An in-context Q&A surface over the cards, reading the pack as
grounding context so its answers stay anchored to the actual change.
Constrained by the same six clamps as every other surface.

## Project boundary (semi-open)

- **Pack generation** lives in brr (runner integration at publish
  time).
- **Substrate** lives in brr — the Textual app under
  `src/brr/diffense/`.
- **Local viewer** ships as part of the brr package via `brr review`.
- **Hosted view** is a brnrd-dashboard target rendering the same pack
  via HTMX ([`plan-brnrd-dashboard-mvp.md`](plan-brnrd-dashboard-mvp.md)).

**Open:** whether the substrate codebase is in-tree or its own
extras-installed `brr-diffense` package. It leans in-tree, decided in
the implementation plan. The likely shape is an interactive viewer over
a pack + substrate that a runner produces as an artifact, which makes
it naturally part of brr; productising it more broadly is a plausible
later step, not a launch concern.

## Where the runner / publish kernel wire in (deferred)

This touches the publish kernel
([`design-publish-kernel.md`](design-publish-kernel.md)): the runner
emits the pack before publish, and on publish the daemon writes the
body projection via `gh pr edit --body` (or equivalent). The runner
prompt in [`src/brr/prompts/`](../src/brr/prompts/) gains a step —
"produce the diffense pack using this schema, under the six clamps;
surface uncertainty cards explicitly when assumptions / concerns /
dilemmas / out-of-scope flags arose; use existing and new tests as
grounding evidence." No code in this commit; the integration points
are named so the implementation plan inherits them.

## Adjacencies that ship-or-shipped already

- The shipped `pr-review` / `pr-review-comment` event handling in
  [`src/brr/gates/github/`](../src/brr/gates/github/) (see
  `constants.py` event kinds and `polling._emit_review_event_if_mentioned`)
  is the **gate-side** counterpart: brr *reacts* to reviews. diffense
  is the **human-side** counterpart: brr *produces* surfaces humans can
  review well. The boundary doc is
  [`design-github-gate-vs-brnrd-app.md`](design-github-gate-vs-brnrd-app.md).
- The accepted [`plan-kb-subcommand.md`](plan-kb-subcommand.md) is
  composable infrastructure for the local viewer (`brr kb doc <page>`
  feeds kb-page cards).
- The [`plan-brnrd-dashboard-mvp.md`](plan-brnrd-dashboard-mvp.md) is
  the natural home for the hosted-web target.

## Open questions narrowed

- **Pack JSON schema.** A discriminated union of item kinds +
  walkthroughs + uncertainty kinds; finalised in the implementation
  plan after a hand-authored prototype against one real recent brr PR.
- **Substrate technology.** Textual proposed; validated via the spike
  before locking.
- **Aesthetic locking.** Validated alongside the substrate spike.
- **GIFs as a future axis.** Textual transcripts at v0; revisit if
  insufficient.
- **Locked-abilities axis.** Deferred future direction.
- **Card-level reviewer state.** Local-only in `.brr/`, or roundtripped
  to forge review comments? Likely local-first.
- **LLM token budget** for the pack-generation step. Bounded by the
  always-vs-conditional split + the six clamps + the uncertainty
  discipline; revisit on real runs.
- **Live agent on cards.** Addressed when that slice opens; same
  clamps.
- **Naming.** `diffense` adopted as the working name; the pop-culture
  alternatives `pensieve` / `holocron` were considered and dismissed as
  cosplay-leaning. Locking deferred until the substrate spike confirms
  the brand fits the surface.

## Read next

1. [`plan-kb-subcommand.md`](plan-kb-subcommand.md) — the kb read
   surface the local viewer composes over.
2. [`design-publish-kernel.md`](design-publish-kernel.md) — where pack
   emission and body projection wire into publish.
3. [`subject-kb.md`](subject-kb.md) — the kb graph the pack renders.
4. [`design-github-gate-vs-brnrd-app.md`](design-github-gate-vs-brnrd-app.md)
   — the gate-side review-event counterpart.
5. [`plan-brnrd-dashboard-mvp.md`](plan-brnrd-dashboard-mvp.md) — the
   home for the hosted-web target.

## Lineage

Drafted 2026-05-28 from a conversation across 2026-05-27/28, through
five refinement passes:

1. audience + LLM-generation;
2. inspect-mode + Souls-menu lore framing;
3. perceived-gain + the sharp / honest / non-prescriptive clamps;
4. tests-as-grounding + the walkthrough kind + parallel rendering +
   "design, not research";
5. small-team audience + the helpful clamp + the `diffense` name +
   uncertainty cards as a first-class kind.

Proposed, not accepted — the substrate spike and a hand-authored
prototype pack against a real PR are the gates before the `Status`
line flips.
