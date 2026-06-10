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
