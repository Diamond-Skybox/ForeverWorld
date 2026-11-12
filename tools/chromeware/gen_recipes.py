#!/usr/bin/env python3
"""Rebuild the pack's Chromeware recipe overrides (kubejs/data/chromeware/recipe) from the mod's own recipes.

Run from the pack root:  python3 tools/chromeware/gen_recipes.py <path to chromeware jar>
Recipes in tools/chromeware/base/ (the pack's hand-made versions, e.g. the Sandevistan) are used instead of the mod's.
Implant capacity costs are read from config/chromeware-server.toml.

Rules, in this order:
  1. per-recipe parts (PARTS): OpenComputers: Rebooted memory, processors, storage and cards where the implant is one,
     and sensors and lenses for the optics
  2. Create copper sheets by what they are in the implant (COPPER): TFMG copper wire in electrical parts, TFMG plastic
     sheets in medical and fluid parts and housings, TFMG rubber sheets in tendons and padding
  3. Create electron tubes -> OpenComputers microchips by implant tier (capacity cost 0-8 tier 1, 9-20 tier 2, 21-35
     tier 3, 36+ tier 4; quickhacks by QUICKHACK_TIER)
  4. Create brass sheets -> titanium sheets (#c:plates/titanium, Create: Cosmonautics); Create iron sheets -> steel
     sheets (#c:plates/steel: Alloyed, Create Gunsmithing, Immersive Engineering, TFMG)
  5. cogwheels in the limbs (cyber arm, cyber leg, mantis blades, projectile launch system) -> Synaxis dynamic joint motors
  6. every crafting-table recipe becomes a Create mechanical crafting recipe with the same pattern
Only recipes that change are written; everything written is listed.
"""
import re
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
OC = 'opencomputers:'
PARTS = {
    # memory
    'ram_upgrade': {'create:polished_rose_quartz': OC + 'ram1'},
    'camillo_ram_manager': {'create:polished_rose_quartz': OC + 'ram2', 'minecraft:comparator': OC + 'cu'},
    'memory_boost': {'create:polished_rose_quartz': OC + 'ram3'},
    'ram_recoup': {'create:polished_rose_quartz': OC + 'ram4'},
    'ram_reallocator': {'create:polished_rose_quartz': OC + 'ram7'},
    # processing and storage
    'cyberdeck': {'create:electron_tube': OC + 'cpu2', 'create:polished_rose_quartz': OC + 'componentbus1'},
    'mechatronic_core': {'create:electron_tube': OC + 'cpu1'},
    'cox_2_cybersomatic_optimizer': {'create:electron_tube': OC + 'cpu4'},
    'quantum_tuner': {'create:electron_tube': OC + 'apu3'},
    'sandevistan': {'create:electron_tube': OC + 'apu3'},
    'cogito_lattice': {'create:polished_rose_quartz': OC + 'alu'},
    'ex_disk': {'create:polished_rose_quartz': OC + 'hdd1'},
    # power
    'microgenerator': {'create:cogwheel': OC + 'generatorupgrade'},
    'electromag_recycler': {'create:precision_mechanism': OC + 'batteryupgrade2'},
    # networked quickhacks (every quickhack also takes an EEPROM, see below)
    'quickhack_contagion': {'create:redstone_link': OC + 'wlancard1'},
    'quickhack_request_backup': {'create:redstone_link': OC + 'wlancard1'},
    'quickhack_blackwall_gateway': {'create:redstone_link': OC + 'linkedcard', 'create:sturdy_sheet': OC + 'internetcard'},
    'quickhack_suicide': {'minecraft:diamond': OC + 'chipdiamond'},
    # optics
    'kiroshi_optics': {'create:andesite_alloy': 'synaxis:camera'},
    'clairvoyant': {'minecraft:amethyst_shard': OC + 'motionsensor'},
    'stalker': {'minecraft:amethyst_shard': 'create_radar:sonar_sensor'},
    'sentry': {'create:redstone_link': OC + 'redstonecard2'},
    'doomsayer': {'minecraft:observer': 'pneumaticcraft:universal_sensor'},
    'the_oracle': {'minecraft:amethyst_shard': OC + 'hologram2'},
    'cockatrice': {'minecraft:amethyst_shard': 'cgs:scope'},
    'visual_cortex_support': {'minecraft:spyglass': 'exposure_space:normal_telescopic_lens'},
    'deep_field_visual_interface': {'minecraft:amethyst_shard': 'exposure_space:excellent_telescopic_lens'},
}
WIRE, PLASTIC, RUBBER = 'tfmg:copper_wire', 'tfmg:plastic_sheet', 'tfmg:rubber_sheet'
COPPER = {
    WIRE: ['atomic_sensors', 'cyberdeck', 'deep_field_visual_interface', 'feen_x', 'memory_boost', 'microgenerator', 'pain_editor',
           'quickhack_overheat', 'quickhack_remote_activation', 'quickhack_short_circuit', 'revulsor', 'self_ice', 'shock_n_awe',
           'visual_cortex_support'],
    PLASTIC: ['adrenaline_booster', 'adrenaline_converter', 'blood_pump', 'monowire', 'scar_coalescer', 'threat_evac',
              'universal_booster', 'zetatech_berserk'],
    RUBBER: ['jenkins_tendons', 'leeroy_ligament_system', 'lynx_paws', 'reinforced_tendons', 'shock_absorber'],
}
COPPER_OF = {name: item for item, names in COPPER.items() for name in names}
QUICKHACK_TIER = {
    'bait': 1, 'memory_wipe': 1, 'reboot_optics': 1, 'remote_activation': 1, 'request_backup': 1, 'weapon_glitch': 1,
    'contagion': 2, 'cripple_movement': 2, 'cyberware_malfunction': 2, 'detonate_grenade': 2, 'overheat': 2, 'short_circuit': 2,
    'cyberpsychosis': 3, 'synapse_burnout': 3,
    'blackwall_gateway': 4, 'suicide': 4, 'system_collapse': 4,
}
CONFIG = 'config/chromeware-server.toml'
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


def capacities():
    caps, current = {}, None
    for line in open(CONFIG):
        m = re.match(r'\s*\[implants\.(\w+)\]', line)
        if m:
            current = m.group(1)
            continue
        m = re.match(r'\s*capacity\s*=\s*(\d+)', line)
        if m and current:
            caps[current] = int(m.group(1))
    return caps


CAPS = {}


def tier(name):
    if name.startswith('quickhack_'):
        return QUICKHACK_TIER[name[len('quickhack_'):]]
    cap = CAPS.get(name, 0)
    if name in ('cyber_arm', 'cyber_leg', 'cyber_torso'):
        return 2
    return 1 if cap <= 8 else 2 if cap <= 20 else 3 if cap <= 35 else 4


def items_in(node):
    text = json.dumps({k: v for k, v in node.items() if k not in ('result', 'results')})
    return set(re.findall(r'"item": "([^"]+)"', text))


def item_swaps(swaps):
    return {k: {'item': v} for k, v in swaps.items()}


def convert(name, recipe):
    out = recipe
    if name in PARTS:
        missing = set(PARTS[name]) - items_in(out)
        if missing:
            raise SystemExit(f'{name}: no {missing} in the recipe any more')
        out = swap(out, item_swaps(PARTS[name]))
    present = items_in(out)
    if 'create:copper_sheet' in present:
        if name not in COPPER_OF:
            raise SystemExit(f'{name}: has copper sheets but no COPPER group')
        out = swap(out, item_swaps({'create:copper_sheet': COPPER_OF[name]}))
    if name.startswith('quickhack_'):
        out = swap(out, item_swaps({'create:polished_rose_quartz': OC + 'eeprom'}))
    out = swap(out, item_swaps({'create:electron_tube': OC + 'chip' + str(tier(name))}))
    out = swap(out, ITEM_SWAPS)
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
    CAPS.update(capacities())
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
