# Dota 2 Multimods: Ardysa + Dota2Mods Coexistence

Mix skins from **ArdysaModsTools** and **Dota2Mods V4** on the same Dota 2 installation.

Currently configured to use Ardysa for all heroes **except**:
- **Windranger**: Green Artemis skin (Dota2Mods) — full model + particle replacement
- **Vengeful Spirit**: Flightless Fury armor + Banished Princess leggings (Dota2Mods) — item swap via script patch

---

## Quick Start

### Requirements
- Python 3.x
- `pip install vpk`
- Ardysa mods already applied to Dota 2

### Apply the patch
```
python patch_ardysa_vpk.py
```
Then restart Dota 2.

### Undo (restore all original Ardysa skins)
```
python patch_ardysa_vpk.py --undo
```

---

## Folder Structure

```
multimods/
  patch_ardysa_vpk.py               # Main script
  README.md                          # This file
  backups/
    green_artemis_windranger/        # 179 Green Artemis WR asset files
      materials/
      models/
      particles/
      resource/
      soundevents/
    vengeful_spirit_d2mods/          # VS mod data
      item_replacements.json         # items_game.txt block replacements
      models/heroes/vengeful/        # VS weapon model
      scripts/                       # Reference scripts (items_game, portraits, precache)
  tools/
    vpk.exe                          # Valve VPK tool (v1 format)
    tier0.dll                        # Required DLLs for vpk.exe
    vstdlib.dll
    vstdlib_s.dll
    filesystem_stdio.dll
```

---

## How It Works

### The Problem

Ardysa and Dota2Mods both modify Dota 2 skins, but they use **different mechanisms**
that conflict with each other:

- **Dota2Mods V4** writes a VPK to `game/mods/pak01_dir.vpk` (~60 MB)
- **ArdysaModsTools** writes a VPK to `game/_ArdysaMods/pak01_dir.vpk` (~858 MB)

The game loads `_ArdysaMods` with **higher priority** than `mods`, so Ardysa's skin
always wins for any hero that both tools modify. You cannot simply overlay one on
top of the other.

### What Doesn't Work (approaches tried and failed)

1. **Loose files in `game/mods/`**: In Source 2, within the same search path, VPK
   entries take priority over loose files. Placing Windranger files as loose files
   alongside a VPK does NOT override the VPK contents.

2. **Patching `game/mods/pak01_dir.vpk`**: Even with a correctly patched VPK in the
   `mods` directory, Ardysa's `_ArdysaMods` directory loads at higher priority and
   overrides everything.

3. **Rebuilding with Python `vpk` library**: The Python `vpk` library creates VPK
   **v2** format files, but Ardysa and Dota2Mods use VPK **v1** format. Dota 2 did
   not correctly load the v2 VPK as a replacement.

4. **Just removing hero files from Ardysa**: Removing hero entries from
   `_ArdysaMods/pak01_dir.vpk` without adding replacements causes a broken/default
   appearance, since some files (like `windrunner.vmdl_c`, the base model)
   only exist in Ardysa's VPK.

### The Solution That Works

The script patches Ardysa's own VPK (`_ArdysaMods/pak01_dir.vpk`) directly:

1. **Extract** all 5000+ files from Ardysa's VPK using the Python `vpk` library
2. **Remove** all Ardysa Windranger files (82 files — includes custom paths like
   `kisilev_ind/`, `zinogre/`, and standard `models/heroes/windrunner/`)
3. **Remove** all Ardysa Vengeful Spirit custom files (72 files — `kisilev_ind/`
   custom arcana models)
4. **Add** all 179 Green Artemis Windranger files from the backup
5. **Add** VS weapon model from Dota2Mods
6. **Patch** `items_game.txt` to swap VS item definitions:
   - Upper Armor: Ardysa arcana -> Flightless Fury (`flightless_fury_shoulder`)
   - Legs: Ardysa arcana -> Banished Princess (`banished_princess_legs`)
7. **Rebuild** the VPK using Valve's own `vpk.exe` tool to ensure **v1 format**
   compatibility

This approach works because:
- We modify the highest-priority VPK directly, so no other file can override it
- We use `vpk.exe` (not the Python library) to rebuild, ensuring correct v1 format
- We replace rather than just remove, so no files are "missing" causing broken skins

### Two Types of Mod Replacement

The script handles two different types of Dota2Mods skins:

**Type 1: File Replacement (Windranger)**
The mod provides entirely custom model/material/particle files that replace the
originals. The script removes Ardysa's files and adds the Dota2Mods files directly.

**Type 2: Item Script Swap (Vengeful Spirit)**
The mod works by changing `items_game.txt` to point the hero's equipment slots to
different existing in-game cosmetic items. Only a weapon model file is custom; the
rest (armor, leggings) are standard Dota 2 items referenced by name. The script
patches the item definitions inside the VPK.

### Key Discovery: Ardysa's Custom Paths

Ardysa doesn't just replace standard game files. It uses custom asset paths:

```
kisilev_ind/models/windrunner/...     # Custom model variants
kisilev_ind/materials/windrunner/...  # Custom materials
kisilev_ind/particles/windrunner/...  # Custom particles
models/heroes/windrunner/windrunner.vmdl_c  # Base model override
```

These custom paths are referenced by modified item definition files inside the VPK
(`scripts/items/items_game.txt`). Simply replacing the standard
`models/heroes/windrunner/` files is not enough — you must also remove these custom
paths, otherwise Ardysa's skin still loads through the custom references.

---

## Workflow After Applying Ardysa Updates

Every time you re-apply Ardysa mods (e.g., after an Ardysa update), the
`_ArdysaMods/pak01_dir.vpk` gets overwritten. You need to re-run the patch:

1. Apply Ardysa mods normally through ArdysaModsTools
2. Run `python patch_ardysa_vpk.py`
3. Restart Dota 2

The backup of the original Ardysa VPK is stored at:
`game/_ArdysaMods/pak01_dir_backup.vpk`

If you want to update the backup (e.g., after an Ardysa update with new content),
delete the backup file first, then run the patch script — it will create a fresh
backup before patching.

---

## Adapting for Other Heroes

### File Replacement Mods (like Windranger)

For mods that provide custom model/material files:

1. **Disable Ardysa** and apply the mod through Dota2Mods
2. **Capture the files** from the working VPK:
   ```python
   import vpk, os, shutil
   pak = vpk.open(r"C:\...\game\mods\pak01_dir.vpk")
   hero = "hero_keyword"  # e.g. "phantom_assassin", "drow"
   for f in pak:
       if hero in f.lower():
           path = os.path.join("backups", "mod_name_hero", f)
           os.makedirs(os.path.dirname(path), exist_ok=True)
           with open(path, "wb") as out:
               out.write(pak.get_file(f).read())
   ```
3. **Update the script**: Add the hero's keywords to the filtering logic

### Item Swap Mods (like Vengeful Spirit)

For mods that swap cosmetic items via script changes:

1. **Apply the mod** through Dota2Mods and check the diff between `base.txt` and
   `replaced.txt` in `Dota2Mods/resources/vpk/scripts/`
2. **Identify the item blocks** that changed in `items_game.txt`
3. **Save the replacement blocks** to `item_replacements.json`
4. **Update `patch_items_game()`** in the script to handle the new replacements

---

## Paths Reference

| Item | Default Path |
|------|-------------|
| Dota 2 install | `C:\Program Files (x86)\Steam\steamapps\common\dota 2 beta` |
| Ardysa VPK | `game\_ArdysaMods\pak01_dir.vpk` |
| Dota2Mods VPK | `game\mods\pak01_dir.vpk` |
| Ardysa config | `%APPDATA%\ArdysaModsTools\config.json` |
| Ardysa cache | `%LOCALAPPDATA%\ArdysaModsTools\AssetCache\` |
| Dota2Mods install | `%LOCALAPPDATA%\Programs\Dota2Mods\` |
| Dota2Mods downloads | `%LOCALAPPDATA%\Programs\Dota2Mods\resources\downloads\files\` |
| Game search paths | `game\dota\gameinfo.gi` (loads `_ArdysaMods` > `mods` > `dota`) |
