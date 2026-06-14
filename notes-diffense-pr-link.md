
## [2026-06-14] #136 — diffense link missing + issue-linking seam (proposal stage)

Task task-260614-2344-in48 on thread github:136. User: merged PR #136 has a
generated diffense body but NO interactive link in the header (unlike other PRs),
and `(#126)` in the title doesn't GitHub-link the issue. Asked to find the right
shape; explicitly a propose-direction task ("not sure exactly what would be the
right shape").

**Diagnosis (verified in code):**
- Rich-link minting lives in the AGENT's `brr review --pr-body --relay` (cli.py
  cmd_review). In the docker task sandbox: no network + no `requests`, so
  `gist.renderer_shell_available()` (network probe via urllib) fails AND importing
  gates.github pulls `requests` → relay skipped → render_url=None →
  `prbody._render_banner` returns "" → linkless body. Matches user's "moved daemon→agent"
  intuition: the 2026-06-10 move of PR finalization to agent `gate: forge` carried the
  relay into the sandbox.
- The github GATE (`gates/github/delivery.py::_deliver_pull_request` → prs.open_or_refresh_pr)
  runs DAEMON-side: has `requests` (client.py _SESSION), network, user's `gh`
  (delivery.post_gist uses `gh gist create`), AND already has `prbody.extract_pack`.
  That's the correct layer to mint the link.

**Proposed direction (issue 1):** move rich-link minting out of the agent into the
github gate's PR delivery. Agent emits embedded-pack body (no --relay). Gate, at
publish: extract_pack(body) → mint secret gist via gh (reuse gist.create_pack_gist /
post_gist machinery) → prepend banner (make _render_banner public) → post. Link
becomes deterministic for every diffense PR, sandbox-independent. NOTE: contradicts
design-diffense.md slice 4 (relay deliberately in `brr review --relay`) — surfaced
to user as a deliberate design shift.

**Proposed direction (issue 2):** carry issue links structurally in pack
metadata (`closes: [126]` / `relates: [126]`), project as forge-agnostic closing
keyword (`Closes #126`) in the body so GitHub actually links + auto-closes on merge.
Title `(#126)` is cosmetic. Forge-agnostic: pack carries abstract intent, projection
emits per-forge keyword.

Awaiting user go-ahead before implementing.
