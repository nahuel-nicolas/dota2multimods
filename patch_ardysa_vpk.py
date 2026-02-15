"""
Patch Ardysa's _ArdysaMods VPK to use Dota2Mods skins for specific heroes.

Currently patches:
  - Windranger: Green Artemis skin (file replacement)
  - Vengeful Spirit: Flightless Fury + Banished Princess (script patch + weapon model)

This script:
1. Extracts all files from Ardysa's _ArdysaMods/pak01_dir.vpk
2. Removes Windranger files and adds Green Artemis replacements
3. Removes Vengeful Spirit custom files (kisilev_ind)
4. Patches items_game.txt to swap VS item definitions
5. Adds VS weapon model from Dota2Mods
6. Rebuilds the VPK using vpk.exe (v1 format)

Requirements:
  pip install vpk

Usage:
  python patch_ardysa_vpk.py          # Patch the VPK
  python patch_ardysa_vpk.py --undo   # Restore original Ardysa VPK from backup
"""

import os
import sys
import json
import re
import shutil
import subprocess
import vpk

# ── Paths (edit these if your install locations differ) ──────────────────────
DOTA2_DIR = r"C:\Program Files (x86)\Steam\steamapps\common\dota 2 beta"
ARDYSA_DIR = os.path.join(DOTA2_DIR, "game", "_ArdysaMods")
VPK_PATH = os.path.join(ARDYSA_DIR, "pak01_dir.vpk")
VPK_BACKUP = os.path.join(ARDYSA_DIR, "pak01_dir_backup.vpk")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REBUILD_DIR = os.path.join(SCRIPT_DIR, "_rebuild_temp")
TEMP_DIR = os.path.join(REBUILD_DIR, "pak01_dir")

# Backup directories
WR_BACKUP = os.path.join(SCRIPT_DIR, "backups", "green_artemis_windranger")
VS_BACKUP = os.path.join(SCRIPT_DIR, "backups", "vengeful_spirit_d2mods")
VS_REPLACEMENTS = os.path.join(VS_BACKUP, "item_replacements.json")

# vpk.exe
VPK_EXE = os.path.join(SCRIPT_DIR, "tools", "vpk.exe")
VPK_EXE_FALLBACK = os.path.join(
    os.environ.get("LOCALAPPDATA", ""),
    "Programs", "Dota2Mods", "resources", "vpk", "vpk.exe"
)

# Keywords for file filtering
WR_KEYWORDS = ["windrunner", "windranger"]
VS_KEYWORDS = ["vengeful"]


def get_vpk_exe():
    if os.path.exists(VPK_EXE):
        return VPK_EXE
    if os.path.exists(VPK_EXE_FALLBACK):
        return VPK_EXE_FALLBACK
    print("ERROR: vpk.exe not found. Place it in multimods/tools/vpk.exe")
    print(f"  Checked: {VPK_EXE}")
    print(f"  Checked: {VPK_EXE_FALLBACK}")
    sys.exit(1)


def matches_keywords(path, keywords):
    path_lower = path.lower()
    return any(kw in path_lower for kw in keywords)


def find_item_block(text, item_name):
    """Find a full item block in items_game.txt by item name, using brace matching."""
    name_pos = text.find(item_name)
    if name_pos == -1:
        return None

    # Go back to find the item ID and opening brace
    chunk_start = max(0, name_pos - 200)
    chunk = text[chunk_start:name_pos]
    matches = list(re.finditer(r'"(\d+)"[\s\t]*\{', chunk))
    if not matches:
        return None

    last_match = matches[-1]
    block_start = chunk_start + last_match.start()
    brace_pos = chunk_start + last_match.end() - 1

    # Match braces
    depth = 0
    for i in range(brace_pos, len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                return text[block_start:i + 1]
    return None


def patch_items_game(filepath):
    """Patch items_game.txt to replace VS item definitions."""
    if not os.path.exists(VS_REPLACEMENTS):
        print("  WARNING: VS item_replacements.json not found, skipping script patch.")
        return False

    with open(VS_REPLACEMENTS, "r", encoding="utf-8") as f:
        replacements = json.load(f)

    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    patched = 0

    # Replace Upper Armor block (Ardysa arcana -> Flightless Fury)
    ard_upper = find_item_block(content, "Vengeful Spirit's Upper Armor")
    if ard_upper and replacements.get("d2mods_upper"):
        # Convert d2mods block to match Ardysa's minified format (newlines -> tabs)
        d2m_block = replacements["d2mods_upper"]
        content = content.replace(ard_upper, d2m_block)
        patched += 1
        print("  Patched: VS Upper Armor -> Flightless Fury")

    # Replace Legs block (Ardysa arcana -> Banished Princess)
    ard_legs = find_item_block(content, "Vengeful Spirit's Legs")
    if ard_legs and replacements.get("d2mods_legs"):
        d2m_block = replacements["d2mods_legs"]
        content = content.replace(ard_legs, d2m_block)
        patched += 1
        print("  Patched: VS Legs -> Banished Princess")

    if patched > 0:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

    return patched > 0


def patch():
    if not os.path.exists(VPK_PATH):
        print(f"ERROR: Ardysa VPK not found at {VPK_PATH}")
        print("Make sure Ardysa mods are applied first.")
        sys.exit(1)

    vpk_exe = get_vpk_exe()

    # 1. Backup original Ardysa VPK
    if not os.path.exists(VPK_BACKUP):
        print("Backing up Ardysa VPK...")
        shutil.copy2(VPK_PATH, VPK_BACKUP)
    else:
        print("Ardysa backup already exists.")

    # 2. Extract files from Ardysa VPK (skip WR and VS custom files)
    print("\nExtracting Ardysa VPK...")
    if os.path.exists(REBUILD_DIR):
        shutil.rmtree(REBUILD_DIR)
    os.makedirs(TEMP_DIR)

    pak = vpk.open(VPK_PATH)
    kept = 0
    removed_wr = 0
    removed_vs = 0
    for filepath in pak:
        if matches_keywords(filepath, WR_KEYWORDS):
            removed_wr += 1
            continue
        if matches_keywords(filepath, VS_KEYWORDS):
            removed_vs += 1
            continue
        full_path = os.path.join(TEMP_DIR, filepath)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb") as f:
            f.write(pak.get_file(filepath).read())
        kept += 1
        if kept % 500 == 0:
            print(f"  {kept} files extracted...")

    print(f"Extracted {kept} files.")
    print(f"  Removed {removed_wr} Windranger files (Ardysa skin)")
    print(f"  Removed {removed_vs} Vengeful Spirit files (Ardysa skin)")

    # 3. Add Green Artemis Windranger files
    if os.path.exists(WR_BACKUP):
        added = 0
        for root, dirs, files in os.walk(WR_BACKUP):
            for fname in files:
                src = os.path.join(root, fname)
                rel = os.path.relpath(src, WR_BACKUP).replace("\\", "/")
                dst = os.path.join(TEMP_DIR, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
                added += 1
        print(f"\nAdded {added} Green Artemis Windranger files.")
    else:
        print(f"\nWARNING: Windranger backup not found at {WR_BACKUP}")

    # 4. Add VS weapon model from Dota2Mods backup
    vs_weapon = os.path.join(VS_BACKUP, "models", "heroes", "vengeful", "vengeful_weapon.vmdl_c")
    if os.path.exists(vs_weapon):
        dst = os.path.join(TEMP_DIR, "models", "heroes", "vengeful", "vengeful_weapon.vmdl_c")
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(vs_weapon, dst)
        print("Added VS weapon model (Dota2Mods).")
    else:
        print("WARNING: VS weapon model not found.")

    # 5. Patch items_game.txt for VS item swaps
    items_game_path = os.path.join(TEMP_DIR, "scripts", "items", "items_game.txt")
    if os.path.exists(items_game_path):
        print("\nPatching items_game.txt for Vengeful Spirit...")
        patch_items_game(items_game_path)
    else:
        print("WARNING: items_game.txt not found in extracted VPK.")

    # 6. Rebuild VPK using vpk.exe (v1 format)
    print("\nRebuilding VPK with vpk.exe (this may take a moment)...")
    result = subprocess.run(
        [vpk_exe, "pak01_dir"],
        cwd=REBUILD_DIR,
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"vpk.exe error: {result.stderr}")
        return

    rebuilt_vpk = os.path.join(REBUILD_DIR, "pak01_dir.vpk")
    if not os.path.exists(rebuilt_vpk):
        print("ERROR: vpk.exe did not create the VPK file.")
        return

    # 7. Replace the original VPK
    shutil.copy2(rebuilt_vpk, VPK_PATH)
    size_mb = os.path.getsize(VPK_PATH) / (1024 * 1024)
    print(f"\nSaved patched VPK ({size_mb:.1f} MB) to {VPK_PATH}")

    # 8. Cleanup
    shutil.rmtree(REBUILD_DIR)
    print("\nDone! Restart Dota 2 for changes to take effect.")
    print("  Windranger: Green Artemis (Dota2Mods)")
    print("  Vengeful Spirit: Flightless Fury + Banished Princess (Dota2Mods)")
    print("  All other heroes: Ardysa skins")


def undo():
    if not os.path.exists(VPK_BACKUP):
        print("No backup found. Nothing to restore.")
        return

    print("Restoring original Ardysa VPK...")
    shutil.copy2(VPK_BACKUP, VPK_PATH)
    print("Done! Original Ardysa skins restored for all heroes.")


if __name__ == "__main__":
    if "--undo" in sys.argv:
        undo()
    else:
        patch()
