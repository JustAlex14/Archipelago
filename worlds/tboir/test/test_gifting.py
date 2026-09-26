import unittest
from enum import Enum
from types import SimpleNamespace

from ..gifting import GiftingManager, normalize_gift
from .bases import TboiTestBase


class TestNormalizeGift(unittest.TestCase):
    def test_v3_gift(self):
        gift = normalize_gift("g1", {"id": "g1", "item_name": "Coffee", "amount": 2,
                                     "traits": [{"trait": "Speed", "quality": 1.5}],
                                     "sender_slot": 2, "is_refund": False})
        self.assertEqual(gift["item_name"], "Coffee")
        self.assertEqual(gift["amount"], 2)
        self.assertEqual(gift["traits"][0], {"trait": "Speed", "quality": 1.5, "duration": 1.0})
        self.assertEqual(gift["sender_slot"], 2)

    def test_v2_gift(self):
        gift = normalize_gift("g2", {"ID": "g2", "ItemName": "Iron Bar", "Amount": 5,
                                     "Traits": [{"Trait": "Metal", "Quality": 1}], "SenderSlot": 3,
                                     "IsRefund": True})
        self.assertEqual((gift["id"], gift["item_name"], gift["amount"]), ("g2", "Iron Bar", 5))
        self.assertEqual(gift["traits"][0]["trait"], "Metal")
        self.assertTrue(gift["is_refund"])

    def test_bad_gift(self):
        self.assertIsNone(normalize_gift("x", "not a dict"))
        self.assertEqual(normalize_gift("x", {"amount": "?"})["amount"], 1)


class TestTargets(unittest.TestCase):
    def make(self, motherbox):
        class State(Enum):
            CONNECTED = 1
        ctx = SimpleNamespace(team=0, slot=1, options={"gifting": 1}, State=State,
                              current_state=State.CONNECTED,
                              player_names={1: "Alex", 2: "Lucas", 3: "Marie", 4: "Old"},
                              slot_info={2: SimpleNamespace(game="Stardew Valley")},
                              stored_data={"GiftBoxes;0": motherbox})
        return GiftingManager(ctx)

    def test_targets(self):
        gm = self.make({
            "1": {"is_open": True, "accepts_any_gift": True, "minimum_gift_data_version": 3, "maximum_gift_data_version": 3},
            "2": {"is_open": True, "accepts_any_gift": True, "minimum_gift_data_version": 2, "maximum_gift_data_version": 3},
            "3": {"is_open": True, "accepts_any_gift": False, "desired_traits": ["Fish"],
                  "minimum_gift_data_version": 3, "maximum_gift_data_version": 3},
            "4": {"IsOpen": True, "AcceptsAnyGift": True, "MinimumGiftDataVersion": 1, "MaximumGiftDataVersion": 2},
        })
        self.assertEqual(gm.targets(), [{"slot": 2, "name": "Lucas", "game": "Stardew Valley", "version": 3},
                                        {"slot": 4, "name": "Old", "game": "?", "version": 2}])
        reasons = {t["slot"]: r for t, r in gm.giftboxes()}
        self.assertEqual(reasons[3], "doesn't want coins")

    def test_v1_only_box(self):
        gm = self.make({"2": {"IsOpen": True, "AcceptsAnyGift": True,
                              "MinimumGiftDataVersion": 1, "MaximumGiftDataVersion": 1}})
        self.assertEqual(gm.targets(), [])
        self.assertIn("not supported", gm.giftboxes()[0][1])


class TestGiftingOption(TboiTestBase):
    def test_slot_data(self):
        self.assertIn("gifting", self.world.fill_slot_data()["options"])


class TestSendVersions(unittest.TestCase):
    def test_v2_gift_format(self):
        class State(Enum):
            CONNECTED = 1
        sent = []
        ctx = SimpleNamespace(team=0, slot=1, options={"gifting": True}, State=State,
                              current_state=State.CONNECTED, player_names={1: "Alex", 2: "Lucas", 3: "Marie"},
                              slot_info={}, queue_mod_command=lambda t, p: sent.append((t, p)),
                              stored_data={"GiftBoxes;0": {
                                  "2": {"IsOpen": True, "AcceptsAnyGift": True,
                                        "MinimumGiftDataVersion": 2, "MaximumGiftDataVersion": 2},
                                  "3": {"is_open": True, "accepts_any_gift": True,
                                        "minimum_gift_data_version": 3, "maximum_gift_data_version": 3}}})
        gm = GiftingManager(ctx)
        gm.active = True
        msgs = []
        gm._send = msgs.extend
        gm.send({"receiver_slot": 2, "item_name": "Coin", "amount": 5, "traits": [{"trait": "Currency"}], "request": 1})
        gm.send({"receiver_slot": 3, "item_name": "Coin", "amount": 5, "traits": [{"trait": "Currency"}], "request": 2})
        v2 = list(msgs[0]["operations"][1]["value"].values())[0]
        v3 = list(msgs[1]["operations"][1]["value"].values())[0]
        self.assertEqual((v2["ItemName"], v2["Amount"], v2["Traits"][0]["Trait"]), ("Coin", 5, "Currency"))
        self.assertEqual((v3["item_name"], v3["amount"], v3["traits"][0]["trait"]), ("Coin", 5, "Currency"))
        self.assertTrue(all(p["ok"] for t, p in sent if t == "GiftResult"))
