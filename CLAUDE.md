# Multimods – Claude Code Context

This file documents the full workflow for mixing Ardysa and Dota2Mods skins in Dota 2.
It is intended as context for future Claude Code sessions working on this project.

---

## Project Goal

Mix skins from two Dota 2 mod managers on the same installation:
- **ArdysaModsTools** (ardysa)
- **Dota2Mods V4** (dota2mods)

There are two approaches depending on which tool you want as the base.

---

## Key Paths (this machine)

| What | Path |
|------|------|
| Dota 2 root | `C:\Program Files (x86)\Steam\steamapps\common\dota 2 beta` |
| **Ardysa VPK** | `game\_ArdysaMods\pak01_dir.vpk` (~858 MB) |
| **Dota2Mods VPK** | `game\mods\pak01_dir.vpk` (~60 MB) |
| Game search paths config | `game\dota\gameinfo.gi` |
| Ardysa app config | `%APPDATA%\ArdysaModsTools\config.json` |
| Ardysa asset cache | `%LOCALAPPDATA%\ArdysaModsTools\AssetCache\` |
| Dota2Mods install | `%LOCALAPPDATA%\Programs\Dota2Mods\` |
| Dota2Mods extracted VPK | `%LOCALAPPDATA%\Programs\Dota2Mods\resources\vpk\pak01_dir\` |
| Dota2Mods downloaded mods | `%LOCALAPPDATA%\Programs\Dota2Mods\resources\downloads\files\<id>\` |
| Dota2Mods script diffs | `%LOCALAPPDATA%\Programs\Dota2Mods\resources\vpk\scripts\` |
| vpk.exe (Valve tool) | `multimods\tools\vpk.exe` (also at Dota2Mods install) |
| multimods folder | `C:\Users\nnahu\multimods\` |
| Ardysa VPK backup | `game\_ArdysaMods\pak01_dir_backup.vpk` |
| Dota2Mods VPK backup | `game\mods\pak01_dir_d2mods_backup.vpk` |

### Game Load Priority (highest to lowest)
```
game/_ArdysaMods/   >   game/mods/   >   game/dota/
```
This is defined in `game/dota/gameinfo.gi` under `SearchPaths`.

---

## How Each Tool Applies Mods

### ArdysaModsTools
- Writes a single large VPK to `game/_ArdysaMods/pak01_dir.vpk`
- Uses **custom asset paths** under `kisilev_ind/` in addition to standard paths:
  ```
  kisilev_ind/models/windrunner/...
  kisilev_ind/materials/vengeful_spirit/...
  ```
- Modifies `scripts/items/items_game.txt` inside the VPK to reference custom paths
- Because `_ArdysaMods` has higher priority than `mods`, Ardysa always wins

### Dota2Mods V4
- Writes a VPK to `game/mods/pak01_dir.vpk`
- Maintains an extracted copy at `resources/vpk/pak01_dir/`
- Two types of mods:
  1. **File replacement**: copies custom model/material/particle files (e.g. Windranger)
  2. **Item swap**: edits `items_game.txt` to point slots to different existing cosmetics (e.g. Vengeful Spirit)
- Tracks changes via `scripts/base.txt` and `scripts/replaced.txt` (diff these to see what changed)

---

## Approach 1: Ardysa Base + Dota2Mods Heroes

Use this when you want most heroes from Ardysa, with specific heroes from Dota2Mods.

**Script:** `patch_ardysa_vpk.py`

**Currently patching:**
- Windranger → Green Artemis (Dota2Mods) — 179 files, full model replacement
- Vengeful Spirit → Flightless Fury + Banished Princess (Dota2Mods) — item swap + weapon model

### Workflow

```
1. Apply Ardysa mods through ArdysaModsTools
2. python multimods/patch_ardysa_vpk.py
3. Restart Dota 2
```

### What the script does internally

1. Opens `_ArdysaMods/pak01_dir.vpk` with the Python `vpk` library
2. Extracts ALL files except Windranger and Vengeful Spirit (skips by keyword)
3. Adds Green Artemis WR files from `backups/green_artemis_windranger/`
4. Adds VS weapon model from `backups/vengeful_spirit_d2mods/models/`
5. Patches `scripts/items/items_game.txt` in the extracted folder to replace VS item blocks
6. Rebuilds the VPK using `vpk.exe` (v1 format) — NOT the Python library
7. Copies rebuilt VPK over the original

### Backing up a new Dota2Mods hero (to add to Approach 1)

```
1. Disable Ardysa (rename _ArdysaMods to _ArdysaMods_disabled)
2. Apply the hero's mod through Dota2Mods
3. Verify it works in-game
4. Run this to capture the files:

python -c "
import vpk, os
pak = vpk.open(r'C:\Program Files (x86)\Steam\steamapps\common\dota 2 beta\game\mods\pak01_dir.vpk')
hero = 'hero_keyword'   # e.g. 'phantom_assassin', 'lina', 'drow'
for f in pak:
    if hero in f.lower():
        path = os.path.join('backups', 'modname_hero', f)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as out:
            out.write(pak.get_file(f).read())
print('Done')
"

5. Re-enable Ardysa
6. Add the hero's keywords + backup path to patch_ardysa_vpk.py
```

### Handling item-swap mods (like VS) in Approach 1

Item-swap mods don't provide new files — they change `items_game.txt`.
To identify what changed:

```
diff Dota2Mods/resources/vpk/scripts/base.txt
     Dota2Mods/resources/vpk/scripts/replaced.txt
```

Or compare items_game.txt between Ardysa's VPK and Dota2Mods' VPK:

```python
import vpk
ardysa = vpk.open(r'..._ArdysaMods\pak01_dir.vpk')
d2mods = vpk.open(r'...\mods\pak01_dir.vpk')
ard_items = ardysa.get_file('scripts/items/items_game.txt').read().decode('utf-8', errors='replace')
d2m_items = d2mods.get_file('scripts/items/items_game.txt').read().decode('utf-8', errors='replace')
# Search for the changed item name in both
```

Save the Dota2Mods item blocks to `backups/<hero>/item_replacements.json` with keys:
- `ardysa_<slot>` — the Ardysa version of the block (found in Ardysa's items_game.txt)
- `d2mods_<slot>` — the Dota2Mods replacement block

Then add patching logic to `patch_items_game()` in the script.

---

## Approach 2: Dota2Mods Base + Ardysa Heroes

Use this when you want most heroes from Dota2Mods, with specific heroes from Ardysa.

**Script:** `patch_dota2mods_vpk.py`

**Currently patching:**
- Drow Ranger → Ardysa skin — 139 files
- Queen of Pain → Ardysa skin — 48 files

### Workflow

```
1. Rename game/_ArdysaMods to game/_ArdysaMods_disabled
   (MUST do this — _ArdysaMods has higher priority and will override everything)
2. Apply all desired mods through Dota2Mods (WR, VS, etc.)
3. python multimods/patch_dota2mods_vpk.py
4. Restart Dota 2
```

### Backing up a new Ardysa hero (to add to Approach 2)

```
1. Re-enable Ardysa (rename _ArdysaMods_disabled back to _ArdysaMods)
2. Run this to capture the files:

python -c "
import vpk, os
pak = vpk.open(r'C:\Program Files (x86)\Steam\steamapps\common\dota 2 beta\game\_ArdysaMods\pak01_dir.vpk')
hero = 'hero_keyword'
for f in pak:
    if hero in f.lower():
        path = os.path.join('backups', f'ardysa_{hero}', f)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as out:
            out.write(pak.get_file(f).read())
print('Done')
"

3. Disable Ardysa again
4. Add the hero's keywords + backup path to patch_dota2mods_vpk.py
```

---

## Switching Between Approaches

### From Approach 1 to Approach 2

```
python multimods/patch_ardysa_vpk.py --undo
Rename: game/_ArdysaMods -> game/_ArdysaMods_disabled
Apply Dota2Mods setup
python multimods/patch_dota2mods_vpk.py
Restart Dota 2
```

### From Approach 2 to Approach 1

```
python multimods/patch_dota2mods_vpk.py --undo
Rename: game/_ArdysaMods_disabled -> game/_ArdysaMods
Apply Ardysa if needed
python multimods/patch_ardysa_vpk.py
Restart Dota 2
```

---

## Errors We Hit & How to Avoid Them

### ❌ Loose files don't override VPK
**What happened:** We placed Windranger files as loose files in `game/mods/` thinking
they would override `game/mods/pak01_dir.vpk`. They didn't.

**Why:** In Source 2, within the same search path directory, VPK entries take priority
over loose files. Loose files only override VPK if they are in a **higher-priority**
search path directory.

**Avoid by:** Always patch the VPK directly, never rely on loose files.

---

### ❌ Patching game/mods VPK doesn't work when Ardysa is active
**What happened:** We correctly patched `game/mods/pak01_dir.vpk` with Dota2Mods
Windranger files, but Ardysa's skin still showed.

**Why:** `game/_ArdysaMods/` has higher load priority than `game/mods/` (defined in
`gameinfo.gi`). Ardysa's VPK always wins regardless of what's in `mods/`.

**Avoid by:** Always patch `_ArdysaMods/pak01_dir.vpk` (Approach 1), or disable
`_ArdysaMods` entirely (Approach 2).

---

### ❌ Python `vpk` library creates v2 VPK, game ignores it
**What happened:** We rebuilt the VPK using `vpk.new(dir).save(path)` from the Python
`vpk` library. The resulting file was read by the game but the skins weren't applied.

**Why:** The Python library creates VPK **version 2** format. Ardysa and Dota2Mods both
produce VPK **version 1**. The game appeared to load it but may not correctly handle
it as a replacement.

**Detection:** Check with:
```python
import struct
with open('pak01_dir.vpk', 'rb') as f:
    sig, ver = struct.unpack('<II', f.read(8))
print(f'Version: {ver}')  # Must be 1, not 2
```

**Avoid by:** Always use `vpk.exe` (Valve's own tool from the Dota2Mods install) to
rebuild VPKs. Command: `vpk.exe pak01_dir` run from the folder containing `pak01_dir/`
directory.

---

### ❌ Removing hero files causes broken/missing assets
**What happened:** We removed all Windranger files from Ardysa's VPK without adding
replacements. In-game, Windranger appeared broken (missing textures or wrong model).

**Why:** Some hero files (like `models/heroes/windrunner/windrunner.vmdl_c`) only exist
in Ardysa's VPK, not in the base game. Removing them without replacement causes the
game to fall back to default, which may also be missing.

**Avoid by:** Always replace, never just remove. If removing Ardysa hero files, add
Dota2Mods or base game replacements in the same step.

---

### ❌ Both tools had identical files — nothing changed visually
**What happened:** We captured Windranger files from Dota2Mods and replaced them in
Ardysa's VPK, but the skin looked the same because both tools had the exact same
Windranger mod (same bytes).

**Why:** The Dota2Mods extracted `pak01_dir/` folder didn't have the new Green Artemis
files yet — it still had the old mod's files.

**Detection:** Compare file sizes and bytes:
```python
import vpk
pak1 = vpk.open('ardysa_backup.vpk')
pak2 = vpk.open('mods/pak01_dir.vpk')
for f in pak1:
    if 'windrunner' in f.lower() and f in pak2:
        a = pak1.get_file(f).read()
        b = pak2.get_file(f).read()
        if a != b:
            print(f'DIFFERENT: {f}')
```

**Avoid by:** Before capturing files, verify in-game that the Dota2Mods mod actually
looks different when Ardysa is disabled. Only capture after confirming.

---

### ❌ Wrong VPK targeted for patching
**What happened:** We spent a long time patching `game/mods/pak01_dir.vpk` while Ardysa
was overriding it from `_ArdysaMods`. We didn't know the `_ArdysaMods` directory existed
at first.

**Why:** Ardysa doesn't use the standard `game/mods/` path that most mods use. It
creates its own separate directory registered in `gameinfo.gi` with higher priority.

**Avoid by:** Always check `gameinfo.gi` search paths before starting:
```
grep -i "game\s" "game/dota/gameinfo.gi"
```
Look for all custom directories listed under `SearchPaths`. Higher entries = higher priority.

---

### ❌ items_game.txt block search matched wrong block
**What happened:** When extracting item blocks from `items_game.txt`, searching for
`"445"` matched a price entry in the store config section, not the actual item definition.

**Why:** The item ID `"445"` appears in multiple places in the file (pricing tables,
item definitions, etc.).

**Avoid by:** Always search by item **name**, not item ID:
```python
def find_item_block(text, item_name):
    name_pos = text.find(item_name)
    # go back ~200 chars to find the item ID + {, then match braces
```

---

### ❌ Ardysa's items_game.txt is minified (no newlines)
**What happened:** Ardysa's `items_game.txt` uses `\t` separators with no newlines
(single long line), while Dota2Mods uses `\n\t` formatting. String replacements that
look for newlines fail.

**Why:** Ardysa minifies the KV file when building its VPK.

**Avoid by:** Use `str.find()` and brace-matching logic rather than line-based parsing.
The replacement block (from Dota2Mods) can keep its original newline formatting — the
game's KV parser accepts both formats.

---

## Finding What Changed Between Mods

### Compare VPK file lists
```python
import vpk
pak1 = vpk.open('pak1.vpk')
pak2 = vpk.open('pak2.vpk')
files1 = set(pak1)
files2 = set(pak2)
print('Only in pak1:', files1 - files2)
print('Only in pak2:', files2 - files1)
for f in files1 & files2:
    if pak1.get_file(f).read() != pak2.get_file(f).read():
        print('CHANGED:', f)
```

### Find hero keyword in VPK
```python
import vpk
pak = vpk.open('pak01_dir.vpk')
hero_files = [f for f in pak if 'hero_keyword' in f.lower()]
print(f'{len(hero_files)} files found')
```

### Check VPK version
```python
import struct
with open('pak01_dir.vpk', 'rb') as f:
    sig, ver, tree_size = struct.unpack('<III', f.read(12))
print(f'VPK v{ver}, tree={tree_size} bytes')
```

### Check Dota2Mods script diff (what items changed)
```
diff %LOCALAPPDATA%\Programs\Dota2Mods\resources\vpk\scripts\base.txt
     %LOCALAPPDATA%\Programs\Dota2Mods\resources\vpk\scripts\replaced.txt
```
Or grep for hero name in `replaced.txt`.

---

## Troubleshooting

**Ardysa still shows after running Approach 2 patch**
→ `_ArdysaMods` folder must be renamed/deleted. The game loads it with highest priority.

**Script says "VPK not found"**
→ Run the mod manager first to create the VPK, then run the patch script.

**Changes not visible in-game**
→ Dota 2 must be fully closed and reopened. A match restart is NOT enough.

**VPK rebuild crashes or produces 0 bytes**
→ `vpk.exe` can fail silently. Check the output file exists and is > 0 bytes before
copying it. The DLLs (tier0.dll, vstdlib.dll, vstdlib_s.dll, filesystem_stdio.dll)
must be in the same folder as vpk.exe.

**vpk.exe extraction fails with "Tried to Write NULL file handle"**
→ Known issue — vpk.exe cannot reliably extract individual files by path. Use the
Python `vpk` library for reading/extracting instead. Only use vpk.exe for building
(creating VPKs from a directory).

**After Ardysa update, patch no longer works**
→ Ardysa has overwritten `_ArdysaMods/pak01_dir.vpk`. Delete the backup file at
`_ArdysaMods/pak01_dir_backup.vpk` and re-run the patch script — it will create
a fresh backup before patching.

**Hero looks broken (missing textures/wrong model)**
→ Files were removed without replacement. Restore from backup and try again, ensuring
all hero files (including the `kisilev_ind/` custom paths) are either kept or replaced.

**items_game.txt patch not applying (0 blocks patched)**
→ The item block search uses the item name string (e.g. `"Vengeful Spirit's Upper Armor"`).
If Ardysa updated their VPK and renamed the item, the search will fail. Re-examine
the items_game.txt from the new VPK and update `item_replacements.json`.

---

## Backups Contents (Example)

| Folder | Source | Files | Size |
|--------|--------|-------|------|
| `backups/green_artemis_windranger/` | Dota2Mods | 179 | 9.7 MB |
| `backups/vengeful_spirit_d2mods/` | Dota2Mods | item_replacements.json + weapon model + ref scripts | 48 MB |
| `backups/ardysa_drow/` | Ardysa | 139 | 71 MB |
| `backups/ardysa_queenofpain/` | Ardysa | 48 | 13 MB |

The `vengeful_spirit_d2mods/scripts/` folder contains full reference copies of
`items_game.txt`, `portraits.txt`, and `precache.txt` from Dota2Mods — useful for
inspecting what Dota2Mods changed vs the base game.

---

## Modifying the Scripts

Both scripts follow the same structure. To add a hero:

1. Add their keyword(s) to the keywords list (check actual file paths in the VPK to confirm the keyword)
2. Add their backup path constant
3. In `patch()`, add an extraction+copy block for the new hero (copy the WR or Drow block as a template)
4. Run the script and verify in-game

Internal name lookup — find what keyword a hero uses in file paths:
```python
import vpk
pak = vpk.open(r'..._ArdysaMods\pak01_dir.vpk')
# Print all unique path segments to find hero's folder name
import os
folders = set(f.split('/')[0] for f in pak if '/' in f)
print(sorted(folders))
```
