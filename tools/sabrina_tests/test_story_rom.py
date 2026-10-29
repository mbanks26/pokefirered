#!/usr/bin/env python3
"""Actual-ROM story, save and Gym regressions after the full progression suite.

First run test_battle_companion_rom.py with --output /tmp/leaf-story-battles.
Its snapshot is accepted only for the exact same ROM SHA-256. Later-map access,
story prerequisites, party strength and edge cases are diagnostic RAM fixtures;
the original progression runner reaches Viridian naturally from a fresh game.
No ROM bytes are patched.
"""
import argparse
import ctypes as C
import hashlib
import json
from pathlib import Path
import struct
import test_battle_companion_rom as battle
from test_follower_rom import Game, ROOT
from test_integration import constants


class StoryGame(Game):
    def __init__(self, rom, output):
        super().__init__(rom)
        self.output = output
        self.seen_text = set()
        self.captures = set()
        self.stable = {}
        self.phase = None
        self.combined = True
        self.world_frames = 0
        self.palette_checked = False
        self.text_frames = {}
        labels = ['Leaf_Text_ViridianBadges', 'Leaf_Text_ViridianSabrinaReply',
                  'Leaf_Text_Cerulean', 'Leaf_Text_Lavender', 'Leaf_Text_SaffronRockets',
                  'Leaf_Text_EeveeChoice', 'Leaf_Text_Vaporeon', 'Leaf_Text_SaffronVaporeon']
        data = rom.read_bytes()
        self.prefixes = {label:data[self.symbols[label]-0x08000000: self.symbols[label]-0x08000000+18]
                         for label in labels}
        self.emu.on_frame = self.observe

    def observe(self):
        e,s = self.emu,self.symbols
        text = e.read(s['gStringVar4'],18)
        for label,prefix in self.prefixes.items():
            if text == prefix:
                self.seen_text.add(label)
                self.text_frames[label] = self.text_frames.get(label,0)+1
                if self.text_frames[label] == 32:
                    e.screenshot(self.output/(label+'.png'))
        cb = e.u32(s['gMain']+4)&~1
        if cb == s['CB2_Overworld']:
            self.world_frames += 1
            f = self.follower()
            if f:
                for npc in self.objects():
                    if npc['local'] not in (254,255):
                        assert npc['pos'] != f['pos'], ('story NPC overlap', self.map(), npc, f)
            leaf = next((o for o in self.objects() if o['graphics']==152),None)
            if leaf and self.map()==(3,1):
                player=self.player()
                red=e.u16(s['gSprites']+68*player['raw'][4]+4)>>12
                green=e.u16(s['gSprites']+68*leaf['raw'][4]+4)>>12
                assert red==0 and green==10, ('Leaf overwrote Red palette',red,green)
                self.palette_checked=True
        if cb != s['BattleMainCB2'] or self.phase is None:
            return
        pair=s['gTrainerBackPicTable_RedSabrina']; solo=s['gTrainerBackPicTable_Red']
        for i in range(64):
            raw=e.read(s['gSprites']+68*i,68)
            if not raw[0x3e]&1 or raw[0x3e]&4:continue
            images=struct.unpack_from('<I',raw,12)[0]
            if images not in (pair,solo):continue
            assert (images==pair)==self.combined, ('wrong story battle artwork',self.phase,images)
            assert e.u8(s['gBattlersCount'])==2
            assert e.u8(s['gPlayerPartyCount'])==1
            assert not e.u32(s['gBattleTypeFlags']) & ((1<<0)|(1<<6))
            x,_,x2,_=struct.unpack_from('<hhhh',raw,32)
            if x+x2==80 and raw[0x2a]==0:
                self.stable[self.phase]=self.stable.get(self.phase,0)+1
                if self.stable[self.phase]==4:
                    e.screenshot(self.output/(self.phase+'.png'))
                    self.captures.add(self.phase)

    def clear_flag(self, flag):
        a=self.pointer('gSaveBlock1Ptr')+0xee0+flag//8
        self.emu.write(a,bytes([self.emu.u8(a)&~(1<<(flag%8))]))

    def diagnostic_script(self, code):
        """Set up the native script interpreter, using spare text-buffer tail.

        This is a test-only RAM fixture; no debug script is linked into the ROM.
        Warp consumes this short payload before any destination text is shown.
        """
        e,s=self.emu,self.symbols
        assert not e.u8(s['sLockFieldControls'])
        a=s['gStringVar4']+900
        assert len(code)<100
        e.write(a,code)
        context=struct.pack('<BBBxII',0,1,0,0,a)+bytes(80)
        context+=struct.pack('<II',s['gScriptCmdTable'],s['gScriptCmdTableEnd'])+bytes(16)
        assert len(context)==116
        e.write(s['sGlobalScriptContext'],context)
        e.write(s['sGlobalScriptContextStatus'],b'\0')
        e.write(s['sLockFieldControls'],b'\1')

    def warp(self, map_pair, x, y):
        self.diagnostic_script(bytes([0x39,*map_pair,0xff])+struct.pack('<HH',x,y)+b'\x6b\x02')
        self.emu.run(240)
        assert self.map()==map_pair, ('diagnostic warp failed',self.map(),map_pair)

    def save_cartridge(self):
        e,s=self.emu,self.symbols
        e.tap('start',2,45)
        count=e.u8(s['sNumStartMenuItems'])
        order=list(e.read(s['sStartMenuOrder'],count))
        target=order.index(4)
        cursor=e.u8(s['sStartMenuCursorPos'])
        for _ in range((target-cursor)%count):e.tap('down',2,10)
        e.tap('a',2,20)
        for _ in range(500):
            e.tap('a',8,8)
            if not e.u8(s['sLockFieldControls']):break
        assert not e.u8(s['sLockFieldControls'])
        size=e.lib.retro_get_memory_size(0)
        assert size==0x20000
        return C.string_at(e.lib.retro_get_memory_data(0),size)

    def continue_cartridge(self, data):
        e,s=self.emu,self.symbols
        C.memmove(e.lib.retro_get_memory_data(0),data,len(data))
        for _ in range(8):e.run(120);e.tap('start')
        e.tap('a')
        for _ in range(40):
            e.run(120);e.tap('b')
            if e.u8(s['gQuestLogState'])==0 and self.follower() is not None:break
        assert not e.u8(s['sLockFieldControls'])
        assert self.follower() is not None

    def talk_up(self):
        self.emu.run(1,('up',));self.emu.run(16);self.emu.tap('a')
        self.finish_script(limit=1200)

    def strength_fixture(self, win):
        # Only party-tail battle stats are adjusted, never species/PID/OT data.
        # This permits testing the real endgame Gym from an early-game snapshot.
        a=self.symbols['gPlayerParty']
        self.emu.write(a+0x50,bytes(4))
        self.emu.write(a+0x54,bytes([100 if win else 5]))
        self.emu.write(a+0x56,struct.pack('<7H',*([999]*7 if win else [1]*7)))


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--rom',type=Path,default=ROOT/'pokefirered_rev1.gba')
    p.add_argument('--progression',type=Path,default=Path('/tmp/leaf-story-battles'))
    p.add_argument('--output',type=Path,default=Path('/tmp/leaf-story-tests'))
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    sha=hashlib.sha256(a.rom.read_bytes()).hexdigest()
    evidence=json.loads((a.progression/'evidence.json').read_text())
    assert evidence['rom_sha256']==sha,'Run full progression on this exact ROM first'
    snapshot=(a.progression/'post-pokedex.state').read_bytes()
    ids=constants(['FLAG_BADGE06_GET','FLAG_GOT_TM04_FROM_SABRINA','FLAG_DEFEATED_SABRINA',
                   'FLAG_RESCUED_MR_FUJI','FLAG_HIDE_SAFFRON_ROCKETS'],'constants/flags.h')
    # Map IDs come from the same preprocessed engine header as the built ROM.
    values=constants(['MAP_CERULEAN_CITY','MAP_LAVENDER_TOWN','MAP_SAFFRON_CITY','MAP_SAFFRON_CITY_GYM'],'constants/maps.h')
    pairs={key:((v>>8)&255,v&255) for key,v in values.items()}
    g=StoryGame(a.rom,a.output)
    try:
        g.emu.load_state(snapshot);g.emu.run(40)
        assert g.flag(0x21) and g.flag(0x20)
        # The original suite already saved/cold-booted before Leaf's scene.
        after_save=g.save_cartridge();g.emu.close()
        g=StoryGame(a.rom,a.output);g.continue_cartridge(after_save)
        assert g.flag(0x21),'reunion flag did not survive cartridge Save/Continue'
        g.warp((3,19),12,1);g.step('up');g.step('up');g.emu.run(100)
        assert g.map()==(3,1) and not g.emu.u8(g.symbols['sLockFieldControls'])
        assert not any(o['graphics']==152 for o in g.objects())
        assert g.follower() is not None
        print('PASS: actual Save/cold-boot Continue after reunion; southern reentry does not repeat it.')

        # All four entrance columns, with native walking over the connection.
        for x in range(10,14):
            g.warp((3,19),x,1);g.clear_flag(0x21);g.clear_flag(0x829)
            g.step('up');g.step('up');g.emu.run(80)
            assert g.map()==(3,1) and g.emu.u8(g.symbols['sLockFieldControls'])
            assert g.follower() is not None
            g.advance_text(80);g.finish_script()
            assert g.flag(0x21) and not g.flag(0x829)
            assert g.follower() is not None
        assert 'Leaf_Text_ViridianBadges' in g.seen_text and g.palette_checked
        print('PASS (diagnostic reset): all four south-entry columns, badge reveal, Red/Leaf separate palettes, and follower recovery before Pokédex.')
        g.warp((3,19),12,1);g.clear_flag(0x21);g.clear_flag(0x20)
        g.step('up');g.step('up');g.emu.run(100)
        assert not g.flag(0x21) and not g.emu.u8(g.symbols['sLockFieldControls'])
        assert not any(o['graphics']==152 for o in g.objects())
        g.set_flag(0x20)
        g.warp((3,19),12,1);g.step('up');g.step('up');g.emu.run(100)
        g.finish_script(limit=1000);assert g.flag(0x21) and g.follower() is not None
        print('PASS (diagnostic missing-companion edge): no-join entry is safe; returning with Sabrina runs the reunion.')
        g.warp((3,19),12,1);g.clear_flag(0x21)
        g.emu.write(g.pointer('gSaveBlock2Ptr')+8,b'\1')
        g.step('up');g.step('up');g.emu.run(100)
        assert not g.flag(0x21) and not any(o['graphics']==152 for o in g.objects())
        assert not g.emu.u8(g.symbols['sLockFieldControls'])
        g.emu.write(g.pointer('gSaveBlock2Ptr')+8,b'\0');g.set_flag(0x21)
        print('PASS (diagnostic gender edge): female route does not create a second Leaf or run the twin-brother scene.')

        g.warp(pairs['MAP_CERULEAN_CITY'],20,23);g.talk_up()
        assert 'Leaf_Text_Cerulean' in g.seen_text and g.follower() is not None
        g.warp(pairs['MAP_LAVENDER_TOWN'],15,10);g.talk_up()
        assert g.flag(0x26) and 'Leaf_Text_Lavender' in g.seen_text
        g.warp(pairs['MAP_CERULEAN_CITY'],20,23)
        assert not any(o['graphics']==152 for o in g.objects())
        g.set_flag(ids['FLAG_RESCUED_MR_FUJI'])
        g.warp(pairs['MAP_SAFFRON_CITY'],22,35);g.talk_up()
        assert 'Leaf_Text_SaffronRockets' in g.seen_text and not g.flag(0x27)
        g.set_flag(ids['FLAG_HIDE_SAFFRON_ROCKETS']);g.talk_up()
        assert g.flag(0x27) and 'Leaf_Text_EeveeChoice' in g.seen_text and 'Leaf_Text_Vaporeon' in g.seen_text
        g.talk_up();assert 'Leaf_Text_SaffronVaporeon' in g.seen_text
        g.warp(pairs['MAP_LAVENDER_TOWN'],15,10)
        assert not any(o['graphics']==152 for o in g.objects())
        print('PASS (diagnostic story prerequisites): Cerulean reunion, Lavender seriousness, Saffron support and one-time on-screen Water Stone/Vaporeon moment; no forced Leaf battle.')

        g.warp(pairs['MAP_SAFFRON_CITY_GYM'],14,12);g.finish_script()
        assert not g.flag(ids['FLAG_BADGE06_GET']) and g.flag(0x20)
        assert g.follower() is None
        assert sum(o['graphics']==85 for o in g.objects())==1
        g.strength_fixture(False);g.phase='gym-loss-intro';g.combined=False
        g.emu.run(1,('up',));g.emu.run(16);g.emu.tap('a');g.advance_text(80)
        battle.finish_battle(g)
        assert g.phase in g.captures
        assert not g.flag(ids['FLAG_BADGE06_GET']) and g.flag(0x20)
        assert g.follower() is not None
        print('PASS (diagnostic weak party): losing Sabrina battle uses solo Red, blackouts safely and retains companion status.')
        g.phase=None;g.warp(pairs['MAP_SAFFRON_CITY_GYM'],14,12);g.finish_script()
        assert g.follower() is None and sum(o['graphics']==85 for o in g.objects())==1
        retry_save=g.save_cartridge();g.emu.close()
        # Continue before the challenge must restore the official leader only.
        g=StoryGame(a.rom,a.output)
        C.memmove(g.emu.lib.retro_get_memory_data(0),retry_save,len(retry_save))
        for _ in range(8):g.emu.run(120);g.emu.tap('start')
        g.emu.tap('a');g.emu.run(500)
        for _ in range(30):g.emu.tap('b');g.emu.run(120)
        assert g.map()==pairs['MAP_SAFFRON_CITY_GYM']
        assert g.follower() is None and sum(o['graphics']==85 for o in g.objects())==1
        g.strength_fixture(True);g.phase='gym-retry-intro';g.combined=False
        g.emu.run(1,('up',));g.emu.run(16);g.emu.tap('a');g.advance_text(80)
        battle.finish_battle(g)
        assert g.phase in g.captures
        assert g.flag(ids['FLAG_BADGE06_GET']) and g.flag(ids['FLAG_GOT_TM04_FROM_SABRINA'])
        assert g.flag(ids['FLAG_DEFEATED_SABRINA']) and g.flag(0x20)
        assert g.follower() is not None and sum(o['graphics']==85 for o in g.objects())==1
        g.emu.screenshot(a.output/'gym-victory-follower.png')
        print('PASS (diagnostic strong party): cartridge Continue/retry, solo Gym introduction, original Marsh Badge/TM04 rewards and exactly one restored follower.')
        # Diagnostic unclaimed-reward flag: the traveling Gym object must still
        # offer TM04 instead of losing the original retry path when it rejoins.
        g.clear_flag(ids['FLAG_GOT_TM04_FROM_SABRINA'])
        assert g.follower()['pos']==(g.player()['pos'][0],g.player()['pos'][1]+1)
        g.emu.run(1,('down',));g.emu.run(16);g.emu.tap('a');g.finish_script(limit=1000)
        assert g.flag(ids['FLAG_GOT_TM04_FROM_SABRINA']) and g.follower() is not None
        print('PASS (diagnostic unclaimed-TM flag): restored Gym companion preserves the TM04 claim path.')
        won_save=g.save_cartridge();g.emu.close()
        g=StoryGame(a.rom,a.output);g.continue_cartridge(won_save)
        assert g.flag(ids['FLAG_BADGE06_GET']) and g.follower() is not None
        assert sum(o['graphics']==85 for o in g.objects())==1
        g.warp((3,19),7,33);g.set_var(0x4020,0)
        g.phase='after-gym-wild-intro';g.combined=True
        battle.enter_wild(g);g.advance_text(80)
        assert g.phase in g.captures
        battle.finish_battle(g)
        assert g.follower() is not None
        print('PASS: post-victory Save/Continue retains one Sabrina; ordinary wild intro restores combined artwork.')
        assert hashlib.sha256(a.rom.read_bytes()).hexdigest()==sha
        (a.output/'evidence.json').write_text(json.dumps({'rom_sha256':sha,'diagnostic_fixtures':True,
            'post_gym_captures':sorted(g.captures),'badge':True,'tm04':True,'reunion_persistent':True},indent=2))
    except BaseException:
        g.emu.screenshot(a.output/'failure.png')
        print('DIAGNOSTIC',g.map(),g.objects())
        raise
    finally:
        g.emu.close()


if __name__=='__main__':main()
