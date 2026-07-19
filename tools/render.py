#!/usr/bin/env python3
"""Shared rendering helpers: turn one decoded pack into patch-card HTML + filter chips.

Used by both build_packs.py (per-pack static JSON) and build_html.py (inlined
default pack) so the card markup has a single source of truth.
"""


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


def build_patch_card(p):
    name = p["name"] or p["_indexName"]
    cat = p["category"]
    genre = p["genre"]
    voice = p["settings"]["polyphonyMode"]
    slot_display = p.get("slotDisplay")
    page = p.get("patchViewPage")
    row = p.get("patchViewRow")
    col = p.get("patchViewCol")
    slot_badge = f"{slot_display:02d}" if slot_display else "??"
    location_line = (
        f"Hold <kbd>Shift</kbd>+<kbd>Synth&nbsp;1</kbd> or <kbd>Synth&nbsp;2</kbd> to open Patch View &middot; "
        f"Page {page}, pad <b>{row}.{col}</b>"
        f"{' &mdash; press the non-lit Oct button to reach page 2 if needed' if page == 2 else ''}"
        if slot_display else "Slot unknown"
    )
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
  <details class="card" data-name="{name.lower()}" data-cat="{cat.lower()}" data-genre="{genre.lower()}" data-voice="{voice.lower()}">
    <summary class="card-head">
      <span class="p-num">{slot_badge}</span>
      <span class="p-name">{name}</span>
      <span class="p-tags"><span class="tag cat-{cat.replace(' ','').replace('/','')}">{cat}</span><span class="tag genre">{genre}</span><span class="tag voice">{voice}</span></span>
      <span class="chev">&#9662;</span>
    </summary>
    <div class="card-body">
      <p class="location-line">{location_line}</p>
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


def _chips(patches, key, data_attr):
    values = sorted({key(p) for p in patches})
    return "".join(f'<button class="chip" data-{data_attr}="{v.lower()}">{v}</button>' for v in values)


def render_pack(decoded, slug):
    """Turn a decoded pack dict into the render bundle the page consumes."""
    patches = decoded["patches"]
    name = decoded["packName"].strip()
    n = len(patches)
    return {
        "slug": slug,
        "name": name,
        "heading": f"{name} &mdash; {n} synth patches",
        "patchCount": n,
        "sampleCount": len(decoded.get("samples", [])),
        "sessionCount": len(decoded.get("sessions", [])),
        "cards": "\n".join(build_patch_card(p) for p in patches),
        "catChips": _chips(patches, lambda p: p["category"], "cat"),
        "genreChips": _chips(patches, lambda p: p["genre"], "genre"),
        "voiceChips": _chips(patches, lambda p: p["settings"]["polyphonyMode"], "voice"),
    }


def slugify(name):
    import re
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", name.lower())).strip("-")
