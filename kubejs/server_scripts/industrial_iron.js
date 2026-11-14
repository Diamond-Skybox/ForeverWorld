// Industrial iron: one iron ingot makes one industrial iron ingot, by smelting.
// Create only has the Industrial Iron Block (a stonecutter made 2 from 1 iron ingot). Create Deco adds the ingot, nugget and sheet
// and treats that block as the ingot's storage block (block <-> 9 ingots), so 1 iron ingot became 18 industrial iron ingots.
// Create Encased also pressed the block into a second industrial iron sheet. Now:
//   - iron ingot -> industrial iron ingot in a furnace or blast furnace (and Create's bulk blasting); the stonecutter recipe is gone
//   - 9 ingots <-> 1 block and 9 nuggets <-> 1 ingot stay as Create Deco has them, so the block costs 9 iron
//   - Create Encased's sheet is no longer made (its recipes take any #c:plates/industrial_iron, i.e. Create Deco's sheet, pressed
//     from one ingot) and is hidden from JEI
ServerEvents.recipes(event => {
	event.remove({ id: 'create:industrial_iron_block_from_ingots_iron_stonecutting' })
	event.remove({ id: 'createcasing:pressing/industrial_iron' })
	event.smelting('createdeco:industrial_iron_ingot', 'minecraft:iron_ingot').xp(0.1).id('foreverworld:industrial_iron_ingot_from_smelting')
	event.blasting('createdeco:industrial_iron_ingot', 'minecraft:iron_ingot').xp(0.1).id('foreverworld:industrial_iron_ingot_from_blasting')
})

ServerEvents.tags('item', event => {
	event.add('c:hidden_from_recipe_viewers', 'createcasing:industrial_iron_sheet')
})
