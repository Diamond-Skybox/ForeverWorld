// Priority 0
/* Recipe script orignally written by L0rdG1gabyt3 for G1gaCraft Reloaded SMP 2026
 *
 * Follow On YouTube
 * https://www.youtube.com/user/L0rdG1gabyt3
 *
 * Follow on Twitch
 * https://www.twitch.tv/l0rdg1gabyt3
 *
 * Join the G1gaCraft Reloaded Discord
 * https://discord.gg/fKGYpuVztf
 *
 */

ServerEvents.recipes(event => {

	//remove default Immersive Aircraft Recipes
	event.remove({ mod: 'immersive_aircraft' })

	// Non-aircaft items.

	//Hull
	event.shaped(
		'immersive_aircraft:hull',
		[
			'AIA',
			'AIA',
			'   '
		],
		{
			A: 'create:andesite_casing',
			I: 'minecraft:iron_ingot'
		}
	)
	
	//Engine
	event.shaped(
		'immersive_aircraft:engine',
		[
			'BPB',
			'SXS',
			'   '
		],
		{
			B: 'create:brass_sheet',
			P: 'create:precision_mechanism',
			S: 'create:sturdy_sheet',
			X: 'immersive_aircraft:boiler'
		}
	)

	//Sail
	event.shaped(
		'immersive_aircraft:sail',
		[
			'SSS',
			'SSS',
			'   '
		],
		{
			S: 'create:white_sail'
		}
	)

	//Propeller
	event.shaped(
		'immersive_aircraft:propeller',
		[
			' S ',
			'SPS',
			' S '
		],
		{
			S: 'create:iron_sheet',
			P: 'create:propeller'
		}
	)

	event.shaped(
		'immersive_aircraft:boiler',
		[
			' S ',
			' T ',
			' B '
		],
		{
			S: 'create:steam_engine',
			T: 'create:fluid_tank',
			B: 'create:blaze_burner'
		}
	)

	//Rotary Cannon
	event.shaped(
		'immersive_aircraft:rotary_cannon',
		[
			' D ',
			'PIW',
			' C ',
		],
		{
			D: 'minecraft:dispenser',
			P: 'create:pulse_timer',
			W: 'create:precision_mechanism',
			I: 'immersive_aircraft:industrial_gears',
			C: 'create:copper_casing'
        }
	)

	//Heavy Crossbow
	event.shaped(
		'immersive_aircraft:heavy_crossbow',
		[
			' A ',
			'SCS',
			' A '
		],
		{
			A: 'create:andesite_alloy',
			S: 'create:sturdy_sheet',
			C: 'minecraft:crossbow'
		}
	)

	//Telescope
	event.shaped(
		'immersive_aircraft:telescope',
		[
			' S ',
			' P ',
			' C ',
		],
		{
			S: 'minecraft:spyglass',
			P: 'create:precision_mechanism',
			C: 'create:copper_casing'
		}
	)

	//Bomb Bay
	event.shaped(
		'immersive_aircraft:bomb_bay',
		[
			'STS',
			'SCS',
			'   '
		],
		{
			S: 'create:iron_sheet',
			T: 'minecraft:redstone_torch',
			C: 'create:chute'
		}
	)

	//Enhanced Propeller
	event.shaped(
		'immersive_aircraft:enhanced_propeller',
		[
			' B ',
			'BPB',
			' B '
		],
		{
			B: 'create:brass_sheet',
			P: 'create:propeller'
		}
	)

	//Eco Engine
	event.shaped(
		'immersive_aircraft:eco_engine',
		[
			'SWS',
			'CBC',
			'   '
		],
		{
			S: 'create:iron_sheet',
			W: 'minecraft:water_bucket',
			C: 'create:copper_sheet',
			B: 'immersive_aircraft:boiler'
		}
	)

	//Nether Engine
	event.shaped(
		'immersive_aircraft:nether_engine',
		[
			'ILI',
			'SBS',
			'   '
		],
		{
			I: 'create:iron_sheet',
			L: 'minecraft:lava_bucket',
			S: 'create:sturdy_sheet',
			B: 'immersive_aircraft:boiler'
		}
	)

	//Steel Boiler
	event.shaped(
		'immersive_aircraft:steel_boiler',
		[
			'   ',	
			'STS',
			'   '
		],
		{
			S: 'create:sturdy_sheet',
			T: 'create:fluid_tank'
		}
	)

	//Industrial Gears
	event.shaped(
		'immersive_aircraft:industrial_gears',
		[
			'WB ',
			'IW ',
			'   '
		],
		{
			W: 'create:cogwheel',
			B: 'create:brass_sheet',
			I: 'create:iron_sheet'
		}
	)

	//Sturdy Pipes
	event.shaped(
		'immersive_aircraft:sturdy_pipes',
		[
			'   ',
			'SPS',
			'   '
		],
		{
			S: 'create:sturdy_sheet',
			P: 'create:fluid_pipe'
		}
	)

	//Gyroscope
	event.shaped(
		'immersive_aircraft:gyroscope',
		[
			' E ',
			' C ',
			'   '
		],
		{
			E: 'create:electron_tube',
			C: 'minecraft:compass'
		}
	)

	//Electronic Gyroscope
	event.shaped(
		'immersive_aircraft:gyroscope_hud',
		[
			'PDP',
			'LGL',
			'ETE'
		],
		{
			P: 'minecraft:glass_pane',
			D: 'create:display_board',
			L: 'create:display_link',
			G: 'immersive_aircraft:gyroscope',
			E: 'create:electron_tube',
			T: 'create:transmitter'
		}
	)

	//Advanced Gyroscope
	event.shaped(
		'immersive_aircraft:gyroscope_dials',
		[
			'NPN',
			'VGV',
			'ETE'
		],
		{
			N: 'create:nixie_tube',
			P: 'create:precision_mechanism',
			V: '#create:valve_handles',
			G: 'immersive_aircraft:gyroscope',
			E: 'create:electron_tube',
			T: 'create:transmitter'
		}
	)

	//Hull Reinforcement
	event.shaped(
		'immersive_aircraft:hull_reinforcement',
		[
			'   ',
			'SHS',
			'   '
		],
		{
			S: 'create:sturdy_sheet',
			H: 'immersive_aircraft:hull'
		}
	)

	//Improved Landing Gears
	event.shaped(
		'immersive_aircraft:improved_landing_gear',
		[
			'SI ',
			'B  ',
			'   '
		],
		{
			S: 'create:iron_sheet',
			I: 'minecraft:iron_ingot',
			B: 'create:belt_connector'
		}
	)

	//Aircraft Vehicles Mechanical Crafting
	//Airship
	event.recipes.create.mechanical_crafting(
		'immersive_aircraft:airship',
		[
			'SSS ',
			'T T ',
			'HLEP',
			'HHH ',
		],
		{
			S: 'immersive_aircraft:sail',
			T: 'minecraft:string',
			H: 'immersive_aircraft:hull',
			L: '#create:seats',
			E: 'immersive_aircraft:engine',
			P: 'immersive_aircraft:propeller'
        }
	)

	//Cargo Airship
	event.recipes.create.mechanical_crafting(
		'immersive_aircraft:cargo_airship',
		[
			'CAC',
			'CSC',
			'HHH',
		],
		{
			C: 'minecraft:chest',
			A: 'immersive_aircraft:airship',
			S: 'create:sturdy_sheet',
			H: 'immersive_aircraft:hull'
		}
	)

	//Warship
	event.recipes.create.mechanical_crafting(
		"immersive_aircraft:warship",
		[
			"RSSSR",
			"RSSSR",
			" T T ",
			"CHAEP",
			" HHH "
		],
		{
			R: "create:railway_casing",
			S: "immersive_aircraft:sail",
			T: "minecraft:string",
			C: "immersive_aircraft:heavy_crossbow",
			H: "immersive_aircraft:hull",
			A: "immersive_aircraft:cargo_airship",
			E: "immersive_aircraft:engine",
			P: "immersive_aircraft:propeller",
		}
	)

	//Biplane
	event.recipes.create.mechanical_crafting(
		"immersive_aircraft:biplane",
		[
			"   S ",
			"S  S ",
			"HHLEP",
			"S  S ",
			"   S "
		],
		{
			S: "immersive_aircraft:sail",
			H: "immersive_aircraft:hull",
			L: "#create:seats",
			E: "immersive_aircraft:engine",
			P: "immersive_aircraft:propeller",
		}
	)

	//Bamboo Hopper
	event.recipes.create.mechanical_crafting(
		"immersive_aircraft:bamboo_hopper",
		[
			"     S ",
			"SHHHHEP",
			"S    S ",
			"SPELLLR",
			"S    S ",
			"SHHHHEP",
			"     S "
		],
		{
			S: "immersive_aircraft:sail",
			H: "immersive_aircraft:hull",
			E: "immersive_aircraft:engine",
			P: "immersive_aircraft:propeller",
			L: "#create:seats",
			R: "create:railway_casing",
		}
	)

	//Gyrodyne
	event.recipes.create.mechanical_crafting(
		"immersive_aircraft:gyrodyne",
		[
			" P ",
			"SMS",
			"HLH"
		],
		{
			P: "immersive_aircraft:propeller",
			S: "immersive_aircraft:sail",
			M: "create:precision_mechanism",
			H: "immersive_aircraft:hull",
			L: "#create:seats",
		}
	)

	//Quadrocopter
	event.recipes.create.mechanical_crafting(
		"immersive_aircraft:quadrocopter",
		[
			"PAP",
			"BEB",
			"PBP"
		],
		{
			P: "immersive_aircraft:propeller",
			B: "minecraft:scaffolding",
			E: "immersive_aircraft:engine",
			A: "create:andesite_casing",
		}
	)
})