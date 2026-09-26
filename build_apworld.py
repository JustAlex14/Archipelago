"""Builds tboir.apworld from the worlds/tboir folder of your fork.

Usage (in the root folder of your fork):
    python build_apworld.py
Result: tboir.apworld next to this script.
"""
import json
import pathlib
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent
WORLD = ROOT / "worlds" / "tboir"
OUTPUT = ROOT / "tboir.apworld"

if not (WORLD / "__init__.py").is_file():
    raise SystemExit(f"Folder not found: {WORLD}\nRun this script from the root folder of your fork.")

manifest = json.loads((WORLD / "archipelago.json").read_text(encoding="utf-8"))
# Fields added by Archipelago's official "Build APWorlds" (apworld format v7)
manifest.update({"compatible_version": 7, "version": 7})

with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
    for path in sorted(WORLD.rglob("*")):
        if path.is_dir() or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        if path.name == "archipelago.json" and path.parent == WORLD:
            continue
        zf.write(path, pathlib.Path("tboir") / path.relative_to(WORLD))
    zf.writestr("tboir/archipelago.json", json.dumps(manifest, indent=4))

print(f"OK: {OUTPUT}")
