# --- Farmer's Delight cooking pot versions of Kaleidoscope stockpot/wok-only dishes --------------------------
# Run from the pack root:  python3 -I tools/kaleidoscope/gen_cooking_pot.py <instance mods folder> [-v] [--dry]
#
# Kaleidoscope's stockpot falls back to cooking pot recipes, but nothing goes the other way: dishes that only have a stockpot or
# wok recipe can't be made in the cooking pot (and so not in Hands On Delight's pot or by Delightful Creators' Create recipes).
# For every such dish (same selection as shared_gaps.py: no cooking pot recipe, no skillet/campfire/furnace/crafting route, not
# vanilla) this writes a farmersdelight:cooking copy of each of its stockpot/wok recipes that fits the pot's 6 slots, to
#   kubejs/data/kaleidoscope_cookery/recipe/cooking_pot_compat/<ns>/<path>.json
# Translation: ingredients as-is; the stockpot's soup base becomes one more ingredient (water = none, see SOUP_BASE); carrier ->
# container (stockpot default bowl, wok default none), except a tag carrier (the Nether "... rice" dishes are served onto a bowl
# of #c:foods/cooked_rice), which becomes an ingredient with a bowl container (the rice's bowl comes back as its remainder);
# result (servings) as-is; time -> cookingtime (stockpot 300, wok 200).
# A recipe is skipped when its ingredients are the same as an existing cooking pot recipe for another dish, or as another generated
# one (the pot takes whichever it finds first, so one of the two dishes would become unmakeable).
# The source recipe's conditions are kept and a mod_loaded condition is added for every mod an item belongs to.
# Files from the previous run (tools/kaleidoscope/cooking_pot_manifest.txt) are removed first, so they don't count as routes.
import collections, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import recipe_index as R

MODS = sys.argv[1]
VERBOSE, DRY = '-v' in sys.argv, '--dry' in sys.argv
OUT = os.path.join('kubejs', 'data')
DIR = 'kaleidoscope_cookery/recipe/cooking_pot_compat'
MANIFEST = os.path.join('tools', 'kaleidoscope', 'cooking_pot_manifest.txt')
SLOTS = 6

# soup base id -> extra cooking pot ingredient (None = nothing to add). Lava and milk buckets hand back the empty bucket in the
# pot (crafting remainder); live-fish bases use the fish itself, so the pot doesn't eat the bucket.
SOUP_BASE = {
    'minecraft:water': None,
    'minecraft:lava': {'item': 'minecraft:lava_bucket'},
    'minecraft:milk': {'tag': 'c:drinks/milk'},
    'minecraft:cod_bucket': {'item': 'minecraft:cod'},
    'minecraft:salmon_bucket': {'item': 'minecraft:salmon'},
    'minecraft:tropical_fish_bucket': {'item': 'minecraft:tropical_fish'},
    'minecraft:pufferfish_bucket': {'item': 'minecraft:pufferfish'},
    'minecraft:axolotl_bucket': {'item': 'minecraft:axolotl_bucket'},
    'minecraft:tadpole_bucket': {'item': 'minecraft:tadpole_bucket'},
    'kaleidoscope_end:dragon_breath': {'item': 'minecraft:dragon_breath'},
}
STOCKPOT = {'kaleidoscope_cookery:stockpot', 'kaleidoscope_cookery:flex_stockpot'}
WOK = {'kaleidoscope_cookery:pot', 'kaleidoscope_cookery:flex_pot'}
OTHER = {'farmersdelight:cooking', 'minecraft:campfire_cooking', 'minecraft:smelting', 'minecraft:smoking',
         'minecraft:crafting_shaped', 'minecraft:crafting_shapeless'}

if os.path.exists(MANIFEST) and not DRY:
    for rel in open(MANIFEST).read().split():
        p = os.path.join(OUT, rel)
        if os.path.exists(p):
            os.remove(p)
    old = set(open(MANIFEST).read().split())
else:
    old = set()

loaded = R.loaded_mods(MODS)
idx = R.index(MODS, OUT)
kc, routed, fd_sigs = collections.defaultdict(list), set(), {}


def sig_of(ings):
    return tuple(sorted(json.dumps(i, sort_keys=True) for i in ings))


for rid, e in idx.items():
    j = e['json']
    if DRY and rid.startswith('kaleidoscope_cookery:cooking_pot_compat/'):
        continue  # a dry run leaves the old files in place; don't let them hide the gaps
    if not R.active(j, loaded):
        continue
    t = R.rtype(j)
    if t in STOCKPOT | WOK:
        for r in R.results(j):
            kc[r].append((rid, j))
    elif t in OTHER:
        routed.update(R.results(j))
    if t == 'farmersdelight:cooking':
        fd_sigs[sig_of(j.get('ingredients') or [])] = (rid, R.results(j))


def item_ids(x):
    """every explicit item id inside an ingredient / stack json"""
    if isinstance(x, list):
        return [i for v in x for i in item_ids(v)]
    if isinstance(x, dict):
        out = [x[k] for k in ('item', 'id') if isinstance(x.get(k), str)]
        return out + [i for k, v in x.items() if isinstance(v, (dict, list)) for i in item_ids(v)]
    return []


def container(carrier):
    """Kaleidoscope carrier (an ingredient) -> cooking pot container stack; a tag or list keeps its first item"""
    if isinstance(carrier, list):
        carrier = carrier[0] if carrier else None
    if not carrier:
        return None
    if 'item' in carrier:
        return {'count': 1, 'id': carrier['item']}
    raise ValueError(f'carrier {carrier} is not a single item')


written, made, skipped, too_big, clashes = [], collections.Counter(), [], [], []
for dish in sorted(set(kc) - routed):
    if dish.split(':')[0] == 'minecraft':
        continue
    seen, fitted, clashed = set(), False, False
    for rid, j in sorted(kc[dish]):
        t = R.rtype(j)
        ings = list(j.get('ingredients') or [])
        if t in STOCKPOT:
            base = j.get('soup_base', 'minecraft:water')
            if base not in SOUP_BASE:
                skipped.append(f'{rid}: unknown soup base {base}')
                continue
            if SOUP_BASE[base]:
                ings.append(SOUP_BASE[base])
            carrier = j.get('carrier', {'item': 'minecraft:bowl'})
            time = j.get('time', 300)
        else:
            carrier = j.get('carrier')
            time = j.get('time', 200)
        if isinstance(carrier, dict) and 'tag' in carrier:
            ings.append(carrier)
            carrier = {'item': 'minecraft:bowl'}
        if len(ings) > SLOTS:
            continue
        sig = sig_of(ings)
        if sig in seen:
            continue  # same ingredients as another variant (Kaleidoscope ships texture-only variants)
        if sig in fd_sigs and dish not in fd_sigs[sig][1]:
            skipped.append(f'{rid}: same ingredients as {fd_sigs[sig][0]} ({", ".join(fd_sigs[sig][1])})')
            clashed = True
            continue
        try:
            cont = container(carrier)
        except ValueError as e:
            skipped.append(f'{rid}: {e}')
            continue
        seen.add(sig)
        fd_sigs[sig] = (f'kaleidoscope_cookery:{DIR.split("/recipe/")[1]}/{rid.replace(":", "/", 1)}', [dish])
        fitted = True
        out = {'type': 'farmersdelight:cooking'}
        mods = sorted({i.split(':')[0] for i in item_ids(ings) + item_ids(j['result']) + ([cont['id']] if cont else [])} - {'minecraft'})
        conds = list(j.get('neoforge:conditions', [])) + [{'type': 'neoforge:mod_loaded', 'modid': m} for m in mods]
        if conds:
            out['neoforge:conditions'] = conds
        out['recipe_book_tab'] = 'meals'
        out['ingredients'] = ings
        out['result'] = j['result']
        if cont:
            out['container'] = cont
        out['experience'] = 1.0
        out['cookingtime'] = time
        ns, path = rid.split(':', 1)
        rel = f'{DIR}/{ns}/{path}.json'
        if not DRY:
            p = os.path.join(OUT, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, 'w') as f:
                json.dump(out, f, indent=2)
                f.write('\n')
        written.append(rel)
        made[dish.split(':')[0]] += 1
        if VERBOSE:
            print(f'  {dish} <- {rid}  ({len(ings)} ingredients{", container " + cont["id"] if cont else ""}, {time} ticks)')
    if not fitted:
        (clashes if clashed else too_big).append(dish)

if not DRY:
    with open(MANIFEST, 'w') as f:
        f.write('\n'.join(sorted(written)) + '\n')
print(f'{"(dry run) " if DRY else ""}{len(written)} cooking pot recipes for '
      f'{len(set(kc) - routed) - len(too_big) - len(clashes) - sum(1 for d in set(kc) - routed if d.startswith("minecraft:"))} dishes '
      f'(by mod: {dict(made.most_common())}); {len(too_big)} dishes have no recipe that fits {SLOTS} slots, '
      f'{len(clashes)} only clash with another dish ({", ".join(clashes) or "none"})')
if old and not DRY:
    print(f'  {len(old - set(written))} files from the last run no longer generated, {len(set(written) - old)} new')
for s in skipped:
    print('  skipped', s)
if VERBOSE:
    print('too big:', ', '.join(too_big))
