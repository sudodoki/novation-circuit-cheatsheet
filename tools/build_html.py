#!/usr/bin/env python3
"""Build the standalone Circuit Cheatsheet HTML file from decoded patch JSON."""
import json
from pathlib import Path

SCRATCH = Path(__file__).parent
DATA = json.loads((SCRATCH / "patches_decoded.json").read_text())

OUT_PATH = Path(__file__).resolve().parent.parent / "index.html"


def fnum(v):
    if isinstance(v, bool):
        return "Yes" if v else "No"
    return v


def osc_summary(o):
    bits = [o["wave"]]
    if o["waveInterpolate"]:
        bits.append(f"interp {o['waveInterpolate']}")
    if o["waveIndex"]:
        bits.append(f"idx {o['waveIndex']:+d}")
    if o["vSyncDepth"]:
        bits.append(f"vsync {o['vSyncDepth']}")
    if o["density"]:
        bits.append(f"density {o['density']}")
    if o["semitones"] or o["cents"]:
        bits.append(f"tune {o['semitones']:+d}st {o['cents']:+d}c")
    return ", ".join(bits)


def build_patch_card(p, idx):
    name = p["name"] or p["_indexName"]
    cat = p["category"]
    genre = p["genre"]
    voice = p["settings"]["polyphonyMode"]
    o1, o2 = p["osc1"], p["osc2"]
    mx = p["mixer"]
    filt = p["filter"]
    e1, e2, e3 = p["env1"], p["env2"], p["env3"]
    l1, l2 = p["lfo1"], p["lfo2"]
    fx = p["fx"]

    mix_bits = []
    for label, key in [("Osc1", "osc1Level"), ("Osc2", "osc2Level"), ("Noise", "noiseLevel"), ("RingMod", "ringModLevel")]:
        if mx[key]:
            mix_bits.append(f"{label} {mx[key]}")

    mod_rows = "".join(
        f"<tr><td>{i+1}</td><td>{m['source1']}" + (f" + {m['source2']}" if m['source2'] != 'Direct' else '') +
        f"</td><td>{m['destination']}</td><td>{m['depth']:+d}</td></tr>"
        for i, m in enumerate(p["modSlots"])
    ) or "<tr><td colspan='4' class='dim'>No active mod matrix routings</td></tr>"

    macro_summary_rows = ""
    for i, m in enumerate(p["macros"]):
        if not m["routings"]:
            continue
        targets = ", ".join(f"{r['destination']} ({r['depth']:+d})" for r in m["routings"])
        macro_summary_rows += f"<tr><td>{i+1}</td><td>{m['value']}</td><td>{targets}</td></tr>"
    if not macro_summary_rows:
        macro_summary_rows = "<tr><td colspan='3' class='dim'>No macro routings assigned in this patch</td></tr>"

    macro_rows = ""
    for i, m in enumerate(p["macros"]):
        if not m["routings"]:
            continue
        targets = "; ".join(
            f"{r['destination']} (depth {r['depth']:+d}, range {r['start']}-{r['end']})" for r in m["routings"]
        )
        macro_rows += f"<tr><td>Macro {i+1}</td><td>{m['value']}</td><td>{targets}</td></tr>"
    if not macro_rows:
        macro_rows = "<tr><td colspan='3' class='dim'>No macro routings assigned</td></tr>"

    return f"""
  <details class="card" data-name="{name.lower()}" data-cat="{cat.lower()}" data-genre="{genre.lower()}">
    <summary class="card-head">
      <span class="p-name">{name}</span>
      <span class="p-tags"><span class="tag cat-{cat.replace(' ','').replace('/','')}">{cat}</span><span class="tag genre">{genre}</span><span class="tag voice">{voice}</span></span>
      <span class="chev">&#9662;</span>
    </summary>
    <div class="card-body">
      <div class="grid2">
        <div class="blk"><h4>Osc 1</h4><p>{osc_summary(o1)}</p></div>
        <div class="blk"><h4>Osc 2</h4><p>{osc_summary(o2)}</p></div>
        <div class="blk"><h4>Mixer</h4><p>{', '.join(mix_bits) or 'Osc1 only'}{f", PreFX {mx['preFXLevel']:+d}dB" if mx['preFXLevel'] else ''}{f", PostFX {mx['postFXLevel']:+d}dB" if mx['postFXLevel'] else ''}</p></div>
        <div class="blk"><h4>Filter</h4><p>{filt['type']} &middot; freq {filt['frequency']} &middot; res {filt['resonance']} &middot; drive {filt['drive']} ({filt['driveType']}) &middot; bypass {filt['routing']} &middot; Env2&gt;Freq {filt['env2Frequency']:+d}</p></div>
        <div class="blk"><h4>Envelope 1 (Amp)</h4><p>A{e1['attack']} D{e1['decay']} S{e1['sustain']} R{e1['release']} &middot; vel {e1['velocity']:+d}</p></div>
        <div class="blk"><h4>Envelope 2 (Filter)</h4><p>A{e2['attack']} D{e2['decay']} S{e2['sustain']} R{e2['release']} &middot; vel {e2['velocity']:+d}</p></div>
        <div class="blk"><h4>Envelope 3 (Mod)</h4><p>Dly{e3['delay']} A{e3['attack']} D{e3['decay']} S{e3['sustain']} R{e3['release']}</p></div>
        <div class="blk"><h4>LFO 1</h4><p>{l1['waveform']} &middot; rate {l1['rate']} &middot; delay {l1['delay']} &middot; {l1['fadeMode']} &middot; {'KeySync' if l1['keySync'] else 'Free'}</p></div>
        <div class="blk"><h4>LFO 2</h4><p>{l2['waveform']} &middot; rate {l2['rate']} &middot; delay {l2['delay']} &middot; {l2['fadeMode']} &middot; {'KeySync' if l2['keySync'] else 'Free'}</p></div>
        <div class="blk"><h4>FX</h4><p>Drive {fx['distortionLevel']} ({fx['distortionType']}) &middot; Chorus {fx['chorusLevel']} &middot; EQ {fx['eqBassLevel']:+d}/{fx['eqMidLevel']:+d}/{fx['eqTrebleLevel']:+d}</p></div>
      </div>
      <h4 class="macros-heading">Macros &rarr; parameters</h4>
      <table class="mini macros-table"><thead><tr><th>Macro</th><th>Knob</th><th>Controls</th></tr></thead><tbody>{macro_summary_rows}</tbody></table>
      <details class="deep">
        <summary>Full Mod Matrix &amp; macro ranges (start/end/depth)</summary>
        <table class="mini"><thead><tr><th>#</th><th>Source</th><th>Destination</th><th>Depth</th></tr></thead><tbody>{mod_rows}</tbody></table>
        <table class="mini"><thead><tr><th>Macro</th><th>Value</th><th>Routings (destination, depth, knob range)</th></tr></thead><tbody>{macro_rows}</tbody></table>
      </details>
    </div>
  </details>"""


patch_cards = "\n".join(build_patch_card(p, i) for i, p in enumerate(DATA["patches"]))
categories = sorted(set(p["category"] for p in DATA["patches"]))
cat_chips = "".join(f'<button class="chip" data-cat="{c.lower()}">{c}</button>' for c in categories)

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
.search-row {{ display:flex; gap:8px; margin:10px 0; }}
.search-row input {{
  flex:1; background:var(--panel); border:1px solid var(--line); border-radius:10px; padding:10px 12px;
  color:var(--text); font-size:0.95em;
}}
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
.card .p-name {{ font-weight:700; flex:1; }}
.p-tags {{ display:flex; gap:4px; flex-wrap:wrap; justify-content:flex-end; }}
.tag {{ font-size:0.68em; padding:2px 7px; border-radius:999px; background:var(--panel2); color:var(--dim); white-space:nowrap; }}
.tag.genre {{ color:var(--accent2); }}
.tag.voice {{ color:var(--accent); }}
.chev {{ color:var(--dim); transition:transform 0.15s; }}
.card[open] .chev {{ transform:rotate(180deg); }}
.card-body {{ padding:0 14px 14px; border-top:1px solid var(--line); }}
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
      <tr><td><kbd>Shift</kbd>+<kbd>Oct&#9650;/Oct&#9660;</kbd></td><td>Transpose the whole pattern up/down an octave</td></tr>
      <tr><td><kbd>Shift</kbd>+<kbd>Note</kbd></td><td>Expanded Note View (2 extra octaves of pads)</td></tr>
      <tr><td><kbd>Shift</kbd>+<kbd>Velocity</kbd></td><td>Toggle Fixed Velocity (locks velocity to 96)</td></tr>
      <tr><td><kbd>Shift</kbd>+<kbd>Gate</kbd> (on a pressed step)</td><td>Microstep menu &mdash; retime individual notes on that step</td></tr>
      <tr><td><kbd>Shift</kbd>+<kbd>Record</kbd></td><td>Toggle quantised vs. non-quantised (microstep) live recording (v1.8+)</td></tr>
    </table>
    <h3>Patch &amp; sound</h3>
    <table>
      <tr><td><kbd>Shift</kbd>+<kbd>Synth 1</kbd> / <kbd>Synth 2</kbd></td><td>Open Patch View to change that synth's patch</td></tr>
      <tr><td><kbd>Shift</kbd>+<kbd>Drum 1&ndash;4</kbd></td><td>Change patch for that drum track</td></tr>
      <tr><td><kbd>Shift</kbd>+ pad (in Patch View)</td><td>Disable audition/preview when browsing patches</td></tr>
    </table>
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
      <tr><td>Gate</td><td>Edit step length in microsteps; Shift+Gate = microstep note editor</td></tr>
      <tr><td>Nudge</td><td>Shift active steps forward/back in time</td></tr>
      <tr><td>Length</td><td>Set pattern length, 1&ndash;16 steps</td></tr>
      <tr><td>Scales</td><td>Choose 1 of 16 scales; transpose keyboard</td></tr>
      <tr><td>Patterns</td><td>8 pattern memories per track + chaining</td></tr>
      <tr><td>Mixer</td><td>Mute/level per synth &amp; drum track</td></tr>
      <tr><td>FX</td><td>Per-track reverb/delay send</td></tr>
      <tr><td>Sessions</td><td>Save/load full sessions (32 slots)</td></tr>
    </table>
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

  <h3>Macros (8 knobs)</h3>
  <div class="box">
    <p>Each Macro knob can drive up to <b>4 simultaneous destinations</b> (A&ndash;D), each with its own <b>Start</b>/<b>End</b> range (which portion of the knob's 0&ndash;127 travel is used) and signed <b>Depth</b>. Macros use a bigger, separate destination catalogue than the Mod Matrix &mdash; 71 targets in total (index 0 = "No Destination"): every oscillator/mixer/filter/envelope/LFO/FX parameter individually, plus the ability to drive the <b>depth</b> of any of the 20 Mod Matrix slots directly (meta-modulation). This list isn't in Novation's published manuals; it was read directly out of the Novation Components web editor's Modulation-tab destination dropdown.</p>
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
  <h2>Team Novation Ci &mdash; 64 synth patches</h2>
  <p class="dim">Tap a patch to expand its full parameter set. This pack also ships {len(DATA['samples'])} one-shot samples and {len(DATA['sessions'])} demo sessions (not covered here &mdash; just audio/session data, nothing to decode).</p>
  <div class="search-row"><input id="search" type="search" placeholder="Search patch name&hellip;" autocomplete="off"></div>
  <div class="chips" id="catChips">
    <button class="chip active" data-cat="all">All</button>
    {cat_chips}
  </div>
  <div id="patchList">
  {patch_cards}
  </div>
  <p class="dim" id="noResults" style="display:none">No patches match.</p>
</section>

<section class="tab" id="tab-about">
  <h2>About this cheatsheet</h2>
  <div class="box">
    <p>Single self-contained HTML file &mdash; no server, no app store. All navigation (tabs, patch cards) works from plain CSS/HTML, so it renders correctly even somewhere that won't run JavaScript.</p>
    <p><b>Getting it into Safari on iPhone</b> (needed for Add to Home Screen): tapping an <code>.html</code> file in Files/Mail/AirDrop usually opens Apple's <b>Quick Look</b> preview, not Safari. From Quick Look, tap the <b>Share</b> icon (square with an arrow) and look for a <b>Safari</b> icon in the row of apps &mdash; tapping it opens the page properly in Safari. From there, tap <b>Share</b> &rarr; <b>Add to Home Screen</b> to launch it full-screen and fully offline afterwards.</p>
    <p>Patch data was reverse-engineered from the Novation Components web editor's client-side code and cross-validated byte-for-byte against Novation's official <i>Circuit Programmer's Reference Guide 1.3</i> (Synth Patch Format table, page 14&ndash;18).</p>
  </div>
  <h3>Regenerating for another pack</h3>
  <div class="box"><p>This page is generated from a <code>.circuitpack</code> export (rename to <code>.zip</code> and unzip: <code>index.json</code> + <code>patches/*.syx</code>). The same decoder works for any Circuit (product 0x60) factory or user pack &mdash; only the embedded patch JSON below needs regenerating.</p></div>
</section>

</main>

<div class="footer-note">Novation Circuit Cheatsheet &middot; unofficial fan reference &middot; not affiliated with Focusrite/Novation</div>

<script>
const search = document.getElementById('search');
const chips = document.querySelectorAll('#catChips .chip');
let activeCat = 'all';

function applyFilter() {{
  const q = search.value.trim().toLowerCase();
  let visible = 0;
  document.querySelectorAll('#patchList .card').forEach(card => {{
    const matchesText = card.dataset.name.includes(q);
    const matchesCat = activeCat === 'all' || card.dataset.cat === activeCat;
    const show = matchesText && matchesCat;
    card.style.display = show ? '' : 'none';
    if (show) visible++;
  }});
  document.getElementById('noResults').style.display = visible ? 'none' : '';
}}

search.addEventListener('input', applyFilter);
chips.forEach(chip => {{
  chip.addEventListener('click', () => {{
    chips.forEach(c => c.classList.remove('active'));
    chip.classList.add('active');
    activeCat = chip.dataset.cat;
    applyFilter();
  }});
}});
</script>
</body>
</html>
"""

OUT_PATH.write_text(HTML)
print(f"Wrote {OUT_PATH} ({len(HTML)/1024:.1f} KB)")
