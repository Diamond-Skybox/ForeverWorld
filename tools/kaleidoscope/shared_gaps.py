# --- Farmer's Delight <-> Kaleidoscope Cookery recipe gaps ------------------------------------------------
# Run from the pack root:  python3 -I tools/kaleidoscope/shared_gaps.py <instance mods folder> [-v]
# Counts dishes one family's stations make that the other's don't, across every add-on, from a static read of the jars plus
# kubejs/data (recipes whose neoforge:conditions name a mod that isn't installed are dropped; kubejs/data copies win).
#   cooking: Farmer's Delight cooking pot  <->  Kaleidoscope stockpot / wok (pot), flex versions included
#   cutting: Farmer's Delight cutting board with a knife  <->  Kaleidoscope chopping board (by input item)
# Kaleidoscope's stockpot already cooks every cooking pot recipe at runtime (CookingPotCompat: no stockpot recipe matched -> it tries
# the cooking pot recipes), except results in #kaleidoscope_cookery:only_stockpot_output_recipe, so the cooking pot -> stockpot gap
# is only those; the other way has no fallback.
# A Kaleidoscope dish only "fits" the cooking pot with at most 6 ingredients (the pot's slots); the stockpot and wok take 9.
# This reads jars and kubejs/data only: the cooking pot copies kubejs/server_scripts/kaleidoscope_cooking_pot.js adds at load time
# (for the stockpot/wok-only dishes counted here) aren't seen, so those gaps still show; the script logs what it covered.
import collections, json, os, sys, zipfile
sys.path.insert(0, os.path.dirname(__file__))
import recipe_index as R

MODS = sys.argv[1]
VERBOSE = '-v' in sys.argv


LOADED = R.loaded_mods(MODS)


def active(j):
    return R.active(j, LOADED)


def ingredients(j):
    v = j.get('ingredients') or []
    return v if isinstance(v, list) else [v]


def knife(j):
    return 'knife' in json.dumps(j.get('tool', '')) or 'knives' in json.dumps(j.get('tool', ''))


def key(ing):
    """an ingredient as a comparable id (item or #tag); a list of alternatives keeps its first entry"""
    if isinstance(ing, list):
        ing = ing[0] if ing else {}
    if isinstance(ing, dict):
        if 'item' in ing:
            return ing['item']
        if 'tag' in ing:
            return '#' + ing['tag']
        for k in ('ingredient', 'children'):
            if k in ing:
                return key(ing[k])
    return json.dumps(ing, sort_keys=True)


idx = R.index(MODS, 'kubejs/data')
FD_COOK = {'farmersdelight:cooking'}
KC_COOK = {'kaleidoscope_cookery:stockpot', 'kaleidoscope_cookery:pot', 'kaleidoscope_cookery:flex_stockpot', 'kaleidoscope_cookery:flex_pot'}
fd, kc = collections.defaultdict(list), collections.defaultdict(list)  # result item -> [(recipe id, ingredient count, source)]
fd_cut, kc_cut = collections.defaultdict(list), collections.defaultdict(list)  # input -> [recipe id]
OTHER = {'minecraft:campfire_cooking', 'minecraft:smelting', 'minecraft:smoking', 'minecraft:crafting_shaped', 'minecraft:crafting_shapeless'}
other = set()  # items with a skillet/campfire, furnace or crafting recipe: a stockpot/wok version of those isn't a gap
for rid, e in idx.items():
    j = e['json']
    if not active(j):
        continue
    t = R.rtype(j)
    if t in FD_COOK:
        for r in R.results(j):
            fd[r].append((rid, len(ingredients(j)), e['src']))
    elif t in KC_COOK:
        for r in R.results(j):
            kc[r].append((rid, len(ingredients(j)), e['src']))
    elif t in OTHER:
        other.update(R.results(j))
    elif t == 'farmersdelight:cutting' and knife(j):
        fd_cut[key(ingredients(j)[0] if ingredients(j) else {})].append(rid)
    elif t == 'kaleidoscope_cookery:chopping_board':
        kc_cut[key(j.get('ingredient', {}))].append(rid)


def owner(item):
    return item.split(':')[0]


vanilla = {r for r in set(fd) | set(kc) if owner(r) == 'minecraft'}  # vanilla items have vanilla routes (furnace, crafting) anyway
fd_only = sorted(set(fd) - set(kc) - vanilla)
def tag_items(tid, seen=()):
    ns, path = tid.split(':', 1)
    out = set()
    for j in os.listdir(MODS):
        if not j.endswith('.jar'):
            continue
        try:
            z = zipfile.ZipFile(os.path.join(MODS, j))
        except Exception:
            continue
        for n in (f'data/{ns}/tags/item/{path}.json', f'packs/always/data/{ns}/tags/item/{path}.json'):
            if n in z.namelist():
                for v in json.loads(z.read(n)).get('values', []):
                    v = v['id'] if isinstance(v, dict) else v
                    out |= tag_items(v[1:], seen + (tid,)) if v.startswith('#') and v[1:] not in seen else ({v} if not v.startswith('#') else set())
    return out
stockpot_only_tag = tag_items('kaleidoscope_cookery:only_stockpot_output_recipe')
fd_blocked = sorted(r for r in fd_only if r in stockpot_only_tag)
kc_only = sorted(set(kc) - set(fd) - other - vanilla)
kc_elsewhere = sorted((set(kc) - set(fd)) & (other | vanilla))
kc_fits = [r for r in kc_only if min(n for _, n, _ in kc[r]) <= 6]
both = set(fd) & set(kc)
print(f'cooking: {len(fd)} cooking pot dishes, {len(kc)} stockpot/wok dishes, {len(both)} made in both')
print(f'  cooking pot dishes with no stockpot/wok recipe of their own: {len(fd_only)}; the stockpot still cooks all of them through its'
      f' fallback except {len(fd_blocked)} ({", ".join(fd_blocked) or "none"})')
print(f'  cooking pot only, by mod: {dict(collections.Counter(map(owner, fd_only)).most_common())}')
print(f'  stockpot/wok only: {len(kc_only)}, of which {len(kc_fits)} fit the cooking pot\'s 6 slots   '
      f'(by mod: {dict(collections.Counter(map(owner, kc_only)).most_common())})')
cut_fd_only = sorted(set(fd_cut) - set(kc_cut))
cut_kc_only = sorted(set(kc_cut) - set(fd_cut))
print(f'  (left out: {len(kc_elsewhere)} stockpot/wok dishes made outside the cooking pot already (skillet/campfire, furnace, crafting,'
      f' vanilla), and {len((set(fd) - set(kc)) & vanilla)} vanilla items the cooking pot makes)')
kc_max = max((n for v in kc.values() for _, n, _ in v), default=0)
print(f'  largest stockpot/wok recipe: {kc_max} ingredients; largest cooking pot recipe going the other way: '
      f'{max((min(n for _, n, _ in fd[r]) for r in fd_only), default=0)}')
print(f'cutting: {len(fd_cut)} knife inputs on the cutting board, {len(kc_cut)} on the chopping board, '
      f'{len(set(fd_cut) & set(kc_cut))} on both; cutting board only {len(cut_fd_only)}, chopping board only {len(cut_kc_only)}')
if VERBOSE:
    for name, items, src in (('COOKING POT ONLY', fd_only, fd), ('STOCKPOT/WOK ONLY', kc_only, kc)):
        print('\n==', name)
        for r in items:
            n = min(c for _, c, _ in src[r])
            print(f'  {r}  ({n} ingredients{"" if n <= 6 else ", too many for the cooking pot"})')
    print('\n== CHOPPING BOARD ONLY')
    for i in cut_kc_only:
        print('  ', i)
