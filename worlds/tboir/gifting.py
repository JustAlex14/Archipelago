"""Archipelago Gifting (data version 3) for the Isaac client.

Used by the AP Character Lock companion mod:
- registers this slot's giftbox in the team's motherbox;
- forwards gifts received in the giftbox to the game ("ReceiveGifts") and removes them from the
  server once the game confirms it applied them ("GiftsReceived"), so a gift is never lost;
- sends gifts built by the game ("SendGift") to other players whose giftbox accepts them;
- tells the game which players can currently receive gifts ("GiftTargets").

Spec: https://github.com/agilbert1412/Archipelago.Gifting.Net/blob/main/Documentation/Gifting%20API.md
"""
from __future__ import annotations

import logging
import time
import typing
from uuid import uuid4

if typing.TYPE_CHECKING:
    from .client import IsaacContext

GIFT_DATA_VERSION = 3
MIN_GIFT_DATA_VERSION = 2      # older (v2, PascalCase) gifts are understood and can be sent
# Traits this game understands when receiving (used to fill desired_traits)
ACCEPTED_TRAITS = [
    "Damage", "Weapon", "Bomb", "Fire", "Metal", "Ore",
    "Mana", "Energy", "Drink", "Ice",
    "Speed", "Animal",
    "Light", "Tool", "Wood", "Stone",
    "Seed", "Fish", "Grass", "Fruit", "Vegetable", "Egg", "Currency", "Resource", "Material",
    "Heal", "Life", "Food", "Meat", "Cure", "Armor", "Buff", "Consumable", "Key",
]
RESEND_AFTER_SECONDS = 10.0
logger = logging.getLogger("Client")


def _get(d: dict, *names, default=None):
    """Reads a field in snake_case (v3) or PascalCase (v1/v2)."""
    for name in names:
        if name in d:
            return d[name]
    return default


def normalize_gift(gift_id: str, raw: dict) -> dict | None:
    if not isinstance(raw, dict):
        return None
    traits = []
    for t in _get(raw, "traits", "Traits", default=[]) or []:
        if not isinstance(t, dict):
            continue
        name = _get(t, "trait", "Trait")
        if not isinstance(name, str):
            continue
        traits.append({
            "trait": name,
            "quality": float(_get(t, "quality", "Quality", default=1.0) or 1.0),
            "duration": float(_get(t, "duration", "Duration", default=1.0) or 1.0),
        })
    try:
        amount = int(_get(raw, "amount", "Amount", default=1) or 1)
    except (TypeError, ValueError):
        amount = 1
    return {
        "id": str(_get(raw, "id", "ID", default=gift_id)),
        "item_name": str(_get(raw, "item_name", "ItemName", default="Gift")),
        "amount": max(1, amount),
        "traits": traits,
        "sender_slot": _get(raw, "sender_slot", "SenderSlot", default=0),
        "sender_team": _get(raw, "sender_team", "SenderTeam", default=0),
        "is_refund": bool(_get(raw, "is_refund", "IsRefund", default=False)),
    }


class GiftingManager:
    def __init__(self, ctx: "IsaacContext"):
        self.ctx = ctx
        self.reset()

    def reset(self) -> None:
        self.delivered: dict[str, float] = {}   # gift id -> time sent to the game (not confirmed yet)
        self.acked: set[str] = set()
        self.last_targets: list | None = None
        self.active = False

    # ------------------------------------------------------------------ keys
    @property
    def motherbox_key(self) -> str:
        return f"GiftBoxes;{self.ctx.team}"

    def giftbox_key(self, slot: int | None = None) -> str:
        return f"GiftBox;{self.ctx.team};{self.ctx.slot if slot is None else slot}"

    def enabled(self) -> bool:
        return bool(self.ctx.options.get("gifting", True))

    # ------------------------------------------------------------------ connection
    def on_connected(self) -> None:
        self.reset()
        if not self.enabled():
            return
        self.active = True
        # written in both v3 (snake_case) and v2 (PascalCase) names, so games on either version see it
        entry = {
            str(self.ctx.slot): {
                "is_open": True,
                "accepts_any_gift": True,
                "desired_traits": ACCEPTED_TRAITS,
                "minimum_gift_data_version": MIN_GIFT_DATA_VERSION,
                "maximum_gift_data_version": GIFT_DATA_VERSION,
                "IsOpen": True,
                "AcceptsAnyGift": True,
                "DesiredTraits": ACCEPTED_TRAITS,
                "MinimumGiftDataVersion": MIN_GIFT_DATA_VERSION,
                "MaximumGiftDataVersion": GIFT_DATA_VERSION,
            }
        }
        self._send([
            {"cmd": "Set", "key": self.motherbox_key, "default": {}, "want_reply": False,
             "operations": [{"operation": "default", "value": {}}, {"operation": "update", "value": entry}]},
            {"cmd": "Set", "key": self.giftbox_key(), "default": {}, "want_reply": False,
             "operations": [{"operation": "default", "value": {}}]},
        ])
        self.ctx.set_notify(self.motherbox_key, self.giftbox_key())

    def on_data(self, keys: typing.Iterable[str]) -> None:
        if not self.active:
            return
        keys = set(keys)
        if self.giftbox_key() in keys:
            self.deliver()
        if self.motherbox_key in keys:
            self.push_targets()

    # ------------------------------------------------------------------ receiving
    def pending_gifts(self) -> dict:
        box = self.ctx.stored_data.get(self.giftbox_key()) or {}
        return {gid: g for gid, g in box.items() if gid not in self.acked} if isinstance(box, dict) else {}

    def deliver(self, force: bool = False) -> None:
        """Sends the gifts waiting in our giftbox to the game (again if not confirmed in time)."""
        if not self.active or self.ctx.current_state != self.ctx.State.CONNECTED:
            return
        now = time.monotonic()
        gifts = []
        for gid, raw in self.pending_gifts().items():
            sent = self.delivered.get(gid)
            if force or sent is None or now - sent > RESEND_AFTER_SECONDS:
                gift = normalize_gift(gid, raw)
                if gift is None:
                    self.ack([gid])          # unreadable: remove it so it doesn't block the box
                    continue
                gift["sender_name"] = self.ctx.player_names.get(gift["sender_slot"], "Someone")
                gifts.append(gift)
                self.delivered[gid] = now
        if gifts:
            self.ctx.queue_mod_command("ReceiveGifts", gifts)

    def ack(self, gift_ids: list) -> None:
        """The game applied these gifts: remove them from our giftbox on the server."""
        ops = []
        for gid in gift_ids:
            gid = str(gid)
            if gid in self.acked:
                continue
            self.acked.add(gid)
            self.delivered.pop(gid, None)
            ops.append({"operation": "pop", "value": gid})
        if ops:
            self._send([{"cmd": "Set", "key": self.giftbox_key(), "default": {}, "want_reply": False,
                         "operations": ops}])

    # ------------------------------------------------------------------ sending
    def giftboxes(self) -> list[tuple[dict, str | None]]:
        """Every other player's giftbox: (target, reason it can't receive coins, or None)."""
        motherbox = self.ctx.stored_data.get(self.motherbox_key) or {}
        result = []
        if not isinstance(motherbox, dict):
            return result
        for slot_str, meta in motherbox.items():
            try:
                slot = int(slot_str)
            except ValueError:
                continue
            if slot == self.ctx.slot or not isinstance(meta, dict):
                continue
            slot_info = self.ctx.slot_info.get(slot)
            target = {
                "slot": slot,
                "name": self.ctx.player_names.get(slot, f"Player {slot}"),
                "game": slot_info.game if slot_info else "?",
            }
            low = _get(meta, "minimum_gift_data_version", "MinimumGiftDataVersion", default=1)
            high = _get(meta, "maximum_gift_data_version", "MaximumGiftDataVersion", default=1)
            versions = [v for v in (GIFT_DATA_VERSION, MIN_GIFT_DATA_VERSION) if low <= v <= high]
            accepts_any = _get(meta, "accepts_any_gift", "AcceptsAnyGift", default=False)
            desired = set(_get(meta, "desired_traits", "DesiredTraits", default=[]) or [])
            reason = None
            if not _get(meta, "is_open", "IsOpen", default=False):
                reason = "giftbox closed"
            elif not versions:
                reason = f"gift data version {low}-{high} not supported"
            elif not accepts_any and not ({"Currency", "Resource"} & desired):
                reason = "doesn't want coins"
            if not reason:
                target["version"] = versions[0]
            result.append((target, reason))
        return sorted(result, key=lambda t: t[0]["slot"])

    def targets(self) -> list[dict]:
        return [target for target, reason in self.giftboxes() if reason is None]

    def push_targets(self, force: bool = False) -> None:
        if self.ctx.current_state != self.ctx.State.CONNECTED:
            return
        targets = self.targets()
        if force or targets != self.last_targets:
            if targets != self.last_targets:
                self.log_giftboxes()
            self.last_targets = targets
            self.ctx.queue_mod_command("GiftTargets", targets)

    def log_giftboxes(self) -> None:
        boxes = self.giftboxes()
        if not boxes:
            logger.info("Gifting: no other player has opened a giftbox (their game must support gifting).")
            return
        for target, reason in boxes:
            state = "can receive coins" if reason is None else f"can't receive coins ({reason})"
            logger.info(f"Gifting: {target['name']} ({target['game']}) {state}")

    def send(self, payload: dict) -> None:
        """Builds and sends a gift requested by the game."""
        if not self.active or not isinstance(payload, dict):
            return
        receiver = payload.get("receiver_slot")
        allowed = {t["slot"]: t for t in self.targets()}
        if receiver not in allowed:
            self.ctx.queue_mod_command("GiftResult", {"ok": False, "request": payload.get("request")})
            return
        gift_id = str(uuid4())
        traits = [{"trait": str(t.get("trait")), "quality": float(t.get("quality", 1.0)),
                   "duration": float(t.get("duration", 1.0))}
                  for t in payload.get("traits", []) if isinstance(t, dict) and t.get("trait")]
        gift = {
            "id": gift_id,
            "item_name": str(payload.get("item_name", "Coin")),
            "amount": max(1, int(payload.get("amount", 1))),
            "item_value": int(payload.get("item_value", 0)),
            "traits": traits,
            "sender_slot": self.ctx.slot,
            "receiver_slot": receiver,
            "sender_team": self.ctx.team,
            "receiver_team": self.ctx.team,
            "is_refund": False,
        }
        if allowed[receiver].get("version") == 2:
            gift = {
                "ID": gift_id, "ItemName": gift["item_name"], "Amount": gift["amount"],
                "ItemValue": gift["item_value"],
                "Traits": [{"Trait": t["trait"], "Quality": t["quality"], "Duration": t["duration"]} for t in traits],
                "SenderSlot": self.ctx.slot, "ReceiverSlot": receiver,
                "SenderTeam": self.ctx.team, "ReceiverTeam": self.ctx.team, "IsRefund": False,
            }
        self._send([{"cmd": "Set", "key": self.giftbox_key(receiver), "default": {}, "want_reply": False,
                     "operations": [{"operation": "default", "value": {}},
                                    {"operation": "update", "value": {gift_id: gift}}]}])
        name = self.ctx.player_names.get(receiver, f"Player {receiver}")
        self.ctx.queue_mod_command("GiftResult", {"ok": True, "request": payload.get("request"),
                                                  "receiver_name": name})

    # ------------------------------------------------------------------ helpers
    def tick(self) -> None:
        if self.active:
            self.deliver()
            self.push_targets()

    def _send(self, msgs: list) -> None:
        import Utils
        Utils.async_start(self.ctx.send_msgs(msgs))
