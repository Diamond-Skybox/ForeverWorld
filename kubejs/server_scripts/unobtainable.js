// CC: Tweaked: only here so OpenComputers can use other mods' CC peripherals (OC's built-in CC bridge). No CC content in survival.
// (The server's own uncraftable items are in server/kubejs/server_scripts/uncraftable.js, which the pack doesn't ship.)
ServerEvents.recipes(event => {
	event.remove({ mod: 'computercraft' })
	event.remove({ output: '@computercraft' })
})
ServerEvents.tags('item', event => {
	// JEI hides everything in this common tag
	event.add('c:hidden_from_recipe_viewers', '@computercraft')
})
