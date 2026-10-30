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
