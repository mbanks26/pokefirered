#!/usr/bin/env python3
"""Run Sabrina's follower inside an actual ROM using a headless mGBA core.

The fresh-game path uses joypad inputs. Optional diagnostic state writes are
explicitly reported separately from those natural gameplay checks.
"""
import argparse
import ctypes as C
import hashlib
import json
from collections import deque
from pathlib import Path
import struct
from emulator import Emulator

ROOT = Path(__file__).resolve().parents[2]


class Game:
    def __init__(self, rom):
        self.emu = Emulator(rom)
        self.rom_hash = hashlib.sha256(rom.read_bytes()).hexdigest()
        sym = rom.with_suffix('.sym')
        self.symbols = {m[3]: int(m[0], 16) for line in sym.read_text().splitlines()
                        if len(m := line.split()) == 4}

    def pointer(self, name):
        return self.emu.u32(self.symbols[name])

    def objects(self):
        result = []
        for index in range(16):
            data = self.emu.read(self.symbols['gObjectEvents'] + 36 * index, 36)
            if data[0] & 1:
                result.append(dict(index=index, local=data[8], graphics=data[5],
                                   pos=tuple(v - 7 for v in struct.unpack_from('<hh', data, 16)),
                                   previous=tuple(v - 7 for v in struct.unpack_from('<hh', data, 20)),
                                   invisible=bool(data[1] & 0x20), raw=data))
        return result

    def player(self):
        return next(o for o in self.objects() if o['local'] == 255)

    def set_flag(self, flag):
        address = self.pointer('gSaveBlock1Ptr') + 0xee0 + flag // 8
        self.emu.write(address, bytes([self.emu.u8(address) | (1 << (flag % 8))]))

    def set_var(self, var, value):
        self.emu.write(self.pointer('gSaveBlock1Ptr') + 0x1000 + 2 * (var - 0x4000), struct.pack('<H', value))

    def follower(self):
        followers = [o for o in self.objects() if o['local'] == 254]
        assert len(followers) <= 1, followers
        return followers[0] if followers else None

    def map(self):
        data = self.emu.read(self.pointer('gSaveBlock1Ptr') + 4, 2)
        return tuple(data)

    def flag(self, flag):
        return bool(self.emu.u8(self.pointer('gSaveBlock1Ptr') + 0xee0 + flag // 8) & (1 << (flag % 8)))

    def step(self, key, run=False):
        old = self.player()['pos']
        old_map = self.map()
        for _ in range(160):
            self.emu.run(1, (key, 'b') if run else (key,))
            try:
                if self.map() != old_map or self.player()['pos'] != old:
                    break
            except StopIteration:
                pass
        self.emu.run(32)
        for _ in range(180):
            try:
                return old, self.player()['pos']
            except StopIteration:
                self.emu.run(1)
        raise AssertionError('Player object was not restored after movement/transition')

    def steps(self, key, count):
        for _ in range(count):
            self.step(key)

    def walk_to(self, map_name, target):
        layout_name = json.loads((ROOT / 'data/maps' / map_name / 'map.json').read_text())['layout']
        layout = next(l for l in json.loads((ROOT / 'data/layouts/layouts.json').read_text())['layouts']
                      if l.get('id') == layout_name)
        width, height = layout['width'], layout['height']
        tiles = struct.unpack('<' + 'H' * width * height, (ROOT / layout['blockdata_filepath']).read_bytes())
        for attempt in range(400):
            start = self.player()['pos']
            if start == target:
                return
            occupied = {o['pos'] for o in self.objects() if o['local'] not in (254, 255)}
            queue = deque([(start, [])])
            seen = {start}
            route = None
            while queue:
                (x, y), path = queue.popleft()
                if (x, y) == target:
                    route = path
                    break
                for dx, dy, key in ((0, -1, 'up'), (0, 1, 'down'), (-1, 0, 'left'), (1, 0, 'right')):
                    nxt = (x + dx, y + dy)
                    if (0 <= nxt[0] < width and 0 <= nxt[1] < height and nxt not in seen
                        and nxt not in occupied and not (tiles[nxt[1] * width + nxt[0]] >> 10 & 3)):
                        seen.add(nxt)
                        queue.append((nxt, path + [key]))
            assert route, ('no safe route', map_name, start, target)
            old, new = self.step(route[0])
            if old == new:
                self.emu.run(60)  # Let a wandering NPC move before replanning.
        raise AssertionError(('walk route did not finish', map_name, target, self.player()))

    def finish_script(self, limit=500):
        for _ in range(limit):
            if not self.emu.u8(self.symbols['sLockFieldControls']):
                self.emu.run(32)
                if not self.emu.u8(self.symbols['sLockFieldControls']):
                    return
            self.emu.tap('a', 8, 8)
        raise AssertionError('Script did not return player control')

    def advance_text(self, count):
        for _ in range(count):
            self.emu.tap('a', 8, 8)

    def fresh_game(self):
        # Boot, title, controls, Oak's introduction, default male, name selection.
        for _ in range(8):
            self.emu.run(120)
            self.emu.tap('start')
        for _ in range(60):
            self.emu.tap('a', 2, 18)
        self.advance_text(60)
        self.emu.tap('start', 2, 20)
        self.emu.tap('a', 2, 20)
        self.advance_text(168)
        assert self.map() == (4, 1), ('new game did not reach bedroom', self.map())
        assert self.player()['pos'] == (6, 6), self.player()
        # Walk around the bed to the staircase; enter the downstairs landing.
        self.steps('right', 3)
        self.steps('up', 2)
        self.steps('right', 2)
        self.steps('up', 2)
        self.steps('left', 2)
        self.emu.run(160)
        assert self.map() == (4, 0), ('downstairs', self.map(), self.player())
        self.steps('down', 5)
        self.steps('left', 6)
        self.steps('down', 2)
        self.emu.run(180)
        assert self.map() == (3, 0), ('Pallet exit', self.map(), self.player())
        assert self.player()['pos'] == (6, 8), self.player()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rom', type=Path, default=ROOT / 'pokefirered_rev1.gba')
    parser.add_argument('--output', type=Path, default=Path('/tmp/sabrina-rom-tests'))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    game = Game(args.rom)
    try:
        game.fresh_game()
        game.emu.screenshot(args.output / '01-pallet-before-talk.png')
        assert not game.flag(0x020), 'follower flag set before first Sabrina conversation'
        assert game.follower() is None, 'follower exists before activation'
        game.step('right')
        game.emu.tap('a')
        game.advance_text(60)
        game.emu.run(60)
        game.emu.screenshot(args.output / '02-pallet-after-talk.png')
        assert game.flag(0x020), 'first Sabrina conversation did not activate persistent follower flag'
        assert game.follower() is not None, 'persistent follower is not spawned after first conversation'
        assert not game.flag(0x828), 'test must activate Sabrina before receiving starter'
        print('PASS: fresh game, original Oak introduction, house exit, Sabrina activation before starter.')
        for key in ('right', 'right', 'down', 'down', 'left', 'left', 'up', 'right'):
            old, new = game.step(key)
            follower = game.follower()
            assert follower is not None, (key, old, new, 'follower missing')
            assert follower['pos'] == old, (key, old, new, follower)
        game.emu.screenshot(args.output / '03-pallet-movement.png')
        print('PASS: four directions, corners, stopping, and one-tile trail in actual engine frames.')
        # The follower remains talkable after moving. A one-frame direction tap
        # turns Red toward Sabrina without taking a step into her tile.
        game.emu.run(1, ('left',))
        game.emu.run(16)
        game.emu.tap('a')
        assert game.emu.u8(game.symbols['sLockFieldControls']), 'follower talk did not start'
        game.finish_script()
        assert game.follower() is not None
        print('PASS: companion conversation returns control without losing follower.')
        state = game.emu.save_state()
        game.step('right')
        game.emu.load_state(state)
        game.emu.run(60)
        assert game.flag(0x020) and game.follower() is not None
        print('PASS: emulator state restoration retains follower (in-game save/reload still separate).')
        Path(args.output / 'pallet-active.state').write_bytes(game.emu.save_state())
        # Enter and leave Red's house naturally, without debug warping.
        game.steps('left', 2)
        game.steps('up', 2)
        game.emu.run(160)
        assert game.map() == (4, 0), ('house entry', game.map(), game.player())
        assert game.follower() is not None, 'follower not recreated inside house'
        game.emu.screenshot(args.output / '04-follower-in-house.png')
        game.steps('down', 2)
        game.emu.run(160)
        assert game.map() == (3, 0), ('house exit', game.map(), game.player())
        assert game.follower() is not None, 'follower not recreated outside house'
        print('PASS: natural building entry/exit recreates exactly one follower.')
        # Oak's grass interception and walk into his laboratory run unchanged.
        game.steps('right', 6)
        game.steps('up', 7)
        game.emu.run(80)
        assert game.emu.u8(game.symbols['sLockFieldControls']), 'Oak grass interception did not start'
        assert game.follower() is not None, 'follower disappeared during Oak interception'
        game.emu.screenshot(args.output / '05-oak-stops-red.png')
        game.finish_script()
        assert game.map() == (4, 3), ('Oak laboratory', game.map(), game.player())
        assert game.follower() is not None, 'follower missing in Oak laboratory'
        assert game.follower()['pos'] != game.player()['pos']
        game.emu.screenshot(args.output / '06-follower-in-lab.png')
        Path(args.output / 'lab-before-starter.state').write_bytes(game.emu.save_state())
        print('PASS: original Oak grass interception and laboratory introduction with visible follower.')
        # Select Bulbasaur, decline a nickname, let Blue choose his counter.
        game.step('down')
        game.steps('right', 2)
        game.emu.run(1, ('up',))
        game.emu.run(16)
        game.emu.tap('a')
        for _ in range(100):
            if game.flag(0x828):
                break
            game.emu.tap('a', 8, 8)
        assert game.flag(0x828)
        for _ in range(200):
            if not game.emu.u8(game.symbols['sLockFieldControls']):
                break
            game.emu.tap('b', 8, 8)
        assert not game.emu.u8(game.symbols['sLockFieldControls'])
        assert game.emu.u8(game.symbols['gPlayerPartyCount']) == 1
        assert game.follower() is not None
        game.emu.screenshot(args.output / '07-starter-obtained.png')
        print('PASS: Oak starter selection, one-mon party, Blue selects his counter, companion retained.')
        game.steps('left', 2)
        game.steps('down', 3)
        for _ in range(500):
            game.emu.tap('a', 8, 8)
            if game.emu.u8(game.symbols['gBattlersCount']) == 2:
                break
        assert game.emu.u8(game.symbols['gBattlersCount']) == 2
        assert game.emu.u8(game.symbols['gPlayerPartyCount']) == 1
        game.emu.run(120)
        assert game.emu.u16(game.symbols['gBattleMons']) == 1, 'player battle species must be Bulbasaur'
        assert game.emu.u16(game.symbols['gBattleMons'] + 0x58) == 4, 'Blue must counter Bulbasaur with Charmander'
        game.emu.screenshot(args.output / '08-rival-battle.png')
        for _ in range(1500):
            game.emu.tap('a', 8, 8)
            if game.flag(0x258) and not game.emu.u8(game.symbols['sLockFieldControls']):
                break
        assert game.flag(0x258), 'first rival battle did not complete'
        assert game.follower() is not None, 'follower not restored after first rival battle'
        assert game.emu.u8(game.symbols['gPlayerPartyCount']) == 1
        game.emu.screenshot(args.output / '09-rival-complete.png')
        print('PASS: original first rival battle completes with two battlers; Sabrina never enters party/battle.')
        # Save through the actual start-menu save UI, preserving cartridge SRAM.
        game.emu.tap('start', 2, 45)
        count = game.emu.u8(game.symbols['sNumStartMenuItems'])
        order = list(game.emu.read(game.symbols['sStartMenuOrder'], count))
        target = order.index(4)  # STARTMENU_SAVE
        cursor = game.emu.u8(game.symbols['sStartMenuCursorPos'])
        for _ in range((target - cursor) % count):
            game.emu.tap('down', 2, 10)
        game.emu.tap('a', 2, 20)
        for _ in range(500):
            game.emu.tap('a', 8, 8)
            if not game.emu.u8(game.symbols['sLockFieldControls']):
                break
        assert not game.emu.u8(game.symbols['sLockFieldControls']), 'in-game save did not finish'
        save_size = game.emu.lib.retro_get_memory_size(0)
        save_pointer = game.emu.lib.retro_get_memory_data(0)
        assert save_size == 0x20000 and save_pointer
        cartridge_save = C.string_at(save_pointer, save_size)
        assert cartridge_save != b'\xff' * save_size
        (args.output / 'sabrina-active.sav').write_bytes(cartridge_save)
        game.emu.screenshot(args.output / '10-in-game-save-complete.png')
        assert hashlib.sha256(args.rom.read_bytes()).hexdigest() == game.rom_hash, 'ROM rebuilt during test'
        print('PASS: real in-game save completed; cartridge SRAM written for cold-boot continuation check.')
    except BaseException:
        game.emu.screenshot(args.output / 'failure.png')
        print('FAILURE map',game.map(),'objects',game.objects())
        raise
    finally:
        game.emu.close()
    game = Game(args.rom)
    try:
        C.memmove(game.emu.lib.retro_get_memory_data(0), cartridge_save, len(cartridge_save))
        for _ in range(8):
            game.emu.run(120)
            game.emu.tap('start')
        game.emu.tap('a')  # Continue
        for _ in range(30):
            game.emu.run(120)
            game.emu.tap('b')
            if game.emu.u8(game.symbols['gQuestLogState']) == 0 and game.follower() is not None:
                break
        assert game.flag(0x020) and game.follower() is not None
        assert not game.emu.u8(game.symbols['sLockFieldControls'])
        old, new = game.step('down')
        assert old != new and game.follower()['pos'] == old
        game.emu.screenshot(args.output / '11-cold-boot-continue.png')
        print('PASS: cold boot from actual cartridge save restores companion after Quest Log replay.')
        game.steps('down', 4)
        game.emu.run(180)
        assert game.map() == (3, 0), ('lab exit', game.map(), game.player())
        assert game.follower() is not None
        # Diagnostic prerequisites only: allow running before shoes are awarded,
        # and set Repel's existing step counter to keep route movement deterministic.
        game.set_flag(0x82f)  # FLAG_SYS_B_DASH
        game.set_var(0x4020, 250)  # VAR_REPEL_STEP_COUNT, starter already level 5+
        game.walk_to('PalletTown', (12, 14))
        game.emu.run(32, ('up', 'b'))
        game.emu.run(32)
        assert game.follower() is not None
        assert game.follower()['pos'] == (game.player()['pos'][0], game.player()['pos'][1] + 1)
        game.emu.screenshot(args.output / '12-running.png')
        print('PASS (debug-assisted prerequisites): running keeps Sabrina on Red’s trail.')
        game.walk_to('PalletTown', (12, 0))
        game.step('up')
        game.emu.run(100)
        assert game.map() == (3, 19), ('Route 1 connection', game.map(), game.player())
        assert game.follower() is not None
        game.emu.screenshot(args.output / '13-route1.png')
        game.walk_to('Route1', (12, 0))
        game.step('up')
        game.emu.run(100)
        assert game.map() == (3, 1), ('Viridian connection', game.map(), game.player())
        if 'Leaf_EventScript_ViridianReunion' in game.symbols:
            assert game.emu.u8(game.symbols['sLockFieldControls']), 'Leaf did not greet Red automatically'
            assert not game.flag(0x021), 'reunion marked complete before goodbye'
            assert any(o['graphics'] == 152 for o in game.objects()), 'Leaf NPC missing'
            game.emu.screenshot(args.output / '14-leaf-reunion.png')
            game.finish_script(limit=1000)
            assert game.flag(0x021), 'Leaf reunion did not finish'
            assert not any(o['graphics'] == 152 for o in game.objects()), 'Leaf did not depart'
            print('PASS: automatic Viridian twin reunion before Parcel; two-badge scene completes and Leaf departs.')
        assert game.follower() is not None
        game.emu.screenshot(args.output / '14-viridian.png')
        print('PASS (debug-assisted Repel): walk Pallet → Route 1 → Viridian; no duplicate Sabrina.')
        # Collect Oak's parcel via the original Mart cutscene, then deliver it.
        game.walk_to('ViridianCity', (36, 20))
        game.step('up')
        game.emu.run(160)
        game.finish_script()
        assert game.follower() is not None, 'follower not restored after Mart parcel cutscene'
        assert not game.flag(0x829), 'Pokédex obtained before parcel delivery'
        game.emu.screenshot(args.output / '15-oaks-parcel.png')
        game.walk_to('ViridianCity_Mart', (4, 7))
        game.step('down')
        game.emu.run(160)
        assert game.map() == (3, 1)
        game.set_var(0x4020, 250)
        game.walk_to('ViridianCity', (22, 39))
        game.step('down')
        game.emu.run(100)
        assert game.map() == (3, 19)
        game.walk_to('Route1', (14, 4))
        before_jump, after_jump = game.step('down')
        game.emu.run(64)
        assert after_jump == (14, 6), ('ledge jump', before_jump, after_jump)
        assert game.follower() is not None, 'follower not restored after ledge jump'
        assert sum(abs(a-b) for a,b in zip(game.player()['pos'],game.follower()['pos'])) == 1
        game.emu.screenshot(args.output / '16-ledge-regroup.png')
        print('PASS: actual Route 1 ledge jump safely regroups Sabrina beside Red.')
        game.walk_to('Route1', (12, 39))
        game.step('down')
        game.emu.run(100)
        assert game.map() == (3, 0)
        game.walk_to('PalletTown', (16, 14))
        game.step('up')
        game.emu.run(160)
        assert game.map() == (4, 3)
        game.walk_to('PalletTown_ProfessorOaksLab', (6, 4))
        game.emu.run(1, ('up',))
        game.emu.run(16)
        game.emu.tap('a')
        game.finish_script(limit=900)
        assert game.flag(0x829), 'original parcel delivery/Pokédex scene did not finish'
        assert game.follower() is not None
        assert game.emu.u8(game.symbols['gPlayerPartyCount']) == 1
        game.emu.screenshot(args.output / '17-pokedex-obtained.png')
        print('PASS: original Oak parcel delivery, Blue scene, and Pokédex award complete with Sabrina retained.')
        assert hashlib.sha256(args.rom.read_bytes()).hexdigest() == game.rom_hash, 'ROM rebuilt during test'
    except BaseException:
        game.emu.screenshot(args.output / 'failure-continued.png')
        print('FAILURE continued map', game.map(), 'objects', game.objects())
        raise
    finally:
        game.emu.close()


if __name__ == '__main__':
    main()
