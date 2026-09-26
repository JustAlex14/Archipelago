from .game_data import data

# Items added by this fork for the AP Character Lock companion mod.
# Always appended at the END of the list so existing item IDs never change.
CHARACTER_KEY_COUNT = 60

# Keys 1-33 unlock the vanilla characters when the mod's LOCK_VANILLA is on (the default), in this order.
VANILLA_KEY_CHARACTERS = [
    "Magdalene", "Cain", "Judas", "Blue Baby", "Eve", "Samson", "Azazel", "Lazarus", "Eden", "The Lost",
    "Lilith", "Keeper", "Apollyon", "The Forgotten", "Bethany", "Jacob & Esau", "Tainted Isaac",
    "Tainted Magdalene", "Tainted Cain", "Tainted Judas", "Tainted Blue Baby", "Tainted Eve", "Tainted Samson",
    "Tainted Azazel", "Tainted Lazarus", "Tainted Eden", "Tainted Lost", "Tainted Lilith", "Tainted Keeper",
    "Tainted Apollyon", "Tainted Forgotten", "Tainted Bethany", "Tainted Jacob",
]
# Optional file next to host.yaml (C:\ProgramData\Archipelago) naming the other keys, one per line:
#     34 = Bael
#     35 = Tainted Bael
# "1 = none" removes a name. Only the person who generates needs it: the names are part of the generated game.
CHARACTER_NAMES_FILE = "tboir_character_names.txt"


def _read_character_names() -> dict[int, str]:
    names: dict[int, str] = dict(enumerate(VANILLA_KEY_CHARACTERS, start=1))
    try:
        from Utils import user_path
        with open(user_path(CHARACTER_NAMES_FILE), encoding="utf-8-sig") as f:
            lines = f.readlines()
    except Exception:
        return names
    for line in lines:
        line = line.split("#", 1)[0].strip()
        if "=" not in line:
            continue
        number, name = (part.strip() for part in line.split("=", 1))
        if not number.isdigit() or not 1 <= int(number) <= CHARACTER_KEY_COUNT:
            continue
        name = " ".join(name.replace("(", "").replace(")", "").split())[:40]
        if name.lower() in ("", "none", "-"):
            names.pop(int(number), None)
        else:
            names[int(number)] = name
    return names


CHARACTER_NAMES = _read_character_names()


def character_key(number: int) -> str:
    """Item name of a Character Key: "Bael (Character Key 34)", or "Character Key 34" without a name."""
    name = CHARACTER_NAMES.get(number)
    return f"{name} (Character Key {number})" if name else f"Character Key {number}"


CHARACTER_KEYS = [character_key(i) for i in range(1, CHARACTER_KEY_COUNT + 1)]

# Collectibles that can be locked behind an "Item Key: <name>" (see the item_keys option).
# The names are the in-game English names; the mod knows their collectible IDs.
# Only append to this list: never reorder or remove entries (that would change item IDs).
LOCKABLE_ITEMS = [
    "20/20", "Brimstone", "C Section", "Chocolate Milk", "Cricket's Head", "Crown of Light",
    "Death's Touch", "Dr. Fetus", "Epic Fetus", "Glitched Crown", "Godhead", "Haemolacria",
    "Holy Mantle", "Incubus", "Ipecac", "Magic Mushroom", "Mom's Knife", "Polyphemus",
    "Proptosis", "Revelation", "Rock Bottom", "Sacred Heart", "Sacred Orb", "Spirit Sword",
    "Spoon Bender", "Stop Watch", "Tech X", "Tech.5", "Technology", "The Wafer", "Twisted Pair",
]
ITEM_KEYS = [f'Item Key: {name}' for name in LOCKABLE_ITEMS]

def item_list():
    items = []

    for name in data['unlocks'].keys():
        items.append(f'{name} Unlock')

    for item in data['items']:
        items.append(item)

    items.extend(CHARACTER_KEYS)
    items.extend(ITEM_KEYS)

    return items

def item_group_list():
    item_name_groups = {}

    for name in data['unlocks'].keys():
        add_to_item_group(item_name_groups, "Unlocks", f'{name} Unlock')

    for item in data['items']:
        if item.endswith(" Item"):
            add_to_item_group(item_name_groups, "Items", item)
        if item.startswith("Random "):
            add_to_item_group(item_name_groups, "Junk", item)
        if item.endswith(" Trap"):
            add_to_item_group(item_name_groups, "Traps", item)
        if item.startswith("Permanent "):
            add_to_item_group(item_name_groups, "Stat Ups", item)

    for number, item in enumerate(CHARACTER_KEYS, start=1):
        add_to_item_group(item_name_groups, "Character Keys", item)
        # "Character Key 34" still works in YAML plando, hints and start_inventory
        if item != f"Character Key {number}":
            add_to_item_group(item_name_groups, f"Character Key {number}", item)
    for item in ITEM_KEYS:
        add_to_item_group(item_name_groups, "Item Keys", item)

    return item_name_groups

def add_to_item_group(item_name_groups, group, item):
    if group not in item_name_groups:
        item_name_groups[group] = set()
    item_name_groups[group].add(item)