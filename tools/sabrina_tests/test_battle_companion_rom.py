#!/usr/bin/env python3
"""Actual GBA battle-art and native-NPC yielding regressions.

Runs the existing follower progression suite first. Additional encounter tests
use the resulting same-ROM emulator snapshot; no release ROM is patched.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import test_follower_rom as follower_test

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = Path('/tmp/sabrina-battle-tests')
CAPTURED = {}
FINAL_STATE = None
EXPECTED_COMBINED = True
PHASE = None
WORLD_FRAMES = 0
THROW_FRAMES = set()
LAST_CAPTURE = {}


def observe(game):
    global WORLD_FRAMES
    e, s = game.emu, game.symbols
    callback = e.u32(s['gMain'] + 4) & ~1
    if callback == s['CB2_Overworld']:
        WORLD_FRAMES += 1
        f = game.follower()
        if f:
            for npc in game.objects():
                if npc['local'] not in (254, 255):
                    assert npc['pos'] != f['pos'], ('NPC overlap', game.map(), npc, f)
    if callback != s['BattleMainCB2']:
        return
    flags = e.u32(s['gBattleTypeFlags'])
    if e.u8(s['gBattlersCount']) != 2:
        return
    assert not flags & ((1 << 0) | (1 << 6)), 'ordinary battle became double/multi'
    assert e.u8(s['gPlayerPartyCount']) == 1, 'companion entered party'
    kind = PHASE or ('first-blue' if flags & (1 << 4) else 'trainer' if flags & 8 else 'wild')
    combined = s['gTrainerBackPicTable_RedSabrina']
    original = s['gTrainerBackPicTable_Red']
    for index in range(64):
        a = s['gSprites'] + index * 68
        raw = e.read(a, 68)
        if not raw[0x3e] & 1 or raw[0x3e] & 4:
            continue
        images = struct.unpack_from('<I', raw, 12)[0]
        if images not in (combined, original):
            continue
        assert (images == combined) == EXPECTED_COMBINED, (kind, 'wrong trainer artwork')
        x, y, x2, y2 = struct.unpack_from('<hhhh', raw, 0x20)
        if raw[0x2a] == 1:
            THROW_FRAMES.add((kind, raw[0x2b]))
        if x + x2 != 80:
            continue  # Wait until the full trainer has slid into view.
        attr0, attr1, attr2 = struct.unpack_from('<HHH', raw)
        assert (attr0 >> 14) == 0 and (attr1 >> 14) == 3, 'not a 64x64 OBJ'
        assert not attr0 & 0x2000, 'unexpected 8bpp graphics'
        if kind not in CAPTURED and raw[0x2a] == 0:
            # The raster framebuffer trails OAM updates; wait a few stable frames.
            LAST_CAPTURE[kind] = LAST_CAPTURE.get(kind, 0) + 1
            if LAST_CAPTURE[kind] >= 4:
                game.emu.screenshot(OUTPUT / (kind + '-intro.png'))
                CAPTURED[kind] = {'sprite':index,'size':[64,64], 'flags':flags,
                                  'images':images, 'palette':(attr2 >> 12)}
                print('PASS: actual combined intro' if EXPECTED_COMBINED else 'PASS: original solo intro', kind)


BaseGame = follower_test.Game
class ObservedGame(BaseGame):
    def __init__(self, rom):
        super().__init__(rom)
        self.emu.on_frame = lambda: observe(self)
        close = self.emu.close
        def finish():
            global FINAL_STATE
            if self.flag(0x829) and self.follower() is not None:
                FINAL_STATE = self.emu.save_state()
            close()
        self.emu.close = finish


def test_native_yield(game):
    """Diagnostic setup: make a real native NPC walk onto Sabrina's tile."""
    e, s = game.emu, game.symbols
    f = game.follower()
    assert f and game.map() == (4,3)
    oak = next(o for o in game.objects() if o['graphics']==71)  # OBJ_EVENT_GFX_PROF_OAK
    x,y = f['pos']
    actor = s['gObjectEvents'] + 36 * oak['index']
    data = bytearray(e.read(actor,36))
    struct.pack_into('<hhhh',data,16,x+7,y+8,x+7,y+8)
    data[0]=(data[0]|0x40)&~0x80  # Native held movement active, not finished.
    data[1]&=~1  # Unfreeze this native actor.
    data[28]=0x11  # MOVEMENT_ACTION_WALK_NORMAL_UP
    e.write(actor,bytes(data))
    follower_sprite=s['gSprites']+68*f['raw'][4]
    npc_sprite=s['gSprites']+68*data[4]
    fx,fy=struct.unpack('<hh',e.read(follower_sprite+32,4))
    e.write(npc_sprite+32,struct.pack('<hh',fx,fy+16))
    e.write(npc_sprite+36,b'\0'*4)
    e.write(npc_sprite+0x32,b'\0\0')  # movement action step index
    e.run(24)
    native=next(o for o in game.objects() if o['index']==oak['index'])
    assert native['pos']==(x,y), ('native did not enter companion tile',native)
    f=game.follower()
    assert f is None or f['pos']!=(x,y)
    e.run(40)
    assert game.follower() is not None, 'companion did not recover after yielding'
    e.screenshot(OUTPUT/'npc-yield.png')
    print('PASS (diagnostic native-movement setup): Sabrina yields before native overlap and restores.')


def route_to_grass(game):
    game.walk_to('PalletTown_ProfessorOaksLab',(6,12))
    game.step('down');game.emu.run(160)
    assert game.map()==(3,0)
    game.set_var(0x4020,250)
    game.walk_to('PalletTown',(12,0));game.step('up');game.emu.run(100)
    assert game.map()==(3,19)
    game.walk_to('Route1',(7,33))
    game.set_var(0x4020,0)


def enter_wild(game):
    # Move only until an encounter starts, without trying to step in battle.
    e,s=game.emu,game.symbols
    for i in range(220):
        e.run(16, ('right',) if i%4<2 else ('left',))
        if (e.u32(s['gMain']+4)&~1)==s['BattleMainCB2']:
            return
    raise AssertionError('No wild encounter started')


def finish_battle(game):
    e,s=game.emu,game.symbols
    for i in range(1800):
        e.tap('a',8,8)
        if (e.u32(s['gMain']+4)&~1)==s['CB2_Overworld'] and not e.u8(s['sLockFieldControls']):
            e.run(80)
            return
    raise AssertionError('Battle did not return to overworld')


def main():
    global OUTPUT,EXPECTED_COMBINED,PHASE,FINAL_STATE,WORLD_FRAMES
    p=argparse.ArgumentParser();p.add_argument('--rom',type=Path,default=ROOT/'pokefirered_rev1.gba')
    p.add_argument('--output',type=Path,default=OUTPUT);p.add_argument('--resume',action='store_true');args=p.parse_args()
    OUTPUT=args.output;OUTPUT.mkdir(parents=True,exist_ok=True)
    romhash=hashlib.sha256(args.rom.read_bytes()).hexdigest()
    if args.resume:
        saved=json.loads((OUTPUT/'progression-evidence.json').read_text())
        assert saved['rom_sha256']==romhash, 'snapshot belongs to another ROM build'
        CAPTURED.update(saved['captures'])
        THROW_FRAMES.update(tuple(v) for v in saved['throw_command_frames'])
        WORLD_FRAMES=saved['overworld_frames_checked']
        FINAL_STATE=(OUTPUT/'post-pokedex.state').read_bytes()
    else:
        follower_test.Game=ObservedGame
        argv=sys.argv
        sys.argv=[argv[0],'--rom',str(args.rom),'--output',str(OUTPUT/'progression')]
        follower_test.main()
        sys.argv=argv
        assert 'first-blue' in CAPTURED,'combined art not shown against first Blue'
        assert FINAL_STATE,'missing post-Pokedex snapshot'
        (OUTPUT/'post-pokedex.state').write_bytes(FINAL_STATE)
        (OUTPUT/'progression-evidence.json').write_text(json.dumps({'rom_sha256':romhash,'captures':CAPTURED,
            'throw_command_frames':sorted(THROW_FRAMES),'overworld_frames_checked':WORLD_FRAMES}))
    g=ObservedGame(args.rom)
    try:
        g.emu.load_state(FINAL_STATE);g.emu.run(10)
        state=g.emu.save_state()
        test_native_yield(g)
        g.emu.load_state(state);g.emu.run(10)
        route_to_grass(g)
        grass_state=g.emu.save_state()
        PHASE='wild';enter_wild(g)
        g.advance_text(80)
        assert 'wild' in CAPTURED,'no wild combined intro'
        finish_battle(g)
        assert g.follower() is not None
        print('PASS: ordinary wild battle completes with one trainer, two battlers, and companion restoration.')
        # Diagnostic flag-only negative control: no join -> original Red artwork.
        g.emu.load_state(grass_state)
        flag_addr=g.pointer('gSaveBlock1Ptr')+0xee0+0x020//8
        g.emu.write(flag_addr,bytes([g.emu.u8(flag_addr)&~1]))
        EXPECTED_COMBINED=False;PHASE='wild-solo-control';enter_wild(g);g.advance_text(80)
        assert PHASE in CAPTURED
        print('PASS (diagnostic join-flag control): unaccompanied Red retains original graphics.')
        EXPECTED_COMBINED=True
        g.emu.load_state(grass_state);g.emu.run(10)
        g.set_var(0x4020,250)
        g.walk_to('Route1',(12,0));g.step('up');g.emu.run(100)
        assert g.map()==(3,1)
        g.walk_to('ViridianCity',(0,16));g.step('left');g.emu.run(100)
        assert g.map()==(3,41),('Route22',g.map(),g.player())
        PHASE='trainer'
        g.walk_to('Route22',(34,6))
        g.step('left')
        g.finish_script(limit=2200)
        assert 'trainer' in CAPTURED,'no ordinary trainer combined intro'
        assert g.follower() is not None
        print('PASS: ordinary trainer encounter completes without double/multi mechanics.')
        assert not (g.emu.u32(g.symbols['gBattleTypeFlags']) & 1)
        for kind in ('first-blue','wild','trainer'):
            assert set(range(4)) <= {frame for k,frame in THROW_FRAMES if k==kind}, ('throw phases missing',kind,THROW_FRAMES)
        assert hashlib.sha256(args.rom.read_bytes()).hexdigest()==romhash
        (OUTPUT/'evidence.json').write_text(json.dumps({'rom_sha256':romhash,'captures':CAPTURED,
            'throw_command_frames':sorted(THROW_FRAMES),'overworld_frames_checked':WORLD_FRAMES},indent=2))
        print('PASS: battle throw animation observed, native overlap monitored across',WORLD_FRAMES,'overworld frames.')
    except BaseException:
        g.emu.screenshot(OUTPUT/'failure.png')
        print('DIAGNOSTIC',g.map(),g.objects())
        raise
    finally:
        g.emu.close()

if __name__=='__main__':main()
