#!/usr/bin/env python3
"""Rebuild the pack's Let it Walk! recipe overrides (kubejs/data/let_it_walk/recipe) from the mod's own recipes.

Run from the pack root:  python3 tools/letitwalk/gen_recipes.py <path to let_it_walk jar>

The walker parts take Synaxis machine parts and OpenComputers: Rebooted computer parts:
  Pilot Controls            electron tube      -> OC microchip (tier 1)
  Remote Pilot Controller   Create transmitter -> OC wireless network card (tier 1)
  Walker Core               shaft              -> OC CPU (tier 2)
  Positioner                shafts             -> Synaxis hydraulic linear actuators
  Articulation Unit         cogwheel step      -> Synaxis dynamic joint motor
  Stabilization Module      electron tube step -> Synaxis IMU, Synaxis PID controller and an OC microchip (tier 2)
  Jet Nozzle                iron sheet step    -> steel sheet (#c:plates/steel)
Every other recipe is left to the mod. Only changed recipes are written; each is listed.
"""
import json, os, sys, zipfile

OUT = 'kubejs/data/let_it_walk/recipe'
OC = 'opencomputers:'
SWAPS = {
    'crafting/pilot_controls': {'create:electron_tube': {'item': OC + 'chip1'}},
    'crafting/remote_pilot_controller': {'create:transmitter': {'item': OC + 'wlancard1'}},
    'crafting/walker_core': {'create:shaft': {'item': OC + 'cpu2'}},
    'crafting/leg_positioner': {'create:shaft': {'item': 'synaxis:hydraulic_linear_actuator'}},
    'sequenced_assembly/articulation_unit': {'create:cogwheel': {'item': 'synaxis:dynamic_joint_motor'}},
    'sequenced_assembly/jet_nozzle': {'create:iron_sheet': {'tag': 'c:plates/steel'}},
}
# a deploying step whose item is replaced by several deploying steps
EXPAND = {
    'sequenced_assembly/stabilization_module': ('create:electron_tube',
        [{'item': 'synaxis:cimulink_imu'}, {'item': 'synaxis:cimulink_pid_controller'}, {'item': OC + 'chip2'}]),
}


def swap(node, swaps, found):
    if isinstance(node, dict):
        if set(node) == {'item'} and node['item'] in swaps:
            found.add(node['item'])
            return dict(swaps[node['item']])
        return {k: (v if k in ('result', 'results') else swap(v, swaps, found)) for k, v in node.items()}
    if isinstance(node, list):
        return [swap(v, swaps, found) for v in node]
    return node


def expand(recipe, item, replacements):
    steps, done = [], False
    for step in recipe['sequence']:
        ings = step.get('ingredients', [])
        if step.get('type') == 'create:deploying' and len(ings) == 2 and ings[1] == {'item': item}:
            for rep in replacements:
                steps.append(dict(step, ingredients=[ings[0], rep]))
            done = True
        else:
            steps.append(step)
    if not done:
        raise SystemExit(f'no deploying step with {item}')
    return dict(recipe, sequence=steps)


def main(jar):
    with zipfile.ZipFile(jar) as z:
        for name in sorted(set(SWAPS) | set(EXPAND)):
            recipe = json.loads(z.read(f'data/let_it_walk/recipe/{name}.json'))
            out = recipe
            if name in SWAPS:
                found = set()
                out = swap(out, SWAPS[name], found)
                missing = set(SWAPS[name]) - found
                if missing:
                    raise SystemExit(f'{name}: {missing} not in the recipe any more')
            if name in EXPAND:
                out = expand(out, *EXPAND[name])
            target = os.path.join(OUT, name + '.json')
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, 'w') as f:
                json.dump(out, f, indent=2)
                f.write('\n')
            print(name)


if __name__ == '__main__':
    main(sys.argv[1])
