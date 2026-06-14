# Pitfalls — trigger-indexed failure memory
#
# The *remember* step of the environment-shaping loop. When you hit
# friction worth recording but not yet worth a forcing function, write it
# here: brr surfaces a pitfall in your wake prompt when one of its
# triggers appears in the task at hand — the lesson placed in your path,
# not prose you must remember to re-read.
#
# Format: a `## ` heading (the lesson's name), a `trigger:` line
# (comma-separated keywords or loci that tend to appear when the failure
# is about to recur), then the lesson. Slash a pitfall once a lint, test,
# or baked tool guards the failure — the forcing function is the better
# memory, and a stale pitfall is just orientation tax.
#
# Example (delete once you have real ones):
#
# ## Blind 5xx retry masks caller bugs
# trigger: retry, 5xx, http client
# The HTTP client surfaces 5xx to the caller without retrying. If you add
# a retry, gate it behind idempotency — a blind retry hid a caller bug
# here before.

## diffense `--relay` needs `requests` + network — use the embedded-pack fallback
trigger: brr review, --relay, diffense, pr-body, review pack, ModuleNotFoundError requests
Publishing a diffense PR from a sandboxed runner: `brr review <pack> --pr-body --relay`
imports the GitHub gate (for repo detection + gist publication), which imports
`requests` — absent in the sandbox — so `--relay` crashes with
`ModuleNotFoundError: No module named 'requests'`. Don't fight it: drop `--relay`.
`brr review <pack> --pr-body` (no relay) projects the same body and embeds the full
pack JSON in a `<!-- diffense:pack:v1 ... -->` HTML comment, which is the renderer's
fallback when no gist URL exists. Then push the branch and publish via a `gate: forge`
outbox file (`head`/`base`/`title` frontmatter, body = the projected PR body). The
`--pr-title` projection works without network. Validated on #128 (task-260614-1637).
