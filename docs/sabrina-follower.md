# Sabrina follower: preservation and story integration

## Protected starting point

The initial audit found branch `work` at
`de1a90d4f12cc954ce1f087431d270acbf3d439e` (`Add Leaf backstory and sabrina
introduction`) with the prior dialogue task still uncommitted. Its complete
working changes comprised 19 files, including three new files. The request
referred to six modified files; the published filesystem contained a larger
dialogue implementation. All 19 were preserved rather than selecting or
recreating a six-file subset.

Before follower development, the complete existing changes were committed as
`1a2c7eb374849285f49bf4b57538c938ee77ce22` on
`backup/pre-sabrina-follower-2026-10-28`. A verified complete-history Git bundle
was written outside the checkout:

`/workspace/backups/pokefirered-pre-sabrina-follower-2026-10-28.bundle`

Follower development uses `feature/sabrina-permanent-follower`. No reset,
force-push, branch deletion, replacement checkout, or upstream source overwrite
was used to establish that checkpoint.

The protected dialogue work includes:

- Pallet Town's Sabrina object and its interaction wrapper.
- The mother's existing Leaf departure dialogue.
- `data/scripts/sabrina.inc` and its event-script inclusion.
- All 37 shared dialogue definitions in `data/text/sabrina.inc`.
- Existing encounters in 11 additional towns/interiors.
- Sabrina's revised Saffron Gym introduction, defeat, postbattle, and TM dialogue,
  including later-badge/Champion branches and the full-bag TM retry path.
- `docs/sabrina-dialogue.md`, the encounter guide and previous validation record.

## Established canon

Red is the intended male protagonist. Leaf is his twin sister and began her
journey three months before him. The male opening dialogue now explicitly says
"twin sister" while preserving her journey and three-month departure. The
original female character option and its opening script remain available.

Sabrina is Red's childhood friend and girlfriend, with her original FireRed
sprite, reserved personality, and official Saffron Gym Leader title. Her first
Pallet conversation keeps the existing introduction and adds her decision to
travel with Red. This happens before receiving a starter when spoken to at the
beginning. She is an overworld companion, not an extra party Pokémon or a
participant in ordinary battles.

Oak's grass intervention, laboratory sequence, starter choice, first rival
battle, Pokédex sequence, and Blue's major story scripts remain the original
progression. The companion flag does not substitute for any of their flags or
variables.

## Script integration

`FLAG_SABRINA_FOLLOWER_ACTIVE` uses the previously unused flag `0x020`, directly
after the temporary range ending at `0x01F`. Existing save structures therefore
need no format change. Ordinary map transitions do not clear the flag. Existing
saves can join through the Pallet interaction with a greeting appropriate to an
already-started journey.

The joining script displays its message, closes the text box, sets the flag,
calls `StartSabrinaFollower`, and releases the player. It does not grant a
starter, badge, item, Pokédex, or party slot.

All 12 non-Gym stationary Sabrina objects use the active flag as their hide
flag. Their coordinates, object IDs, scripts, and other map events are preserved.
The original Saffron Gym Sabrina remains for the existing challenge. The follower
engine must suppress its dynamic object there; replacing the challenge with a
substitute trainer is a later feature.

The engine selects the existing location-specific dialogue when possible.
`Sabrina_EventScript_Companion` provides route and interior conversations before
the starter, during the journey, after the Boulder/Marsh/Earth Badges, and after
becoming Champion. These only read progression flags. The existing 37 shared
dialogue blocks remain unchanged; the new joining and companion blocks are
appended.

## Overworld engine

`src/sabrina_follower.c` creates a normal animated Sabrina object with reserved
local ID 254, outside the map's template list. The existing Sabrina graphics,
walking animations, and standard NPC palette are reused. A bounded eight-step
trail records Red's actual traveled tiles, including turns and scripted steps.
Running uses faster NPC walking frames instead of incompatible player running
frames. The controller runs after overworld sprite movement each frame.

Doors, connected maps, battle returns, and save loading can rebuild or adopt the
companion. Safe adjacent land is preferred when regrouping; the engine avoids
warps, coordinate-event tiles, solid tiles, water, and occupied spawn positions.
If there is no safe position or object slot, it waits rather than replacing an
NPC. Native NPC spawning can reclaim Sabrina's slot if the 16-object runtime
limit is reached. Sabrina never blocks Red or scripted NPC movement.

Dynamic objects receive a synthetic read-only template and context-sensitive
interaction script, avoiding null map-template lookups. Despawning the follower
does not clear her persistent join flag. No party, battle-party, save-structure,
starter, or rival-battle data is changed by the engine.

This is a conservative first implementation with explicit limitations:

- Red's scripted movement in Pallet and Oak's laboratory is supported. Other
  cutscenes temporarily remove Sabrina, then restore her when control returns.
- Sabrina is temporarily hidden while cycling, surfing, in link areas, and
  during Quest Log playback. Her companion status remains active.
- Ledges regroup her on safe land after Red lands; a separate follower ledge-hop
  animation has not been implemented.
- Sabrina does not animate opening doors herself. She is recreated safely in
  the destination, and may appear beside Red if the tile behind him is blocked.
- The original Gym leader object is retained and the follower is suppressed
  inside Saffron Gym, until the future substitute-trainer feature is implemented.
- Prior location dialogue is deliberately preserved, including references to
  waiting at a location; those lines can receive a separate narrative polish.

The technical references were examined for design only; their code and hooks
were not imported:

- [CFRU follower](https://github.com/Skeli789/Complete-Fire-Red-Upgrade/blob/b637a27898b14e25dd24d0f69a3e302f0069deb8/src/follow_me.c): FireRed behavior, but its fixed-address assembly hooks are incompatible here.
- [Emerald follow_me branch](https://github.com/ghoulslash/pokeemerald/blob/295081b1d7bdcad9b676829addc62c4e7d5c7ab0/src/follow_me.c): reserved follower ID, movement tracking, and warp recovery concepts; its save layout and engine assumptions are incompatible here.

## Build and gameplay review

From `/workspace/pokefirered`:

```sh
source /workspace/.pokefirered-env/activate.sh
make -j5 GAME_VERSION=FIRERED GAME_REVISION=1 all syms
```

The expected artifact is `pokefirered_rev1.gba`, with revision 1 in its ROM
header. The original-ROM checksum is expected to differ because the hack changes
content. A successful build establishes compilation and linking, not complete
follower behavior.

Repeatable automated checks:

```sh
python3 tools/sabrina_tests/test_integration.py
python3 tools/sabrina_tests/test_follower_rom.py --rom pokefirered_rev1.gba
```

The ROM test uses a local mGBA libretro core at the path documented in
`tools/sabrina_tests/emulator.py`. This tests real emulated GBA execution, but
does not establish compatibility with every Manic EMU setting or save state.

Run the repeatable integration checks with:

```sh
python3 tools/sabrina_tests/test_integration.py
```

The suite uses Python's standard library, Git, and the installed C preprocessor.
It checks the protected 37 dialogue blocks, unchanged Gym/Oak/Blue progression,
all 12 stationary hide flags, persistent flag allocation, the reserved dynamic
object ID, script references, appended special indices, party/save isolation,
and new dialogue pixel widths using all three dialogue fonts with one pixel of
letter spacing. When the Rev 1 ROM and symbols exist, it also verifies the ROM
revision/header checksum and the mother's assembled twin-sister dialogue.

All 13 integration tests passed against the current source and Rev 1 artifact.
These checks establish those specific contracts, not movement correctness. One
preserved older Saffron dialogue line, "I say that as your GYM LEADER.", occupies
204 pixels with letter spacing: it fits the 208-pixel box but leaves less than
the eight-pixel margin reserved for the lower-line arrow in new dialogue. It is
preserved exactly from the checkpoint and should be inspected in emulator review.

The final Rev 1 ROM also passed 14 actual-ROM mGBA scenario groups: fresh-game
introduction; joining before the starter; walking/corners/stopping; companion
interaction; emulator-state restoration; house doors; Oak's grass intervention
and lab escort; starter selection and Blue's response; the first rival battle;
real in-game saving; cold-boot Continue after Quest Log replay; running;
Pallet–Route 1–Viridian travel; ledge regrouping; and the parcel/Pokédex sequence
(some related checks are grouped together in the runner's output).

Running was tested with the running-shoes flag enabled early, and route travel
used a diagnostic Repel counter to avoid random encounters. Story scenes,
starter selection, battle, and saving were exercised through game inputs;
those diagnostic prerequisites do not alter the shipped ROM. Party size stayed
one, and the rival battle contained the ordinary two battlers.

Validated ROM SHA-256:
`37f831fefc0cd1ac2976fc5f95311de48a7b4499dd8f6efa5e1e184b3c5d2c4b`.

Manic EMU/iPhone visuals, long play sessions, every later map/cutscene, full
object-slot pressure, and the original Gym's full-bag reward retry have not been
emulator-tested in this task. The Gym scripts and dialogue are byte-for-byte
preserved by the integration checks. Use in-game Save/Continue when switching
ROM builds: an emulator save state can contain addresses from the previous
build, and cross-build states were incompatible during development testing.

## Main changed files

| Files | Purpose |
| --- | --- |
| `src/sabrina_follower.c`, `include/sabrina_follower.h` | Companion lifecycle, trail, speed, recovery, and local dialogue |
| `src/overworld.c`, `src/event_object_movement.c` | Frame update, interaction/template safety, collision, NPC slot priority |
| `include/constants/flags.h`, `include/constants/event_objects.h` | Persistent join flag and reserved dynamic ID |
| `data/scripts/sabrina.inc`, `data/specials.inc`, `data/text/sabrina.inc` | Join event, companion interaction, and new dialogue |
| 12 non-Gym Sabrina `map.json` files | Hide stationary copies after joining |
| `data/maps/PalletTown_PlayersHouse_1F/text.inc` | Explicit twin-sister wording |
| `tools/sabrina_tests/` | Preservation/integration checks and headless actual-ROM tests |

Emulator review should cover joining before obtaining a starter, Oak's grass
intervention, the laboratory and first rival battle, the Pokédex sequence,
four-direction walking/running/corners, building doors, connected map edges,
ledges, saving/loading, battle return, interactions, and cutscene restoration.
Check that only one Sabrina is visible and that she never blocks the player or
enters the ordinary battle party. After joining, revisit earlier town dialogue
and the Saffron Gym reward/retry flow.

## Requirements reserved for later development

These remain project requirements and are not replacements for a reliable
follower implementation:

- Pikachu, Charmander, and Bulbasaur as the three starter choices.
- Each Red starter obtained at level 5 with a genuinely shiny personality/OT
  combination; only Red's starter is forced shiny.
- A coherent corresponding Blue starter selection.
- Recurring Leaf story encounters and later Pokémon battles.
- A substitute Psychic Gym Trainer conducting Sabrina's Saffron challenge while
  she retains her official Gym Leader title.
- The combined Red/Sabrina battle-back sprite is now implemented; see
  [the battle companion report](sabrina-battle-companion.md). Sabrina observes
  while Red remains the only active trainer.
- The recognizable original FireRed adventure with expanded story content.
