# Sabrina's battle companion and NPC overlap fix

This records the initial battle-companion checkpoint. For current Leaf events,
Sabrina's personal Gym battle and its solo-Red exception, see the
[story integration report](red-leaf-sabrina-story.md).

Development branch: `feature/sabrina-battle-companion`.
Protected starting checkpoint: `62c94ca0a4d3625f28f22d5bda0d0ed0cb8b3096`, also
saved as `backup/pre-sabrina-battle-companion-2026-10-28`.

The previous downloadable follower ROM remains unchanged at
`/workspace/artifacts/FireRed-Rev1-Sabrina-Follower-Test.gba`, SHA-256
`37f831fefc0cd1ac2976fc5f95311de48a7b4499dd8f6efa5e1e184b3c5d2c4b`.

## Battle graphics

After Sabrina joins, Red's normal battle introduction uses a combined back
sprite. Sabrina stands behind and to his left in her original FireRed red outfit
and long blue hair. She remains in a static observing pose while Red performs
the original five-frame throwing animation. Both leave the foreground with the
normal trainer slide; Sabrina is not an additional persistent battle-screen OBJ.

Every nontransparent pixel of Red's five original frames is preserved at its
original coordinate and palette index. His original source PNG, palette,
animation commands, and timings are unchanged. New art is drawn behind him and
quantized to his existing 16-entry palette, with index 0 transparent.

The combined sheet is 64x320: five 64x64 4bpp frames, 0x800 bytes each, 0x2800
bytes total. It uses the original single 64x64 trainer OBJ, one palette slot,
and the same per-frame VRAM allocation. No new EWRAM allocation is needed.

A new back-picture ID is appended after the six original IDs. A narrow graphics
selection in `SetMultiuseSpriteTemplateToTrainerBack` chooses it only for Red
after the persistent companion flag is set. Female-player graphics, unaccompanied
Red, link/multi, Safari, Old Man, and Pokédude paths retain their normal assets.

No battle flags, party contents, trainer AI, battle controllers, turn logic,
Pokémon send-out commands, or trainer count are changed. Legitimate existing
Double Battle mechanics are not enabled or rewritten by this graphics feature.

Changed production files:

- `graphics/trainers/back_pics/sabrina_observer.png`: prepared observer artwork.
- `graphics/trainers/back_pics/red_sabrina_back_pic.png`: combined animation sheet.
- `src/data/graphics/trainers.h`, `src/data.c`, `include/graphics.h`,
  `include/data.h`: asset and frame declarations.
- `src/data/trainer_graphics/back_pic_tables.h`, `back_pic_anims.h`,
  `include/constants/trainers.h`: appended ID, size/palette metadata, and reuse
  of Red's existing animation.
- `src/pokemon.c`: appended graphics template and conditional selection.

## Scripted NPC overlap

Native actors retain movement priority. After sprite movement and before OAM is
built, the follower checks whether another NPC occupies either her current tile
or the tile she is leaving mid-step. She yields immediately if so, then respawns
on a clear adjacent tile on the next safe field frame. This prevents scripted
actors from drawing through her without blocking or changing their scripts.

The change is confined to `src/sabrina_follower.c`. No map, dialogue, Leaf,
Oak, Blue, starter, Pokédex, Gym, or save-layout files are changed by this task.

## Build and tests

```sh
source /workspace/.pokefirered-env/activate.sh
make -j5 GAME_VERSION=FIRERED GAME_REVISION=1 all syms
python3 tools/sabrina_tests/test_integration.py
python3 tools/sabrina_tests/test_battle_graphics.py
python3 tools/sabrina_tests/test_battle_companion_rom.py
```

The original 13 preservation/integration checks pass. Four graphics checks
verify the original assets/throw, all five frames and every original Red pixel,
the stationary observer, exact palette and frame byte sizes, linked ROM data,
and the untouched previous working ROM.

Actual headless mGBA testing covers:

- The complete prior follower progression regression, including Oak's escort,
  starter and Blue selection, first battle, save/cold-boot Continue, doors,
  running, map transitions, ledge recovery, parcel delivery, and Pokédex.
- Combined artwork in the first Blue battle, a Route 1 wild battle, and the
  ordinary Route 22 rival trainer battle; completion and follower restoration.
- Original solo artwork when the join flag is cleared diagnostically.
- One Pokémon in the player party and two battlers in all tested encounters,
  with no Double/Multi Battle flags.
- Original throw animation phases in all three battle contexts.
- Frame-by-frame checks for native NPC/follower tile overlap during progression.
- Diagnostic placement followed by an actual native NPC step onto Sabrina's
  tile, confirming she yields and returns nearby.

Running shoes and Repel are enabled diagnostically in movement tests, as in the
previous test suite; they are not granted early in the shipped game. The NPC
fixture and negative join-flag control modify emulator memory only. No release
ROM is patched by tests.

New Rev 1 ROM SHA-256:
`0b709bf2cd11f88f35072ad0386e8fc30015ad94b35ae581f135f47eed59b3eb`.

## Manic EMU review still needed

Check the artwork at native screen scale, hair/outfit colors, Red's throwing
sequence and slide, Poké Ball alignment, and sprite clipping during wild/trainer
introductions. Check Oak/Blue and other later scripted actor paths and follower
recovery during a longer play session. Safari, tutorials, link/multi, genuine
Double Battles, and every later scripted encounter have not been emulated in
this task. The static companion pose can receive an independent animation pass
later without changing battle mechanics.

Use in-game Save/Continue rather than a save state from another ROM build.
