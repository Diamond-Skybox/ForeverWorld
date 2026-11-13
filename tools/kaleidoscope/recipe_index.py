"""Static recipe index of a mods folder (+ the pack's kubejs/data): every data/<ns>/recipe/**.json, keyed by recipe id.
When several jars ship the same id, all copies are kept in 'copies' (which one wins depends on load order; kubejs/data always wins).
Usage as a module: index(mods_dir, kubejs_data_dir_or_None) -> {id: {'json':..., 'src':..., 'copies':[src,...]}}"""
import json, os, re, sys, zipfile

PAT = re.compile(r'^(?:packs/always/)?data/([^/]+)/recipe/(.+)\.json$')  # 1.21 loads recipe/ only; packs/always = Kaleidoscope Compat's built-in pack

def _load(raw):
    try:
        return json.loads(raw)
    except Exception:
        return None

def index(mods, kubejs_data=None):
    out = {}
    for j in sorted(os.listdir(mods)):
        if not j.endswith('.jar'):
            continue
        try:
            z = zipfile.ZipFile(os.path.join(mods, j))
        except Exception:
            continue
        for n in z.namelist():
            m = PAT.match(n)
            if not m:
                continue
            rid = f'{m.group(1)}:{m.group(2)}'
            e = out.setdefault(rid, {'copies': []})
            e['copies'].append(j)
            e['json'] = _load(z.read(n)); e['src'] = j
    if kubejs_data and os.path.isdir(kubejs_data):
        for root, _, files in os.walk(kubejs_data):
            for f in files:
                p = os.path.join(root, f)
                m = PAT.match('data/' + os.path.relpath(p, kubejs_data).replace(os.sep, '/'))
                if not m:
                    continue
                rid = f'{m.group(1)}:{m.group(2)}'
                e = out.setdefault(rid, {'copies': []})
                e['copies'].append('kubejs')
                e['json'] = _load(open(p, 'rb').read()); e['src'] = 'kubejs'
    return out

def rtype(j):
    return j.get('type') if isinstance(j, dict) else None

def results(j):
    """output item ids of a recipe json (handles result / results / output, item or id keys)"""
    if not isinstance(j, dict):
        return []
    ids = []
    for k in ('result', 'results', 'output', 'outputs'):
        v = j.get(k)
        for x in (v if isinstance(v, list) else [v]):
            if isinstance(x, str):
                ids.append(x)
            elif isinstance(x, dict):
                for kk in ('id', 'item'):
                    if isinstance(x.get(kk), str):
                        ids.append(x[kk]); break
                else:
                    inner = x.get('item')
                    if isinstance(inner, dict) and isinstance(inner.get('id'), str):
                        ids.append(inner['id'])
    return ids

if __name__ == '__main__':
    import collections
    idx = index(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    c = collections.Counter(rtype(e['json']) for e in idx.values())
    for t, n in c.most_common():
        if t and re.search(sys.argv[3] if len(sys.argv) > 3 else '.', t):
            print(n, t)
