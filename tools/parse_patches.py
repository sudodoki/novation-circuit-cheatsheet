#!/usr/bin/env python3
"""Decode Novation Circuit (product 0x60) .syx patch dumps into structured JSON.

Byte layout reverse-engineered from the Novation Components web app bundle
(components.novationmusic.com/circuit/synth/editor), specifically the CK({...
AK.byteOffset(n)...}) patch-model definitions. All patch-body offsets are
relative to absolute file offset 9 (i.e. right after the 9-byte sysex header
F0 00 20 29 01 60 00 00 00). Every field is exactly one raw 7-bit byte;
"signed" fields store (actual_value + 64).
"""
import json
import re
import sys
from pathlib import Path

HEADER_LEN = 9  # F0 00 20 29 01 60 00 00 00
BODY_START = HEADER_LEN

OSC_WAVES = [
    "Sine", "Triangle", "Sawtooth",
    "Saw [9:1] PW", "Saw [8:2] PW", "Saw [7:3] PW", "Saw [6:4] PW", "Saw [5:5] PW",
    "Saw [4:6] PW", "Saw [3:7] PW", "Saw [2:8] PW", "Saw [1:9] PW",
    "Pulse Width", "Square",
    "Sine Table", "Analogue Pulse", "Analogue Sync", "Tri-Saw Blend",
    "Digital Nasty 1", "Digital Nasty 2", "Digital Saw-Square",
    "Digital Vocal 1", "Digital Vocal 2", "Digital Vocal 3",
    "Digital Vocal 4", "Digital Vocal 5", "Digital Vocal 6",
    "Collection 1", "Collection 2", "Collection 3",
]

FILTER_TYPES = ["Lowpass 12dB", "Lowpass 24dB", "Bandpass 6dB", "Bandpass 12dB", "Highpass 12dB", "Highpass 24dB"]
DRIVE_TYPES = ["Diode", "Valve", "Clipper", "Cross-Over", "Rectifier", "Bit Reducer", "Rate Reducer"]
# Official Programmer's Reference Guide 1.3, "LFO Waveform Table" (values 0-37).
LFO_WAVES = [
    "Sine", "Triangle", "Sawtooth", "Square", "Random S/H", "Time S/H", "Piano Envelope",
    "Sequence 1", "Sequence 2", "Sequence 3", "Sequence 4", "Sequence 5", "Sequence 6", "Sequence 7",
    "Alternative 1", "Alternative 2", "Alternative 3", "Alternative 4",
    "Alternative 5", "Alternative 6", "Alternative 7", "Alternative 8",
    "Chromatic", "Chromatic 16", "Major", "Major 7", "Minor 7", "Min Arp 1", "Min Arp 2",
    "Diminished", "Dec Minor", "Minor 3rd", "Pedal", "4ths", "4ths x12",
    "1625 Maj", "1625 Min", "2511",
]
FADE_MODES = ["Fade In", "Fade Out", "Gate In", "Gate Out"]
FILTER_ROUTING = ["None", "Osc 1", "Osc 1 & 2"]
CATEGORIES = ["None", "Arp", "Bass", "Bell", "Classic", "Drum", "Keyboard", "Lead", "Movement", "Pad", "Poly", "SFX", "String", "User", "Voc/Tune"]
GENRES = ["None", "Classic", "D&B/Breaks", "House", "Industrial", "Jazz", "R&B/HHop", "Rock/Pop", "Techno", "Dubstep"]
# Official Programmer's Reference Guide 1.3, "Voice" section: 0=Mono, 1=Mono AG, 2=Poly.
POLYPHONY_MODES = ["Mono", "Mono AG", "Poly"]

MOD_SOURCES = [
    "Direct", "Mod Wheel", "Aftertouch", "Expression", "Velocity", "Keyboard",
    "LFO 1 +", "LFO 1 +/-", "LFO 2 +", "LFO 2 +/-",
    "Envelope 1 (Amp)", "Envelope 2 (Filter)", "Envelope 3 (Mod)",
]

MOD_DESTINATIONS = [
    "Osc 1/2 Pitch", "Osc 1 Pitch", "Osc 2 Pitch",
    "Osc 1 V-Sync", "Osc 2 V-Sync", "Osc 1 PW", "Osc 2 PW",
    "Osc 1 Level", "Osc 2 Level", "Noise Level", "Ring Mod Level",
    "Drive Amount", "Filter Frequency", "Filter Resonance",
    "LFO 1 Rate", "LFO 2 Rate",
    "Envelope 1 (Amp) Decay", "Envelope 2 (Filter) Decay",
]

# Macros use a *different*, larger destination catalogue than the Mod Matrix
# (0 = "No Destination" sentinel, then 70 real targets, values 51-70 let a
# macro drive another Mod Matrix slot's depth). Captured live, value-by-value,
# from the <option value="N"> elements in the Novation Components web
# editor's Modulation tab (Macro sub-slot "DESTINATION" dropdown) - the DOM
# display order does NOT match these values, so this list is built by
# reading each option's actual `value` attribute, not its screen position.
# Not published in the Programmer's Reference Guide, which only documents
# the valid 0-70 range without naming them.
MACRO_DESTINATIONS = [
    "No Destination", "Portamento Rate", "Post FX Volume",
    "Osc 1 Wave Interpolate", "Osc 1 Pulse Width Index", "Osc 1 VSync Depth",
    "Osc 1 Density", "Osc 1 Density Detune", "Osc 1 Semitones Tune", "Osc 1 Cents Tune",
    "Osc 2 Wave Interpolate", "Osc 2 Pulse Width Index", "Osc 2 VSync Depth",
    "Osc 2 Density", "Osc 2 Density Detune", "Osc 2 Semitones Tune", "Osc 2 Cents Tune",
    "Osc 1 Volume", "Osc 2 Volume", "Ring Mod Volume", "Noise Volume",
    "Filter Cutoff Frequency", "Filter Resonance", "Filter Drive", "Filter Key Track", "Filter Env2 Mod",
    "Envelope 1 Attack", "Envelope 1 Decay", "Envelope 1 Sustain", "Envelope 1 Release",
    "Envelope 2 Attack", "Envelope 2 Decay", "Envelope 2 Sustain", "Envelope 2 Release",
    "Envelope 3 Delay", "Envelope 3 Attack", "Envelope 3 Decay", "Envelope 3 Sustain", "Envelope 3 Release",
    "LFO 1 Rate", "LFO 1 Sync", "LFO 1 Slew", "LFO 2 Rate", "LFO 2 Sync", "LFO 2 Slew",
    "Distortion Level", "Chorus Level", "Chorus Rate", "Chorus Feedback", "Chorus Depth", "Chorus Delay",
] + [f"Mod Matrix {i} Depth" for i in range(1, 21)]


def signed(b):
    return b - 64


def enum(lst, i, prefix="Value"):
    if 0 <= i < len(lst):
        return lst[i]
    return f"{prefix} {i}"


def ascii_str(body, offset, length):
    return "".join(chr(b) for b in body[offset:offset + length] if 32 <= b <= 125).strip()


def parse_osc(body, off):
    return {
        "wave": enum(OSC_WAVES, body[off], "Wave"),
        "waveInterpolate": body[off + 1],
        "waveIndex": signed(body[off + 2]),
        "vSyncDepth": body[off + 3],
        "density": body[off + 4],
        "densityDetune": body[off + 5],
        "semitones": signed(body[off + 6]),
        "cents": signed(body[off + 7]),
        "pitchBend": signed(body[off + 8]),
    }


def parse_mixer(body, off):
    return {
        "osc1Level": body[off + 0],
        "osc2Level": body[off + 1],
        "ringModLevel": body[off + 2],
        "noiseLevel": body[off + 3],
        "preFXLevel": signed(body[off + 4]),
        "postFXLevel": signed(body[off + 5]),
    }


def parse_filter(body, off):
    return {
        "routing": enum(FILTER_ROUTING, body[off + 0], "Routing"),
        "drive": body[off + 1],
        "driveType": enum(DRIVE_TYPES, body[off + 2], "Drive"),
        "type": enum(FILTER_TYPES, body[off + 3], "Type"),
        "frequency": body[off + 4],
        "tracking": body[off + 5],
        "resonance": body[off + 6],
        "qNormalize": body[off + 7],
        "env2Frequency": signed(body[off + 8]),
    }


def parse_env(body, off, has_delay):
    if has_delay:
        return {
            "delay": body[off + 0],
            "attack": body[off + 1],
            "decay": body[off + 2],
            "sustain": body[off + 3],
            "release": body[off + 4],
        }
    return {
        "velocity": signed(body[off + 0]),
        "attack": body[off + 1],
        "decay": body[off + 2],
        "sustain": body[off + 3],
        "release": body[off + 4],
    }


def parse_lfo(body, off):
    config = body[off + 7]
    return {
        "waveform": enum(LFO_WAVES, body[off + 0], "Wave"),
        "phase": body[off + 1],
        "slewRate": body[off + 2],
        "delay": body[off + 3],
        "delaySync": bool(body[off + 4]),
        "rate": body[off + 5],
        "rateSync": body[off + 6],
        "oneShot": bool(config & 0x1),
        "keySync": bool(config & 0x2),
        "commonSync": bool(config & 0x4),
        "delayTrigger": "Multi" if (config & 0x8) else "Single",
        "fadeMode": enum(FADE_MODES, (config >> 4) & 0x3, "Fade"),
    }


def parse_fx(body, off):
    return {
        "distortionLevel": body[off + 0],
        "chorusLevel": body[off + 2],
        "eqBassFrequency": body[off + 5],
        "eqBassLevel": signed(body[off + 6]),
        "eqMidFrequency": body[off + 7],
        "eqMidLevel": signed(body[off + 8]),
        "eqTrebleFrequency": body[off + 9],
        "eqTrebleLevel": signed(body[off + 10]),
        "distortionType": DRIVE_TYPES[body[off + 16]] if body[off + 16] < len(DRIVE_TYPES) else body[off + 16],
        "distortionCompensation": body[off + 17],
        "chorusType": body[off + 18],
        "chorusRate": body[off + 19],
        "chorusRateSync": body[off + 20],
        "chorusFeedback": signed(body[off + 21]),
        "chorusModDepth": body[off + 22],
        "chorusDelay": body[off + 23],
    }


def parse_mod_slot(body, off):
    source1 = body[off + 0]
    source2 = body[off + 1]
    depth = signed(body[off + 2])
    destination = body[off + 3]
    return {
        "source1": enum(MOD_SOURCES, source1, "Source"),
        "source2": enum(MOD_SOURCES, source2, "Source"),
        "depth": depth,
        "destination": enum(MOD_DESTINATIONS, destination, "Dest"),
    }


def parse_macro(body, off):
    value = body[off]
    sub_slots = []
    for i in range(4):
        s_off = off + 1 + i * 4
        destination = body[s_off + 0]
        start = body[s_off + 1]
        end = body[s_off + 2]
        depth = signed(body[s_off + 3])
        if destination == 0:  # "No Destination" sentinel = sub-slot unused
            continue
        sub_slots.append({
            "destination": enum(MACRO_DESTINATIONS, destination, "Dest"),
            "start": start,
            "end": end,
            "depth": depth,
        })
    return {"value": value, "routings": sub_slots}


def parse_patch(raw: bytes, patch_name_hint=None):
    body = raw[BODY_START:-1]  # strip header + trailing F7
    assert len(body) == 340, f"unexpected body length {len(body)}"

    name = ascii_str(body, 0, 16)
    category = enum(CATEGORIES, body[16], "Category")
    genre = enum(GENRES, body[17], "Genre")

    settings_off = 32
    settings = {
        "polyphonyMode": enum(POLYPHONY_MODES, body[settings_off + 0], "Mode"),
        "portamentoRate": body[settings_off + 1],
        "preGlide": signed(body[settings_off + 2]),
        "keyboardOctave": signed(body[settings_off + 3]),
    }

    osc1 = parse_osc(body, 36)
    osc2 = parse_osc(body, 45)
    mixer = parse_mixer(body, 54)
    filt = parse_filter(body, 60)
    env1 = parse_env(body, 69, has_delay=False)
    env2 = parse_env(body, 74, has_delay=False)
    env3 = parse_env(body, 79, has_delay=True)
    lfo1 = parse_lfo(body, 84)
    lfo2 = parse_lfo(body, 92)
    fx = parse_fx(body, 100)

    mod_slots = []
    for i in range(20):
        off = 124 + i * 4
        slot = parse_mod_slot(body, off)
        if slot["depth"] == 0:  # zero depth = no audible effect regardless of routing
            continue
        mod_slots.append(slot)

    macros = []
    for i in range(8):
        off = 204 + i * 17
        macros.append(parse_macro(body, off))

    return {
        "name": name or patch_name_hint or "",
        "category": category,
        "genre": genre,
        "settings": settings,
        "osc1": osc1,
        "osc2": osc2,
        "mixer": mixer,
        "filter": filt,
        "env1": env1,
        "env2": env2,
        "env3": env3,
        "lfo1": lfo1,
        "lfo2": lfo2,
        "fx": fx,
        "modSlots": mod_slots,
        "macros": macros,
    }


def main():
    pack_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "extracted")
    index = json.loads((pack_dir / "index.json").read_text())

    patches = []
    for p in index["patches"]:
        raw = (pack_dir / p["url"]).read_bytes()
        decoded = parse_patch(raw, patch_name_hint=p["name"])
        decoded["_indexName"] = p["name"]
        decoded["_url"] = p["url"]

        # patches/patch_N.syx: N is the actual Flash slot (0-63), i.e. the MIDI
        # Program Change value that recalls this patch on either synth track
        # ("Format of a Synth Patch (Bank) Sysex File" concatenates Replace
        # Patch messages "starting from 0 and counting up to 63"). Hardware
        # Patch View shows patches 1-32 on page 1, 33-64 on page 2 (Shift+Synth1/2,
        # then the non-lit Oct button flips page) - both numbered from this slot.
        # The 32-pad grid is 4 rows x 8 columns, filled row-major from the top-left
        # (slot 0 = row 1/col 1; verified against hardware: patch 1 = top-left of
        # page 1, patch 64 = row 4/col 8 of page 2).
        m = re.search(r"patch_(\d+)\.syx$", p["url"])
        slot = int(m.group(1)) if m else None
        decoded["slot"] = slot
        if slot is not None:
            decoded["slotDisplay"] = slot + 1
            decoded["patchViewPage"] = 1 if slot < 32 else 2
            pos = slot % 32
            decoded["patchViewPosition"] = pos + 1
            decoded["patchViewRow"] = (pos // 8) + 1
            decoded["patchViewCol"] = (pos % 8) + 1

        patches.append(decoded)

    out = {
        "packName": index["name"],
        "product": index["product"],
        "patches": patches,
        "samples": [s["name"] for s in index.get("samples", [])],
        "sessions": [s["name"] for s in index.get("sessions", [])],
    }
    out_path = Path(sys.argv[2] if len(sys.argv) > 2 else "patches_decoded.json")
    out_path.write_text(json.dumps(out, indent=2))
    print(f"Wrote {len(patches)} patches to {out_path}")


if __name__ == "__main__":
    main()
