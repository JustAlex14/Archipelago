"""State of the AP Character Lock additions (Character Keys, boss characters, Item Keys) for the map tracker.

Kept free of kivy so it can be tested on its own. Names come from the server's data package, so keys named by
the generator ("Bael (Character Key 34)") show their character even if this computer has no names file.
"""
from __future__ import annotations

import re
import typing

KEY_PATTERN = re.compile(r"Character Key (\d+)")
ITEM_KEY_PREFIX = "Item Key: "


def key_number(item_name: str) -> int | None:
    match = KEY_PATTERN.search(item_name or "")
    return int(match.group(1)) if match else None


def display_name(item_name: str) -> str:
    """"Bael (Character Key 34)" -> "Bael"; an unnamed key keeps its name."""
    stripped = re.sub(r"\s*\(Character Key \d+\)$", "", item_name or "")
    return stripped or item_name


def game_item_names(ctx) -> dict[int, str]:
    try:
        return dict(ctx.item_names[ctx.game].items())
    except Exception:
        return {}


def key_names(ctx) -> dict[int, str]:
    """Character Key number -> item name, from the data package."""
    names: dict[int, str] = {}
    for name in game_item_names(ctx).values():
        number = key_number(name)
        if number is not None and number not in names:
            names[number] = name
    return names


def received_counts(ctx) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in getattr(ctx, "items_received", []):
        name = ctx.item_names.lookup_in_game(item.item, ctx.game)
        counts[name] = counts.get(name, 0) + 1
    return counts


def has_key(counts: dict[str, int], number: int) -> bool:
    return any(key_number(name) == number and amount > 0 for name, amount in counts.items())


def character_rows(ctx) -> list[tuple[int, str, bool]]:
    """(key number, character shown, unlocked) for every Character Key of this game."""
    total = int(ctx.options.get("character_keys", 0) or 0)
    if total <= 0:
        return []
    names = key_names(ctx)
    counts = received_counts(ctx)
    return [(n, display_name(names.get(n, f"Character Key {n}")), has_key(counts, n)) for n in range(1, total + 1)]


def boss_rules(ctx) -> dict[str, list[int]]:
    rules = ctx.options.get("boss_character_keys") or {}
    result: dict[str, list[int]] = {}
    if isinstance(rules, dict):
        for boss, numbers in rules.items():
            if isinstance(numbers, int):
                numbers = [numbers]
            if isinstance(numbers, (list, tuple)) and numbers:
                result[boss] = [int(n) for n in numbers]
    return result


def boss_rows(ctx) -> list[tuple[str, list[str], bool]]:
    """(boss, characters that count, one of them unlocked)."""
    names = key_names(ctx)
    counts = received_counts(ctx)
    rows = []
    for boss, numbers in boss_rules(ctx).items():
        characters = [display_name(names.get(n, f"Character Key {n}")) for n in numbers]
        rows.append((boss, characters, any(has_key(counts, n) for n in numbers)))
    return rows


def boss_ok(ctx, boss: str, counts: dict[str, int] | None = None) -> bool:
    """False while none of the characters a boss needs is unlocked (the boss's rewards are out of logic)."""
    numbers = boss_rules(ctx).get(boss)
    if not numbers:
        return True
    counts = received_counts(ctx) if counts is None else counts
    return any(has_key(counts, n) for n in numbers)


def item_key_rows(ctx) -> list[tuple[str, bool]]:
    """(collectible, unlocked) for every item locked by the item_keys option."""
    counts = received_counts(ctx)
    return [(name, counts.get(ITEM_KEY_PREFIX + name, 0) > 0) for name in sorted(ctx.options.get("item_keys") or [])]


def is_lock_item(item_name: str) -> bool:
    return key_number(item_name) is not None or item_name.startswith(ITEM_KEY_PREFIX)


if typing.TYPE_CHECKING:
    from .client import IsaacContext  # noqa: F401
