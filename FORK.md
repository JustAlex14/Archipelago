# Isaac apworld fork: Character Keys, boss logic and Item Keys

This fork of NaveTK's Isaac apworld adds four YAML options, used by the **AP Character Lock** mod:

| Option | What it does |
|---|---|
| `character_keys` (0-60) | Adds "Character Key 1" to "Character Key N" (progression items). The mod uses them to unlock characters. |
| `boss_character_keys` | Bosses that only count with some characters, given as Character Key numbers. Their reward checks and goal require one of those keys **in logic**, so a key can never end up behind its own boss. |
| `item_keys` | Collectibles locked until "Item Key: <name>" is received (31 lockable items). |
| `gifting` (on by default) | The Isaac client joins Archipelago Gifting: gifts from other games are passed to the mod (permanent stat bonuses), and the mod's Gift Box sends coins to players whose game supports gifting. Needs AP Character Lock; without it, received gifts just wait in the giftbox. |

With `character_keys`, `boss_character_keys` and `item_keys` left at their defaults, generation is exactly
like the original. `gifting` only changes what the Isaac client does once connected; set it to `false` to
turn it off.

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
  gifting: true                       # default
  junk_percentage: 0                  # optional: no junk, it isn't kept between runs
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
| `0001-tboir-add-Character-Keys-boss-character-logic-and-It.patch` | Change 1: Character Keys, boss logic, Item Keys |
| `0002-tboir-add-Archipelago-Gifting-support-gifting-option.patch` | Change 2: Gifting (apply after change 1) |
| `build_apworld.py` | Rebuilds `tboir.apworld` from your fork |

## Option 1: use the ready-made apworld (easiest)

1. Close the Archipelago Launcher.
2. Delete the old `tboir.apworld` from `C:\ProgramData\Archipelago\custom_worlds\`.
3. Double-click the new `tboir.apworld` (or use **Install APWorld** in the Launcher).
4. Start the Launcher again. In Options Creator, the Isaac game now has **Character Keys**,
   **Boss Character Keys**, **Item Keys** and **Gifting**.

The Isaac Client is part of the apworld, so installing it also updates the client (needed for gifting).

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
git am C:\path\to\0002-tboir-add-Archipelago-Gifting-support-gifting-option.patch
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

If `git merge` reports a conflict, NaveTK changed the same lines as the patches (`worlds/tboir/items.py`,
`options.py`, `__init__.py` or `client.py`). Open the file, keep his changes **and** the Character Key / Item Key lines,
then `git add .` and `git commit`.

## What the patches change

- `items.py`: adds "Character Key 1-60" and "Item Key: <name>" **at the end** of the item list, so existing
  item IDs don't change. Adds the "Character Keys" and "Item Keys" item groups. Only ever append to
  `LOCKABLE_ITEMS`: reordering it would change item IDs.
- `options.py`: adds `character_keys`, `boss_character_keys` and `item_keys`.
- `__init__.py`: puts the keys in the pool (Character Keys as progression, Item Keys as useful), adds the
  boss rules, checks that every `boss_character_keys` number is at most `character_keys`, and sends the three
  options in slot data so the mod can read them.
- `test/test_character_lock.py`: tests for all of the above.
- `gifting.py` (new): Archipelago Gifting, data version 3. Registers the giftbox in the team's `GiftBoxes;<team>`
  entry, forwards the gifts of `GiftBox;<team>;<slot>` to the game, removes them (`pop`) only once the game
  confirms, and sends the game's gifts to players whose giftbox is open and accepts coins.
- `client.py`: wires the gifting manager in (connection, data storage replies, the game's `SendGift` and
  `GiftsReceived` commands).
- `options.py`: adds `gifting`; `__init__.py` sends it in slot data.
- `test/test_gifting.py`: tests for gifting.

The Workshop mod "!The Archipelago of Isaac" doesn't need any change: it shows the keys as unknown items with
no effect, and AP Character Lock replaces their message with "Lucas sent you Bael".

## Verified

- All 207 tests of the Isaac apworld pass (the 174 original ones + the new ones).
- Gifting tested against a real Archipelago server: giftbox registration, gifts received (v3 and older v2
  format), removal after confirmation, coins sent to another player, refused when the target can't receive.
- Generation tested with Archipelago (NaveTK fork source, August 27, 2026): Isaac + APQuest,
  `character_keys: 34`, `boss_character_keys` and `item_keys`, over several seeds.
- Forcing "Character Key 34" onto "Mother Reward #1" while Mother needs key 34 makes generation fail
  ("Could not place"), which proves the rule is in logic.
- A `boss_character_keys` number above `character_keys` stops generation with a clear error.
