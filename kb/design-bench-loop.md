# Design: the seam bench — lesser-light runners as measuring instruments

Status: active — opened 2026-07-03 from the maintainer's proposal (telegram,
evt-1783111339545383830): reshape the sub-spawn substance so the resident can
spawn a lesser-light runner against controlled events, observe the
interaction seams from outside, iterate on prompts/daemon code, and PR the
changes that hold.

## The premise

The resident reads the wake scroll from inside, but a strong core (Fable,
Opus) *routes around* rough seams silently — it follows the protocol even
when the context shape barely carries it. An economy core (haiku, gpt-5.4-mini)
breaks exactly where the shape is weak: it drops the card, misses the inbox
fold-in, closes without a next-move line, respawns what should have folded.
That failure surface is signal, not noise — **the lesser-light is the
measuring instrument for the seams**: voicing, procedure-following, temporal
and cost awareness, mid-run responsiveness, user feedback shape.

The maintainer's observation driving this: respawn testing generally works,
but simpler incarnations handle responsiveness unreliably — they mostly
follow the protocol but often break down. The resident is the one who can
see *why*, because it can read both the seam's implementation and the
transcript of a lesser core failing against it.

## The loop

```
edit seam (prompts/*.md, daemon.py, hooks…)      ← editable install: applies live
  → brr bench run --shell claude-haiku --scenario followup-fold
  → read report.md (probe verdicts) + transcript.md (judgment read)
  → repeat, vary --shell to compare cores
  → change holds across runs/cores → PR, maintainer reviews
```

One command per cycle; everything else is files the resident already reads
natively. The dev tree's editable pip install means no build step between
seam edit and next probe.

## Anatomy of a bench run (`src/brr/bench.py`)

1. **Sandbox** — scratch repo (git-initialized scaffold: `AGENTS.md`,
   `kb/`, `notes.md`) plus a scratch `BRNRD_HOME`, so the probed wake rides
   the *real* orientation stack — fresh dominion, seeded playbook, identity
   core — fully isolated from the operator's account and dominion.
2. **Daemon** — `python -m brr up` spawned against the sandbox
   (`start_new_session`, log to `daemon.log`), torn down at scenario end.
3. **Scenario** — a scripted lead event injected through the real inbox
   protocol (`protocol.create_event`, source `bench`), plus optional
   follow-ups injected mid-run: `after: first-signal` (once the run shows a
   card note or interim reply — the earliest plausible fold-in moment) or
   `after: +N` seconds.
4. **Harvest** — conversation records (`.brr/conversations/**/*.jsonl`),
   terminal responses *and* queued partials (a folded reply lands as
   `write_partial` when no gate drains it), run-dir count, timings
   (first-signal latency, wall time), and the exact `prompt.md` each spawned
   runner saw — the flight recorder for "what did the lesser core actually
   read".
5. **Probes** — deterministic seam checks; judgment stays with the resident
   reading `transcript.md`.

## Probe rubric (v1)

| probe | seam it measures | pass condition |
| --- | --- | --- |
| `response` | basic delivery | non-empty terminal response, no timeout |
| `next_move` | closeout contract (#211) | reply tail matches `done/continuing/blocked —` or a numbered fork |
| `card` | live narration | ≥1 non-empty `card_composed` packet |
| `interim` | mid-run communication | ≥1 `interim_response` record |
| `fold` | inbox fold-in seam | every injected follow-up got a routed reply (response / partial / targeted interim) |
| `single_run` | fold vs respawn | follow-ups did not spawn a second run |

Deliberately *not* probed deterministically: voicing quality, spiral shape,
cost narration — those are the judgment half, read from the transcript. The
rubric may grow a `keepalive`/`attending` probe once linger scenarios land.

## Scenarios (v1)

- **`simple-ask`** — one self-contained question; probes reply shape +
  next-move with no task pressure.
- **`followup-fold`** — small write task + a correction injected at first
  signal; probes card, fold, single-run, and whether the correction actually
  redirects the work.

Planned next: `linger` (chatty exchange → keepalive + attending posture),
`cost-aware` (does the run narrate budget stinginess), `correction-cascade`
(multiple follow-ups — the "1a 2a 3c and do x" flow from the director loop).

## What this is not

- **Not CI.** A bench run spends real runner quota and needs runner CLI
  auth. `tests/test_bench.py` covers only the deterministic core (sandbox
  prep, probes over synthetic transcripts, rendering, CLI wiring).
- **Not an eval suite.** No scores to optimize, no leaderboard. It exists to
  make one resident-judged loop cheap: change the seam, watch a lesser core
  live it, keep what holds.
- **Not the respawn path.** `respawn:` hands work to another run in
  production; the bench spawns a *disposable* daemon+runner against a
  disposable account. The two share the runner catalog, nothing else.

## Open seams (candidates for the next iterations)

- **Cost capture** — pull `total_cost_usd` / token counts from runner traces
  into the report so seam changes can be priced per core.
- **Cross-core diff** — `brr bench run` writes one report; a comparator that
  tables the same scenario across `--shell` values is the natural v2.
- **Scenario files** — v1 scenarios are in-code; if the set grows past ~5,
  move to data files so a bench wake can add one without touching code.
- **Bench-driven pitfalls** — a reproducible lesser-core failure is exactly
  the trigger-indexed pitfall shape; wire the report into the pitfall
  workflow rather than leaving findings in `/tmp`.

## Receipts

- Implementation: `src/brr/bench.py`, CLI `brr bench scenarios|run`
  (`src/brr/cli.py`), tests `tests/test_bench.py`.
- First live firing: 2026-07-03, `simple-ask` @ `claude-haiku` (see
  `kb/log.md` entry of the same date).
