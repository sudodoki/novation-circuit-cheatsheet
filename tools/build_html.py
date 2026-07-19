#!/usr/bin/env python3
"""Assemble index.html: static reference content + the default pack inlined, plus a
pack picker that fetches data/<slug>.json (built by build_packs.py) to swap packs.

Run build_packs.py first — it produces the data/ files this reads.
"""
import json
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
DATA_DIR = ROOT / "data"
OUT_PATH = ROOT / "index.html"

_manifest = json.loads((DATA_DIR / "packs.json").read_text())
default_slug = _manifest["defaultSlug"]
default_pack = json.loads((DATA_DIR / f"{default_slug}.json").read_text())

# Default pack is rendered inline (instant + offline first paint, works even without JS).
patch_cards = default_pack["cards"]
cat_chips = default_pack["catChips"]
genre_chips = default_pack["genreChips"]
voice_chips = default_pack["voiceChips"]
default_heading = default_pack["heading"]

# Inlined for the dropdown. The default pack is already rendered into the page below;
# the JS snapshots that DOM into its cache, so switching back to it needs no fetch and
# still works offline (rather than inlining the same cards a second time as JSON).
packs_json = json.dumps(_manifest["packs"])

TAB_IDS = ["workflow", "patches", "synth", "about"]
tabset_css = "\n".join(
    f'#tabset-{t}:checked ~ header label[for="tabset-{t}"] {{ background:var(--accent); color:#fff; border-color:var(--accent); }}\n'
    f'#tabset-{t}:checked ~ main #tab-{t} {{ display:block; }}'
    for t in TAB_IDS
)
tabset_radios = "\n".join(
    f'<input type="radio" name="tabs" id="tabset-{t}" class="tabset"{" checked" if t == TAB_IDS[0] else ""}>'
    for t in TAB_IDS
)
tabset_labels = "\n".join(f'<label for="tabset-{t}">{label}</label>' for t, label in zip(TAB_IDS, ["Workflow", "Patches", "Reference", "About"]))

HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>Circuit Cheatsheet</title>
<style>
:root {{
  --bg:#0c0e12; --panel:#161a20; --panel2:#1e232b; --line:#2a313c;
  --text:#e8ecf1; --dim:#8b96a5; --accent:#8b5cf6; --accent2:#22d3ee;
  --bass:#f59e0b; --lead:#ef4444; --pad:#22c55e; --poly:#3b82f6; --default:#64748b;
}}
* {{ box-sizing: border-box; -webkit-tap-highlight-color: transparent; }}
body {{
  margin:0; background:var(--bg); color:var(--text);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
  font-size:15px; line-height:1.45; padding-bottom:60px;
}}
h1,h2,h3,h4 {{ margin:0.4em 0 0.3em; font-weight:700; }}
h2 {{ font-size:1.15em; color:var(--accent2); border-bottom:1px solid var(--line); padding-bottom:6px; margin-top:1.4em; }}
h3 {{ font-size:1.02em; color:var(--text); margin-top:1.1em; }}
h4 {{ font-size:0.82em; color:var(--dim); text-transform:uppercase; letter-spacing:0.03em; }}
p {{ margin:0.3em 0; }}
a {{ color:var(--accent2); }}
header.top {{
  position:sticky; top:0; z-index:20; background:rgba(12,14,18,0.96); backdrop-filter:blur(6px);
  padding:10px 12px 0; border-bottom:1px solid var(--line);
}}
header.top .title {{ font-size:1.05em; font-weight:800; padding-bottom:8px; display:flex; justify-content:space-between; align-items:center; }}
header.top .title small {{ color:var(--dim); font-weight:400; font-size:0.7em; }}
nav.tabs, .chips {{ scrollbar-width:none; -ms-overflow-style:none; }}
nav.tabs::-webkit-scrollbar, .chips::-webkit-scrollbar {{ display:none; height:0; }}
nav.tabs {{ display:flex; gap:6px; overflow-x:auto; padding-bottom:8px; }}
nav.tabs label {{
  flex:0 0 auto; background:var(--panel2); color:var(--dim); border:1px solid var(--line);
  padding:8px 14px; border-radius:999px; font-size:0.88em; font-weight:600; cursor:pointer; user-select:none;
}}
main {{ padding:14px; max-width:720px; margin:0 auto; }}
section.tab {{ display:none; }}
/* Pure CSS tabs: hidden radios (siblings of header/main) gate which label looks
   active and which section is shown. No JavaScript required, so this works even
   in viewers that don't run JS (e.g. iOS Quick Look when opened from Files). */
input.tabset {{ display:none; }}
{tabset_css}
.box {{ background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:12px 14px; margin:10px 0; }}
table {{ width:100%; border-collapse:collapse; font-size:0.85em; margin:8px 0; }}
table th, table td {{ text-align:left; padding:5px 6px; border-bottom:1px solid var(--line); vertical-align:top; }}
table th {{ color:var(--dim); font-weight:600; font-size:0.82em; }}
table.mini {{ font-size:0.8em; }}
.macros-heading {{ margin-top:14px; margin-bottom:2px; }}
.macros-table {{ background:var(--panel2); border-radius:8px; overflow:hidden; }}
.macros-table th, .macros-table td {{ padding:6px 8px; }}
.macros-table td:first-child, .macros-table th:first-child {{ color:var(--accent); font-weight:700; width:2.2em; }}
kbd {{
  background:var(--panel2); border:1px solid var(--line); border-bottom-width:2px; border-radius:5px;
  padding:1px 6px; font-family:inherit; font-weight:700; font-size:0.85em; color:var(--accent2);
}}
.dim {{ color:var(--dim); }}
.pack-row {{ display:flex; align-items:center; gap:8px; margin:12px 0 2px; }}
.pack-row label {{ font-size:0.72em; font-weight:700; color:var(--dim); text-transform:uppercase; letter-spacing:0.04em; flex:0 0 auto; }}
.pack-row select {{
  flex:1; background:var(--panel2); border:1px solid var(--line); border-radius:10px; padding:9px 12px;
  color:var(--text); font-size:0.95em; font-weight:600;
}}
.search-row {{ display:flex; gap:8px; margin:10px 0; }}
.search-row input {{
  flex:1; background:var(--panel); border:1px solid var(--line); border-radius:10px; padding:10px 12px;
  color:var(--text); font-size:0.95em;
}}
.filter-label {{ font-size:0.72em; font-weight:700; color:var(--dim); text-transform:uppercase; letter-spacing:0.04em; margin:10px 0 4px; }}
.chips {{ display:flex; gap:6px; overflow-x:auto; padding:4px 0 10px; }}
.chip {{
  flex:0 0 auto; background:var(--panel); border:1px solid var(--line); color:var(--dim);
  padding:6px 12px; border-radius:999px; font-size:0.8em; font-weight:600;
}}
.chip.active {{ background:var(--accent2); border-color:var(--accent2); color:#04222a; }}
.card {{ background:var(--panel); border:1px solid var(--line); border-radius:12px; margin:8px 0; overflow:hidden; }}
.card-head {{
  width:100%; padding:12px 14px; list-style:none; cursor:pointer;
  display:flex; align-items:center; gap:8px; text-align:left; font-size:0.95em;
}}
.card-head::-webkit-details-marker {{ display:none; }}
.p-num {{
  flex:0 0 auto; font-family:ui-monospace,Menlo,monospace; font-size:0.78em; font-weight:700;
  color:var(--bg); background:var(--accent2); border-radius:6px; padding:2px 6px; letter-spacing:0.02em;
}}
.card .p-name {{ font-weight:700; flex:1; }}
.p-tags {{ display:flex; gap:4px; flex-wrap:wrap; justify-content:flex-end; }}
.tag {{ font-size:0.68em; padding:2px 7px; border-radius:999px; background:var(--panel2); color:var(--dim); white-space:nowrap; }}
.tag.genre {{ color:var(--accent2); }}
.tag.voice {{ color:var(--accent); }}
.chev {{ color:var(--dim); transition:transform 0.15s; }}
.card[open] .chev {{ transform:rotate(180deg); }}
.card-body {{ padding:0 14px 14px; border-top:1px solid var(--line); }}
.location-line {{ font-size:0.8em; color:var(--dim); margin:10px 0 0; }}
.location-line kbd {{ font-size:0.95em; }}
.grid2 {{ display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:10px; }}
.blk p {{ font-size:0.83em; color:var(--dim); }}
.blk h4 {{ margin-bottom:2px; }}
details.deep {{ margin-top:12px; }}
details.deep summary {{ cursor:pointer; color:var(--accent2); font-size:0.85em; font-weight:600; }}
.hw-list {{ list-style:none; padding:0; margin:0; }}
.hw-list li {{ display:flex; gap:10px; padding:6px 0; border-bottom:1px solid var(--line); font-size:0.9em; }}
.hw-list li:last-child {{ border-bottom:none; }}
.hw-num {{ flex:0 0 22px; height:22px; border-radius:50%; background:var(--panel2); color:var(--accent2); font-weight:700; font-size:0.75em; display:flex; align-items:center; justify-content:center; }}
.pill-row {{ display:flex; gap:6px; flex-wrap:wrap; margin:6px 0; }}
.footer-note {{ text-align:center; color:var(--dim); font-size:0.78em; padding:20px 14px; }}
</style>
</head>
<body>

{tabset_radios}

<header class="top">
  <div class="title">Novation Circuit <small>pocket cheatsheet</small></div>
  <nav class="tabs">
    {tabset_labels}
  </nav>
</header>

<main>

<section class="tab" id="tab-workflow">
  <h2>Shift shortcuts</h2>
  <div class="box">
    <h3>Clear &amp; Duplicate (no Shift needed)</h3>
    <table>
      <tr><td>Hold <kbd>Duplicate</kbd>, press a step/pattern pad (source, lights green), then press another pad (destination)</td><td>Copies notes/automation from source to destination. Keep holding <kbd>Duplicate</kbd> and press more destination pads to paste to several at once.</td></tr>
      <tr><td>In Note View: hold <kbd>Duplicate</kbd> and press a step pad</td><td>Copies all synth notes from the previously-entered step onto that pad</td></tr>
      <tr><td>In Patterns View: hold <kbd>Duplicate</kbd>, press the pattern to copy, then press an empty memory pad</td><td>Duplicates that pattern into the new memory slot</td></tr>
      <tr><td>Press and hold <kbd>Clear</kbd> (lights bright red = Clear Mode), then press step pad(s)</td><td>Deletes all notes/hits assigned to that step. Press <kbd>Clear</kbd> again to exit Clear Mode.</td></tr>
      <tr><td>In Patterns/Sessions View: hold <kbd>Clear</kbd>, press the pattern/session pad</td><td>Deletes that pattern or session (pad flashes red to confirm)</td></tr>
      <tr><td>Hold <kbd>Clear</kbd> + turn a Macro knob</td><td>Erases recorded macro automation for that macro on the current pattern</td></tr>
    </table>
    <h3>Pattern &amp; sequencing</h3>
    <table>
      <tr><td><kbd>Shift</kbd>+<kbd>Play</kbd></td><td>Continue pattern from where sequencer last stopped</td></tr>
      <tr><td><kbd>Shift</kbd>+ pattern pad</td><td>Jump to / start playing that pattern immediately from the cursor's step</td></tr>
      <tr><td><kbd>Shift</kbd>+<kbd>Patterns</kbd></td><td>Toggle "Append to Sequence" for pattern-chain building</td></tr>
      <tr><td><kbd>Shift</kbd>+<kbd>Oct&#9650;/Oct&#9660;</kbd> (in a Synth View)</td><td>"Pattern Octave" &mdash; transpose the whole synth pattern up/down an octave (works playing or stopped). In <i>Patterns</i> View the Oct buttons do something different &mdash; see Pattern Chaining below.</td></tr>
      <tr><td><kbd>Shift</kbd>+<kbd>Note</kbd></td><td>Expanded Note View (2 extra octaves of pads)</td></tr>
      <tr><td><kbd>Shift</kbd>+<kbd>Velocity</kbd></td><td>Toggle Fixed Velocity (locks velocity to 96)</td></tr>
    </table>
    <h3>Microsteps &amp; non-quantised record <span class="dim">(v1.8+)</span></h3>
    <table>
      <tr><td><kbd>Shift</kbd>+<kbd>Record</kbd> (any view)</td><td>Toggle quantised (default) vs. non-quantised recording. Record button bright = quantised (snaps hits to the 16 steps); dim = non-quantised (records your exact sub-step timing). Persists across session change / power cycle; applies to synth and drum tracks.</td></tr>
      <tr><td>In <kbd>Gate</kbd> view, hold <kbd>Shift</kbd> (on a step that has notes)</td><td>Opens the microstep menu to retime individual notes. Row 2 (purple/green) lists that step's notes left-to-right by assignment order, all selected by default &mdash; tap one to select just it (also previews it), or hold one and tap others to multi-select. Then row 1 (yellow, 6 positions) sets which microstep the selected note(s) trigger on.</td></tr>
    </table>
    <p class="dim"><b>Per-note velocity (v1.8+):</b> with Fixed Velocity <b>off</b>, notes stacked on the same step keep independent velocities &mdash; hit the step at one velocity, then hit it again at another. To change one, unassign it and re-hit the pad at the new velocity. Velocity view shows the step's spread: brightest pad = lowest velocity present, dimmest = highest.</p>
    <h3>Patch &amp; sound</h3>
    <table>
      <tr><td><kbd>Shift</kbd>+<kbd>Synth 1</kbd> / <kbd>Synth 2</kbd></td><td>Open Patch View to change that synth's patch. Each pad = one of 64 patches: page 1 = patches 1&ndash;32, page 2 = patches 33&ndash;64. Press the non-lit Oct button to flip page. The Patches tab shows each patch's number for exactly this.</td></tr>
      <tr><td><kbd>Shift</kbd>+<kbd>Drum 1&ndash;4</kbd></td><td>Change patch for that drum track</td></tr>
      <tr><td><kbd>Shift</kbd>+ pad (in Patch View)</td><td>Disable audition/preview when browsing patches</td></tr>
    </table>
    <p class="dim">Pressing plain <kbd>Drum 1</kbd>/<kbd>2</kbd>/<kbd>3</kbd>/<kbd>4</kbd> (no Shift) selects which single drum track is active for editing. This matters for Macros: each Macro knob's function is fixed but <b>shared</b> between two drum tracks (1&amp;3, or 2&amp;4) &mdash; it affects whichever one of that pair is currently selected, not both. See Reference &rarr; Drum Macros for the full fixed mapping (pitch/decay/distortion/filter).</p>
    <h3>Tempo, save &amp; system</h3>
    <table>
      <tr><td><kbd>Shift</kbd>+<kbd>Tempo</kbd> (tap in time)</td><td>Tap Tempo</td></tr>
      <tr><td>Hold <kbd>Shift</kbd>+<kbd>Save</kbd> while powering on</td><td>Toggle Save on/off</td></tr>
      <tr><td>Hold <kbd>Shift</kbd>+<kbd>Clear</kbd> while powering on</td><td>Force-load a blank session</td></tr>
      <tr><td>Hold <kbd>Shift</kbd> while powering on</td><td>Enter Setup Page (MIDI clock/TX-RX/channel assignment); press Play to save &amp; reboot</td></tr>
    </table>
    <p class="dim">Sourced from Novation's official Circuit User Guide (v1.6) &amp; v1.8 New Features addendum. "Mutate" and note-repeat are Circuit Rhythm/Tracks features, not present on the original Circuit.</p>
  </div>

  <h2>Hardware overview</h2>
  <div class="box">
    <ul class="hw-list">
      <li><span class="hw-num">1</span><div><b>32-pad grid</b> &mdash; 4&times;8 RGB performance/step pads, layout depends on active View.</div></li>
      <li><span class="hw-num">2</span><div><b>Filter</b> knob &mdash; always-active cutoff frequency control.</div></li>
      <li><span class="hw-num">3</span><div><b>Macro 1-8</b> &mdash; context-sensitive rotary encoders; movements can be recorded live.</div></li>
      <li><span class="hw-num">4</span><div><b>Master Volume</b>.</div></li>
      <li><span class="hw-num">5</span><div><b>Synth 1 / Synth 2 / Drums</b> track-select buttons.</div></li>
      <li><span class="hw-num">6</span><div><b>Note / Velocity / Gate</b> (STEP buttons) &mdash; per-step editing views.</div></li>
      <li><span class="hw-num">7</span><div><b>Nudge / Length</b> (PATTERN buttons) &mdash; timing &amp; pattern length.</div></li>
      <li><span class="hw-num">8</span><div><b>Scales</b> &mdash; pick 1 of 16 scales, transpose keyboard.</div></li>
      <li><span class="hw-num">9</span><div><b>Patterns</b> &mdash; 8 memories/track, chaining.</div></li>
      <li><span class="hw-num">10</span><div><b>Mixer</b> &mdash; mute/level per track.</div></li>
      <li><span class="hw-num">11</span><div><b>FX</b> &mdash; per-track reverb/delay send.</div></li>
      <li><span class="hw-num">12</span><div><b>Play / Record</b>.</div></li>
      <li><span class="hw-num">13</span><div><b>Oct &#9650; / Oct &#9660;</b> &mdash; transpose synth pads &plusmn;5/6 octaves.</div></li>
      <li><span class="hw-num">14</span><div><b>Tempo</b> (with Macro 1 to adjust BPM).</div></li>
      <li><span class="hw-num">15</span><div><b>Swing</b> (with Macro 1 to adjust amount).</div></li>
      <li><span class="hw-num">16</span><div><b>Clear</b> &mdash; delete steps / macro automation / patterns / sessions.</div></li>
      <li><span class="hw-num">17</span><div><b>Duplicate</b> &mdash; copy/paste patterns &amp; steps.</div></li>
      <li><span class="hw-num">18</span><div><b>Save / Sessions</b>.</div></li>
      <li><span class="hw-num">19</span><div><b>Shift</b> &mdash; secondary function for most buttons (see above).</div></li>
    </ul>
  </div>

  <h2>Views quick reference</h2>
  <div class="box">
    <table>
      <tr><th>Button</th><th>View shows</th></tr>
      <tr><td>Note</td><td>Enter synth notes / drum hits per step</td></tr>
      <tr><td>Velocity</td><td>Edit per-step (or per-note) velocity</td></tr>
      <tr><td>Gate</td><td>Edit step length; hold Shift in Gate view = microstep note editor (v1.8+)</td></tr>
      <tr><td>Nudge</td><td>Shift active steps forward/back in time</td></tr>
      <tr><td>Length</td><td>Set pattern length, 1&ndash;16 steps</td></tr>
      <tr><td>Scales</td><td>Choose 1 of 16 scales; transpose keyboard</td></tr>
      <tr><td>Patterns</td><td>8 pattern memories per track + chaining</td></tr>
      <tr><td>Mixer</td><td>Mute/level per synth &amp; drum track</td></tr>
      <tr><td>FX</td><td>Per-track reverb/delay send</td></tr>
      <tr><td>Sessions</td><td>Save/load full sessions (32 slots)</td></tr>
    </table>
  </div>

  <h2>Pattern Chaining &amp; Sequences</h2>
  <div class="box">
    <p>Each track has 8 pattern memories. Play them back-to-back for a longer arrangement &mdash; up to <b>128 steps</b> (8 &times; 16), each track switching pattern every 16 steps. Chaining is <b>per-track</b>.</p>
    <h3>Basic chain (contiguous patterns)</h3>
    <table>
      <tr><td>In Patterns View: hold the <b>lowest</b> pattern pad, then press the <b>highest</b></td><td>Chains every pattern in between (all light up in the track colour). Patterns must be <b>contiguous</b> &mdash; 1-2-3-4 or 4-5 works, 1-2-6 does not.</td></tr>
    </table>
    <p class="dim">The longest chain across tracks sets the overall sequence length; shorter chains just loop to fill it (a 1-pattern track repeats 4&times; against a 4-pattern track). <kbd>Shift</kbd>+<kbd>Play</kbd> restarts from where the sequencer stopped rather than the very start.</p>
    <h3>Pattern Chain Sequences <span class="dim">(v1.7+)</span></h3>
    <p>For repeated, reordered or non-contiguous playback, build an explicit sequence: with the transport <b>stopped</b>, hold <kbd>Shift</kbd> in Patterns View and tap patterns/chains in any order &mdash; up to <b>32 patterns or 16 chains</b> per track (defined independently per track). Release <kbd>Shift</kbd> to finish.</p>
    <table>
      <tr><td>Hold <kbd>Shift</kbd> in Patterns View, tap pads</td><td>Add patterns (and whole chains) to the track's sequence in any order; repeats allowed. Only the last-entered one stays lit while building. A chain counts as two entries.</td></tr>
      <tr><td><kbd>Oct&#8722;</kbd> / <kbd>Oct+</kbd> (in this mode)</td><td>Navigate the four <b>Sequence Banks</b> (4 &times; 8 = 32 patterns) shown on the macro-knob LEDs, and pick which track's sequence those LEDs display.</td></tr>
      <tr><td><kbd>Shift</kbd>+<kbd>Patterns</kbd></td><td>Toggle <b>Append</b>: on = new taps add to the existing sequence (even while playing) instead of replacing it. Off = a new sequence <b>replaces</b> the track's old one.</td></tr>
    </table>
    <p class="dim">Tip: leave one pattern memory empty and drop it into the sequence wherever you want that track to fall silent for 16 steps.</p>
  </div>

  <h2>Scales View</h2>
  <div class="box">
    <p>Press <kbd>Scales</kbd> to lock the synth pads to one of 16 musical scales in any root note &mdash; both apply live, even mid-pattern, and are saved with the pattern.</p>
    <table>
      <tr><td>Top 2 rows (pads 1&ndash;16)</td><td><b>Root note</b> &mdash; piano-style layout: row 1 = black keys (pads 2,3,5,6,7 = C&#9839;, E&#9837;, F&#9839;, A&#9837;, B&#9837;), row 2 = white keys (pads 9&ndash;15 = C, D, E, F, G, A, B). Pads 1, 4, 8, 16 are always disabled (spacing for the black-key gaps).</td></tr>
      <tr><td>Bottom 2 rows (pads 17&ndash;32)</td><td><b>Scale</b> &mdash; one pad per scale, in the fixed order listed in Reference &rarr; Scales.</td></tr>
      <tr><td>Press <kbd>Note</kbd> to exit</td><td>Upper two rows of Note View now play the selected scale over two octaves (one octave if Chromatic, since it's all 12 notes)</td></tr>
    </table>
    <p class="dim">Notes outside the current scale are 'snapped' to the nearest in-scale note, including incoming external MIDI notes. Changing scale after recording a pattern re-interprets existing notes into the new scale rather than transposing them literally.</p>
  </div>

</section>

<section class="tab" id="tab-synth">
  <div class="box">
    <p>This is a <b>parameter reference</b>, not a tutorial &mdash; it explains what each value shown on the <b>Patches</b> tab actually means (what a "Wave 5" or "Env2&gt;Freq +12" is). For hardware button-pressing instructions, see the <b>Workflow</b> tab instead.</p>
  </div>
  <h2>Signal flow</h2>
  <div class="box">
    <p><b>Osc 1</b> + <b>Osc 2</b> + <b>Noise</b> + <b>Ring Mod (Osc1&times;Osc2)</b> &rarr; <b>Mixer</b> &rarr; <b>Filter</b> (with Drive) &rarr; <b>Amp (Env 1)</b> &rarr; <b>FX</b> (Distortion/Chorus-Phaser/3-band EQ) &rarr; Out.</p>
    <p>Three envelopes and two LFOs are <i>generic</i> modulators. <b>Env 2</b> also has a dedicated hardwired amount knob straight to filter frequency ("Env2&gt;Freq"). Beyond that, a 20-slot <b>Mod Matrix</b> and 8 <b>Macro</b> knobs route any of 13 sources to a fixed set of destinations (Mod Matrix) or a larger internal set (Macros).</p>
  </div>

  <h3>Oscillators (&times;2, identical layout)</h3>
  <div class="box">
    <table>
      <tr><th>Control</th><th>Range</th><th>What it does</th></tr>
      <tr><td>Wave</td><td>0&ndash;29</td><td>14 "Classic" analogue-style shapes (Sine&hellip;Square, PWM saws) + 16 "Wavetable" digital shapes (Sine Table, Analogue Pulse/Sync, Tri-Saw Blend, Digital Nasty/Vocal 1-6, Collection 1-3)</td></tr>
      <tr><td>Interpolate</td><td>0&ndash;127</td><td>Morphs/crossfades within the wavetable position</td></tr>
      <tr><td>Index (PW)</td><td>&plusmn;64</td><td>Pulse-width / wavetable index, shapes the waveform</td></tr>
      <tr><td>VSync</td><td>0&ndash;127</td><td>Virtual sync depth (oscillator sync emulation)</td></tr>
      <tr><td>Density</td><td>0&ndash;127</td><td>Unison-style voice stacking</td></tr>
      <tr><td>Detune</td><td>0&ndash;127</td><td>Detune spread between the "density" stacked voices</td></tr>
      <tr><td>Semitones / Cents</td><td>&plusmn;64</td><td>Coarse / fine tune</td></tr>
      <tr><td>Pitchbend range</td><td>&plusmn;12</td><td>Per-oscillator pitch-bend depth</td></tr>
    </table>
  </div>

  <h3>Mixer</h3>
  <div class="box"><p>Osc 1 Level, Osc 2 Level, Noise Level, Ring Mod (Osc1&times;Osc2) Level &mdash; all 0&ndash;127. Pre-FX Level and Post-FX Level trim gain (&minus;12dB&hellip;+18dB) before/after the FX block.</p></div>

  <h3>Filter</h3>
  <div class="box">
    <table>
      <tr><td>Bypass</td><td>None / Osc 1 / Osc 1 &amp; 2 &mdash; routes oscillators around the filter</td></tr>
      <tr><td>Type</td><td>Low Pass 12/24dB, Band Pass 6/12dB, High Pass 12/24dB</td></tr>
      <tr><td>Drive / Drive Type</td><td>Diode, Valve, Clipper, Cross-Over, Rectifier, Bit Reducer, Rate Reducer</td></tr>
      <tr><td>Frequency / Resonance</td><td>Standard cutoff &amp; resonance</td></tr>
      <tr><td>Key Track</td><td>How much cutoff follows keyboard pitch</td></tr>
      <tr><td>Q Normalize</td><td>Keeps perceived resonance loudness constant across cutoff sweep</td></tr>
      <tr><td>Env2&gt;Freq</td><td>Dedicated Envelope 2 &rarr; cutoff modulation amount (&plusmn;64), independent of the Mod Matrix</td></tr>
    </table>
  </div>

  <h3>Envelopes 1 / 2 / 3</h3>
  <div class="box">
    <p><b>Envelope 1 (Amp)</b> and <b>Envelope 2 (Filter)</b> share the same 5-stage shape: Velocity&rarr;amount, Attack, Decay, Sustain, Release. <b>Envelope 3 (Mod)</b> swaps the Velocity stage for a <b>Delay</b> stage (Delay, Attack, Decay, Sustain, Release), making it suited to free-running modulation via the Mod Matrix.</p>
  </div>

  <h3>LFOs 1 / 2</h3>
  <div class="box">
    <p>38 waveform choices (0&ndash;37): the 4 basics (Sine, Triangle, Sawtooth, Square), Random S/H, Time S/H, Piano Envelope, 7 step "Sequence" shapes, 8 "Alternative" shapes, and a set of scale/arp-flavoured shapes (Chromatic, Major, Minor 7, Diminished, Pedal, 4ths, 1625 Maj/Min, 2511, &hellip;).</p>
    <table>
      <tr><td>Rate / Rate Sync</td><td>Free-running Hz or tempo-synced division</td></tr>
      <tr><td>Delay / Delay Sync</td><td>Delay before the LFO starts after a note-on</td></tr>
      <tr><td>Slew</td><td>Smooths stepped waveforms</td></tr>
      <tr><td>Phase</td><td>Start phase offset, 0&deg;&ndash;357&deg; in 3&deg; steps</td></tr>
      <tr><td>One Shot</td><td>Runs once instead of looping</td></tr>
      <tr><td>Key Sync</td><td>Restarts phase on every note-on ("Free" when off)</td></tr>
      <tr><td>Common Sync</td><td>All voices share one LFO phase (vs. per-voice)</td></tr>
      <tr><td>Delay Trigger</td><td>Single (first note only) or Multi (every note re-triggers delay)</td></tr>
      <tr><td>Fade Mode</td><td>Fade In, Fade Out, Gate In, Gate Out</td></tr>
    </table>
  </div>

  <h3>FX</h3>
  <div class="box"><p><b>Distortion</b> (level, type &mdash; same 7 types as filter drive &mdash; + compensation) &middot; <b>Chorus/Phaser</b> (level, type, rate/sync, feedback, mod depth, delay) &middot; 3-band <b>EQ</b> (bass/mid/treble frequency &amp; level).</p></div>

  <h3>Mod Matrix (20 slots)</h3>
  <div class="box">
    <p>Each slot: <b>Source 1</b> (+ optional <b>Source 2</b>, combined) &rarr; <b>Destination</b>, scaled by a <b>Depth</b> (&plusmn;64).</p>
    <div class="grid2">
      <div class="blk"><h4>13 Sources</h4><p>Direct, Mod Wheel, Aftertouch, Expression, Velocity, Keyboard, LFO1+, LFO1+/&minus;, LFO2+, LFO2+/&minus;, Envelope 1 (Amp), Envelope 2 (Filter), Envelope 3 (Mod)</p></div>
      <div class="blk"><h4>18 Destinations</h4><p>Osc1&amp;2/Osc1/Osc2 Pitch, Osc1/Osc2 V-Sync, Osc1/Osc2 PW-Index, Osc1/Osc2 Level, Noise Level, Ring Mod Level, Filter Drive, Filter Frequency, Filter Resonance, LFO1 Rate, LFO2 Rate, Amp Envelope Decay, Filter Envelope Decay</p></div>
    </div>
  </div>

  <h3>Synth Macros (8 knobs)</h3>
  <div class="box">
    <p>Each Macro knob can drive up to <b>4 simultaneous destinations</b> (A&ndash;D), each with its own <b>Start</b>/<b>End</b> range (which portion of the knob's 0&ndash;127 travel is used) and signed <b>Depth</b>. Macros use a bigger, separate destination catalogue than the Mod Matrix &mdash; 71 targets in total (index 0 = "No Destination"): every oscillator/mixer/filter/envelope/LFO/FX parameter individually, plus the ability to drive the <b>depth</b> of any of the 20 Mod Matrix slots directly (meta-modulation). This list isn't in Novation's published manuals; it was read directly out of the Novation Components web editor's Modulation-tab destination dropdown.</p>
    <p>This per-patch, freely-assignable behaviour is what's decoded on the Patches tab. It only applies to <b>synth</b> patches &mdash; drum tracks work completely differently, see below.</p>
  </div>

  <h3>Drum Macros (fixed)</h3>
  <div class="box">
    <p>Unlike synth patches, the drum macro <b>functions are fixed in hardware</b> &mdash; identical for every drum sample loaded; only the sonic result changes. There's no per-patch assignment to decode, which is why drum samples aren't covered on the Patches tab (they're just <code>.wav</code> audio, nothing to decode).</p>
    <p>Drum tracks are handled in pairs, so each Macro knob is <b>shared</b> by two tracks &mdash; it controls whichever <i>one</i> of the pair is currently selected (via the Drum 1/2/3/4 track buttons), not both at the same time. Odd-numbered knobs (1, 3, 5, 7) are shared between <b>Drum 1 and 3</b>; even-numbered knobs (2, 4, 6, 8) are shared between <b>Drum 2 and 4</b>. Switch which drum is selected to move the same knob's effect to the other track in its pair.</p>
    <table>
      <tr><th>Function</th><th>Drums 1 &amp; 3</th><th>Drums 2 &amp; 4</th></tr>
      <tr><td>Static pitch</td><td>Macro 1</td><td>Macro 2</td></tr>
      <tr><td>Decay envelope time</td><td>Macro 3</td><td>Macro 4</td></tr>
      <tr><td>Distortion</td><td>Macro 5</td><td>Macro 6</td></tr>
      <tr><td>Filter</td><td>Macro 7</td><td>Macro 8</td></tr>
    </table>
    <p class="dim">Turning Macro 3/4 fully clockwise makes the decay envelope unlimited, playing the full sample duration &mdash; useful for sample loops or long one-shots. Hold <kbd>Clear</kbd> and turn a Macro knob clockwise ~20% to reset it to the sample's default (LED flashes blue).</p>
  </div>

  <h3>Scales (16)</h3>
  <div class="box">
    <p>Selected in Scales View (see Workflow tab) &mdash; pads 17&ndash;32, in this fixed order. Notes shown for root note C; picking a different root note transposes the same interval pattern.</p>
    <table>
      <tr><th>Pad</th><th>Scale</th><th>Notes (root C)</th></tr>
      <tr><td>17</td><td>Natural Minor</td><td>C, D, E&#9837;, F, G, A&#9837;, B&#9837;</td></tr>
      <tr><td>18</td><td>Major</td><td>C, D, E, F, G, A, B</td></tr>
      <tr><td>19</td><td>Dorian</td><td>C, D, E&#9837;, F, G, A, B&#9837;</td></tr>
      <tr><td>20</td><td>Phrygian</td><td>C, C&#9839;, E&#9837;, F, G, A&#9837;, B&#9837;</td></tr>
      <tr><td>21</td><td>Mixolydian</td><td>C, D, E, F, G, A, B&#9837;</td></tr>
      <tr><td>22</td><td>Melodic Minor (ascending)</td><td>C, D, E&#9837;, F, G, A, B</td></tr>
      <tr><td>23</td><td>Harmonic Minor</td><td>C, D, E&#9837;, F, G, A&#9837;, B</td></tr>
      <tr><td>24</td><td>Bebop Dorian</td><td>C, D, E&#9837;, E, F, G, A, B&#9837;</td></tr>
      <tr><td>25</td><td>Blues</td><td>C, E&#9837;, F, F&#9839;, G, B&#9837;</td></tr>
      <tr><td>26</td><td>Minor Pentatonic</td><td>C, E&#9837;, F, G, B&#9837;</td></tr>
      <tr><td>27</td><td>Hungarian Minor</td><td>C, D, E&#9837;, F&#9839;, G, A&#9837;, B</td></tr>
      <tr><td>28</td><td>Ukrainian Dorian</td><td>C, D, E&#9837;, F&#9839;, G, A, B&#9837;</td></tr>
      <tr><td>29</td><td>Marva</td><td>C, C&#9839;, E, F&#9839;, G, A, B</td></tr>
      <tr><td>30</td><td>Todi</td><td>C, C&#9839;, E&#9837;, F&#9839;, G, A&#9837;, B</td></tr>
      <tr><td>31</td><td>Whole Tone</td><td>C, D, E, F&#9839;, A&#9837;, B&#9837;</td></tr>
      <tr><td>32</td><td>Chromatic</td><td>all 12 notes</td></tr>
    </table>
    <p class="dim">Root note (top 2 rows of Scales View, pads 1&ndash;16): black keys at pads 2, 3, 5, 6, 7 (C&#9839;, E&#9837;, F&#9839;, A&#9837;, B&#9837;); white keys at pads 9&ndash;15 (C, D, E, F, G, A, B). Pads 1, 4, 8, 16 are unused spacers.</p>
  </div>

  <h3>Patch metadata</h3>
  <div class="box">
    <p><b>Category</b>: None, Arp, Bass, Bell, Classic, Drum, Keyboard, Lead, Movement, Pad, Poly, SFX, String, User, Voc/Tune.<br>
    <b>Genre</b>: None, Classic, D&amp;B/Breaks, House, Industrial, Jazz, R&amp;B/HHop, Rock/Pop, Techno, Dubstep.<br>
    <b>Voice mode</b>: Mono, Mono AG (auto-glide), Poly.</p>
  </div>
  <p class="dim">All parameter names, ranges and enum tables above are taken directly from Novation's official <i>Circuit Programmer's Reference Guide 1.3</i> (MIDI CC/NRPN + Synth Patch sysex byte tables), cross-checked against the Novation Components web editor.</p>
</section>

<section class="tab" id="tab-patches">
  <h2 id="patchHeading">{default_heading}</h2>
  <div class="pack-row">
    <label for="packSelect">Pack</label>
    <select id="packSelect"><option value="{default_slug}">loading&hellip;</option></select>
  </div>
  <div class="search-row"><input id="search" type="search" placeholder="Search patch name&hellip;" autocomplete="off"></div>
  <div class="filter-label">Category</div>
  <div class="chips" id="catChips">
    <button class="chip active" data-cat="all">All</button>
    {cat_chips}
  </div>
  <div class="filter-label">Genre</div>
  <div class="chips" id="genreChips">
    <button class="chip active" data-genre="all">All</button>
    {genre_chips}
  </div>
  <div class="filter-label">Voice</div>
  <div class="chips" id="voiceChips">
    <button class="chip active" data-voice="all">All</button>
    {voice_chips}
  </div>
  <div id="patchList">
  {patch_cards}
  </div>
  <p class="dim" id="noResults" style="display:none">No patches match.</p>
</section>

<section class="tab" id="tab-about">
  <h2>About this cheatsheet</h2>
  <div class="box">
    <p>The page and its <b>default pack</b> are self-contained &mdash; the tabs, the reference content, and the default pack's patch cards all render from plain inline HTML/CSS, with no server and even with JavaScript disabled. Switching to <b>another pack</b> is the one thing that needs more: the page fetches that pack's data from a <code>data/&lt;pack&gt;.json</code> file sitting next to it, which requires the page to be served over http(s) (GitHub Pages, or a local server) with the <code>data/</code> folder alongside. Opened as a bare <code>file://</code> the extra packs won't load &mdash; only the default one.</p>
    <p><b>Getting it into Safari on iPhone</b> (needed for Add to Home Screen): tapping an <code>.html</code> file in Files/Mail/AirDrop usually opens Apple's <b>Quick Look</b> preview, not Safari. From Quick Look, tap the <b>Share</b> icon (square with an arrow) and look for a <b>Safari</b> icon in the row of apps &mdash; tapping it opens the page properly in Safari. From there, tap <b>Share</b> &rarr; <b>Add to Home Screen</b> to launch it full-screen. The default pack then works fully offline; other packs load while you're online (they aren't cached for offline yet).</p>
    <p>Patch data was reverse-engineered from the Novation Components web editor's client-side code and cross-validated byte-for-byte against Novation's official <i>Circuit Programmer's Reference Guide 1.3</i> (Synth Patch Format table, page 14&ndash;18).</p>
  </div>
  <h3>Official Novation resources</h3>
  <div class="box">
    <ul class="hw-list">
      <li><a href="https://components.novationmusic.com/circuit/updates" target="_blank" rel="noopener">What's new &mdash; firmware changelog</a> &mdash; check your firmware version for the v1.7 / v1.8 features noted here</li>
      <li><a href="https://fael-downloads-prod.focusrite.com/customer/prod/s3fs-public/downloads/Circuit%201.8%20User%20Guide.pdf" target="_blank" rel="noopener">Circuit v1.8 New Features (PDF)</a></li>
      <li><a href="https://fael-downloads-prod.focusrite.com/customer/prod/s3fs-public/novation/downloads/15909/circuit-v1-7-new-features-addendum.pdf" target="_blank" rel="noopener">Circuit v1.7 New Features (PDF)</a></li>
      <li><a href="https://fael-downloads-prod.focusrite.com/customer/prod/s3fs-public/novation/downloads/15792/circuit-ug-en-03-v1-6.pdf" target="_blank" rel="noopener">Circuit User Guide v1.6 (PDF)</a></li>
      <li><a href="https://fael-downloads-prod.focusrite.com/customer/prod/downloads/Circuit%20Programmer%27s%20Reference%20Guide%201.3_2.pdf" target="_blank" rel="noopener">Programmer's Reference Guide 1.3 (PDF)</a></li>
    </ul>
  </div>
  <h3>Patches</h3>
  <div class="box">
    <p>Use the <b>Pack</b> dropdown on the Patches tab to switch between the decoded packs; your last choice is remembered on this device. Tap a patch to expand its full parameter set. (Packs also ship one-shot samples and demo sessions &mdash; not covered here, they're just audio/session data with nothing to decode.)</p>
    <p>The numbered badge on each patch (e.g. <span class="p-num" style="display:inline">01</span>) is its slot 1&ndash;64 in Patch View on the hardware &mdash; stays visible even when filtered, so you always know where to find it. See Workflow &rarr; Shift shortcuts &rarr; Patch &amp; sound for how Patch View is laid out.</p>
  </div>
  <h3>Regenerating / adding packs</h3>
  <div class="box"><p>Each pack is a <code>.circuitpack</code> export (a zip: <code>index.json</code> + <code>patches/*.syx</code>). Drop more into <code>packs/</code> and re-run <code>tools/build_packs.py</code> then <code>tools/build_html.py</code> &mdash; the decoder works for any Circuit (product 0x60) factory or user pack. The default pack is inlined for instant load; the rest are fetched from <code>data/&lt;slug&gt;.json</code> when selected.</p></div>
</section>

</main>

<div class="footer-note">Novation Circuit Cheatsheet &middot; unofficial fan reference &middot; not affiliated with Focusrite/Novation</div>

<script>
const PACKS = {packs_json};
const DEFAULT_SLUG = "{default_slug}";
const LS_KEY = 'circuitPack';

const search = document.getElementById('search');
const patchList = document.getElementById('patchList');
const patchHeading = document.getElementById('patchHeading');
const packSelect = document.getElementById('packSelect');
const noResults = document.getElementById('noResults');

// The default pack is rendered inline above; snapshot that DOM so we can switch back to
// it without a fetch (and offline). chipValues() drops the leading "All" chip so renderPack
// can re-add it uniformly for every pack.
function chipValues(id) {{
  return [...document.querySelectorAll('#' + id + ' .chip')].slice(1).map(c => c.outerHTML).join('');
}}
const cache = {{ [DEFAULT_SLUG]: {{
  heading: patchHeading.innerHTML,
  cards: patchList.innerHTML,
  catChips: chipValues('catChips'),
  genreChips: chipValues('genreChips'),
  voiceChips: chipValues('voiceChips'),
}} }};

// ---- filtering (rebound whenever the pack's chips are replaced) ----
let filterGroups = [];
function applyFilter() {{
  const q = search.value.trim().toLowerCase();
  let visible = 0;
  patchList.querySelectorAll('.card').forEach(card => {{
    const matchesText = card.dataset.name.includes(q);
    const matchesGroups = filterGroups.every(g => g.active === 'all' || card.dataset[g.key] === g.active);
    const show = matchesText && matchesGroups;
    card.style.display = show ? '' : 'none';
    if (show) visible++;
  }});
  noResults.style.display = visible ? 'none' : '';
}}
function initFilters() {{
  filterGroups = [
    {{ id: 'catChips', key: 'cat' }},
    {{ id: 'genreChips', key: 'genre' }},
    {{ id: 'voiceChips', key: 'voice' }},
  ].map(g => ({{ ...g, active: 'all', chips: document.querySelectorAll('#' + g.id + ' .chip') }}));
  filterGroups.forEach(group => {{
    group.chips.forEach(chip => {{
      chip.addEventListener('click', () => {{
        group.chips.forEach(c => c.classList.remove('active'));
        chip.classList.add('active');
        group.active = chip.dataset[group.key];
        applyFilter();
      }});
    }});
  }});
  applyFilter();
}}
search.addEventListener('input', applyFilter);

// ---- pack switching ----
function renderPack(data) {{
  patchHeading.innerHTML = data.heading;
  document.getElementById('catChips').innerHTML = '<button class="chip active" data-cat="all">All</button>' + data.catChips;
  document.getElementById('genreChips').innerHTML = '<button class="chip active" data-genre="all">All</button>' + data.genreChips;
  document.getElementById('voiceChips').innerHTML = '<button class="chip active" data-voice="all">All</button>' + data.voiceChips;
  patchList.innerHTML = data.cards;
  search.value = '';
  initFilters();
}}
async function loadPack(slug) {{
  let data = cache[slug];
  if (!data) {{
    try {{
      const res = await fetch('data/' + slug + '.json');
      if (!res.ok) throw new Error('HTTP ' + res.status);
      data = await res.json();
      cache[slug] = data;
    }} catch (e) {{
      console.warn('Could not load pack', slug, e);
      packSelect.value = localStorage.getItem(LS_KEY) || DEFAULT_SLUG;
      return;
    }}
  }}
  renderPack(data);
  packSelect.value = slug;
  localStorage.setItem(LS_KEY, slug);
}}

packSelect.innerHTML = PACKS.map(p =>
  '<option value="' + p.slug + '">' + p.name + ' (' + p.patchCount + ')</option>'
).join('');
packSelect.addEventListener('change', () => loadPack(packSelect.value));

// Default pack is already inline; wire its filters up immediately so it stays interactive
// even if a later fetch fails. Then, if a different pack was last used, load it.
packSelect.value = DEFAULT_SLUG;
initFilters();
const saved = localStorage.getItem(LS_KEY);
if (saved && saved !== DEFAULT_SLUG && PACKS.some(p => p.slug === saved)) loadPack(saved);
</script>
</body>
</html>
"""

OUT_PATH.write_text(HTML)
print(f"Wrote {OUT_PATH} ({len(HTML)/1024:.1f} KB)")
