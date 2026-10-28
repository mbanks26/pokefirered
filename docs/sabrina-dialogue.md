# Sabrina's journey dialogue

Sabrina and the player are childhood friends who started dating before the
journey. She is reserved, affectionate, and occasionally teasing. Her psychic
abilities do not replace trust: she lets the player surprise her, including in
her Gym battle. Her first Pallet Town conversation now invites her to accompany
the player immediately, including before starter selection. Later conversations
remain optional and do not advance Oak's, Blue's, or the Gym story events.

## Where to find her

Coordinates are map tile coordinates, as used by `map.json`.

| Location | Coordinates | Dialogue changes |
| --- | --- | --- |
| Pallet Town | 8, 8 (existing NPC) | Starter, Boulder Badge, Marsh Badge, Earth Badge, Champion |
| Viridian City | 33, 14 | Before / after Giovanni's Gym battle |
| Pewter City | 18, 18 | Before / after Brock |
| Cerulean City | 28, 23 | Before Misty, Bill's ticket before Misty, after Misty |
| Vermilion City | 17, 20 | Before CUT, after helping the captain, after Lt. Surge |
| Lavender Town | 14, 8 | Before / after rescuing Mr. Fuji |
| Celadon City | 22, 24 | Erika and Rocket Hideout victories, in either order |
| Fuchsia Pokémon Center, 1F | 10, 5 | Before / after Koga |
| Saffron City | 43, 15 | Rocket occupation, Silph rescue, Marsh Badge |
| Saffron Gym | Existing leader | Battle, defeat, TM04, Volcano Badge, Earth Badge, Champion |
| Cinnabar Island | 16, 6 | Before / after Blaine |
| Indigo Plateau Pokémon Center, 1F | 14, 14 | Before / after becoming Champion |
| One Island | 15, 10 | Initial visit, Lostelle rescued, postgame without Lostelle rescued |

The Fuchsia encounter is indoors because its exterior already has 16 object
templates. The League encounter is indoors to avoid the exterior credits scene.
Before she joins, Sabrina uses these existing encounter locations. After she
joins, the stationary copies are hidden and her follower interaction selects
the corresponding location dialogue. Routes and other interiors use companion
dialogue. The existing Saffron Gym leader remains in place for the original
challenge; the follower is suppressed there to avoid a duplicate.

## Editing and checking

- Shared conversations: `data/scripts/sabrina.inc` and `data/text/sabrina.inc`.
- Pallet's existing interaction delegates to the shared conversation.
- Gym battle and reward scripts remain in `data/maps/SaffronCity_Gym/`.
- Existing badge and story flags select dialogue. The new persistent
  `FLAG_SABRINA_FOLLOWER_ACTIVE` at the previously unused flag `0x020` records
  joining and hides stationary copies. No save structure changes are needed.
- Existing saves can activate the companion by speaking to Sabrina in Pallet
  Town. Their greeting avoids telling a player who already has a starter to
  begin their journey again.
- Gym dialogue after later milestones runs only after TM04 has been collected.
  The original full-bag retry and reward flow remains available.
- Player references use `{PLAYER}` instead of a fixed name or gender.

Activate the environment with `source /workspace/.pokefirered-env/activate.sh`,
then run `make -j5 GAME_VERSION=FIRERED GAME_REVISION=1 all syms` from the
repository root to build FireRed Rev 1. The original-ROM checksum will differ
because this fork changes the game's content.

Historical dialogue-only validation: the ROM and symbols built successfully. Checks against
the compiled scripts passed 34 story scenarios, 64 local flag combinations,
and nine Gym/TM reward routing scenarios. All 41 new or revised dialogue blocks
fit two-line pages in the normal, male, and female dialogue fonts, including a
seven-character player name. New map objects preserve existing event templates,
warps, triggers, and object limits. Those checks predate the follower integration;
they do not establish follower movement or cutscene compatibility. See
`docs/sabrina-follower.md` for the feature audit and current review checklist.

For gameplay review, talk to Sabrina before and after each listed milestone.
Check Erika before and after the Rocket Hideout in both orders, and obtain the
Marsh Badge both before and after Koga/Blaine. With a full TM Case, win Sabrina's
battle, free a slot, and return: TM04 must still be awarded once. Revisit after
the Earth Badge and after entering the Hall of Fame. Confirm text stays inside
the message box and every interaction returns control to the player.
