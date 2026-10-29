# Red, Leaf and Sabrina story integration

Branch: `feature/red-leaf-sabrina-story`.
Starting checkpoint: `534bd3a2543cf93e91f96052bc9d4c1bd824ea0c`, protected by
`backup/pre-leaf-story-2026-10-29`. The working tree was clean before this task,
and the existing Rev 1 build passed before implementation. This starting
version includes the tested permanent follower, scripted-NPC yielding, all
previous Sabrina dialogue, Leaf's opening backstory, and polished combined
battle artwork. No original repository reset or replacement was performed.

The first reunion was implemented and emulator-tested separately, then committed
as `03542238bfd47e13cef27dcabc2b77ec08610164` before the later integration.

## Viridian reunion

Viridian's existing map-transition script now initializes a temporary gate.
A new map frame script checks Red's first entry from Route 1: x=22..25,
y>=38, facing north. It requires the existing joined-companion flag and checks
the persistent reunion flag. It does not require Oak's Parcel or the Pokédex.
The original roadblock, tutorial, Gym-door and coordinate events are preserved.

Leaf uses the heroine's original FireRed graphics/animation data, with a new NPC
graphics descriptor in palette slot 10. Red retains player palette slot 0; her
appearance cannot replace his colors. All original NPC IDs remain in place;
Leaf's templates append to the maps.

During the scene Sabrina is safely staged beside Red without clearing her joined
status. Leaf approaches from ahead, greets both as familiar people, teases her
twin about training on dates, explicitly opens a case containing exactly the
Boulder and Cascade Badges, mentions her unevolved Eevee and unhurried travels,
then says goodbye and walks away. No battle, gift Pokémon or badge award occurs.
Normal follower control and player movement resume after her departure.

An unaccompanied arrival does not mark the reunion complete: a later southern
arrival with Sabrina can run it. Quest Log playback and completed scenes do not
replay the reunion. Save layout and the original temporary-flag range are intact.

## Family and later encounters

Additive dialogue calls preserve native events and rewards:

- Mother welcomes Sabrina, mentions the fathers' longstanding connection,
  asks about Leaf and reacts to eight badges/the Championship. Healing remains
  the original routine. No fate or whereabouts are invented for Red's father.
- Oak recognizes Sabrina and Leaf's three-month head start at starter selection
  and the Pokédex scene. Blue keeps his rivalry while recognizing both women.
- Brock and Misty remember Leaf and Eevee. Erika acknowledges a fellow Gym
  Leader. Silph's Giovanni notices Sabrina but challenges Red himself.

Leaf can be spoken to near Cerulean's Pokémon Center as a second encounter.
Their shared childhood receives a brief, playful recollection. In Lavender she
helps Mr. Fuji's friends and takes Rocket's treatment of Pokémon seriously,
without changing Pokémon Tower's events. Later-town conversations replace her
earlier Cerulean placement as her journey progresses.

After Mr. Fuji's rescue she appears in Saffron. During the occupation she offers
support without taking over Silph Co. After liberation she presents a Water
Stone to Eevee on screen; the scene shows Eevee, then Vaporeon with cries and a
fanfare, and records the evolution. Later dialogue acknowledges Vaporeon.
This is an NPC story presentation, not a change to the player's party or a full
NPC-party evolution animation. No Leaf battle or complete long-term team is
added in this phase.

## Sabrina's Gym

Sabrina remains the official opposing Gym Leader. An entry message establishes
her duties; her follower is suppressed before the badge is earned and her
native leader object remains in place. Her challenge adds a firm statement
that their relationship grants no favors. The original Psychic team, leader
music/presentation, trainer flag, Marsh Badge, Gym flags and TM04 paths remain.

The combined back sprite is excluded specifically when the opposing trainer is
Sabrina. Red uses his original solo artwork and original throw in that battle.
Ordinary battles keep the polished combined artwork, without adding battlers,
turns, send-outs or Double Battle flags.

After victory, the native leader is hidden and one traveling Sabrina returns,
including inside the Gym. Later Gym visits and cartridge Continue retain that
state. Losing leaves the companion flag intact and the official leader ready
for a retry. Gym companion conversation can deliver an unclaimed TM04 and
retain the previous Blaine/Giovanni/Champion dialogue branches.

## Persistent state

No save structure is enlarged. These were unused flags in the existing save:

| Flag | Value | Purpose |
| --- | --- | --- |
| `FLAG_SABRINA_FOLLOWER_ACTIVE` | 0x020 | Existing companion status; unchanged |
| `FLAG_LEAF_VIRIDIAN_REUNION` | 0x021 | Reunion completed exactly once |
| `FLAG_HIDE_VIRIDIAN_LEAF` | 0x022 | Hide Leaf outside the scripted reunion |
| `FLAG_HIDE_GYM_SABRINA` | 0x023 | Hide native leader when she resumes following |
| `FLAG_SABRINA_GYM_DUTY_INTRO` | 0x024 | Gym-duty entry message seen |
| `FLAG_HIDE_LATER_LEAF` | 0x025 | Recomputed visibility for later Leaf placements |
| `FLAG_LEAF_LEFT_CERULEAN` | 0x026 | Progress past the Cerulean meeting |
| `FLAG_LEAF_EEVEE_EVOLVED` | 0x027 | Water Stone/Vaporeon story moment completed |

Viridian and Saffron Gym use map-local `VAR_TEMP_F` to gate their frame scripts.
Transient follower staging is runtime state only, with normal-control/map-change
recovery. Hide flags are recomputed on map entry, including older saves.

## Deferred requirements

The user selected **keep the original female route for now**. Gender selection,
female-player graphics and mother's female opening remain functional and
unchanged. New Leaf/twin-brother events and Leaf NPC placements are gated to
Red's route. An alternate expanded female storyline is not finalized.

Starters remain the original three choices and original shiny rules in this
phase. The next starter phase must replace Squirtle's ball with Pikachu, retain
level 5, generate a valid genuinely shiny PID/OT relationship only for Red's
initial Pokémon, and validate Blue's corresponding parties throughout the game.
Those changes are deliberately deferred under the user's conflict exception
instead of mixing a party/progression rewrite into this story integration.

Leaf's eventual friendly battle, full team/levels/moves (including later Dratini),
and League-era encounters are also future work. No contests are implemented.
The eight Gyms, Rocket plot, League and Sevii event paths remain recognizable.

## Validation and manual review

Build and check commands:

```sh
source /workspace/.pokefirered-env/activate.sh
make -j5 GAME_VERSION=FIRERED GAME_REVISION=1 all syms
python3 tools/sabrina_tests/test_integration.py
python3 tools/sabrina_tests/test_battle_graphics.py
python3 -u tools/sabrina_tests/test_battle_companion_rom.py --output /tmp/leaf-story-battles
python3 -u tools/sabrina_tests/test_story_rom.py
```

The existing preservation checks protect all 37 original shared Sabrina text
blocks, native progression commands, save structures, original female opening,
native Gym rewards and original trainer artwork. Message fitting now also
checks the new Leaf/family text with seven-character names and all three fonts.

The final Rev 1 build, all **18 preservation/graphics checks**, the full actual-ROM
follower/battle suite and the additional story runner passed. The full suite
checks native overlap across **35,707 overworld frames** and naturally reaches
the reunion from a fresh Red game, then completes Oak's Parcel and Pokédex.
Ordinary wild/trainer/first-Blue intros retain the combined art and original
throw, one party Pokémon and two battlers.

The story runner also passed cartridge Save/cold-boot Continue after the reunion,
non-repeating reentry, all four southern columns, missing-companion and female
edges, later Leaf dialogue/evolution, Gym loss/blackout, cartridge Continue before
retry, victory and native rewards, an unclaimed-TM claim control, and cartridge
Continue after victory followed by combined artwork in a wild encounter.
Screenshots of Leaf's staging, Vaporeon, solo Red against Sabrina, and the restored
Gym follower were inspected.

Final ROM SHA-256:
`bf51a4de1547739f7448faf64c18fb76a72867b42c72e3888c63a10d31cfffcb`.
The previous three downloadable ROMs remain byte-for-byte intact. Runtime memory
usage remains 261,116 bytes EWRAM and 29,824 bytes IWRAM, matching the protected
starting build; no save-structure expansion is used.

Later-map, gender, story-prerequisite and Gym-strength setups in the story runner
are explicitly diagnostic RAM fixtures. They do not patch the release ROM and
are distinct from the genuine fresh-game progression through Viridian/Parcel.

Manic EMU review remains necessary for native-scale art, levitation/walking,
dialogue pacing, long play sessions and later cutscene interactions. Automated
tests are not a full natural playthrough of all eight Gyms, Team Rocket,
the League or Sevii. Safari/tutorial/link/multi/genuine Double Battles and the
TM-full inventory edge also need review where not explicitly covered below.

On iPhone, download the ZIP in Safari, open it in Files → Downloads to extract
the `.gba`, then import it into Manic EMU. Keep the previous ROM and save.
Use in-game Save/Continue instead of a save state from another ROM build.
Start a new Red game to see all opening dialogue; an existing save before the
first southern Viridian arrival can also trigger the reunion after joining
Sabrina. Test saving before/after that scene, revisiting the city, and checking
that Sabrina remains talkable and follows through the Mart and Oak's laboratory.

## Changed files

36 files relative to the protected sprite-polish checkpoint:

```text
data/event_scripts.s
data/maps/CeladonCity_Gym/scripts.inc
data/maps/CeruleanCity/map.json
data/maps/CeruleanCity/scripts.inc
data/maps/CeruleanCity_Gym/scripts.inc
data/maps/LavenderTown/map.json
data/maps/LavenderTown/scripts.inc
data/maps/PalletTown_PlayersHouse_1F/scripts.inc
data/maps/PalletTown_ProfessorOaksLab/scripts.inc
data/maps/PewterCity_Gym/scripts.inc
data/maps/SaffronCity/map.json
data/maps/SaffronCity/scripts.inc
data/maps/SaffronCity_Gym/map.json
data/maps/SaffronCity_Gym/scripts.inc
data/maps/SilphCo_11F/scripts.inc
data/maps/ViridianCity/map.json
data/maps/ViridianCity/scripts.inc
data/scripts/family_story.inc
data/scripts/leaf_story.inc
data/specials.inc
data/text/family_story.inc
data/text/leaf_story.inc
docs/red-leaf-sabrina-story.md
docs/sabrina-battle-companion.md
docs/sabrina-follower.md
include/constants/event_objects.h
include/constants/flags.h
include/sabrina_follower.h
src/data/object_events/object_event_graphics_info.h
src/data/object_events/object_event_graphics_info_pointers.h
src/pokemon.c
src/sabrina_follower.c
tools/sabrina_tests/README.md
tools/sabrina_tests/test_follower_rom.py
tools/sabrina_tests/test_integration.py
tools/sabrina_tests/test_story_rom.py
```
