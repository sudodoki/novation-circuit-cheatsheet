# Novation Circuit Cheatsheet

A mobile-friendly HTML cheatsheet for the original **Novation Circuit** (the 2-synth + 4-drum groovebox, product ID `0x60` — not Circuit Tracks, Circuit Rhythm, or Circuit Mono Station, which use a different patch format).

No app, no build step to *use* it. `index.html` plus a `data/` folder of per-pack JSON is all you serve. The page and its default pack are self-contained (render with no server and even without JavaScript); switching to another pack fetches `data/<pack>.json` alongside the page, so the extra packs need it served over http(s) rather than opened as a bare `file://`. Open the hosted copy:

**https://sudodoki.github.io/novation-circuit-cheatsheet/**

On iPhone: open that link in Safari, then **Share → Add to Home Screen** for a full-screen icon. The default pack works fully offline; other packs load while you're online.

## What's in it

- **Workflow** — hardware button map, Shift shortcuts, and how Clear/Duplicate actually work, sourced from Novation's official Circuit User Guide.
- **Reference** — a parameter reference for the synth engine itself: oscillators, filter, envelopes, LFOs, FX, Mod Matrix, and Macros. Explains what the values shown on the Patches tab mean, not how to press buttons.
- **Patches** — every patch of a Circuit pack, decoded byte-for-byte from the pack's `.syx` dumps: oscillator/filter/envelope/LFO/FX settings, and — per patch — exactly which parameter each of the 8 Macro knobs controls. A **pack dropdown** switches between all decoded packs; your choice is remembered in `localStorage`. The default pack is baked into the page; the rest load on demand from `data/<slug>.json`.

Tabs and the default pack's patch cards work via plain CSS/HTML (`<details>` + radio-button tabs), not JavaScript, so they still render in restrictive viewers (e.g. iOS Quick Look). Search, filtering, and switching packs are JavaScript layered on top as an enhancement.

## Getting a Circuit pack

Patches are bundled with each pack Novation publishes for the Circuit. To get one:

1. Go to [components.novationmusic.com/circuit](https://components.novationmusic.com/circuit) and sign in.
2. Open **Packs**, browse factory or user packs, and download one — it saves as a `.circuitpack` file.
3. A `.circuitpack` is just a zip archive. Rename it to `.zip` and unzip it. You'll get:
   - `index.json` — pack manifest (patch/sample/session names)
   - `patches/patch_N.syx` — one sysex dump per synth patch (64 total)
   - `samples/sample_N.wav` — one-shot audio samples
   - `sessions/session_N.circuitsession` — demo sessions

Only `index.json` and `patches/*.syx` are used by this project; samples and sessions aren't decoded (there's nothing to decode — they're just audio/session data).

## Building & adding packs

Drop one or more `.circuitpack` files into a `packs/` folder, then run from the repo root:

```bash
python3 tools/build_packs.py packs   # decode packs/*.circuitpack -> data/<slug>.json + data/packs.json
python3 tools/build_html.py          # assemble index.html (default pack inlined, others fetched)
```

- `build_packs.py` unzips each `.circuitpack` itself, decodes all its `.syx` patches, pre-renders the patch cards + filter chips to HTML, and writes one `data/<slug>.json` per pack plus a `data/packs.json` manifest (which names the default pack).
- `build_html.py` reads `data/`, inlines the default pack for instant/offline first paint, and adds the pack dropdown + the small loader that fetches the other packs.

The default pack is `Team Novation Ci` (set via `DEFAULT_PACK_NAME` in `build_packs.py`). Any Circuit (product `0x60`) factory or user pack works; packs that fail to decode are skipped with a warning. The `packs/` inputs are gitignored — they're Novation's copyrighted content (see below).

## Project structure

```
index.html               the published page (generated)
data/                    generated per-pack JSON + packs.json (runtime assets — deploy these)
tools/
  parse_patches.py       decodes Circuit .syx patch dumps to a dict
  render.py              shared patch-card / chip HTML rendering
  build_packs.py         decodes all packs -> data/*.json
  build_html.py          assembles index.html from data/
```

`index.html` and `data/*.json` are the deployed artifacts and **must be committed** (the page fetches `data/` at runtime).

## Why the raw packs aren't in this repo

The samples, patch data, and sessions inside a Circuit pack are Novation's copyrighted content. This repo publishes only the *numeric parameter values* extracted from patches (as `data/*.json`, needed to build the readable reference) and the decoder source — not the original `.circuitpack`/`.syx`/`.wav`/`.circuitsession` files. Download packs yourself from Novation Components to regenerate or extend this.

## How the byte format was figured out

The Circuit's `.syx` patch format isn't fully documented publicly. The byte layout used here was reverse-engineered from the Novation Components web editor's client-side code, then cross-validated field-by-field against Novation's official *Circuit Programmer's Reference Guide 1.3* (its "Synth Patch Format" byte table) and the live editor's UI (including the macro destination catalogue, which isn't in the published manual at all — it was read directly out of the editor's Modulation-tab dropdown).

## Disclaimer

Unofficial fan project. Not affiliated with, endorsed by, or supported by Focusrite/Novation.
