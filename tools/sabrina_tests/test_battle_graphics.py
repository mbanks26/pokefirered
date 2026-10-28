#!/usr/bin/env python3
"""Protect original trainer artwork and validate the GBA companion asset."""
import io
from pathlib import Path
import subprocess
import unittest
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
BASE='62c94ca0a4d3625f28f22d5bda0d0ed0cb8b3096'

def original(path):return subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT)

class CombinedBackSpriteTests(unittest.TestCase):
    def test_original_assets_and_throw_animation_preserved(self):
        for name in ('graphics/trainers/back_pics/red_back_pic.png',
                     'graphics/trainers/back_pics/leaf_back_pic.png',
                     'graphics/trainers/palettes/red_back_pic.pal'):
            self.assertEqual((ROOT/name).read_text(),original(name).decode().replace('\r\n','\n'),name) if name.endswith('.pal') else self.assertEqual((ROOT/name).read_bytes(),original(name),name)
        path='src/data/trainer_graphics/back_pic_anims.h'
        # The addition is an extra reference to Red's original animation table.
        before=original(path).decode()
        after=(ROOT/path).read_text()
        self.assertEqual(after.replace('    sBackAnims_OldMan,\n    sBackAnims_Red\n','    sBackAnims_OldMan\n'),before)

    def test_five_frames_palette_and_every_original_red_pixel(self):
        red=Image.open(ROOT/'graphics/trainers/back_pics/red_back_pic.png')
        pair=Image.open(ROOT/'graphics/trainers/back_pics/red_sabrina_back_pic.png')
        self.assertEqual(red.mode,'P');self.assertEqual(pair.mode,'P')
        self.assertEqual(pair.size,(64,320))
        self.assertEqual(pair.getpalette()[:48],red.getpalette()[:48])
        self.assertEqual(pair.info.get('transparency'),0)
        self.assertLessEqual(max(pair.tobytes()),15)
        observer=Image.open(ROOT/'graphics/trainers/back_pics/sabrina_observer.png')
        self.assertEqual(observer.size,(30,58))
        self.assertEqual(observer.getpalette()[:48],red.getpalette()[:48])
        for frame in range(5):
            added=0
            for y in range(frame*64,(frame+1)*64):
                for x in range(64):
                    r,p=red.getpixel((x,y)),pair.getpixel((x,y))
                    if r:
                        self.assertEqual(p,r,(frame,x,y))
                    else:
                        local_y=y-frame*64-2
                        expected=observer.getpixel((x,local_y)) if x<30 and 0<=local_y<58 else 0
                        self.assertEqual(p,expected,('observer moved',frame,x,y))
                        if p: added+=1
            self.assertGreater(added,350,('Sabrina missing',frame,added))

    def test_one_64x64_frame_uses_only_2048_bytes(self):
        data=(ROOT/'graphics/trainers/back_pics/red_sabrina_back_pic.4bpp').read_bytes()
        self.assertEqual(len(data),5*0x800)
        syms={v[3]:int(v[0],16) for line in (ROOT/'pokefirered_rev1.sym').read_text().splitlines() if len(v:=line.split())==4}
        rom=(ROOT/'pokefirered_rev1.gba').read_bytes()
        offset=syms['gTrainerBackPic_RedSabrina']-0x08000000
        self.assertEqual(rom[offset:offset+len(data)],data)
        self.assertEqual(rom[0xbc],1)

    def test_previous_follower_rom_is_untouched(self):
        import hashlib
        p=Path('/workspace/artifacts/FireRed-Rev1-Sabrina-Follower-Test.gba')
        self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),
            '37f831fefc0cd1ac2976fc5f95311de48a7b4499dd8f6efa5e1e184b3c5d2c4b')

if __name__=='__main__':unittest.main(verbosity=2)
