# Novation Circuit Cheatsheet

A single self-contained, mobile-friendly HTML page for the original **Novation Circuit** (the 2-synth + 4-drum groovebox, product ID `0x60` — not Circuit Tracks, Circuit Rhythm, or Circuit Mono Station, which use a different patch format).

No app, no build step to *use* it — `index.html` is the entire thing. Open it, or visit the hosted copy:

**https://sudodoki.github.io/novation-circuit-cheatsheet/**

On iPhone: open that link in Safari, then **Share → Add to Home Screen** for a full-screen, fully offline icon.

## What's in it

- **Workflow** — hardware button map, Shift shortcuts, and how Clear/Duplicate actually work, sourced from Novation's official Circuit User Guide.
- **Reference** — a parameter reference for the synth engine itself: oscillators, filter, envelopes, LFOs, FX, Mod Matrix, and Macros. Explains what the values shown on the Patches tab mean, not how to press buttons.
- **Patches** — every patch in a specific factory pack ("Team Novation Ci"), decoded byte-for-byte from the pack's `.syx` dumps: oscillator/filter/envelope/LFO/FX settings, and — per patch — exactly which parameter each of the 8 Macro knobs controls.

Tabs and patch cards work via plain CSS/HTML (`<details>` + radio-button tabs), not JavaScript, so they still work in restrictive viewers (e.g. iOS Quick Look). Search and category filtering are JavaScript, layered on top as an enhancement.

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

## Regenerating for a different pack

```bash
python3 tools/parse_patches.py <path-to-extracted-pack> tools/patches_decoded.json
python3 tools/build_html.py
```

The first command decodes every `.syx` in `<pack>/patches/` into `tools/patches_decoded.json`. The second renders `index.html` from that JSON plus the static Workflow/Reference content in `tools/build_html.py`. Re-run both any time you want to swap in a different pack.

## Project structure

```
index.html                    the published page — the only file you need to view it
tools/parse_patches.py        decodes Circuit .syx patch dumps to JSON
tools/build_html.py           renders index.html from the decoded JSON
```

`tools/patches_decoded.json` and the raw pack files (`.circuitpack`/`.zip`/`extracted/`) are gitignored — they're regenerated locally from a pack you download yourself, not redistributed here (see below).

## Why the pack itself isn't in this repo

The samples, patch data, and sessions inside a Circuit pack are Novation's copyrighted content. This repo only publishes the *numeric parameter values* extracted from patches (needed to build a readable reference table) and the decoder source — not the original `.syx`/`.wav`/`.circuitsession` files. Download a pack yourself from Novation Components if you want to regenerate or extend this.

## How the byte format was figured out

The Circuit's `.syx` patch format isn't fully documented publicly. The byte layout used here was reverse-engineered from the Novation Components web editor's client-side code, then cross-validated field-by-field against Novation's official *Circuit Programmer's Reference Guide 1.3* (its "Synth Patch Format" byte table) and the live editor's UI (including the macro destination catalogue, which isn't in the published manual at all — it was read directly out of the editor's Modulation-tab dropdown).

## Disclaimer

Unofficial fan project. Not affiliated with, endorsed by, or supported by Focusrite/Novation.
