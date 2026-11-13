// CC: Tweaked is a library for OpenComputers here: empty its creative tab (recipes and JEI: server_scripts/unobtainable.js).
StartupEvents.modifyCreativeTab('computercraft:tab', event => {
	event.remove('@computercraft')
})

// Advanced Peripherals: items that need real CC computers (list in server_scripts/cc_bridge_recipes.js)
StartupEvents.modifyCreativeTab('advancedperipherals:advancedperipherals', event => {
	;['weak_automata_core', 'end_automata_core', 'husbandry_automata_core', 'overpowered_weak_automata_core', 'overpowered_end_automata_core',
		'overpowered_husbandry_automata_core', 'chunk_controller', 'smart_glasses', 'smart_glasses_netherite', 'smart_glasses_interface',
		'ar_controller', 'hotkey_module', 'nightvision_module', 'overlay_module', 'keyboard', 'smart_chestplate']
		.forEach(id => event.remove(`advancedperipherals:${id}`))
})
