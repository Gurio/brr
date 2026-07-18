# graph-mock

Standalone visual prototype of the "dense time-based cells" loom graph.
Evaluation artifact for the P3 loom design decision (maintainer, 2026-07-18).

## Data snapshot

2026-07-18 23:54 UTC — 15 most recent runs for Gurio/brr, baked in.
Run frames from `/home/gurio/.local/state/brnrd/accounts/acc_bdda426da378d4f0c3cad2eb/home/run-state/Gurio__brr/`.

## Design refs

- Palette: `src/frontend/src/routes/layout.css` — dark void `#0c0906`, parchment `#f3e8d8`, amber `#d9a441`, ice `#6fd3ff`
- Panel chrome: bracket-cornered instrument panels (same grammar as `layout.css .panel`)
- CRT overlay, scanline bar, phosphor glow: cloned from dashboard idiom
- Edge routing: orthogonal circuit-board traces (not bezier); staggered tracks in channel between spine and lanes

## Screenshots

- `desktop-1440w.png` — 1440px viewport
- `phone-390w.png` — 390px viewport

## Self-contained

No build step. Open `index.html` directly in a browser.
`snap.js` is the Playwright snapshot script; run from `/tmp/shotwork/` where playwright is installed:
```
cd /tmp/shotwork && node graph-snap.js
```
