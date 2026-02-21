# Dota 2 Multimods: Ardysa + Dota2Mods Coexistence

This code aims to allow you to combine skin mods from two different mods providers **Dota2Mods V4** (dota2mods.com) and **ArdysaModsTools* (ardysamods.my.id).

This Project was built using Claude Code. You may want to perform the backups using Claude Code too.

This folder contains **two approaches**:

---

## Approach 1: Ardysa Base + Dota2Mods Heroes

**Use Case:** You want most heroes using Ardysa skins, but specific heroes from Dota2Mods.

**Script:** `patch_ardysa_vpk.py`

**Heroes patched (Example):**
- Windranger: Green Artemis (Dota2Mods)
- Vengeful Spirit: Flightless Fury + Banished Princess (Dota2Mods)
- All others: Ardysa

**Requirements:**
- Apply Ardysa mods first through ArdysaModsTools
- Run `python patch_ardysa_vpk.py`
- Restart Dota 2

---

## Approach 2: Dota2Mods Base + Ardysa Heroes

**Use Case:** You want most heroes using Dota2Mods skins, but specific heroes from Ardysa.

**Script:** `patch_dota2mods_vpk.py`

**Heroes patched (Example):**
- Drow Ranger: Ardysa skin
- Queen of Pain: Ardysa skin
- All others: Dota2Mods

**Requirements:**
- Apply your desired mods through Dota2Mods (including Windranger, VS, etc.)
- **Disable ArdysaModsTools** or rename/delete the `_ArdysaMods` folder
- Run `python patch_dota2mods_vpk.py`
- Restart Dota 2

**Important:** The `_ArdysaMods` folder has higher priority than `mods`, so you must disable/remove it for this approach to work. You can rename it to `_ArdysaMods_disabled` to preserve it.

---

## Quick Start

### Common Requirements
- Python 3.x
- `pip install vpk`

### Approach 1 Usage
```bash
python patch_ardysa_vpk.py          # Apply patch
python patch_ardysa_vpk.py --undo   # Undo
```

### Approach 2 Usage
```bash
# First, disable Ardysa:
# Rename: game/_ArdysaMods -> game/_ArdysaMods_disabled

python patch_dota2mods_vpk.py        # Apply patch
python patch_dota2mods_vpk.py --undo # Undo
```

---

## Folder Structure

```
multimods/
  patch_ardysa_vpk.py                # Approach 1 script
  patch_dota2mods_vpk.py             # Approach 2 script
  README.md                          # This file
  backups/			     # Backup content is and example
    green_artemis_windranger/        # WR skin from Dota2Mods
    vengeful_spirit_d2mods/          # VS skin from Dota2Mods
    ardysa_drow/                     # Drow skin from Ardysa
    ardysa_queenofpain/              # QoP skin from Ardysa
  tools/
    vpk.exe                          # Valve VPK tool
    *.dll                            # Required libraries
```

---

## How It Works

### The Problem

Ardysa and Dota2Mods use **different VPK locations** with different priorities:

- **Dota2Mods V4** writes to `game/mods/pak01_dir.vpk` (~60 MB)
- **ArdysaModsTools** writes to `game/_ArdysaMods/pak01_dir.vpk` (~858 MB)

The game loads `_ArdysaMods` with **higher priority** than `mods`, so Ardysa always
wins when both are active. You can't simply overlay one on top of the other.

### What Doesn't Work

1. **Loose files**: VPK entries override loose files within the same search path
2. **Patching the lower-priority VPK**: `_ArdysaMods` always overrides `mods`
3. **Python VPK library for rebuilding**: Creates v2 format, Dota 2 expects v1
4. **Removing files without replacement**: Causes broken/missing assets

### The Solution

Both scripts work by **extracting, modifying, and rebuilding** the target VPK:

**Approach 1** (Ardysa base):
1. Extract `_ArdysaMods/pak01_dir.vpk`
2. Remove selected heroes' Ardysa files
3. Add Dota2Mods replacements
4. Rebuild with `vpk.exe` (v1 format)

**Approach 2** (Dota2Mods base):
1. Extract `mods/pak01_dir.vpk`
2. Remove selected heroes' Dota2Mods files (if any)
3. Add Ardysa replacements
4. Rebuild with `vpk.exe` (v1 format)
5. **Disable `_ArdysaMods`** so the patched `mods` VPK takes effect

### Two Types of Mods

**File Replacement Mods** (WR, Drow, QoP):
Custom model/material/particle files that fully replace the hero's assets.

**Script Patch Mods** (VS):
Changes to `items_game.txt` that swap equipment slots to different cosmetic items.
Only needs the script changes + any custom models (like VS weapon).

### Ardysa's Custom Paths

Ardysa uses custom asset paths like:
```
kisilev_ind/models/drow/...
kisilev_ind/materials/drow/...
kisilev_ind/particles/drow/...
```

These are referenced by modified `items_game.txt` entries. You must remove both the
custom paths AND the standard paths to fully replace an Ardysa hero.

---

## Switching Between Approaches

To switch from Approach 1 to Approach 2:

1. Run `python patch_ardysa_vpk.py --undo` (restore original Ardysa)
2. Rename `game/_ArdysaMods` to `game/_ArdysaMods_disabled`
3. Apply your Dota2Mods setup
4. Run `python patch_dota2mods_vpk.py`
5. Restart Dota 2

To switch back:

1. Run `python patch_dota2mods_vpk.py --undo` (restore original Dota2Mods)
2. Rename `game/_ArdysaMods_disabled` back to `game/_ArdysaMods`
3. Re-apply Ardysa if needed
4. Run `python patch_ardysa_vpk.py`
5. Restart Dota 2

---

## Workflow After Updates

### Approach 1 (Ardysa base)
After re-applying Ardysa mods:
1. Run `python patch_ardysa_vpk.py`
2. Restart Dota 2

### Approach 2 (Dota2Mods base)
After re-applying Dota2Mods:
1. Ensure `_ArdysaMods` is still disabled
2. Run `python patch_dota2mods_vpk.py`
3. Restart Dota 2

---

## Adding More Heroes

### To Approach 1 (add Dota2Mods heroes to Ardysa base)

1. Disable Ardysa and apply the hero through Dota2Mods
2. Extract the hero's files:
   ```python
   import vpk, os
   pak = vpk.open(r"C:\...\game\mods\pak01_dir.vpk")
   hero = "hero_keyword"
   for f in pak:
       if hero in f.lower():
           path = os.path.join("backups", f"d2mods_{hero}", f)
           os.makedirs(os.path.dirname(path), exist_ok=True)
           with open(path, "wb") as out:
               out.write(pak.get_file(f).read())
   ```
3. Update `patch_ardysa_vpk.py`: add hero to keywords and backup paths

### To Approach 2 (add Ardysa heroes to Dota2Mods base)

1. Re-enable Ardysa temporarily to capture files:
   ```python
   import vpk, os
   pak = vpk.open(r"C:\...\game\_ArdysaMods\pak01_dir.vpk")
   hero = "hero_keyword"
   for f in pak:
       if hero in f.lower():
           path = os.path.join("backups", f"ardysa_{hero}", f)
           os.makedirs(os.path.dirname(path), exist_ok=True)
           with open(path, "wb") as out:
               out.write(pak.get_file(f).read())
   ```
2. Update `patch_dota2mods_vpk.py`: add hero to keywords and backup paths
3. Disable Ardysa again

---

## Paths Reference

| Item | Path |
|------|------|
| Dota 2 install | `C:\Program Files (x86)\Steam\steamapps\common\dota 2 beta` |
| Ardysa VPK | `game\_ArdysaMods\pak01_dir.vpk` |
| Dota2Mods VPK | `game\mods\pak01_dir.vpk` |
| Ardysa config | `%APPDATA%\ArdysaModsTools\config.json` |
| Dota2Mods install | `%LOCALAPPDATA%\Programs\Dota2Mods\` |
| Game search paths | `game\dota\gameinfo.gi` (loads `_ArdysaMods` > `mods` > `dota`) |

---

## Troubleshooting

**Q: Ardysa still overrides everything in Approach 2**
A: Make sure `_ArdysaMods` folder is renamed/deleted. The game loads it first.

**Q: Getting "VPK not found" error**
A: Run the appropriate mod manager first to create the VPK file.

**Q: Changes not showing in-game**
A: Fully restart Dota 2 (close and reopen, not just restart match).

**Q: Want to use both approaches at once?**
A: Not possible. Choose one base (Ardysa or Dota2Mods) and patch from there.
