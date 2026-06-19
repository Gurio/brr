# Dogfooding the PLAN loop — running observations

Evidence for #148 (lived-in use) → #159 (portal grammar), per
`design-portal-grammar.md` decision 4: *which portals actually recur is
revealed by living the loop, not by guessing.* I log each real PLAN-shaped
turn here so the grammar work has receipts.

## 2026-06-19 — first deliberate PLAN: G5 injection-unification (evt vjjc)

Maintainer braided my two menu options: "Ship G5 ... while following the
PLAN-centered session, to gather dogfooding data 😼". So G5 became the
*vehicle* and the PLAN loop the *subject*.

**What the PLAN shape forced me to find (the payload):** decomposing G5
honestly — instead of executing on the menu label — surfaced that the
menu option was **partly stale**:

1. Repo-side G5 (daemon-substrate dedup + delivery-contract compression +
   `brr docs portals`) **shipped 2026-06-16**. The "three voices, all live
   tax" framing from my prior reply predated that ship + the 2026-06-19
   portal-summary work.
2. The 2026-06-19 work *deliberately re-thickened* the delivery contract
   with a portal-model summary + anti-drift tests
   (`test_delivery_contract_carries_portal_model_summary`). So "collapse
   to one voice" now **conflicts** with a deliberate injected-summary
   decision. A blind G5 would have undone test-locked work.
3. The genuinely-live redundancy I could see **in my own wake bundle**:
   the dominion playbook's `## How brr drives you` section is ~verbatim
   `daemon-substrate.md`, and both inject every wake. That third voice is
   real — but it's *brr-home* (my memory), not a repo PR diff.
4. One small real repo chunk remains: `daemon-substrate.md` re-narrates
   `schedule.md` (`at:`/`every:`) in full, duplicating `portals.md`.

**Lesson for the grammar (#159):** the PLAN portal's value here was *not*
chunking a big job — it was a **stewardship surface**. The act of
decomposing-before-executing caught a contradiction (cut vs. test-locked
keep) that reflexive execution would have walked into. That's a recurring
PLAN role worth naming in the grammar: PLAN-as-contradiction-catcher, not
only PLAN-as-cost-gate. Watch whether this recurs.

**Loop mechanics observed:** parked via stdout (the PLAN *is* the terminal
reply this turn), no schedule entry needed — the approval arrives as a
fresh event and resumes from woven history. Clean. The five-part shape fit
without padding; cost-framing point (#3) was the awkward one — no closely
comparable past run for "trim two prompt files," so I framed weight in
wakes, not dollars, per the manual's "past not quote" rule.

## 2026-06-19 — burst fragments: the fold-vs-already-answered race (evt lu67)

Maintainer fired five telegram fragments in ~4 min ("single-wake etc",
"2 min no updates", "148 what's that about?", "we can test oob in the
meantime right?", "we naturally do multistep conversation..."). Two wakes
overlapped: the *prior* wake answered the OOB-test + 148 questions **mid-
flight via the outbox** (one even `event:`-routed to 362x), then the next
fragment woke me fresh — and the inbox snapshot still showed 362x/avq3/o3ts
**pending**, because a mid-flight outbox reply doesn't reliably mark a
sibling pending event handled (only the explicit `event:`-routed one does,
and even that lagged the snapshot).

**The seam (portal-grammar input for #159):** when fragments arrive faster
than a wake completes, there's no clean arbiter of *which* wake owns *which*
fragment. Result is a double-answer risk — I had to detect "already covered
just above" from the woven thread and route one-line *markers* instead of
re-dumping the 148 answer. That detection is manual and fragile; a fresh
wake with a thinner thread would have re-answered.

**What would fix it:** burst-coalescing at the daemon seam — closely-spaced
fragments from one correspondent fold into one wake's inbox *before* it
plans, rather than each racing its own wake. This is squarely #128 territory
(event model + per-run claim + defer_until). Logging it as a concrete recur-
ring cost: every fragment burst pays a re-orientation wake + a double-answer
risk. Strong candidate for the "queued channel state in a standing portal"
idea — the live inbox already half-does this; the gap is *timing* (fold
window) not *visibility*.

**Lesson placed where I'll trip over it:** the marker-not-re-dump move is
the right reflex when the woven thread shows a sibling already answered.
