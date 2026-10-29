# Sabrina battle-sprite polish

Development branch: `feature/sabrina-sprite-polish`.
Protected starting checkpoint: `b41c0791fbaad92535dd8eeb664ce63b84e85fa6`,
also saved as `backup/pre-sabrina-sprite-polish-2026-10-29`.

The updated battle artwork retains Sabrina's FireRed outfit, long blue hair,
and quiet observing pose. The replacement refines her hair highlights and
silhouette. It is custom artwork, prepared from a generated image and reduced
to the game's native indexed-pixel format.

Only the two battle-art PNGs change in production:

- `graphics/trainers/back_pics/sabrina_observer.png`: 30x58 observer artwork.
- `graphics/trainers/back_pics/red_sabrina_back_pic.png`: five 64x64 frames,
  with the observer at the existing position behind Red.

Red's original pixels and palette indices, original throw animation, shared
16-color palette, sprite dimensions, and graphics memory requirements are
preserved. Sabrina keeps her static pose. This artwork update does not change
the follower, scripts, maps, dialogue, save format, or battle mechanics.

The previous working downloads remain unchanged:

- `FireRed-Rev1-Sabrina-Battle-Companion-Test.gba`: SHA-256
  `0b709bf2cd11f88f35072ad0386e8fc30015ad94b35ae581f135f47eed59b3eb`.
- `FireRed-Rev1-Sabrina-Follower-Test.gba`: SHA-256
  `37f831fefc0cd1ac2976fc5f95311de48a7b4499dd8f6efa5e1e184b3c5d2c4b`.

## Validation

```sh
source /workspace/.pokefirered-env/activate.sh
make -j5 GAME_VERSION=FIRERED GAME_REVISION=1 all syms
python3 tools/sabrina_tests/test_integration.py
python3 tools/sabrina_tests/test_battle_graphics.py
python3 tools/sabrina_tests/test_battle_companion_rom.py --output /tmp/sabrina-sprite-polish-tests
```

The Rev 1 build and all 17 preservation/graphics checks passed. These checks
verify Red's original pixels in every frame, the palette, packed ROM data,
Sabrina's stationary pose, and preserved story/progression integration.

The complete mGBA regression also passed: the first Blue battle, an ordinary
wild battle, an ordinary trainer battle, Red's throw phases, the solo-Red
negative control, and the existing follower progression suite. That suite
includes Oak's escort, starter selection, save/cold-boot Continue, running,
doors, Route 1/Viridian transitions, ledge recovery, parcel delivery, and the
Pokédex sequence. Native NPC overlap checks covered 33,326 overworld frames,
including the diagnostic NPC-yield fixture. Test screenshots were inspected
for all three battle introductions.

The earlier implementation details and compatibility limits remain in
[the battle companion report](sabrina-battle-companion.md) and
[the follower report](sabrina-follower.md). Safari, tutorials, link/multi,
genuine Double Battles, and every later encounter have not been emulated in
this task.

New ROM SHA-256:
`f4334b79b3538a1061606b22fecd40fd6e65c1f2e0525256f696abcefc68aaf1`.

Manic EMU on iPhone still needs a visual review at normal screen size: hair
and outfit colors, silhouette, clipping, and the throw/slide sequence. Use an
in-game Save/Continue when changing builds; do not transfer emulator save
states across ROM versions.
