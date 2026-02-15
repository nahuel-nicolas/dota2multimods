"""
Patch Ardysa's _ArdysaMods VPK: replace Windranger skin with Dota2Mods Green Artemis.

This script:
1. Extracts all files from Ardysa's _ArdysaMods/pak01_dir.vpk
2. Removes ALL Windranger files (including Ardysa's custom kisilev_ind paths)
3. Adds Green Artemis Windranger files from the backup
4. Rebuilds the VPK using vpk.exe (v1 format)

Requirements:
  pip install vpk

Usage:
  python patch_ardysa_vpk.py          # Patch the VPK
  python patch_ardysa_vpk.py --undo   # Restore original Ardysa VPK from backup
"""

import os
import sys
import shutil
import subprocess
import vpk

# ── Paths (edit these if your install locations differ) ──────────────────────
DOTA2_DIR = r"C:\Program Files (x86)\Steam\steamapps\common\dota 2 beta"
ARDYSA_DIR = os.path.join(DOTA2_DIR, "game", "_ArdysaMods")
VPK_PATH = os.path.join(ARDYSA_DIR, "pak01_dir.vpk")
VPK_BACKUP = os.path.join(ARDYSA_DIR, "pak01_dir_backup.vpk")

# Green Artemis files live next to this script in backups/green_artemis_windranger
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WR_BACKUP = os.path.join(SCRIPT_DIR, "backups", "green_artemis_windranger")

# Temp directory for extracting and rebuilding the VPK
REBUILD_DIR = os.path.join(SCRIPT_DIR, "_rebuild_temp")
TEMP_DIR = os.path.join(REBUILD_DIR, "pak01_dir")

# vpk.exe from Dota2Mods (ships with this folder, or edit path)
VPK_EXE = os.path.join(SCRIPT_DIR, "tools", "vpk.exe")
# Fallback: try Dota2Mods install location
VPK_EXE_FALLBACK = os.path.join(
    os.environ.get("LOCALAPPDATA", ""),
    "Programs", "Dota2Mods", "resources", "vpk", "vpk.exe"
)

KEYWORDS = ["windrunner", "windranger"]


def get_vpk_exe():
    if os.path.exists(VPK_EXE):
        return VPK_EXE
    if os.path.exists(VPK_EXE_FALLBACK):
        return VPK_EXE_FALLBACK
    print("ERROR: vpk.exe not found. Place it in multimods/tools/vpk.exe")
    print(f"  Checked: {VPK_EXE}")
    print(f"  Checked: {VPK_EXE_FALLBACK}")
    sys.exit(1)


def is_windrunner(path):
    return any(kw in path.lower() for kw in KEYWORDS)


def patch():
    if not os.path.exists(VPK_PATH):
        print(f"ERROR: Ardysa VPK not found at {VPK_PATH}")
        print("Make sure Ardysa mods are applied first.")
        sys.exit(1)

    if not os.path.exists(WR_BACKUP):
        print(f"ERROR: Green Artemis backup not found at {WR_BACKUP}")
        sys.exit(1)

    vpk_exe = get_vpk_exe()

    # 1. Backup original Ardysa VPK
    if not os.path.exists(VPK_BACKUP):
        print("Backing up Ardysa VPK...")
        shutil.copy2(VPK_PATH, VPK_BACKUP)
    else:
        print("Ardysa backup already exists.")

    # 2. Extract all NON-Windranger files from Ardysa VPK
    print("Extracting Ardysa VPK (skipping Windranger files)...")
    if os.path.exists(REBUILD_DIR):
        shutil.rmtree(REBUILD_DIR)
    os.makedirs(TEMP_DIR)

    pak = vpk.open(VPK_PATH)
    kept = 0
    removed = 0
    for filepath in pak:
        if is_windrunner(filepath):
            removed += 1
            continue
        full_path = os.path.join(TEMP_DIR, filepath)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb") as f:
            f.write(pak.get_file(filepath).read())
        kept += 1
        if kept % 500 == 0:
            print(f"  {kept} files extracted...")
    print(f"Extracted {kept} files, removed {removed} Ardysa Windranger files.")

    # 3. Add Green Artemis Windranger files from backup
    added = 0
    for root, dirs, files in os.walk(WR_BACKUP):
        for fname in files:
            src = os.path.join(root, fname)
            rel = os.path.relpath(src, WR_BACKUP).replace("\\", "/")
            dst = os.path.join(TEMP_DIR, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            added += 1
    print(f"Added {added} Green Artemis Windranger files.")

    # 4. Rebuild VPK using vpk.exe (v1 format)
    print("Rebuilding VPK with vpk.exe (this may take a moment)...")
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

    # 5. Replace the original VPK
    shutil.copy2(rebuilt_vpk, VPK_PATH)
    size_mb = os.path.getsize(VPK_PATH) / (1024 * 1024)
    print(f"Saved patched VPK ({size_mb:.1f} MB) to {VPK_PATH}")

    # 6. Cleanup
    shutil.rmtree(REBUILD_DIR)
    print("\nDone! Restart Dota 2 for changes to take effect.")
    print("Ardysa skins for all other heroes + Green Artemis for Windranger.")


def undo():
    if not os.path.exists(VPK_BACKUP):
        print("No backup found. Nothing to restore.")
        return

    print("Restoring original Ardysa VPK...")
    shutil.copy2(VPK_BACKUP, VPK_PATH)
    print("Done! Original Ardysa Windranger skin restored.")


if __name__ == "__main__":
    if "--undo" in sys.argv:
        undo()
    else:
        patch()
