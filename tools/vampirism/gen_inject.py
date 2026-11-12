#!/usr/bin/env python3
"""Rebuild Vampirism's chest loot injections (kubejs/data/vampirism/loot_table/inject) from the mod's own.

Run from the pack root:  python3 tools/vampirism/gen_inject.py <path to Vampirism jar>

Vampirism adds a pool pointing at vampirism:inject/<chest> to five vanilla chests (abandoned mineshaft, jungle temple,
desert pyramid, stronghold corridor and library). Its tables there give several rolls, some guaranteed (an accessory
in every desert pyramid, a book and three accessories in every stronghold library). Here each becomes one roll with a
CHANCE of a single Vampirism item; which item keeps the mod's own proportions for that chest (each item weighted by
how many of it the original table gave on average), with the item's own functions (blood fill, book, refinements).
"""
import json, os, sys, zipfile

CHANCE = 0.10
SCALE = 1000
OUT = 'kubejs/data/vampirism/loot_table/inject'


def mean_rolls(rolls):
    if isinstance(rolls, (int, float)):
        return float(rolls)
    if rolls.get('type', 'minecraft:uniform').endswith('uniform'):
        return (rolls['min'] + rolls['max']) / 2.0
    if rolls.get('type', '').endswith('constant'):
        return float(rolls['value'])
    raise SystemExit(f'unknown rolls {rolls}')


def convert(table):
    expected = {}
    for pool in table['pools']:
        total = sum(e.get('weight', 1) for e in pool['entries'])
        rolls = mean_rolls(pool.get('rolls', 1))
        for e in pool['entries']:
            if e['type'] != 'minecraft:item':
                continue
            entry = {k: v for k, v in e.items() if k not in ('weight', 'quality')}
            key = json.dumps(entry, sort_keys=True)
            expected[key] = expected.get(key, 0.0) + rolls * e.get('weight', 1) / total
    entries = []
    for key, value in sorted(expected.items(), key=lambda kv: -kv[1]):
        entry = json.loads(key)
        entry['weight'] = max(1, round(value * SCALE))
        entries.append(entry)
    items = sum(e['weight'] for e in entries)
    entries.append({'type': 'minecraft:empty', 'weight': round(items * (1 - CHANCE) / CHANCE)})
    return {'type': table.get('type', 'minecraft:chest'), 'pools': [{'rolls': 1.0, 'bonus_rolls': 0.0, 'entries': entries}]}


def main(jar):
    os.makedirs(OUT, exist_ok=True)
    with zipfile.ZipFile(jar) as z:
        for entry in sorted(z.namelist()):
            if entry.startswith('data/vampirism/loot_table/inject/') and entry.endswith('.json'):
                name = os.path.basename(entry)
                out = convert(json.loads(z.read(entry)))
                with open(os.path.join(OUT, name), 'w') as f:
                    json.dump(out, f, indent=2)
                    f.write('\n')
                pool = out['pools'][0]['entries']
                total = sum(e['weight'] for e in pool)
                shares = ', '.join(f"{e['name'].split(':')[1]} {100 * e['weight'] / total:.2f}%" for e in pool if e['type'] == 'minecraft:item')
                print(f'{name[:-5]:22} {shares}')


if __name__ == '__main__':
    main(sys.argv[1])
