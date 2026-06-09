## Publishing your change

When this task produced a review-worthy committed change and Review pack
publishing is enabled in the Task Context Bundle, you own the PR delivery:
validate the pack, project it into the PR body, then address the forge
through your outbox.

1. Validate the pack before publishing:
   `brr review --check <Review pack path>`.
2. Derive the title and body from the same pack:
   `brr review <Review pack path> --pr-title --fallback-title <head-branch>`
   and `brr review <Review pack path> --pr-body --relay`.
3. Drop one complete outbox file. Use `gate: github` (or `gate: forge`,
   an alias for the GitHub forge gate), `github_delivery: pull-request`,
   `base`, `head`, and `title` in frontmatter; the file body is the PR
   body. `head` is the branch brr will publish when the thought ends, and
   `base` is the branch the PR should target.

Example shape:

```markdown
---
gate: github
github_delivery: pull-request
base: main
head: brr/descriptive-branch
title: feat: publish review packs from the resident
---
<the Markdown body from `brr review <pack> --pr-body --relay`>
```

The GitHub gate opens or refreshes an open PR for that head branch
idempotently. If the outbox drains before brr finishes pushing the head,
the done forge event stays queued and the gate retries on its next loop.
Do not publish when the task produced no review-worthy change, when the
pack failed `--check`, or when Review pack publishing is disabled.
