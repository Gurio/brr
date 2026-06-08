# brr-home — the resident agent's working memory

This is an **orphan branch**: it shares no history with `main` and never merges
into it, so it won't appear in `main`'s diffs or pull requests. It's named
plainly so it reads as ordinary infrastructure to anyone browsing the repo —
nothing here needs your review.

It is brr's durable, owned working memory: the space the agent governs and
carries across runs (the design calls it the *dominion*; see
`kb/design-agent-dominion.md`). You're welcome to look — it's inspectable on
purpose. You just don't have to.
