import zipfile, os, json, re, sys, collections
M = sys.argv[1]
tags = collections.defaultdict(list)   # tag id -> entries
items = set()
def add_tag(tid, data):
    if data.get('replace'):
        tags[tid] = []
    for v in data.get('values', []):
        tags[tid].append(v['id'] if isinstance(v, dict) else v)
for j in sorted(os.listdir(M)):
    if not j.endswith('.jar'): continue
    try: z = zipfile.ZipFile(os.path.join(M, j))
    except Exception: continue
    for n in z.namelist():
        m = re.match(r'^data/([^/]+)/tags/items?/(.+)\.json$', n)
        if m:
            try: add_tag(f'{m.group(1)}:{m.group(2)}', json.loads(z.read(n)))
            except Exception: pass
        m = re.match(r'^assets/([^/]+)/models/item/([^/]+)\.json$', n)
        if m: items.add(f'{m.group(1)}:{m.group(2)}')
kj = os.path.join('kubejs', 'data')
for root, _, files in os.walk(kj):
    for f in files:
        p = os.path.join(root, f); m = re.search(r'data/([^/]+)/tags/items?/(.+)\.json$', p)
        if m and m.group(1) != 'vegandelight': add_tag(f'{m.group(1)}:{m.group(2)}', json.load(open(p)))
memo = {}
def resolve(tid, seen=()):
    if tid in memo: return memo[tid]
    out = set()
    for e in tags.get(tid, []):
        if e.startswith('#'):
            if e[1:] not in seen: out |= resolve(e[1:], seen + (tid,))
        else: out.add(e)
    memo[tid] = out; return out
notv = resolve('vegandelight:not_vegan'); vegan = resolve('vegandelight:vegan')
# --- Vegan Delight label tags for the pack -------------------------------------------------------------
# Run from the pack root:  python3 tools/vegandelight/gen_tags.py <instance mods folder>
# Vegan Delight labels from (in order) its vegandelight:vegan tag, its vegandelight:not_vegan tag, then a recipe scan.
# Its own tags only reach modded food through shared tags many mods leave out, and Pam's HarvestCraft puts avocado and
# banana in c:eggs (as egg substitutes), so they read as not vegan. This writes the pack's additions:
#   not_vegan: modded raw/cooked meats and seafood, eggs, dairy and honey foods not in its tags (whole-word name scan,
#              with the false positives in DROP); dishes made from them follow through its recipe scan
#   vegan:     crop, seed, vegetable, fruit, berry and mushroom tags plus vanilla plants (checked before not_vegan)
RAW = {'meat','beef','pork','porkchop','chicken','mutton','venison','bison','turkey','cassowary','kangaroo','moose','rib','ribs','liver','brain','tentacle','tentacles','crab','shrimp','lobster','clam','oyster','squid','calamari','fish','fillet','salmon','cod','tuna','trout','bass','carp','perch','pike','catfish','eel','lionfish','spinefish','blobfish','bacon','ham','sausage','jerky','steak','drumstick','chop','naga','yeti','hoglin','strider','ghast','frog','clawster','crawfish','shellfish','roe','caviar','wilden','chimera','leviathan','berserker','koboleton','meef','smeak','duck','goose','lamb','rabbit','emu','crocodile','caiman'}
DAIRY = {'egg','eggs','milk','cheese','butter','honey','yogurt','cream','milkshake','custard','mayonnaise','omelet','omelette'}
NOT = {'bucket','barrel','spawn','knife','medal','mount','block','statue','idol','trophy','head','skull','sign','banner','incubator','chestplate','helmet','boots','leggings','sword','axe','hook','net','trap','crate','sack','eating','gui','hand','huge','model','incomplete','unfinished','bed','crib','plush','figure','painting','shell','scute','tusk','feather','hide','leather','bone','bones','scale','scales','seeds','seed','sapling','plant','wax','beeswax','lights','entity','form','press','churn','machine','jar','cabinet'}
MEAT_ONLY_NOT = {'sauce','soy','coconut','peanut','oat','almond','rice','candy'}
SINGLE = re.compile(r'(^|_)(raw|cooked)(_|$)|(^|_)(meat|steak|fillet|venison|bison|turkey|liver|brain|tentacles?|ribs?|crab|shrimp|lobster|clam)$')
DROP = {'block_factorys_bosses:undying_tentacle','traveloptics:abyssal_tentacle','koopascritters:potof_tree_lobster',
        'crabbersdelight:coconut_milk','doggytalents:soy_milk','moredelight:toast_with_peanut_butter','cocktailsdelight:cream_ale',
        'create_connected:fan_honey_coating_catalyst','create_things_and_misc:spout_gun_honey','sable_schematic_api:honey_welder',
        'occultism:mysterious_egg_icon','familiarslib:familiar_egg','hazennstuff:servant_of_ender_egg','hazennstuff:the_recluse_egg',
        'hazennstuff:void_wanderer_egg','forbidden_arcanus:arcane_dragon_egg','golemoverhaul:honey_blob','occultism:cursed_honey',
        'occultism:sweet_honey_heart','doggytalents:easter_egg_candy','hexalia:egg_cluster','wandering_ribbit:ribbit_egg',
        'biomesoplenty:spider_egg','meadow:pine_cheese_rack'}
PLANT_TAGS = ['c:crops','c:seeds','c:foods/vegetable','c:foods/fruit','c:foods/berry','c:mushrooms']
PLANT_ITEMS = ['minecraft:cactus','minecraft:sugar_cane','minecraft:sugar','minecraft:kelp','minecraft:dried_kelp','minecraft:bamboo',
               'minecraft:sweet_berries','minecraft:glow_berries','minecraft:chorus_fruit','minecraft:wheat','minecraft:potato',
               'minecraft:baked_potato','minecraft:carrot','minecraft:beetroot','minecraft:apple','minecraft:melon_slice',
               'minecraft:pumpkin','minecraft:cocoa_beans','minecraft:bread']
# the pack's own additions are not counted when deciding what is missing
for tid in ('vegandelight:not_vegan', 'vegandelight:vegan'):
    memo.clear()
own = os.path.join('kubejs', 'data', 'vegandelight', 'tags', 'item')
notv = resolve('vegandelight:not_vegan'); vegan = resolve('vegandelight:vegan')
add = set()
for i in sorted(items):
    if i.startswith('minecraft:') or i in DROP: continue
    t = set(i.split(':')[1].replace('-', '_').split('_'))
    if t & NOT: continue
    if t & RAW and not t & MEAT_ONLY_NOT and SINGLE.search(i.split(':')[1]): add.add(i)
    elif t & DAIRY: add.add(i)
plants = set(PLANT_ITEMS)
for t in PLANT_TAGS: plants |= resolve(t)
clash = sorted(plants & add)
if clash: raise SystemExit(f'plant tags would mark these vegan: {clash}')
def write(name, values):
    with open(os.path.join(own, name), 'w') as f:
        json.dump({'replace': False, 'values': [{'id': v, 'required': False} for v in values]}, f, indent=2); f.write('\n')
write('not_vegan.json', sorted(add))
write('vegan.json', ['#' + t for t in PLANT_TAGS] + PLANT_ITEMS)
print(f'not_vegan.json: {len(add)} items; vegan.json: {len(PLANT_TAGS)} tags + {len(PLANT_ITEMS)} items; '
      f'plants already in not_vegan, now vegan: {sorted(plants & notv)}')
