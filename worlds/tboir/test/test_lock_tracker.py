import unittest
from types import SimpleNamespace

from .. import lock_tracker

GAME = "The Binding of Isaac Repentance"
NAMES = {1: "Magdalene (Character Key 1)", 2: "Cain (Character Key 2)", 34: "Bael (Character Key 34)",
         35: "Character Key 35", 100: "Item Key: Brimstone", 101: "Item Key: Sacred Heart", 200: "1-UP"}


class Names:
    def __getitem__(self, game):
        return NAMES

    def lookup_in_game(self, code, game=None):
        return NAMES[code]


def make_ctx(received, **options):
    base = {"character_keys": 35, "boss_character_keys": {"Mom": (34,), "Mother": [2, 35]},
            "item_keys": ["Sacred Heart", "Brimstone"]}
    base.update(options)
    return SimpleNamespace(game=GAME, options=base, item_names=Names(),
                           items_received=[SimpleNamespace(item=code) for code in received])


class TestLockTracker(unittest.TestCase):
    def test_characters(self):
        rows = lock_tracker.character_rows(make_ctx([1, 34, 200]))
        self.assertEqual(len(rows), 35)
        self.assertEqual(rows[0], (1, "Magdalene", True))
        self.assertEqual(rows[1], (2, "Cain", False))
        self.assertEqual(rows[33], (34, "Bael", True))
        self.assertEqual(rows[34], (35, "Character Key 35", False))
        self.assertEqual(lock_tracker.character_rows(make_ctx([], character_keys=0)), [])

    def test_bosses(self):
        ctx = make_ctx([34])
        self.assertTrue(lock_tracker.boss_ok(ctx, "Mom"))
        self.assertFalse(lock_tracker.boss_ok(ctx, "Mother"))
        self.assertTrue(lock_tracker.boss_ok(ctx, "Satan"))
        rows = dict((boss, (names, ok)) for boss, names, ok in lock_tracker.boss_rows(ctx))
        self.assertEqual(rows["Mom"], (["Bael"], True))
        self.assertEqual(rows["Mother"], (["Cain", "Character Key 35"], False))

    def test_item_keys(self):
        self.assertEqual(lock_tracker.item_key_rows(make_ctx([100])),
                         [("Brimstone", True), ("Sacred Heart", False)])

    def test_lock_items(self):
        self.assertTrue(lock_tracker.is_lock_item("Bael (Character Key 34)"))
        self.assertTrue(lock_tracker.is_lock_item("Item Key: Brimstone"))
        self.assertFalse(lock_tracker.is_lock_item("1-UP"))
