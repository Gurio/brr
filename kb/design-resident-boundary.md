# Design: the boundary — one envelope, two rails, and the medium vocabulary

Status: active synthesis on 2026-06-27. Reconciles a maintainer design message
(Telegram, evt-9dp2/slhg) against the three pages shipped the same day —
[`design-runner-back-channel.md`](design-runner-back-channel.md) (the boundary
mechanism), [`design-runner-media.md`](design-runner-media.md) (cost/medium
layer), and [`plan-cost-aware-cockpit.md`](plan-cost-aware-cockpit.md) (the
cost/notification braid). It carries the conversation's settled answers and the
two open forks that still need a maintainer nod.

The message braided several threads; this page keeps them in one place so a
future wake resumes the frame instead of re-deriving it.

## 1. The boundary is one concept — two rails of different density

**Question (maintainer):** *"Do the boundary portal and hooks want to be one
concept? Why do we still want `portal-state.json` separate from the hooked
stats — should they show identical data, just that the file is more 'live'?"*

**Answer: one concept, one source, two delivery rails — and deliberately not
identical at every instant.**

The *boundary* is the resident's perception of its operating envelope: pending
events, delivery/budget posture, SCM state, and the work-status resources facet
(quota / cost / coexisting runs / remote SCM). There is one concept and one
source of truth. It reaches the resident on two rails:

- **The snapshot rail** — `portal-state.json` / `inbox.json`, daemon-written
  every heartbeat. *Always complete*, queryable, daemon-owned. It is (a) the
  source the injection rail reads from, and (b) the fallback for Tier-0/1
  runners that have no hook at all. This is the *query* tier of the
  perception model (large/complete state, fetched on demand).
- **The injection rail** — the hook capsule (`brr hook <phase>` →
  `format_delta`), woven into the scroll at runner boundaries. It is a
  **salience-gated delta**: it renders only what is worth spending a turn on,
  and (mid-run) only when `change_token` moved. The resources line is rendered
  only at the **seed/stop** boundaries, not on every post-tool tick, precisely
  so editing churn injects no noise.

So the file is **not** "the same data, just more live." It is the complete-state
rail; the hook is the gated-projection rail. Collapsing them into one
byte-identical surface would re-introduce the firehose we cut once already
(see the volatility × relevance × size placement rule in
[`design-runner-back-channel.md`](design-runner-back-channel.md) and the
perception model: inject what is small-or-volatile, query what is
large-and-complete). The portal json is not redundant; it is the snapshot the
gated injection reads from and the no-hook fallback.

**The concrete divergence the maintainer spotted is real but expected.** Today
two renderers project the same resources data: `daemon._resources_facet` builds
the JSON snapshot; `hooks._format_resources` builds the woven one-liner. They
already agree on the four facets (quota / cost / coexisting-runs / remote-scm),
but the woven line is seed/stop-gated, so a mid-run boundary shows the rich
snapshot in the file and a quieter capsule in the scroll. That asymmetry is the
tier-2/tier-3 design, not a bug.

**The genuine improvement** is not "make them identical" but **"let a
*salience-relevant* resource change ride the post-tool delta"** — e.g. quota
crossing near-empty, a coexisting run appearing, a relay cap approaching. Those
are exactly the moments the boundary should interrupt with the resource line
mid-run. The plumbing already supports it (`change_token` gating); what is
missing is the collectors that make any resource facet move at all. So the work
is *populate the facets*, not *merge the rails*. The one cheap hardening worth
doing regardless: keep the JSON and the woven projection reading from a **single
projection helper** so they can never drift in *which* facets they carry (still
open — there are now three renderers: `_resources_facet`, `_format_resources`,
`_format_portal_state`, agreeing on the same four keys by convention).

**Shipped 2026-06-27 (evt-go5z): three-state facet honesty.** The maintainer
agreed the rails are not identical *but* asked the boundary to "show
substantially more missing data" than the old flat `unavailable`. The fix
distinguishes the two kinds of "missing" the resident must not conflate:

- `known` — proven value this heartbeat.
- `absent` — the collector ran and there is genuinely nothing: **no PR for this
  branch yet**, no quota snapshot the medium exposes, **no outbound message
  sent**. Affirmative-empty — the same logic the closeout capsule uses for "0
  pending events". Absence is data, surfaced on purpose.
- `unimplemented` — the collector is not built (cost metering, coexisting runs),
  with a `required` flag separating expected-to-grow from someday-niceties.

The same wake also surfaced **"running long"** (elapsed past the soft budget,
flagged in `budget.long_running`) and the **no-outbound-at-closeout** receipt,
across all three rails (JSON portal, woven hook line, `brr portal state` CLI).
This is the visible half of §5's PR posture and the first concrete step of
"populate the facets"; the *values* behind `known` (live quota/cost numbers)
still need their collectors.

## 2. The open-source vs brnrd split — the static envelope is not too limiting

**Question (maintainer):** *"Self-deployed / brr daemon handles CLI medium,
quotas and credits data; brnrd (subscription) handles the boundary. Self-deployed
defines the boundary statically — isn't that too limiting? Still
open-source-friendly?"*

The earlier "limits" model is the resolution: the user sets an **envelope**, and
the resident **acts freely, attentively, and analytically within it**. Split
that into mechanism vs data source and the open-source worry dissolves:

- **The envelope mechanism is open-source.** A self-deployed user defines the
  boundary in config — allowed media, per-run/per-day caps, fallback policy,
  which providers to probe. The resident reads that static envelope and acts
  freely inside it. Static does **not** mean limiting: the runner is not asking
  permission for every step; it is operating analytically within a declared
  envelope, exactly the agreed model.
- **The live/authoritative data source is the brnrd value-add.** brnrd owns the
  wallet and the relay keys, so it can supply *authoritative live* quota/credit
  signals and *remote* envelope control (adjust caps, top-up, pause from the
  service side) without the user editing a file. That is the "service helps you
  with remote controls" half — a paid convenience layer over an open mechanism,
  not a gate on the open mechanism.

So the boundary is **not** "brnrd-only." Self-deployed gets the full boundary
concept with a static envelope + best-effort local signals (CLI error text,
manual snapshots, response headers for owned keys). brnrd adds the live
authoritative rail and remote control on top. This keeps brr genuinely
open-source-friendly while giving the service a real, fair value-add — consistent
with [`decision-llm-relay.md`](decision-llm-relay.md) (BYO stays free/default;
brnrd-owned intelligence pays provider cost + a transparent service fee).

## 3. Vocabulary — runner / run / weave / medium (SETTLED → `medium`)

**Maintainer's clarification:** stop conflating the *entity* (the weaver) with
the *executor type* (Codex / Claude / Gemini). Proposed:

- **runner = the resident & LLM weaving** (the weaver/entity).
- **run = the weave** (one wake's work).
- the executor (Codex / Claude / Gemini / custom) = **medium / substrate /
  shell** — he is reaching for the right noun.

**Recommendation: adopt `medium` for the executor.** Reasons:

1. The codebase already glosses it that way — the Mode block literally renders
   *"Runner: claude — the compute medium this thought runs on."* The word is
   already drifting into place.
2. [`design-runner-media.md`](design-runner-media.md) already uses "medium" for
   the layer above static profiles.
3. **Séance resonance.** A medium *channels a spirit*. The maintainer's own
   phrase was "the tools we use to invoke the spirit from remote LLMs," and the
   playbook frames the resident as a spirit of air/fire. "Medium" is the
   poetically-true noun, and it ties to the *ornamented-scroll* register the
   portal reshape is converging on. "Shell" is evocative but overloaded (Unix
   shell); "substrate" is a fine clinical synonym to keep for technical prose.

With `medium` as the executor, **`runner` largely dissolves** — the weaver is
"the resident" (our existing word) and the wake's work is the "run/weave." That
is a satisfying *cut*, not just a rename, and fits the pre-release bias toward
collapsing names that no longer carry their weight.

**Resolved 2026-06-27 (evt-go5z): the maintainer picked `medium`** ("let's do
medium"). So the noun is fixed: the executor (Codex / Claude / Gemini / custom)
is the **medium**, `run`/`weave` is the wake's work, and `runner` dissolves into
"the resident". `substrate` stays available as a clinical synonym for technical
prose.

**The rename is now a sanctioned follow-up run, deliberately not folded into the
boundary work.** `runner` is embedded across config keys (`runner`,
`runner_cmd`), prompts (`runners.md`), kb page names (`design-runner-*`), and
code (`resolve_runner`, runner profiles). It is a wide, mechanical blast that
earns its own dedicated run with a migration shim for live config — kept
separate so a behavioural change (this boundary enrichment) and a pure rename
do not tangle in one diff.

## 4. Cost manifests per medium, and the respawn navigation matrix

**Maintainer:** *"Cost manifests per medium (not sure how)"* and the respawn
matrix — *"a sorted / heat-mapped matrix giving clear navigation by price per
token, grouped by medium type, noting whether already successfully used,
followed by the subscription quotas ranked beside the matrix."*

This is the structured `runner_media` portal facet already sketched in
[`design-runner-media.md`](design-runner-media.md) §Quota and credit signals,
read as a *navigation surface* rather than a flat string. The manifest per
medium = the medium's row: model, provider, owner, cost class, cost_rank
(price-per-token proxy), quota source + freshness, hook capability, billing
posture, and **whether it was already used successfully this thread**. The
matrix = those rows sorted/heat-mapped by cost_rank and grouped by medium type;
the quota rankings sit beside it as the subscription view.

Crucial guardrail from [`plan-cost-aware-cockpit.md`](plan-cost-aware-cockpit.md):
this is **historical pre-analysis, never a forward dollar estimate**. The matrix
shows price *rank* and what comparable past weaves consumed; it does not quote a
projected total for this run. The "crisp visualization → simpler decision"
intuition is right, and it is a *boundary* surface (a perception the resident
weaves), not a separate dashboard.

This is also the substrate of the society-of-mind concurrency the maintainer
described: cheap respawns chosen off the matrix + live consumption stats on the
injection rail let a weave spawn siblings, block on their output files / events,
or continue — and see the ready ones arrive on the boundary. brr is single-flight
*per dominion* today, so `coexisting_runs` renders `unavailable`; the matrix is
the precondition for lighting it up.

## 5. Failover as a receipt, not a perfect classifier — and PR stats on the boundary

**Maintainer (named honestly):** deciding whether an agent *legitimately* failed
is "quite problematic to situationally triage," and "we gotta release the product,
avoiding this rabbit hole."

**Stance: do not build a perfect failure classifier before release. Make failure
cheap to recover from, and make the recovery state *visible on the boundary*.**

- **Interim work receipt.** Every run commits early and keeps a continuously
  updated branch (the diff is the receipt that survives a kill — already the
  cost-aware chunking discipline). A crashed or exhausted weave leaves a real,
  resumable artifact, not nothing.
- **Paid cloud failover** (pass-through-billed agents) is the *smooth* recovery
  path when a self-deployed daemon dies — consistent with
  [`plan-failover-compute.md`](plan-failover-compute.md) and the relay decision.
  It is the easiest fallback, not the only one (the user can also wait for quota
  reset, fix the daemon, or clarify).
- **PR stats belong on the boundary interweave.** The boundary already carries
  the local SCM facet (`scm`: unpushed/modified on the worktree). Extend the
  resources facet's `remote_scm` to carry the **PR posture** — branch pushed?,
  **PR open / not yet created**, checks state — so a weave perceives "your work
  has a branch but no PR yet" as woven context. Especially the *not-yet-created*
  case the maintainer called out: the receipt is most valuable exactly when the
  PR does not exist yet, because that is when the work is at risk of being
  invisible. This is the same "affirmative-empty signal" logic the closeout
  capsule already uses for pending events.

The triage minimum brr *does* need is the failure-class distinction already in
[`design-runner-media.md`](design-runner-media.md) §Implementation sequence step
5 (quota / auth / provider-outage / quality-escalation / no-response) — enough to
route automatic fallback for the *unambiguous* operational failures, while
*ambiguous* failures surface to the user with the receipt attached rather than
being auto-adjudicated. That is the release-able shape: cheap recovery + honest
escalation, not a perfect judge.

## 6. Fairness / business posture — BYO free, paid-through-the-house everywhere it fits

**Maintainer:** *"Don't cling to previously planned shapes; don't gate
open-source users, but offer as much as possible paid through the house. Pricing
fair, but everywhere we can offer. Make a viable business — be fair with me."*

This does not contradict the open-source posture in §2; it sharpens it.
[`decision-llm-relay.md`](decision-llm-relay.md) already holds the spine: **BYO
stays free/default; the house offers a paid path everywhere a user would
otherwise hit friction** (no local quota, no credentials, a crashed daemon, a
need for a stronger medium). The fairness contract is *transparency*: provider
cost and the relay/service fee shown as separate line items, per-run caps, no
silent card-on-file top-ups. The product line can call it "intelligence credits,"
but the ledger keeps `llm_provider_cost`, `llm_relay_service_fee`, and
`managed_compute_ops` distinct. The viable-business requirement and the
open-source requirement meet at "fair, transparent, everywhere — never a gate on
the free mechanism, always an offered convenience over it."

## Settled vs open

**Settled this conversation:**
- The boundary is one concept, two rails of different density; the portal json
  is the snapshot/fallback rail, not a redundant copy. (§1)
- Self-deployed static envelope + best-effort local signals is the open
  mechanism; brnrd adds the live authoritative rail + remote control. (§2)
- **Vocabulary:** `medium` is the noun for the executor; `runner` dissolves into
  "the resident". A dedicated rename run follows. (§3, evt-go5z)
- Failover = cheap-recovery + visible receipt + honest escalation, not a perfect
  classifier; PR posture (incl. not-yet-created) joins the boundary. (§5)
- Business posture reconciles with open-source via transparent
  paid-everywhere-it-fits. (§6)

**Shipped (evt-go5z):**
- Three-state facet honesty (`known`/`absent`/`unimplemented` + `required`),
  PR-not-created posture, `long_running`, and no-outbound-at-closeout — across
  the JSON portal, the woven hook line, and `brr portal state`. (§1)

**Open forks / next builds:**
- **The rename run** (§3) — `runner` → `medium`/`resident`, its own dedicated run.
- **Populate the `known` values:** live quota/cost collectors so a facet carries
  a real number, not just an honest `absent`. The matrix (§4) and the
  near-empty-quota mid-run injection both depend on it.
- **Single projection helper** so the three renderers can never drift in *which*
  facets they carry. (§1)

## See also

- [`design-runner-back-channel.md`](design-runner-back-channel.md) — the boundary
  mechanism (native hooks; the injection rail).
- [`design-runner-media.md`](design-runner-media.md) — the medium/cost layer and
  the structured `runner_media` facet behind the matrix.
- [`plan-cost-aware-cockpit.md`](plan-cost-aware-cockpit.md) — cost
  self-awareness, the historical-pre-analysis guardrail, operator legibility.
- [`decision-llm-relay.md`](decision-llm-relay.md) — BYO-free / paid-relay
  pricing spine.
- [`plan-failover-compute.md`](plan-failover-compute.md) — compute-host failover,
  the sibling axis to medium failover.
