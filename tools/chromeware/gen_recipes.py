#!/usr/bin/env python3
"""Rebuild the pack's Chromeware recipe overrides (kubejs/data/chromeware/recipe) from the mod's own recipes.

Run from the pack root:  python3 tools/chromeware/gen_recipes.py <path to chromeware jar>
Recipes in tools/chromeware/base/ (the pack's hand-made versions, e.g. the Sandevistan) are used instead of the mod's.

Rules:
  - every crafting-table recipe becomes a Create mechanical crafting recipe with the same pattern
  - Create brass sheets -> titanium sheets (#c:plates/titanium, Create: Cosmonautics)
  - Create iron sheets  -> steel sheets   (#c:plates/steel: Alloyed, Create Gunsmithing, Immersive Engineering, TFMG)
  - cogwheels in the limbs (cyber arm, cyber leg, mantis blades, projectile launch system) -> Synaxis dynamic joint motors
Only recipes that change are written; everything written is listed.
"""
import json, os, sys, zipfile

ITEM_SWAPS = {
    'create:brass_sheet': {'tag': 'c:plates/titanium'},
    'create:iron_sheet': {'tag': 'c:plates/steel'},
}
LIMBS = {'cyber_arm', 'cyber_leg', 'mantis_blades', 'projectile_launch_system'}
LIMB_SWAPS = {
    'create:cogwheel': {'item': 'synaxis:dynamic_joint_motor'},
    'create:large_cogwheel': {'item': 'synaxis:dynamic_joint_motor'},
}
OUT = 'kubejs/data/chromeware/recipe'
BASE = 'tools/chromeware/base'


def swap(node, swaps):
    """replaces ingredient objects ({"item": ...}) anywhere in the recipe, except in its results"""
    if isinstance(node, dict):
        if set(node) == {'item'} and node['item'] in swaps:
            return dict(swaps[node['item']])
        return {k: (v if k in ('result', 'results') else swap(v, swaps)) for k, v in node.items()}
    if isinstance(node, list):
        return [swap(v, swaps) for v in node]
    return node


def convert(name, recipe):
    out = swap(recipe, ITEM_SWAPS)
    if name in LIMBS:
        out = swap(out, LIMB_SWAPS)
    if out.get('type') == 'minecraft:crafting_shaped':
        out = {
            'type': 'create:mechanical_crafting',
            'accept_mirrored': True,
            'category': out.get('category', 'misc'),
            'key': out['key'],
            'pattern': out['pattern'],
            'result': out['result'],
            'show_notification': False,
        }
    return out


def main(jar):
    written = []
    with zipfile.ZipFile(jar) as z:
        for entry in sorted(z.namelist()):
            if not entry.startswith('data/chromeware/recipe/') or not entry.endswith('.json'):
                continue
            rel = entry[len('data/chromeware/recipe/'):]
            base = os.path.join(BASE, rel)
            recipe = json.load(open(base)) if os.path.exists(base) else json.loads(z.read(entry))
            out = convert(os.path.basename(rel)[:-5], recipe)
            target = os.path.join(OUT, rel)
            if out == recipe and not os.path.exists(base):
                if os.path.exists(target):
                    os.remove(target)
                continue
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, 'w') as f:
                json.dump(out, f, indent=2)
                f.write('\n')
            written.append((rel, recipe.get('type'), out.get('type')))
    for rel, before, after in written:
        print(f'{rel:45} {before} -> {after}' if before != after else f'{rel:45} {after}')
    print(len(written), 'recipes written')


if __name__ == '__main__':
    main(sys.argv[1])
