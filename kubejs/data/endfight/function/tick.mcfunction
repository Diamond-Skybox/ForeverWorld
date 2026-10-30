# ForeverWorld override of End Dragon Fight Remastered's tick function. Its commands search every entity in every dimension
# (@e[tag=...]) many times per tick; they now run only while a player is in the End, or still carries its boss music tags
# (so leaving mid-fight still clears them). The original commands are in foreverworld:endfight_tick.
execute if entity @a[predicate=foreverworld:in_the_end] run return run function foreverworld:endfight_tick
execute if entity @a[tag=playerMusic] run return run function foreverworld:endfight_tick
execute if entity @a[tag=playerMusicMAD] run return run function foreverworld:endfight_tick
