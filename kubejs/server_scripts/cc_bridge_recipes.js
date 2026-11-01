// CC add-ons used through OpenComputers' built-in CC peripheral bridge. CC: Tweaked's own recipes are removed
// (unobtainable.js), so add-on recipes that need CC parts use the OC equivalents instead.

// Items that only work with real CC computers (turtle upgrades, the Smart Glasses pocket-computer system): no recipes, hidden.
const CC_ONLY_ITEMS = [
	'advancedperipherals:weak_automata_core', 'advancedperipherals:end_automata_core', 'advancedperipherals:husbandry_automata_core',
	'advancedperipherals:overpowered_weak_automata_core', 'advancedperipherals:overpowered_end_automata_core',
	'advancedperipherals:overpowered_husbandry_automata_core', 'advancedperipherals:chunk_controller',
	'advancedperipherals:smart_glasses', 'advancedperipherals:smart_glasses_netherite', 'advancedperipherals:smart_glasses_interface',
	'advancedperipherals:glasses_interface', 'advancedperipherals:ar_controller', 'advancedperipherals:hotkey_module',
	'advancedperipherals:nightvision_module', 'advancedperipherals:overlay_module', 'advancedperipherals:keyboard',
	'advancedperipherals:smart_chestplate'
]

ServerEvents.recipes(event => {
	// CC wired modem -> OC network card, CC disk -> OC floppy, CC monitor -> OC screen
	event.replaceInput({ mod: 'advancedperipherals' }, 'computercraft:wired_modem_full', 'opencomputers:lancard')
	event.replaceInput({ mod: 'advancedperipherals' }, 'computercraft:wired_modem', 'opencomputers:lancard')
	event.replaceInput({ mod: 'advancedperipherals' }, 'computercraft:disk', 'opencomputers:floppy')
	event.replaceInput({ mod: 'cccbridge' }, 'computercraft:monitor_normal', 'opencomputers:screen1')
	CC_ONLY_ITEMS.forEach(id => event.remove({ output: id }))
})

ServerEvents.tags('item', event => {
	CC_ONLY_ITEMS.forEach(id => event.add('c:hidden_from_recipe_viewers', id))
})
