// CC: Tweaked is a library for OpenComputers here: empty its creative tab (recipes and JEI: server_scripts/unobtainable.js).
StartupEvents.modifyCreativeTab('computercraft:tab', event => {
	event.remove('@computercraft')
})
