#!/usr/bin/env python3
"""Decode every .circuitpack in a given folder and write one static JSON per pack to data/.

Usage: python3 tools/build_packs.py <path/to/packs-folder>


Output:
  data/<slug>.json   - one per pack: {slug, name, heading, patchCount, sampleCount,
                       sessionCount, cards, catChips, genreChips, voiceChips}
                       (cards/chips are pre-rendered HTML strings)
  data/packs.json    - manifest: {defaultSlug, packs: [{slug, name, patchCount}, ...]}

These data files are runtime assets (the page fetches them to switch packs), so
they must be committed/deployed alongside index.html, not gitignored.
"""
import json
import sys
from pathlib import Path

from parse_patches import decode_circuitpack
from render import render_pack, slugify

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent                 # novation-cheatsheet/
DATA_DIR = ROOT / "data"

# The pack shown by default (and inlined into index.html for instant/offline first paint).
DEFAULT_PACK_NAME = "Team Novation Ci"


def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: python3 tools/build_packs.py <path/to/packs-folder>")
    packs_dir = Path(sys.argv[1]).expanduser()
    if not packs_dir.is_dir():
        sys.exit(f"Not a directory: {packs_dir}")

    DATA_DIR.mkdir(exist_ok=True)
    circuitpacks = sorted(packs_dir.glob("*.circuitpack"))
    if not circuitpacks:
        sys.exit(f"No .circuitpack files found in {packs_dir}")
    print(f"Reading packs from {packs_dir}")

    manifest = []
    default_slug = None
    for cp in circuitpacks:
        try:
            decoded = decode_circuitpack(cp)
        except Exception as e:  # skip anything that isn't a decodable product-0x60 pack
            print(f"  SKIP {cp.name}: {e}")
            continue
        name = decoded["packName"].strip()
        slug = slugify(name) or slugify(cp.stem)
        bundle = render_pack(decoded, slug)
        (DATA_DIR / f"{slug}.json").write_text(json.dumps(bundle))
        manifest.append({"slug": slug, "name": name, "patchCount": bundle["patchCount"]})
        if name == DEFAULT_PACK_NAME:
            default_slug = slug
        print(f"  {name:<24} -> data/{slug}.json ({bundle['patchCount']} patches)")

    manifest.sort(key=lambda m: m["name"].lower())
    if default_slug is None:
        default_slug = manifest[0]["slug"]  # fall back to first alphabetically
    (DATA_DIR / "packs.json").write_text(
        json.dumps({"defaultSlug": default_slug, "packs": manifest}, indent=2)
    )
    print(f"Wrote {len(manifest)} packs to {DATA_DIR}/ (default: {default_slug})")


if __name__ == "__main__":
    main()
