import unittest
from .bases import TboiTestBase
from ..items import CHARACTER_KEYS, ITEM_KEYS, LOCKABLE_ITEMS, character_key


class TestNoCharacterLockOptions(TboiTestBase):
    """With the new options left at their defaults, nothing is added."""

    def test_no_keys_in_pool(self) -> None:
        names = self.item_names()
        for key in CHARACTER_KEYS + ITEM_KEYS:
            self.assertNotIn(key, names)


class TestCharacterKeys(TboiTestBase):
    options = {"character_keys": 34}

    def test_keys_in_pool(self) -> None:
        pool = [item.name for item in self.multiworld.itempool]
        for i in range(1, 35):
            self.assertEqual(pool.count(character_key(i)), 1)
        self.assertNotIn(character_key(35), pool)

    def test_keys_are_progression(self) -> None:
        self.assertTrue(self.world.create_item(character_key(1)).advancement)


class TestItemKeys(TboiTestBase):
    options = {"item_keys": {"Brimstone", "Sacred Heart"}}

    def test_item_keys_in_pool(self) -> None:
        names = self.item_names()
        self.assertIn("Item Key: Brimstone", names)
        self.assertIn("Item Key: Sacred Heart", names)
        self.assertNotIn("Item Key: Godhead", names)

    def test_every_lockable_item_has_a_key(self) -> None:
        for name in LOCKABLE_ITEMS:
            self.assertIn(f"Item Key: {name}", self.world.item_name_to_id)


class TestBossCharacterKeys(TboiTestBase):
    options = {
        "goals": {"Mother", "Mom"},
        "character_keys": 34,
        "boss_character_keys": {"Mother": [34], "Mom": [3, 20]},
    }

    def test_mother_needs_key_34(self) -> None:
        location = self.multiworld.get_location("Mother Reward #1", self.player)
        state = self.multiworld.get_all_state(False)
        self.assertTrue(location.can_reach(state))
        state.remove(self.world.create_item(character_key(34)))
        self.assertFalse(location.can_reach(state))

    def test_mom_needs_one_of_two_keys(self) -> None:
        location = self.multiworld.get_location("Defeat Mom", self.player)
        state = self.multiworld.get_all_state(False)
        state.remove(self.world.create_item(character_key(3)))
        self.assertTrue(location.can_reach(state))
        state.remove(self.world.create_item(character_key(20)))
        self.assertFalse(location.can_reach(state))


class TestCharacterKeyNames(unittest.TestCase):
    def test_names(self) -> None:
        self.assertEqual(character_key(1), "Magdalene (Character Key 1)")
        self.assertEqual(character_key(20), "Tainted Judas (Character Key 20)")
        self.assertEqual(character_key(33), "Tainted Jacob (Character Key 33)")
        self.assertEqual(len(set(CHARACTER_KEYS)), 60)

    def test_number_group(self) -> None:
        from .. import TboiWorld
        self.assertEqual(TboiWorld.item_name_groups["Character Key 1"], {character_key(1)})
