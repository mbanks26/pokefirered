#!/usr/bin/env python3
"""Repeatable source/ROM integration contracts for the Sabrina follower.

Run from any directory with Python 3 (standard library only). This suite checks
preservation, persistent state allocation, event wiring, text fit and the built
Rev 1 ROM header. It does not simulate movement; use test_follower_rom.py for
actual-ROM emulator checks.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]
BASELINE = "1a2c7eb374849285f49bf4b57538c938ee77ce22"
ROM = ROOT / "pokefirered_rev1.gba"


def read(path: str) -> str:
    return (ROOT / path).read_text()


def baseline(path: str) -> str:
    return subprocess.check_output(
        ["git", "show", f"{BASELINE}:{path}"], cwd=ROOT, text=True)


def text_blocks(source: str) -> dict[str, str]:
    return dict(re.findall(r"^(\w+)::\n((?:\s*\.string[^\n]+\n?)+)", source, re.M))


def joined_text(block: str) -> str:
    return "".join(re.findall(r'\.string "(.*)"', block))


def constants(names: list[str], header: str) -> dict[str, int]:
    source = f'#include "{header}"\n' + "\n".join(names)
    values = subprocess.check_output(
        ["cc", "-E", "-P", "-Iinclude", "-x", "c", "-"],
        cwd=ROOT, input=source, text=True).strip().splitlines()
    if len(values) != len(names):
        raise AssertionError(f"Unexpected constant preprocessing: {values}")
    result = {}
    for name, value in zip(names, values):
        # Only integer expressions emitted from the constants header are allowed.
        if not re.fullmatch(r"[-0-9a-fA-FxX()+ \t]+", value):
            raise AssertionError(f"Unresolved constant {name}: {value}")
        result[name] = eval(value, {"__builtins__": {}})
    return result


def charmap() -> dict[str, int]:
    return {
        match[1].replace(r"\'", "'"): int(match[2], 16)
        for match in re.finditer(r"^'(.+)'\s*=\s*([0-9A-F]{2})\s*$",
                                 read("charmap.txt"), re.M)
    }


def symbols() -> dict[str, int]:
    result = {}
    for line in ROM.with_suffix(".sym").read_text().splitlines():
        parts = line.split()
        if len(parts) == 4:
            result[parts[3]] = int(parts[0], 16)
    return result


class PreservationTests(unittest.TestCase):
    def test_all_37_original_shared_dialogue_blocks_preserved(self):
        old = text_blocks(baseline("data/text/sabrina.inc"))
        current = text_blocks(read("data/text/sabrina.inc"))
        self.assertEqual(len(old), 37)
        for label, block in old.items():
            with self.subTest(label=label):
                self.assertIn(label, current)
                self.assertEqual(current[label].rstrip(), block.rstrip())
        self.assertGreaterEqual(len(current), 45)

    def test_gym_battle_rewards_and_dialogue_unchanged(self):
        for path in ("data/maps/SaffronCity_Gym/scripts.inc",
                     "data/maps/SaffronCity_Gym/text.inc",
                     "data/maps/SaffronCity_Gym/map.json"):
            with self.subTest(path=path):
                self.assertEqual(read(path), baseline(path))

    def test_oak_blue_starter_and_pokedex_progression_unchanged(self):
        for path in ("data/maps/PalletTown/scripts.inc",
                     "data/maps/PalletTown_ProfessorOaksLab/scripts.inc",
                     "src/new_game.c", "src/battle_setup.c", "include/global.h",
                     "include/global.fieldmap.h"):
            with self.subTest(path=path):
                self.assertEqual(read(path), baseline(path))

    def test_twin_canon_and_original_female_selection(self):
        path = "data/maps/PalletTown_PlayersHouse_1F/text.inc"
        current = text_blocks(read(path))
        previous = text_blocks(baseline(path))
        male = joined_text(current[
            "PalletTown_PlayersHouse_1F_Text_AllBoysLeaveOakLookingForYou"])
        self.assertIn("twin sister LEAF", male)
        self.assertIn(r"journey three\lmonths ago", male)
        female = "PalletTown_PlayersHouse_1F_Text_AllGirlsLeaveOakLookingForYou"
        self.assertEqual(current[female], previous[female])


class EventIntegrationTests(unittest.TestCase):
    def test_active_flag_persistent_and_unused_in_baseline(self):
        values = constants(["FLAG_SABRINA_FOLLOWER_ACTIVE", "TEMP_FLAGS_END"],
                           "constants/flags.h")
        self.assertEqual(values["FLAG_SABRINA_FOLLOWER_ACTIVE"], 0x20)
        self.assertLess(values["TEMP_FLAGS_END"], 0x20)
        self.assertRegex(baseline("include/constants/flags.h"),
                         r"#define\s+FLAG_0x020\s+0x020\b")
        references = subprocess.check_output(
            ["git", "grep", "-n", "FLAG_0x020", BASELINE],
            cwd=ROOT, text=True).splitlines()
        self.assertEqual(len(references), 1, references)
        self.assertIn("include/constants/flags.h:", references[0])

    def test_stationary_maps_only_change_sabrina_hide_flag(self):
        hidden = []
        for path in sorted((ROOT / "data/maps").glob("*/map.json")):
            current = json.loads(path.read_text())
            # New Leaf NPCs append to the protected native/Sabrina templates.
            current["object_events"] = [obj for obj in current["object_events"]
                                        if obj.get("graphics_id") != "OBJ_EVENT_GFX_LEAF_NPC"]
            copies = [obj for obj in current["object_events"]
                      if obj.get("graphics_id") == "OBJ_EVENT_GFX_SABRINA"]
            if not copies or path.parent.name == "SaffronCity_Gym":
                continue
            relative = str(path.relative_to(ROOT))
            old = json.loads(baseline(relative))
            for obj in copies:
                self.assertEqual(obj["flag"], "FLAG_SABRINA_FOLLOWER_ACTIVE")
                obj["flag"] = "0"
            self.assertEqual(current, old, relative)
            hidden.append(relative)
        self.assertEqual(len(hidden), 12, hidden)

    def test_reserved_dynamic_id_not_consumed_by_map_template(self):
        value = constants(["LOCALID_SABRINA_FOLLOWER"],
                          "constants/event_objects.h")["LOCALID_SABRINA_FOLLOWER"]
        self.assertEqual(value, 254)
        header = read("include/constants/event_objects.h")
        owners = re.findall(r"^#define\s+(LOCALID_\w+)\s+254\b", header, re.M)
        self.assertEqual(owners, ["LOCALID_SABRINA_FOLLOWER"])
        for path in (ROOT / "data/maps").glob("*/map.json"):
            for obj in json.loads(path.read_text())["object_events"]:
                self.assertNotIn(str(obj.get("local_id", "")),
                                 ("254", "LOCALID_SABRINA_FOLLOWER"), str(path))

    def test_join_event_and_new_references_resolve(self):
        script = read("data/scripts/sabrina.inc")
        label_list = re.findall(r"^(\w+)::?", script, re.M)
        self.assertEqual(len(label_list), len(set(label_list)))
        labels = set(label_list)
        texts = set(text_blocks(read("data/text/sabrina.inc")))
        self.assertIn("Sabrina_EventScript_Companion", labels)
        self.assertIn("Sabrina_EventScript_Join", labels)
        for number, line in enumerate(script.splitlines(), 1):
            line = line.split("@", 1)[0].strip()
            if not line:
                continue
            parts = line.split(None, 1)
            command = parts[0]
            args = parts[1] if len(parts) == 2 else ""
            if command.startswith("goto") or command.startswith("call"):
                target = args.split(",")[-1].strip()
                self.assertIn(target, labels, f"line {number}: {line}")
            elif command == "msgbox":
                self.assertIn(args.split(",")[0].strip(), texts,
                              f"line {number}: {line}")
        join = script.split("Sabrina_EventScript_StartCompanion::", 1)[1].split("\n\n", 1)[0]
        self.assertLess(join.index("closemessage"), join.index("setflag"))
        self.assertLess(join.index("setflag FLAG_SABRINA_FOLLOWER_ACTIVE"),
                        join.index("special StartSabrinaFollower"))
        self.assertRegex(join, r"special StartSabrinaFollower\s+release\s+end")

    def test_special_appended_without_changing_old_indices(self):
        special_names = lambda source: re.findall(r"^\s*def_special\s+(\w+)", source, re.M)
        old = special_names(baseline("data/specials.inc"))
        current = special_names(read("data/specials.inc"))
        self.assertEqual(current[:len(old)], old)
        self.assertEqual(current[len(old):], ["StartSabrinaFollower", "StageSabrinaForLeafScene", "EndSabrinaLeafScene"])
        self.assertEqual(current.count("StartSabrinaFollower"), 1)

    def test_follower_does_not_mutate_party_or_unrelated_flags(self):
        source = re.sub(r"//[^\n]*|/\*.*?\*/", "", read("src/sabrina_follower.c"), flags=re.S)
        self.assertNotRegex(source, r"\b(?:gPlayerParty|gPlayerPartyCount|gEnemyParty|CreateMon|"
                            r"SetMonData|AddEnemyMonToPlayerParty|GiveMonToPlayer)\b")
        for argument in re.findall(r"\b(?:FlagSet|FlagClear)\(([^)]+)\)", source):
            self.assertEqual(argument.strip(), "FLAG_SABRINA_FOLLOWER_ACTIVE")


class DialogueFitTests(unittest.TestCase):
    def test_new_companion_text_fits_real_message_box_with_letter_spacing(self):
        previous = text_blocks(baseline("data/text/sabrina.inc"))
        current = text_blocks(read("data/text/sabrina.inc"))
        mapping = charmap()
        font_source = read("src/text.c")
        fonts = {}
        for font in ("Normal", "Male", "Female"):
            body = re.search(r"sFont" + font + r"LatinGlyphWidths\[\]\s*=\s*\{(.*?)\};",
                             font_source, re.S)[1]
            fonts[font] = [int(value) for value in re.findall(r"\d+", body)]
        printer = read("src/new_menu_helpers.c")
        self.assertRegex(printer, r"printer\.letterSpacing\s*=\s*1;")
        new_labels = sorted(current.keys() - previous.keys())
        self.assertGreaterEqual(len(new_labels), 8)
        for label in new_labels:
            text = joined_text(current[label])
            self.assertTrue(text.endswith("$"), label)
            self.assertEqual(text.count("$"), 1, label)
            # The longest player name has seven characters; W is a wide letter.
            text = text[:-1].replace("{PLAYER}", "W" * 7)
            self.assertNotRegex(text, r"\{[^}]+\}", label)
            for page in text.split(r"\p"):
                lines = page.split(r"\n")
                self.assertLessEqual(len(lines), 2, label)
                for index, line in enumerate(lines):
                    for font, widths in fonts.items():
                        width = sum(widths[mapping[letter]] + 1 for letter in line)
                        # 26 tiles = 208px; reserve 8px on the lower line for arrow.
                        limit = 208 if index == 0 else 200
                        with self.subTest(label=label, line=line, font=font):
                            self.assertLessEqual(width, limit)


@unittest.skipUnless(ROM.exists() and ROM.with_suffix(".sym").exists(),
                     "Build pokefirered_rev1.gba and .sym for artifact checks")
class BuiltRomTests(unittest.TestCase):
    def test_revision_one_and_gba_header_checksum(self):
        rom = ROM.read_bytes()
        self.assertEqual(len(rom), 16 * 1024 * 1024)
        self.assertEqual(rom[0xAC:0xB0], b"BPRE")
        self.assertEqual(rom[0xBC], 1)
        self.assertEqual(rom[0xBD], (-sum(rom[0xA0:0xBD]) - 0x19) & 0xFF)

    def test_mothers_twin_dialogue_is_in_the_assembled_rom(self):
        mapping = charmap()
        label = "PalletTown_PlayersHouse_1F_Text_AllBoysLeaveOakLookingForYou"
        address = symbols()[label] - 0x08000000
        rom = ROM.read_bytes()
        end = rom.index(b"\xFF", address)
        message = rom[address:end]
        encode = lambda text: bytes(mapping[character] for character in text)
        self.assertIn(encode("twin sister LEAF"), message)
        self.assertIn(encode("journey three") + b"\xFA" + encode("months ago"), message)


if __name__ == "__main__":
    unittest.main(verbosity=2)
