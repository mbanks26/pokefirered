# Sabrina follower checks

Build from the repository root:

```sh
source /workspace/.pokefirered-env/activate.sh
make -j5 GAME_VERSION=FIRERED GAME_REVISION=1 all syms
python3 tools/sabrina_tests/test_integration.py
python3 tools/sabrina_tests/test_follower_rom.py --rom pokefirered_rev1.gba
python3 tools/sabrina_tests/test_battle_graphics.py
python3 tools/sabrina_tests/test_battle_companion_rom.py --rom pokefirered_rev1.gba
python3 tools/sabrina_tests/test_battle_companion_rom.py --output /tmp/leaf-story-battles
python3 tools/sabrina_tests/test_story_rom.py
```

The integration suite uses Python's standard library, Git, and the C
preprocessor. It compares preserved content against checkpoint
`1a2c7eb374849285f49bf4b57538c938ee77ce22`.

The actual-ROM suite uses the mGBA libretro core plus Pillow for screenshots.
The cloud instance has Debian's `libretro-mgba` 0.10.5 package extracted at
`/workspace/.pokefirered-env/sysroot/usr/lib/x86_64-linux-gnu/libretro/mgba_libretro.so`.
Pillow is already available. These dependencies were used for the recorded tests;
the test runner does not install software or fetch ROMs or BIOS files.

If refreshing this optional emulator dependency in the same cloud setup:

```sh
cd /workspace/.pokefirered-env/debs
APT_CONFIG=/workspace/.pokefirered-env/apt.conf /usr/bin/apt-get download libretro-mgba
for pkg in libretro-mgba_*.deb; do
    dpkg-deb -x "$pkg" /workspace/.pokefirered-env/sysroot
done
```

The package index and TLS/checksum verification remain enabled. Run the ROM
checks from the repository root afterward. Do not rebuild a ROM while a test
runs; the harness guards emulator states using the ROM SHA-256.

The tests exercise genuine emulated GBA frames and input. Diagnostic RAM writes
(such as granting running shoes early and suppressing random wild encounters
for a movement test) are identified in test output. They do not patch the
release ROM or change starter/battle code. Emulator save-state round trips and
real in-game Save/Continue are reported separately.

Screenshots, test logs, and generated test saves go under
`/tmp/sabrina-rom-tests` by default. They are test output, not source files or
saves to import over a player's own game. Manic EMU on iPhone still needs visual
and control verification; an mGBA pass is not a claim that every map or cutscene
has been tested.

The battle companion runner includes the original follower progression suite,
captures Blue/wild/trainer introductions, checks the actual sprite image table,
64x64 4bpp OAM settings, party and battler counts, and Red's throwing phases.
It also performs a clearly labeled diagnostic NPC movement into Sabrina's tile
and a negative join-flag control. Frame-by-frame overworld checks reject native
NPC/follower tile overlap. `--resume` can reuse its post-Pokédex checkpoint only
when the stored ROM SHA-256 matches; use the full command for final validation.

The story runner uses the exact-ROM post-Pokédex snapshot from
`/tmp/leaf-story-battles`. It tests real cartridge Save/Continue after Leaf's
reunion, all southern entry columns, missing-Sabrina and female-route edges,
later Leaf conversations/evolution, and Sabrina's Gym loss/retry/victory,
rewards and battle-art exception. Later-map warps, prerequisites, and strong/weak
party setups are clearly marked diagnostic RAM fixtures, not release changes.
The first runner reaches the Viridian scene naturally from a fresh Red game and
also performs the original in-game save/cold-boot check before that scene.
