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

## compact business kb before launch
at: 2026-06-12T10:00:00Z
Compact the launch-critical business kb pages before they become preflight
wallpaper. Start with `kb/decision-pricing-shape.md` and `kb/design-billing.md`;
if time remains, inspect `kb/subject-managed-mode.md` for duplicated pricing /
billing prose. Preserve current-state synthesis, move history into short lineage
breadcrumbs, keep accepted lifecycle markers, update inbound links if a split is
needed, run the kb health check, add a focused `kb/log.md` entry, and commit the
repo changes. Do not turn this into a broad kb cleanup wake.
