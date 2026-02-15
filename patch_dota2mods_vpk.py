"""
Patch Dota2Mods' pak01_dir.vpk to use Ardysa skins for specific heroes.

REVERSE MODE: Use Dota2Mods as the base, overlay Ardysa skins for selected heroes.

Currently patches:
  - Drow Ranger: Ardysa skin (file replacement)
  - Queen of Pain: Ardysa skin (file replacement)

This script:
1. Extracts all files from Dota2Mods' game/mods/pak01_dir.vpk
2. Removes Drow and QoP files (if any exist)
3. Adds Ardysa Drow and QoP files
4. Rebuilds the VPK using vpk.exe (v1 format)

Requirements:
  pip install vpk

Usage:
  python patch_dota2mods_vpk.py          # Patch the VPK
  python patch_dota2mods_vpk.py --undo   # Restore original Dota2Mods VPK from backup
"""

import os
import sys
import shutil
import subprocess
import vpk

# ── Paths (edit these if your install locations differ) ──────────────────────
DOTA2_DIR = r"C:\Program Files (x86)\Steam\steamapps\common\dota 2 beta"
MODS_DIR = os.path.join(DOTA2_DIR, "game", "mods")
VPK_PATH = os.path.join(MODS_DIR, "pak01_dir.vpk")
VPK_BACKUP = os.path.join(MODS_DIR, "pak01_dir_d2mods_backup.vpk")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REBUILD_DIR = os.path.join(SCRIPT_DIR, "_rebuild_temp_d2mods")
TEMP_DIR = os.path.join(REBUILD_DIR, "pak01_dir")

# Backup directories (Ardysa heroes)
DROW_BACKUP = os.path.join(SCRIPT_DIR, "backups", "ardysa_drow")
QOP_BACKUP = os.path.join(SCRIPT_DIR, "backups", "ardysa_queenofpain")

# vpk.exe
VPK_EXE = os.path.join(SCRIPT_DIR, "tools", "vpk.exe")
VPK_EXE_FALLBACK = os.path.join(
    os.environ.get("LOCALAPPDATA", ""),
    "Programs", "Dota2Mods", "resources", "vpk", "vpk.exe"
)

# Keywords for file filtering
DROW_KEYWORDS = ["drow"]
QOP_KEYWORDS = ["queen", "queenofpain"]


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


def patch():
    if not os.path.exists(VPK_PATH):
        print(f"ERROR: Dota2Mods VPK not found at {VPK_PATH}")
        print("Make sure Dota2Mods has created the VPK first.")
        sys.exit(1)

    vpk_exe = get_vpk_exe()

    # 1. Backup original Dota2Mods VPK
    if not os.path.exists(VPK_BACKUP):
        print("Backing up Dota2Mods VPK...")
        shutil.copy2(VPK_PATH, VPK_BACKUP)
    else:
        print("Dota2Mods backup already exists.")

    # 2. Extract files from Dota2Mods VPK (skip Drow and QoP if they exist)
    print("\nExtracting Dota2Mods VPK...")
    if os.path.exists(REBUILD_DIR):
        shutil.rmtree(REBUILD_DIR)
    os.makedirs(TEMP_DIR)

    pak = vpk.open(VPK_PATH)
    kept = 0
    removed_drow = 0
    removed_qop = 0
    for filepath in pak:
        if matches_keywords(filepath, DROW_KEYWORDS):
            removed_drow += 1
            continue
        if matches_keywords(filepath, QOP_KEYWORDS):
            removed_qop += 1
            continue
        full_path = os.path.join(TEMP_DIR, filepath)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb") as f:
            f.write(pak.get_file(filepath).read())
        kept += 1

    print(f"Extracted {kept} files.")
    if removed_drow > 0:
        print(f"  Removed {removed_drow} Drow files (Dota2Mods skin)")
    if removed_qop > 0:
        print(f"  Removed {removed_qop} QoP files (Dota2Mods skin)")

    # 3. Add Ardysa Drow Ranger files
    if os.path.exists(DROW_BACKUP):
        added = 0
        for root, dirs, files in os.walk(DROW_BACKUP):
            for fname in files:
                src = os.path.join(root, fname)
                rel = os.path.relpath(src, DROW_BACKUP).replace("\\", "/")
                dst = os.path.join(TEMP_DIR, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
                added += 1
        print(f"\nAdded {added} Ardysa Drow Ranger files.")
    else:
        print(f"\nWARNING: Drow backup not found at {DROW_BACKUP}")

    # 4. Add Ardysa Queen of Pain files
    if os.path.exists(QOP_BACKUP):
        added = 0
        for root, dirs, files in os.walk(QOP_BACKUP):
            for fname in files:
                src = os.path.join(root, fname)
                rel = os.path.relpath(src, QOP_BACKUP).replace("\\", "/")
                dst = os.path.join(TEMP_DIR, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
                added += 1
        print(f"Added {added} Ardysa Queen of Pain files.")
    else:
        print(f"WARNING: QoP backup not found at {QOP_BACKUP}")

    # 5. Rebuild VPK using vpk.exe (v1 format)
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

    # 6. Replace the original VPK
    shutil.copy2(rebuilt_vpk, VPK_PATH)
    size_mb = os.path.getsize(VPK_PATH) / (1024 * 1024)
    print(f"\nSaved patched VPK ({size_mb:.1f} MB) to {VPK_PATH}")

    # 7. Cleanup
    shutil.rmtree(REBUILD_DIR)
    print("\nDone! Restart Dota 2 for changes to take effect.")
    print("  Drow Ranger: Ardysa skin")
    print("  Queen of Pain: Ardysa skin")
    print("  All other heroes: Dota2Mods skins")
    print("\nIMPORTANT: Disable ArdysaModsTools or remove _ArdysaMods folder")
    print("to prevent it from overriding this patched VPK.")


def undo():
    if not os.path.exists(VPK_BACKUP):
        print("No backup found. Nothing to restore.")
        return

    print("Restoring original Dota2Mods VPK...")
    shutil.copy2(VPK_BACKUP, VPK_PATH)
    print("Done! Original Dota2Mods skins restored for all heroes.")


if __name__ == "__main__":
    if "--undo" in sys.argv:
        undo()
    else:
        patch()
