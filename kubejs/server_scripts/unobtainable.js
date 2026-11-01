// Items kept in the pack but not craftable (admin/creative only).
ServerEvents.recipes(event => {
	// Edit Enchanting: disenchantment table
	event.remove({ output: 'editenchanting:enchantment_edit_table' })
	// Create: Enchantment Industry: printer
	event.remove({ output: 'create_enchantment_industry:printer' })
	// Printing Press: every recipe of the mod, and any other recipe that makes one of its items
	event.remove({ mod: 'printingpress' })
	event.remove({ output: '@printingpress' })
})

// CC: Tweaked: only here so OpenComputers can use other mods' CC peripherals (OC's built-in CC bridge). No CC content in survival.
ServerEvents.recipes(event => {
	event.remove({ mod: 'computercraft' })
	event.remove({ output: '@computercraft' })
})
ServerEvents.tags('item', event => {
	// JEI hides everything in this common tag
	event.add('c:hidden_from_recipe_viewers', '@computercraft')
})
