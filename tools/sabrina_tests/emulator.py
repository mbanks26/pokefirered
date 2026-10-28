"""Small headless libretro frontend for actual-ROM regression checks.

Uses a locally installed mGBA libretro core, without a system emulator UI.
No ROM or copyrighted BIOS is included. mGBA's built-in BIOS is used.
"""
from __future__ import annotations

import ctypes as C
from dataclasses import dataclass
from pathlib import Path
import struct

DEFAULT_CORE = Path('/workspace/.pokefirered-env/sysroot/usr/lib/x86_64-linux-gnu/libretro/mgba_libretro.so')
KEYS = {'b': 0, 'select': 2, 'start': 3, 'up': 4, 'down': 5, 'left': 6,
        'right': 7, 'a': 8, 'l': 10, 'r': 11}


class GameInfo(C.Structure):
    _fields_ = [('path', C.c_char_p), ('data', C.c_void_p),
                ('size', C.c_size_t), ('meta', C.c_char_p)]


class MemoryDescriptor(C.Structure):
    _fields_ = [('flags', C.c_uint64), ('ptr', C.c_void_p),
                ('offset', C.c_size_t), ('start', C.c_size_t),
                ('select', C.c_size_t), ('disconnect', C.c_size_t),
                ('length', C.c_size_t), ('addrspace', C.c_char_p)]


class MemoryMap(C.Structure):
    _fields_ = [('descriptors', C.POINTER(MemoryDescriptor)), ('count', C.c_uint)]


class Variable(C.Structure):
    _fields_ = [('key', C.c_char_p), ('value', C.c_char_p)]


@dataclass
class Region:
    start: int
    length: int
    pointer: int
    offset: int
    select: int
    disconnect: int


class Emulator:
    """One mGBA instance. The libretro ABI has process-global core state."""

    def __init__(self, rom: Path, core: Path = DEFAULT_CORE):
        self.lib = C.CDLL(str(core))
        self.pressed = set()
        self.frame = 0
        self.pixels = None
        self.pixel_format = 0
        self.regions = []
        self.directory = b'/tmp'
        self.options = {
            b'mgba_use_bios': b'OFF',
            b'mgba_skip_bios': b'ON',
            b'mgba_frameskip': b'disabled',
            b'mgba_solar_sensor_level': b'0',
            b'mgba_allow_opposing_directions': b'no',
        }
        self._callbacks = []
        self._set_callback('retro_set_environment', C.CFUNCTYPE(C.c_bool, C.c_uint, C.c_void_p), self._environment)
        self._set_callback('retro_set_video_refresh', C.CFUNCTYPE(None, C.c_void_p, C.c_uint, C.c_uint, C.c_size_t), self._video)
        self._set_callback('retro_set_audio_sample', C.CFUNCTYPE(None, C.c_int16, C.c_int16), lambda left, right: None)
        self._set_callback('retro_set_audio_sample_batch', C.CFUNCTYPE(C.c_size_t, C.c_void_p, C.c_size_t), lambda data, frames: frames)
        self._set_callback('retro_set_input_poll', C.CFUNCTYPE(None), lambda: None)
        self._set_callback('retro_set_input_state', C.CFUNCTYPE(C.c_int16, C.c_uint, C.c_uint, C.c_uint, C.c_uint), self._input)
        self.lib.retro_init()
        data = Path(rom).read_bytes()
        self._rom_buffer = C.create_string_buffer(data)
        self._rom_path = str(Path(rom).resolve()).encode()
        game = GameInfo(self._rom_path, C.cast(self._rom_buffer, C.c_void_p), len(data), None)
        self.lib.retro_load_game.argtypes = [C.POINTER(GameInfo)]
        self.lib.retro_load_game.restype = C.c_bool
        if not self.lib.retro_load_game(C.byref(game)):
            raise RuntimeError('mGBA rejected the ROM')
        self.lib.retro_serialize_size.restype = C.c_size_t
        self.lib.retro_serialize.argtypes = [C.c_void_p, C.c_size_t]
        self.lib.retro_serialize.restype = C.c_bool
        self.lib.retro_unserialize.argtypes = [C.c_void_p, C.c_size_t]
        self.lib.retro_unserialize.restype = C.c_bool
        self.lib.retro_get_memory_data.argtypes = [C.c_uint]
        self.lib.retro_get_memory_data.restype = C.c_void_p
        self.lib.retro_get_memory_size.argtypes = [C.c_uint]
        self.lib.retro_get_memory_size.restype = C.c_size_t

    def _set_callback(self, name, signature, function):
        callback = signature(function)
        self._callbacks.append(callback)
        setter = getattr(self.lib, name)
        setter.argtypes = [signature]
        setter(callback)

    def _environment(self, command, data):
        command &= ~0x10000  # experimental API marker
        if command == 3:  # GET_CAN_DUPE
            C.cast(data, C.POINTER(C.c_bool))[0] = True
            return True
        if command in (9, 30, 31):  # SYSTEM, CONTENT, SAVE directory
            C.cast(data, C.POINTER(C.c_char_p))[0] = self.directory
            return True
        if command == 10:  # SET_PIXEL_FORMAT
            value = C.cast(data, C.POINTER(C.c_int))[0]
            if value not in (0, 1, 2):
                return False
            self.pixel_format = value
            return True
        if command == 15:  # GET_VARIABLE
            variable = C.cast(data, C.POINTER(Variable)).contents
            value = self.options.get(variable.key)
            if value is None:
                return False
            variable.value = value
            return True
        if command == 17:  # GET_VARIABLE_UPDATE
            C.cast(data, C.POINTER(C.c_bool))[0] = False
            return True
        if command == 36:  # SET_MEMORY_MAPS
            memory = C.cast(data, C.POINTER(MemoryMap)).contents
            self.regions = [Region(d.start, d.length, d.ptr, d.offset, d.select, d.disconnect)
                            for d in memory.descriptors[:memory.count] if d.ptr and d.length]
            return True
        if command == 39:  # GET_LANGUAGE
            C.cast(data, C.POINTER(C.c_uint))[0] = 0
            return True
        if command == 51:  # GET_INPUT_BITMASKS
            return False
        if command == 52:  # GET_CORE_OPTIONS_VERSION
            C.cast(data, C.POINTER(C.c_uint))[0] = 0
            return True
        return command in (11, 16, 18, 32, 35, 42, 44, 63)

    def _video(self, data, width, height, pitch):
        if data and data != C.c_void_p(-1).value:
            self.pixels = (width, height, pitch, C.string_at(data, pitch * height))

    def _input(self, port, device, index, key):
        return int(port == 0 and device == 1 and index == 0 and key in self.pressed)

    def run(self, frames, keys=()):
        self.pressed = {KEYS[key] if isinstance(key, str) else key for key in keys}
        for _ in range(frames):
            self.lib.retro_run()
            self.frame += 1
        self.pressed = set()

    def tap(self, key, hold=2, release=12):
        self.run(hold, (key,))
        self.run(release)

    def _pointer(self, address, length):
        for region in self.regions:
            if region.start <= address and address + length <= region.start + region.length:
                return region.pointer + region.offset + address - region.start
        raise ValueError(f'Unmapped emulator address {address:#x}+{length:#x}')

    def read(self, address, length):
        return C.string_at(self._pointer(address, length), length)

    def write(self, address, data):
        C.memmove(self._pointer(address, len(data)), data, len(data))

    def u8(self, address):
        return self.read(address, 1)[0]

    def u16(self, address):
        return struct.unpack('<H', self.read(address, 2))[0]

    def u32(self, address):
        return struct.unpack('<I', self.read(address, 4))[0]

    def save_state(self):
        size = self.lib.retro_serialize_size()
        data = C.create_string_buffer(size)
        if not self.lib.retro_serialize(data, size):
            raise RuntimeError('Cannot serialize emulator state')
        return data.raw

    def load_state(self, state):
        data = C.create_string_buffer(state)
        if not self.lib.retro_unserialize(data, len(state)):
            raise RuntimeError('Cannot restore emulator state')

    def screenshot(self, path):
        from PIL import Image
        if self.pixels is None:
            raise RuntimeError('No video frame produced')
        width, height, pitch, pixels = self.pixels
        if self.pixel_format == 1:
            image = Image.frombytes('RGB', (width, height), pixels, 'raw', 'BGRX', pitch)
        else:
            image = Image.new('RGB', (width, height))
            rows = []
            for y in range(height):
                for x in range(width):
                    pixel = struct.unpack_from('<H', pixels, y * pitch + 2 * x)[0]
                    if self.pixel_format == 2:
                        rows.append((((pixel >> 11) & 31) * 255 // 31, ((pixel >> 5) & 63) * 255 // 63, (pixel & 31) * 255 // 31))
                    else:
                        rows.append((((pixel >> 10) & 31) * 255 // 31, ((pixel >> 5) & 31) * 255 // 31, (pixel & 31) * 255 // 31))
            image.putdata(rows)
        image.save(path)

    def close(self):
        self.lib.retro_unload_game()
        self.lib.retro_deinit()
