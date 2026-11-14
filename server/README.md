# Server-only content

Everything under `server/` is the ForeverWorld server's own balance. It is **not** shipped in the pack (`server/` is in
`.packwizignore`), so players' singleplayer worlds keep each mod's own behaviour. On a multiplayer world the server's data wins,
so players on the server see these changes there.

The server's `kubejs/` folder = the pack's `kubejs/` + `server/kubejs/` laid over it (same paths). The "ForeverWorld - Test"
reference instance carries both, like the server.

- `kubejs/data/let_it_walk`: walker parts mechanical crafting only, with Synaxis and OpenComputers parts
- `kubejs/data/chromeware`: implant recipes (OpenComputers parts by tier, TFMG/titanium/steel materials, mechanical crafting)
- `kubejs/data/vampirism`: chest injections give one item 10% of the time
- `kubejs/data/ars_nouveau`: drygmys can't farm modded bosses
- `kubejs/server_scripts/immersive_aircraft.js`: replacement Immersive Aircraft recipes
- `kubejs/server_scripts/uncraftable.js`: disenchantment table, CEI printer and Printing Press uncraftable

The server's world datapacks (`world/datapacks/heimdall_*`) are server-only too; of those, only the loot fix ships in the pack
(`kubejs/data/nova_structures`, a copy of `heimdall_lootfix`).
