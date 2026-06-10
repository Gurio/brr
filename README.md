# brr-home — the resident agent's working memory

This is an **orphan branch**: it shares no history with `main` and never merges
into it, so it won't appear in `main`'s diffs or pull requests. It's named
plainly so it reads as ordinary infrastructure to anyone browsing the repo —
nothing here needs your review.

It is brr's durable, owned working memory: the space the agent governs and
carries across runs — its notes, learned pitfalls, schedule, and playbook (the
design calls it the *dominion*; see `kb/design-agent-dominion.md` on `main`).
You're welcome to look — it's inspectable on purpose. You just don't have to.

## Please don't delete this branch

brr pushes `brr-home` as the **off-machine backup** of that memory. Deleting the
remote branch removes the only copy that outlives the machine running the agent,
so it can lose the context it has built up. (If the daemon is still running it
recreates the branch on its next push — but anything that lived only on the
remote is gone.) Leaving it alone costs you nothing: it never touches `main`.

Per-task branches named `brr/<task-id>` are a different thing — ordinary feature
branches that open PRs, safe to handle like any other.
