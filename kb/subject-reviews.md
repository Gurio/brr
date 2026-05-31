# Subject: reviews

Review knowledge currently centers on **diffense**, brr's kb-first PR
review surface. The accepted product shape is a structured review pack
rendered as a zoomable graph of cards: summary first, then concerns, then
item and walkthrough cards that bottom out in mechanical evidence such as
the real diff, source file, rendered kb page, or commit-pinned forge
permalink.

The implemented slice today is deliberately narrower than the full
design. [`src/brr/diffense/`](../src/brr/diffense) contains a render-only
web spike over the hand-authored
[`diffense-prototype-pr64.md`](diffense-prototype-pr64.md) pack: static
HTML/CSS/vanilla JS plus a stdlib inliner. It validates the read model
(one breadcrumb stack for lateral moves and zoom-drills; code leaves
jump to the forge at v0) but does not yet provide pack generation,
schema validation, pack transport, runner/publish wiring, a local
`brr review` server, or card feedback actions.

The canonical design is [`design-diffense.md`](design-diffense.md). The
PR #64 prototype is a receipt and schema pressure test, not a separate
product surface; its durable findings are the summary card, open
card-kind taxonomy, gloss-first uncertainty cards, and blocking locator
resolution. The feedback loop depends on the shipped GitHub
`pr-review-comment` handling described in
[`design-github-gate-vs-brnrd-app.md`](design-github-gate-vs-brnrd-app.md),
while pack emission and PR-body projection belong to the publish path in
[`design-publish-kernel.md`](design-publish-kernel.md).
