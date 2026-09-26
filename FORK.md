# Isaac apworld fork: Character Keys, boss logic and Item Keys

This fork of NaveTK's Isaac apworld adds three YAML options, used by the **AP Character Lock** mod:

| Option | What it does |
|---|---|
| `character_keys` (0-60) | Adds "Character Key 1" to "Character Key N" (progression items). The mod uses them to unlock characters. |
| `boss_character_keys` | Bosses that only count with some characters, given as Character Key numbers. Their reward checks and goal require one of those keys **in logic**, so a key can never end up behind its own boss. |
| `item_keys` | Collectibles locked until "Item Key: <name>" is received (31 lockable items). |

With all three left at their defaults, the apworld behaves exactly like the original.

Only **the person who generates the game** and **the person who plays Isaac** need this modified apworld.
It replaces the original one: same game name, same `tboir.apworld` file name.

## Example YAML

```yaml
name: Alex
game: The Binding of Isaac Repentance
requires:
  plando: items
The Binding of Isaac Repentance:
  character_keys: 34                  # 33 vanilla characters + Bael
  boss_character_keys:
    Mother: [34]                      # Mother only counts with Bael
  item_keys: [Brimstone, Sacred Heart]
  plando_items:
    - item: Character Key 34
      world: Lucas
      location: "Exact quest name"
      force: true
```

## What's in this folder

| File | Use |
|---|---|
| `tboir.apworld` | The ready-to-install apworld (based on NaveTK's version 0.4.4) |
| `0001-tboir-add-Character-Keys-boss-character-logic-and-It.patch` | The change, to apply to your own fork |
| `build_apworld.py` | Rebuilds `tboir.apworld` from your fork |

## Option 1: use the ready-made apworld (easiest)

1. Close the Archipelago Launcher.
2. Delete the old `tboir.apworld` from `C:\ProgramData\Archipelago\custom_worlds\`.
3. Double-click the new `tboir.apworld` (or use **Install APWorld** in the Launcher).
4. Start the Launcher again. In Options Creator, the Isaac game now has **Character Keys**,
   **Boss Character Keys** and **Item Keys**.

## Option 2: make your own fork (to update it yourself)

You need a GitHub account, [Git for Windows](https://git-scm.com/download/win) and Python 3.11 or newer.

**1. Create the fork.** Go to https://github.com/NaveTK/Archipelago and click **Fork**.

**2. Clone it and apply the change** (in a command prompt):

```
git clone https://github.com/YOUR_NAME/Archipelago.git
cd Archipelago
git remote add upstream https://github.com/NaveTK/Archipelago.git
git config user.name "Your name"
git config user.email "you@example.com"
git am C:\path\to\0001-tboir-add-Character-Keys-boss-character-logic-and-It.patch
git push
```

**3. Build the apworld.** Copy `build_apworld.py` to the root of your fork, then:

```
python build_apworld.py
```

`tboir.apworld` appears at the root of the fork. Install it as in option 1.

## Updating when NaveTK releases a new version

```
cd Archipelago
git fetch upstream
git merge upstream/main
python build_apworld.py
git push
```

Then install the new `tboir.apworld` again. Also update the Workshop mod "!The Archipelago of Isaac": its
version must match the apworld.

If `git merge` reports a conflict, NaveTK changed the same lines as the patch (`worlds/tboir/items.py`,
`options.py` or `__init__.py`). Open the file, keep his changes **and** the Character Key / Item Key lines,
then `git add .` and `git commit`.

## What the patch changes (3 files + 1 test file)

- `items.py`: adds "Character Key 1-60" and "Item Key: <name>" **at the end** of the item list, so existing
  item IDs don't change. Adds the "Character Keys" and "Item Keys" item groups. Only ever append to
  `LOCKABLE_ITEMS`: reordering it would change item IDs.
- `options.py`: adds `character_keys`, `boss_character_keys` and `item_keys`.
- `__init__.py`: puts the keys in the pool (Character Keys as progression, Item Keys as useful), adds the
  boss rules, checks that every `boss_character_keys` number is at most `character_keys`, and sends the three
  options in slot data so the mod can read them.
- `test/test_character_lock.py`: tests for all of the above.

The Workshop mod "!The Archipelago of Isaac" doesn't need any change: it shows the keys as unknown items with
no effect, and AP Character Lock replaces their message with "Lucas sent you Bael".

## Verified

- All 196 tests of the Isaac apworld pass (the 174 original ones + the new ones).
- Generation tested with Archipelago (NaveTK fork source, August 27, 2026): Isaac + APQuest,
  `character_keys: 34`, `boss_character_keys` and `item_keys`, over several seeds.
- Forcing "Character Key 34" onto "Mother Reward #1" while Mother needs key 34 makes generation fail
  ("Could not place"), which proves the rule is in logic.
- A `boss_character_keys` number above `character_keys` stops generation with a clear error.
