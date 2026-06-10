# Schedule — thoughts you wake yourself for
#
# This is how you stop being purely reactive. Each entry here becomes an
# event in your inbox when it comes due — a fresh thought, woken on your
# own clock rather than by a user. Use it to defer work, run periodic
# upkeep, or chain a train of thought across wakes.
#
# Format: a `## ` heading (the entry's id), one trigger line, then the
# body — the prompt for the woken thought.
#   trigger:  at: <ISO-8601>   one-shot   e.g. at: 2026-06-10T09:00:00Z
#             every: <dur>     recurring  e.g. every: 24h  (s/m/h/d, summable: 1h30m)
# `every` is anchored when first seen (adding it doesn't fire instantly),
# then fires each interval. A self-scheduled thought's effect is the work
# it does (an edit, a commit, a reconcile) — it has no chat to reply to.
# This file is yours: add, edit, and remove entries freely.
#
# Example (delete once you have real ones):
#
# ## reconcile my dominion
# every: 24h
# Fetch and reconcile the brr-home branch: pull, resolve any conflicts
# with the remote, and push. Then skim pitfalls.md and self-inject for
# anything stale.
