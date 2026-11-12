// Chromeware: implants and their parts take Create: Cosmonautics' titanium sheets instead of Create's iron sheets.
// Titanium ore generates in every overworld biome (Y -64 to 160); its ingot is pressed into a sheet like iron.
ServerEvents.recipes(event => {
	event.replaceInput([{ mod: 'chromeware' }, { output: '@chromeware' }], 'create:iron_sheet', 'rocketnautics:titanium_sheet')
})
