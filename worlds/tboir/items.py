from .game_data import data

# Items added by this fork for the AP Character Lock companion mod.
# Always appended at the END of the list so existing item IDs never change.
CHARACTER_KEY_COUNT = 60
CHARACTER_KEYS = [f'Character Key {i}' for i in range(1, CHARACTER_KEY_COUNT + 1)]

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

    for item in CHARACTER_KEYS:
        add_to_item_group(item_name_groups, "Character Keys", item)
    for item in ITEM_KEYS:
        add_to_item_group(item_name_groups, "Item Keys", item)

    return item_name_groups

def add_to_item_group(item_name_groups, group, item):
    if group not in item_name_groups:
        item_name_groups[group] = set()
    item_name_groups[group].add(item)