// Farmer's Delight cooking pot versions of Kaleidoscope stockpot/wok-only dishes, made from the recipes actually loaded (so it keeps
// up with Kaleidoscope and its add-ons by itself; pack tools/kaleidoscope/shared_gaps.py reports the gaps without these).
// Kaleidoscope's stockpot already falls back to cooking pot recipes, but nothing goes the other way, so dishes with only a stockpot or
// wok recipe couldn't be made in the cooking pot (nor in Hands On Delight's pot, nor by Delightful Creators' Create recipes).
// A dish gets copies when nothing else makes it (no cooking pot, campfire/skillet, furnace, smoker or crafting recipe) and it isn't
// vanilla. Each stockpot/wok recipe that fits the pot's 6 slots becomes kaleidoscope_cookery:cooking_pot_compat/<ns>/<path>:
//   ingredients as-is, plus the stockpot's soup base as one more (SOUP_BASE; water adds nothing);
//   carrier -> container (stockpot default bowl, wok default none); a tag carrier (the Nether "... rice" dishes are served onto a
//   bowl of #c:foods/cooked_rice) becomes an ingredient with a bowl container, the rice's bowl coming back as its remainder;
//   result (servings) as-is; time -> cookingtime (stockpot 300, wok 200).
// A list of alternatives (Kaleidoscope writes [a, b] as one ingredient) becomes a neoforge:compound ingredient: Farmer's Delight's
// recipe reader (via KubeJS Delight's schema) only takes objects. Source recipes naming an item that doesn't exist (recipes for mods
// that aren't installed still reach this event) are skipped quietly.
// Skipped: a copy with the same ingredients as a cooking pot recipe for another dish, or as another copy (the pot takes whichever it
// finds first, so one dish would become unmakeable: meat pie loses to dumplings), and texture-only variants with equal ingredients.

const KCP_SLOTS = 6
// soup base id -> extra cooking pot ingredient. Lava/milk buckets hand back the empty bucket in the pot (crafting remainder); live-fish
// bases use the fish itself so the pot doesn't eat the bucket
const KCP_SOUP_BASE = {
	'minecraft:water': null,
	'minecraft:lava': { item: 'minecraft:lava_bucket' },
	'minecraft:milk': { tag: 'c:drinks/milk' },
	'minecraft:cod_bucket': { item: 'minecraft:cod' },
	'minecraft:salmon_bucket': { item: 'minecraft:salmon' },
	'minecraft:tropical_fish_bucket': { item: 'minecraft:tropical_fish' },
	'minecraft:pufferfish_bucket': { item: 'minecraft:pufferfish' },
	'minecraft:axolotl_bucket': { item: 'minecraft:axolotl_bucket' },
	'minecraft:tadpole_bucket': { item: 'minecraft:tadpole_bucket' },
	'kaleidoscope_end:dragon_breath': { item: 'minecraft:dragon_breath' }
}
const KCP_STOCKPOT = ['kaleidoscope_cookery:stockpot', 'kaleidoscope_cookery:flex_stockpot']
const KCP_WOK = ['kaleidoscope_cookery:pot', 'kaleidoscope_cookery:flex_pot']
const KCP_ROUTES = ['minecraft:campfire_cooking', 'minecraft:smelting', 'minecraft:smoking', 'minecraft:crafting_shaped',
	'minecraft:crafting_shapeless']

ServerEvents.recipes(event => {
	const resultIds = j => {
		const out = []
		;['result', 'results', 'output'].forEach(k => {
			let v = j[k]
			if (v == null) return
			if (!Array.isArray(v)) v = [v]
			v.forEach(x => {
				if (typeof x == 'string') out.push(x)
				else if (x && typeof x.id == 'string') out.push(x.id)
				else if (x && typeof x.item == 'string') out.push(x.item)
			})
		})
		return out
	}
	const itemIds = x => Array.isArray(x) ? x.reduce((a, v) => a.concat(itemIds(v)), [])
		: x && typeof x == 'object' ? Object.keys(x).reduce((a, k) => a.concat((k == 'item' || k == 'id') && typeof x[k] == 'string' ? [x[k]]
			: typeof x[k] == 'object' ? itemIds(x[k]) : []), []) : []
	// format first: a malformed id (one source recipe's result is "'farmersdelight:mutton_chops'") throws inside KubeJS's id parser
	// past any try/catch and ends the whole recipes handler
	const KCP_ID = /^[a-z0-9_.-]+:[a-z0-9_.\/-]+$/
	const exists = id => { if (!KCP_ID.test(id)) return false; try { return Item.exists(id) } catch (e) { return false } }
	const compound = i => Array.isArray(i) ? { type: 'neoforge:compound', children: i.map(compound) } : i
	const sigOf = ings => ings.map(i => JSON.stringify(i)).sort().join('|')  // ingredient multiset (Kaleidoscope and FD write them alike)
	const each = (type, fn) => event.forEachRecipe({ type: type }, r => fn(String(r.getId()), JSON.parse(String(r.json))))

	const routed = {}
	const fdSigs = {}  // ingredient signature -> {id, results}
	each('farmersdelight:cooking', (id, j) => {
		const res = resultIds(j)
		res.forEach(x => routed[x] = true)
		fdSigs[sigOf(j.ingredients || [])] = { id: id, results: res }
	})
	KCP_ROUTES.forEach(t => each(t, (id, j) => resultIds(j).forEach(x => routed[x] = true)))

	const dishes = {}  // dish -> [{id, json, stockpot}]
	KCP_STOCKPOT.concat(KCP_WOK).forEach(t => each(t, (id, j) => resultIds(j).forEach(x => {
		if (!routed[x] && x.split(':')[0] != 'minecraft') (dishes[x] = dishes[x] || []).push({ id: id, json: j, stockpot: KCP_STOCKPOT.indexOf(t) >= 0 })
	})))

	let made = 0, covered = 0, tooBig = 0, absent = 0
	const skipped = []
	Object.keys(dishes).sort().forEach(dish => {
		const seen = {}
		let any = false
		dishes[dish].sort((a, b) => a.id < b.id ? -1 : a.id > b.id ? 1 : 0).forEach(src => {
			const j = src.json
			if (!itemIds([j.ingredients, j.result, j.carrier]).every(exists)) { absent++; return }
			const ings = (j.ingredients || []).map(compound)
			let carrier, time
			if (src.stockpot) {
				const base = j.soup_base || 'minecraft:water'
				if (!(base in KCP_SOUP_BASE)) { skipped.push(src.id + ': unknown soup base ' + base); return }
				if (KCP_SOUP_BASE[base]) ings.push(KCP_SOUP_BASE[base])
				carrier = 'carrier' in j ? j.carrier : { item: 'minecraft:bowl' }
				time = j.time || 300
			} else {
				carrier = j.carrier
				time = j.time || 200
			}
			if (Array.isArray(carrier)) carrier = carrier.length ? carrier[0] : null
			if (carrier && carrier.tag) { ings.push(compound(carrier)); carrier = { item: 'minecraft:bowl' } }
			if (ings.length > KCP_SLOTS) return
			const sig = sigOf(ings)
			if (seen[sig]) return
			const clash = fdSigs[sig]
			if (clash && clash.results.indexOf(dish) < 0) { skipped.push(src.id + ': same ingredients as ' + clash.id); return }
			if (carrier && !carrier.item) { skipped.push(src.id + ': carrier is not an item'); return }
			const recipe = { type: 'farmersdelight:cooking', recipe_book_tab: 'meals', ingredients: ings, result: j.result,
				experience: 1.0, cookingtime: time }
			if (carrier) recipe.container = { id: carrier.item, count: 1 }
			const id = 'kaleidoscope_cookery:cooking_pot_compat/' + src.id.replace(':', '/')
			event.custom(JsonUtils.fromString(JSON.stringify(recipe))).id(id)
			seen[sig] = true
			fdSigs[sig] = { id: id, results: [dish] }
			made++
			any = true
		})
		if (any) covered++
		else tooBig++
	})
	console.info('Kaleidoscope -> cooking pot: ' + made + ' recipes for ' + covered + ' dishes; ' + tooBig +
		' dishes have no recipe that fits (too many ingredients or a clash); ' + absent +
		' source recipes skipped for items that don\'t exist')
	skipped.forEach(s => console.info('  skipped ' + s))
})
