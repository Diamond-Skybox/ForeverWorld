# --- Kaleidoscope Texture Expansion fixes for the pack ---------------------------------------------------
# Run from the pack root:  python3 -I tools/kaleidoscope/gen_restore.py <instance mods folder>
#
# Kaleidoscope Texture Expansion (soup_pot_texture_expansion) ships stockpot/wok versions of Farmer's Delight cooking pot recipes
# under the SAME recipe ids as the originals (Farmer's Delight, Rustic Delight, Brewin' and Chewin', Trail and Tales Delight, Cultural
# Delights), which replaces them: those dishes could no longer be made in the cooking pot, and Delightful Creators (which builds its
# Create recipes from cooking pot recipes) skipped them too. Several of its files are also broken JSON (a stray "}," after the type
# line, a trailing comma), so those recipes didn't load at all, including Kaleidoscope's own dumpling stockpot recipes it restyles.
#
# This writes into kubejs/data (which loads after every mod):
#   - each replaced cooking pot recipe back under its own id (the original from the mod it came from), and
#   - the texture mod's stockpot/wok version under kaleidoscope_cookery:<stockpot|pot>/fd_compat/<ns>/<path>, so both stations work;
#   - repaired copies of its broken files that restyle Kaleidoscope's own recipes, under the same ids.
# Files it wrote before are listed in tools/kaleidoscope/restore_manifest.txt and are removed first, so reruns stay clean.
import json, os, re, sys, zipfile

MODS = sys.argv[1]
OUT = os.path.join('kubejs', 'data')
MANIFEST = os.path.join('tools', 'kaleidoscope', 'restore_manifest.txt')
TE_PREFIX = 'Kaleidoscope Texture Expansion-'
PAT = re.compile(r'^data/([^/]+)/(recipe)/(.+)\.json$')  # 1.21 loads recipe/ only (old recipes/ folders are ignored)


def repair(raw):
    """the texture mod's two JSON mistakes: '"type": "...",\n  },' and a trailing comma before the closing brace"""
    try:
        return json.loads(raw)
    except ValueError:
        pass
    fixed = re.sub(r'("type"\s*:\s*"[^"]+"\s*,)\s*\}\s*,', r'\1', raw)
    fixed = re.sub(r',(\s*[}\]])', r'\1', fixed)
    return json.loads(fixed)


def write(rel, data, written):
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
        f.write('\n')
    written.append(rel)


if os.path.exists(MANIFEST):
    for rel in open(MANIFEST).read().split():
        p = os.path.join(OUT, rel)
        if os.path.exists(p):
            os.remove(p)

jars = sorted(j for j in os.listdir(MODS) if j.endswith('.jar'))
te_name = next(j for j in jars if j.startswith(TE_PREFIX))
te = zipfile.ZipFile(os.path.join(MODS, te_name))
others = {}  # zip entry -> [(jar name, raw bytes)] for every other jar that ships the same entry
te_entries = {n for n in te.namelist() if PAT.match(n)}
for j in jars:
    if j == te_name:
        continue
    try:
        z = zipfile.ZipFile(os.path.join(MODS, j))
    except Exception:
        continue
    for n in te_entries.intersection(z.namelist()):
        others.setdefault(n, []).append((j, z.read(n)))

written, restored, moved, repaired, skipped = [], [], [], [], []
for n in sorted(te_entries):
    ns, _, path = PAT.match(n).groups()
    raw = te.read(n).decode('utf-8-sig')
    try:
        te_json = repair(raw)
    except ValueError as e:
        skipped.append(f'{n}: unrepairable ({e})')
        continue
    try:
        json.loads(raw)
        was_broken = False
    except ValueError:
        was_broken = True
    if n not in others:
        if was_broken:  # a new recipe of its own that never loaded
            write(f'{ns}/recipe/{path}.json', te_json, written)
            repaired.append(f'{ns}:{path}')
        continue
    # originals: prefer an add-on's copy over Farmer's Delight's own (add-ons override Farmer's Delight on purpose)
    copies = [(j, json.loads(b)) for j, b in others[n]]
    cooking = [(j, d) for j, d in copies if d.get('type') == 'farmersdelight:cooking']
    if cooking:
        cooking.sort(key=lambda c: c[0].startswith('FarmersDelight'))
        write(f'{ns}/recipe/{path}.json', cooking[0][1], written)
        restored.append(f'{ns}:{path} ({cooking[0][0]})')
        station = te_json.get('type', '').split(':')[-1]
        if station in ('stockpot', 'pot'):
            write(f'kaleidoscope_cookery/recipe/{station}/fd_compat/{ns}/{path}.json', te_json, written)
            moved.append(f'kaleidoscope_cookery:{station}/fd_compat/{ns}/{path}')
    elif was_broken:  # a restyle of another Kaleidoscope recipe that failed to load: keep the restyle, repaired
        write(f'{ns}/recipe/{path}.json', te_json, written)
        repaired.append(f'{ns}:{path}')

os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
with open(MANIFEST, 'w') as f:
    f.write('\n'.join(sorted(written)) + '\n')
print(f'{len(restored)} cooking pot recipes restored, {len(moved)} stockpot/wok versions kept under fd_compat ids, '
      f'{len(repaired)} broken recipes repaired, {len(skipped)} skipped')
for s in skipped:
    print('  skipped', s)
if '-v' in sys.argv:
    for group, items in (('restored', restored), ('moved', moved), ('repaired', repaired)):
        for i in items:
            print(group, i)
