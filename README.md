# Dota 2 Multimods: Ardysa + Dota2Mods Coexistence

Mix skins from **ArdysaModsTools** and **Dota2Mods V4** on the same Dota 2 installation.
Currently configured to use Ardysa for all heroes except **Windranger**, which uses
the **Green Artemis** skin from Dota2Mods.

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

### Undo (restore original Ardysa skin for Windranger)
```
python patch_ardysa_vpk.py --undo
```

---

## Folder Structure

```
multimods/
  patch_ardysa_vpk.py        # Main script
  README.md                   # This file
  backups/
    green_artemis_windranger/ # 179 Green Artemis Windranger asset files
      materials/
      models/
      particles/
      resource/
      soundevents/
  tools/
    vpk.exe                   # Valve VPK tool (v1 format)
    tier0.dll                 # Required DLLs for vpk.exe
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

4. **Just removing Windranger files from Ardysa**: Removing Windranger entries from
   `_ArdysaMods/pak01_dir.vpk` without adding replacements causes a broken/default
   Windranger appearance, since some files (like `windrunner.vmdl_c`, the base model)
   only exist in Ardysa's VPK.

### The Solution That Works

The script patches Ardysa's own VPK (`_ArdysaMods/pak01_dir.vpk`) directly:

1. **Extract** all 5000+ files from Ardysa's VPK using the Python `vpk` library
2. **Remove** all 82 Ardysa Windranger files (includes custom paths like
   `kisilev_ind/`, `zinogre/`, and standard `models/heroes/windrunner/`)
3. **Add** all 179 Green Artemis Windranger files from the backup
4. **Rebuild** the VPK using Valve's own `vpk.exe` tool to ensure **v1 format**
   compatibility

This approach works because:
- We modify the highest-priority VPK directly, so no other file can override it
- We use `vpk.exe` (not the Python library) to rebuild, ensuring correct v1 format
- We replace rather than just remove, so no files are "missing" causing broken skins

### Key Discovery: Ardysa's Custom Paths

Ardysa doesn't just replace standard game files. It uses custom asset paths:

```
kisilev_ind/models/windrunner/...     # Custom model variants
kisilev_ind/materials/windrunner/...  # Custom materials
kisilev_ind/particles/windrunner/...  # Custom particles
models/heroes/windrunner/windrunner.vmdl_c  # Base model override
```

These custom paths are referenced by modified item definition files inside the VPK
(`resource/` folder). Simply replacing the standard `models/heroes/windrunner/` files
is not enough — you must also remove these custom paths, otherwise Ardysa's skin
still loads through the custom references.

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

To replace a different hero's skin (not Windranger), you need to:

1. **Identify the hero's keywords**: Find the internal name used in file paths
   (e.g., `windrunner` for Windranger, `phantom_assassin` for PA, `drow` for Drow
   Ranger)

2. **Capture the desired skin files**: Apply the skin you want through Dota2Mods
   (with Ardysa disabled), then extract the hero's files from the working VPK:
   ```python
   import vpk, os
   pak = vpk.open(r"path\to\working\pak01_dir.vpk")
   for f in pak:
       if "hero_keyword" in f.lower():
           # save to backups/skin_name_hero/
   ```

3. **Update the script**: Add the new hero's keywords to the `KEYWORDS` list and
   point `WR_BACKUP` to the new backup directory (or modify the script to support
   multiple hero replacements).

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
