# Design: diffense - kb-first PR review experience

Status: accepted on 2026-05-29 - the card / zoom / navigation model is
validated by the hand-authored [PR #64 pack](diffense-prototype-pr64.md)
and the renderer spike in [`src/brr/diffense/`](../src/brr/diffense/).
Only the renderer spike exists in code today; pack generation, schema
lock, transport, runner wiring, and the `brr review` local server remain
implementation work.

diffense is brr's PR review surface for agent-produced changes. It turns
the raw PR into a structured **review pack** - a zoomable graph of cards
grounded in code, kb pages, commits, tests, and the conversation that
drove the work - and renders that pack for a human reviewer. The design
exists because a brr PR is often half `kb/`; raw forge diffs flatten the
knowledge graph exactly where reviewers need synthesis, lifecycle
markers, subject hubs, and rendered Markdown.

Companion pages:

- [`subject-kb.md`](subject-kb.md) - kb structure diffense reads from.
- [`plan-kb-subcommand.md`](plan-kb-subcommand.md) - the planned `brr kb`
  read surface for rendered kb-page leaves.
- [`design-publish-kernel.md`](design-publish-kernel.md) - the publish
  boundary where pack generation and PR-body projection attach.
- [`design-github-gate-vs-brnrd-app.md`](design-github-gate-vs-brnrd-app.md)
  - the shipped `pr-review-comment` event path used by the feedback
  loop.
- [`plan-brnrd-dashboard-mvp.md`](plan-brnrd-dashboard-mvp.md) - future
  hosted renderer home.
- [`design-agent-ergonomics.md`](design-agent-ergonomics.md) - sibling
  back-channel for operator-facing agent friction signals.

## Current shape

diffense is one pack, multiple projections:

- **Review pack.** A JSON artifact with metadata, reading order, cards,
  typed lateral edges, zoom levels, and locators. It is the contract; all
  renderers consume the same bytes.
- **Responsive web renderer.** The first real surface. The spike in
  [`src/brr/diffense/`](../src/brr/diffense/) is dependency-free:
  `render.py` inlines a pack into `template.html` and produces a
  self-contained HTML file. The spike validates the read model, not the
  full product.
- **PR-body projection.** A lossy Markdown fallback written to the forge
  PR so any reviewer gets the summary and surfaced concerns without
  installing brr.
- **Later consumers.** CLI/TUI, hosted brnrd dashboard view, pack diffs,
  and live Q&A over cards remain follow-up surfaces over the same pack.

The first implementation slice is web-first and brnrd-independent. A
local `brr review` server is planned so self-hosters can open the surface
in a browser or phone on a LAN/tunnel. Hosted brnrd rendering becomes the
clean no-tunnel mobile path later, but diffense must not wait for brnrd
or depend on brnrd-specific services.

## Inputs

The runner can build a better review pack than a generic PR tool because
brr already has structured context:

- PR metadata and diff from the forge.
- Commit graph and conventional commit messages.
- `.brr/conversations/` history for the conversation that drove the run.
- `kb/` graph, lifecycle markers, subject hubs, and curated
  [`kb/log.md`](log.md) entries.
- Test names and assertions as grounding evidence for usage demos.
- Runner-side uncertainty: assumptions, concerns, trade-offs, and
  explicit out-of-scope calls formed while doing the work.

The pack should carry summaries and locators, not regenerated copies of
large artifacts. Ground truth remains the source file, rendered kb page,
diff hunk, test, or forge permalink the card points at.

## Card model

The review surface is a graph with two navigation axes:

- **Lateral edges** connect related cards: calls, implements, part-of,
  exercises, shares-invariant, referenced-by, and similar relationships.
- **Zoom** descends from gloss to detail to a mechanical ground-truth
  leaf. The leaf is not LLM prose; it is a locator to the actual source.

Core card families:

- **Summary card.** One per pack, always first. It orients the reviewer:
  shape of the change, main arcs, surface area, counts in service of the
  shape, and a pointer to any concerns.
- **Item cards.** Typed units of change such as `code-fn-edit`,
  `code-fn-new`, `code-module-split`, `code-move`, `kb-page-edit`,
  `lifecycle-flip`, `test-add`, or `dep-add`.
- **Walkthrough cards.** Ordered composite stories with setup, action,
  outcome, and member cards; useful when the human story crosses several
  item cards.
- **Uncertainty cards.** First-class assumptions, concerns, dilemmas,
  out-of-scope calls, follow-ups, and meta-schema gaps. They lead with
  the plain-language worry, then show nuance, tension references,
  locators, and proposed resolution where that is useful.

The kind set is an open core. A pack may declare a `custom` item kind
when the core taxonomy lacks an honest shape, but it must still carry the
normal locators and should raise a meta uncertainty card so recurring
custom kinds can be promoted deliberately. The PR #64 prototype promoted
`code-module-split` through exactly that path.

## Rendering model

The renderer spike settled the v0 interaction model:

- A focused card renders as the main panel.
- Opening a lateral edge or zoom member pushes the current card into a
  breadcrumb heading-bar stack; lateral navigation and zoom-drills share
  that one stack.
- Code leaves are jump-to-forge at v0: the card shows `path:line` and a
  commit-pinned permalink. Inline diff/code rendering can come later.
- Cards keep a terminal-looking, dense, information-first aesthetic, but
  the substrate is ordinary responsive HTML. The design keeps the
  aesthetic only where it improves readability or navigation.

The renderer is deliberately small: `template.html` is generic over any
pack, and `render.py` embeds the JSON into a self-contained page. That
matches the near-term self-hosting story and avoids adding runtime
dependencies before the generator is proven.

## Feedback loop

diffense is not a separate review authority. The forge PR remains the
shared source of review state. When a reviewer flags a card, the durable
path is:

1. The UI creates an anchored forge comment, ideally tied to the card's
   locator.
2. The shipped GitHub gate sees the `pr-review-comment` mention.
3. brr creates a scoped task.
4. The next publish emits a new pack.

Ephemeral "ask about this card" interactions can later run through a
live agent over the pack. Durable requested changes route through the
forge comment path so the normal task lifecycle, branch publication, and
audit trail stay intact.

## Validation

Pack validation is a planned command, not shipped code yet. The accepted
design requires `brr review --check` or an equivalent validator to reject
packs with unresolvable locators, broken card targets, invalid kind
payloads, missing ground-truth leaves, or overlong summary prose. The PR
#64 prototype demonstrated why this matters: grounding caught an invented
`cache.get_with_etag` symbol and forced the conditional-GET card to point
at the real `client._request` / `_api_get` home.

Validation should separate LLM-authored summaries from mechanical data.
Counts, file lists, locators, and test names are derived. Prose earns its
place by being short, checkable, and connected to ground truth.

## Open implementation work

- Lock the pack JSON schema and versioning story.
- Build pack generation at the runner/publish boundary.
- Add the local `brr review` render/serve command and a validator.
- Choose transport for making the pack reachable from the PR: body
  marker block, git note, `refs/diffense/*`, or a size-threshold mix.
- Define how pack iterations are stored and how a reviewer sees "what
  changed since I last reviewed."
- Add card-level reviewer state if it proves useful.
- Decide whether and when inline diff/code leaves, GIF demos, live Q&A,
  CLI/TUI, and hosted brnrd rendering earn their slices.

## Rejected alternatives

- **Plain PR body only.** Useful as fallback, too lossy as the product.
- **Forge-hosted static artifact.** Too little interaction, too much
  drift, and too tightly coupled to comment semantics.
- **TUI first.** Friendly for terminal-native self-hosters, but a poor
  phone review surface and a second renderer before the pack is proven.
- **Hosted web only.** Good long-term, but blocks local dogfooding on
  brnrd and network availability.
- **Reviewable / Graphite-style workflow clone.** Those tools optimize
  stack mechanics and skim-approval. diffense is the depth-first,
  kb-aware understanding surface that can sit beside them.

## Lineage

Lineage: drafted 2026-05-28 and accepted 2026-05-29 after the design
converged on a web-first zoomable card graph, a hand-authored PR #64 pack
validated the schema pressure points, and the renderer spike validated
the breadcrumb/zoom read model. Earlier PR-body-first, Textual/TUI-first,
and separate-graph-navigation shapes were replaced because mobile review,
local dogfooding, and implementation simplicity all pointed to one
responsive web renderer over a shared pack.

## Read next

1. [`diffense-prototype-pr64.md`](diffense-prototype-pr64.md) - concrete
   hand-authored pack against PR #64, rendered with findings.
2. [`plan-kb-subcommand.md`](plan-kb-subcommand.md) - kb read surface the
   renderer will compose with.
3. [`design-publish-kernel.md`](design-publish-kernel.md) - publish step
   where pack emission and PR-body projection attach.
4. [`design-github-gate-vs-brnrd-app.md`](design-github-gate-vs-brnrd-app.md)
   - review-event handling the feedback loop rides.
5. [`design-agent-ergonomics.md`](design-agent-ergonomics.md) - sibling
   task-boundary side channel with a different audience.
