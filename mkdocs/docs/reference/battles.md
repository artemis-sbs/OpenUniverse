# Battles and fleets

Every fight in a universe is a **fleet**: a group of enemy ships that arrive and fight
together. This page says where fleets come from, how big they are, every line that
changes them, and how to count what you are asking a crew to fight.

Most of it you have already written without counting it: a `foe` side, its `Home:`, its
`Flies:`, the `Enemy mix:` of the galaxy and of each region, and a landmark's `Guards:`.

| Word | Meaning |
|---|---|
| Fleet | A group of enemy ships that arrive and fight together |
| Tier | How strong a fleet is, from 1 to 11. A higher tier has more ships, and bigger ones |
| Difficulty | One number, from 1 to 11, that the whole game reads. It decides how many fleets, and their tier |
| Guards | A fleet you put on a landmark |
| Set piece | A fight you stage yourself: this place, these ships, this moment in the story |
| Budget | The most ships you will let one system hold |

## Where enemy ships come from

| Where | What is there | The line that decides it |
|---|---|---|
| An enemy system | One to four fleets of a `foe` side | The `Enemy mix:` of the galaxy and the region, times **Danger**, decides which systems. Difficulty decides how many fleets, and their tier |
| A foe's home | One fleet, close to the station. Mines, if the system is mined | `Home:` on the side decides where. Difficulty decides the tier |
| A landmark with `Guards:` | One fleet, near the landmark | The `Guards:` line. It can carry a tier of its own |
| A set piece | Whatever you stage | A card in `story.mast`. See [A battle that waits for the story](#a-battle-that-waits-for-the-story) |

Which ships a side's fleets are made of comes from the side's `Flies:` line. A system
exists only while a crew is in it: when the last ship jumps out, every ship and rock in
it is removed, and it is built again on the next arrival.

## How big a fleet is

The number of ships in one fleet, at each tier, read from the game for each of the six
kinds of ship:

| Tier | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Torgoth | 1 | 1-2 | 1-2 | 1-3 | 2-3 | 3 | 3 | 3-4 | 4-5 | 5 | 6 |
| Kralien | 1-2 | 2-3 | 2-3 | 2-4 | 3-4 | 3-5 | 4-6 | 4-6 | 5-6 | 5-6 | 6 |
| Arvonian | 1 | 1-3 | 2-3 | 1-3 | 1-3 | 3-4 | 2-4 | 3-4 | 3-5 | 4-6 | 6 |
| Pirate | 1 | 1-2 | 1-2 | 1-2 | 1-2 | 1-3 | 1-3 | 2-3 | 3-4 | 4-5 | 6 |
| Ximni | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1-2 | 6 |
| Skaraan | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |

`1-3` means the game picks: one ship, two, or three. A higher tier also means heavier
ships. A Torgoth fleet at tier 11 is six of their largest. A tier above 11 is 11, and a
tier below 1 is 1.

## Difficulty

Difficulty is the `DIFFICULTY:` line in your mission's `settings.yaml`:

```
DIFFICULTY: 4
```

The start screen's **Difficulty** slider sets the same number. The line in the file is
what the slider starts at, and it is what the game uses when the start screen is skipped
(`map=0`). Keep the capital letters and the space after the colon.

Difficulty counts twice. It is the **tier** of every fleet that has no tier of its own,
and it decides **how many** fleets an enemy system holds: one, then one more at 3, at 6
and at 9. Counted in Torgoth enemy systems:

| Difficulty | Fleets in an enemy system | Ships counted |
|---|---|---|
| 1 | 1 | 1 |
| 3 | 2 | 3 |
| 4 | 2 | 4 |
| 5 | 2 | 6 |
| 8 | 3 | 11 |
| 11 | 4 | 24 |

It also sets the number of mines in a mined system (four at Difficulty 4, six at 11) and
of black holes in an anomaly.

| You write in `settings.yaml` | What the game does |
|---|---|
| `DIFFICULTY: 15` | Plays, past the top of the table: six fleets of six in an enemy system |
| `DIFFICULTY: 0` | Plays as the gentlest setting: one fleet of one ship |
| `DIFFICULTY: four` | The game stops with an error soon after it starts. `mast.runtime.log` holds it |
| `DIFFICULTY:4`, no space after the colon | Plays at Difficulty 5. `mast.runtime.log` has a line beginning `ryaml refused` |
| `Difficulty: 4`, in small letters | Ignored. The game plays at 5 |

Lint does not read `settings.yaml`.

## Danger and Encounters

Two more dials shape the fights of a whole galaxy. In the Open Universe mission they
are on the start screen's **Map** tab. In a mission of your own they are two lines near
the top of `story.mast`, beside the travel lines:

```
default shared DANGER = "Quiet"
default shared ENCOUNTERS = "Dormant"
```

**`DANGER`** - `"Quiet"`, `"Balanced"` or `"Dangerous"` - multiplies every `Enemy mix:`,
the galaxy's and each region's. It does not add fleets to a system. It makes more systems
enemy systems. Counted over the 169 systems nearest home with `Enemy mix: 12%`:

| `DANGER` | Enemy mix is multiplied by | Enemy systems | Empty systems |
|---|---|---|---|
| `"Quiet"` (the default) | 1 | 14 | 85 |
| `"Balanced"` | 1.67 | 33 | 69 |
| `"Dangerous"` | 2.67 | 54 | 54 |

A region that says `Enemy mix: 0%` stays empty of enemy systems even at `"Dangerous"`.
Change Danger and the map a crew remembers from last week is a different map.

**`ENCOUNTERS`** - `"On Arrival"` or `"Dormant"` - decides where an enemy system's fleets
wait.

| `ENCOUNTERS` | Distance to the nearest enemy ship on arrival |
|---|---|
| `"On Arrival"` (the default) | About 18,000 to 20,000 |
| `"Dormant"` | About 40,000 to 44,000 |

`"Dormant"` gives a crew time to read the card, look at the map and talk. It moves only
the fleets of an enemy system. Guards and a foe's home fleet stay where they are.

Spell both words exactly, capitals and quote marks and all. A wrong word is not an error:
it is the gentler setting, in silence.

| You write | What the game does |
|---|---|
| `"dangerous"` or `"dormant"`, in small letters | `"Quiet"`, or `"On Arrival"` |
| `ENCOUNTER` for `ENCOUNTERS` | `"On Arrival"` |
| `DANGER = Dangerous`, no quote marks | Nothing runs. `mast.runtime.log` says `name 'Dangerous' is not defined` |
| `DANGER: "Dangerous"` in `settings.yaml` | Ignored. This dial is read only from `story.mast` |
| `Difficulty: 8` or `Danger: Dangerous` in the title record of the `.amd` | Ignored. Lint warns: "is not a field a map has" |
| The two lines indented, or pasted at the very end of `story.mast` | Nothing runs: no ship, no station. Lint gives an error (`mast-compile`) |

Leave `default shared` in front of both: it is what lets the start screen change them.

## Guards on a landmark

`Guards:` puts one fleet near a landmark, to contest it once:

```
### [The Bone Pile](bone_pile)
---
At: -4, -3
Prefab: derelict
Guards: torgoth 7
---
```

The first word is the kind of ship: `torgoth`, `kralien`, `arvonian`, `pirate`, `ximni`
or `skaraan`, in any capitals. The number after it is the fleet's tier.

| You write | The guards are |
|---|---|
| `Guards: torgoth` | A fleet at the Difficulty. It grows when Difficulty grows |
| `Guards: torgoth 7` | A tier 7 fleet, three Torgoth ships, at any Difficulty |
| `Guards: pirate 2` | One or two small ships |

Use a tier where the story needs a fight of a known size, and no tier where the place
should be as hard as everything else.

Four things are true of every guard fleet:

1. **The crew is warned.** On arrival a card titled **Threat** says "The Tern is
   guarded - hostiles on approach.", with the landmark's name.
2. **They wait by the landmark, not by the crew.** How far that is from where the ship
   arrives changes from game to game. Measured: about 13,000 to 24,000 at one landmark,
   7,600 to 18,300 at another.
3. **They belong to nobody.** Guards are raiders, whatever kind of ship they are. A
   ceasefire with a side does not call them off.
4. **They do not come back.** When every guard is destroyed the game remembers it, in the
   save. The next visit has no guards and no warning.

The long form names a prefab, how many fleets, and what to pass it. `Count: 2` puts two
fleets side by side:

```
Guards:
  Prefab: fleet/raider
  Count: 2
  Data:
    Race: torgoth
    Fleet difficulty: 3
```

| You write | What the game does |
|---|---|
| `Guard: torgoth 7` | No guards. Lint asks "Did you mean `Guards`?" |
| `Guards:` on a region or a side | Nothing. Only a landmark has guards. Lint warns |
| `Guards: torgoth seven`, `x7` or `7.5` | The tier is not a whole number, so the guards follow the Difficulty |
| `Guards: 7 torgoth`, or `Guards: torgoth, 7` | No guards. `mast.runtime.log` says there is no fleet for `7` (or `torgoth,`) and lists the six kinds. The Threat card is still shown |
| `Guards: gleaners 7`, a side's key | No guards: the word is a kind of ship, never a side. The log names it. The Threat card is still shown |
| `Guards: none` | No guards, a line in the log, and a Threat card for a threat that is not there. To have no guards, write no `Guards:` line |
| `Guards: torgoth 70` | Six of the largest. Any tier above 11 is 11 |
| `Guards: torgoth 200` | A number this large means "two above the Difficulty" |
| `Guards: torgoth 7, kralien 7` | One Torgoth fleet at the Difficulty. A landmark has one `Guards:` line |
| Two `Guards:` lines | The second one only |
| `Guards: torgoth 7` on a station landmark | Works. Raiders wait near the station |

## A foe's home

A `foe` side's home system has its station, and the station has one fleet to defend it,
at the Difficulty, close by: measured between 1,700 and 4,400 from where the crew arrives.

| Difficulty | Ships in the home fleet |
|---|---|
| 1 | 1 |
| 4 | 1 or 2 |
| 5 | 2 |
| 8 | 3 |
| 11 | 6 |

In five visits out of seven the station also launched four fighters of its own, named
after the side (`The Gleaners Red 1` to `Red 4`). No line of yours sets their number. A
foe's home is the one place a crew arrives with the enemy already on top of it. Send a
story there on purpose, not by accident.

Read from the game's code, and not played for this page: when none of the side's ships
has been within 12,000 of the home station for about twenty seconds, the station is
captured and flies the crew's side. On a later visit the side sends a fleet to take it
back, and if no player ship stays within 12,000 of it while that fleet is there, it is
retaken: "Starbase retaken by the enemy!"

## A side's own fleets: `Flies:` and `Fleet:`

| Line on a side | What it does |
|---|---|
| `Flies: Torgoth` | Every fleet of this side is Torgoth |
| `Flies: Kralien, Torgoth` | An even mix, picked fleet by fleet |
| `Flies: 60% Kralien, 40% Arvonian` | A weighted mix |
| No `Flies:` | A random mix |
| `Fleet: fleet/raider` | The prefab the side's fleets are built by. Unwritten, it is this one. The nested `Prefab:` / `Count:` / `Data:` block works as for `Guards:` |

A `Flies:` word that is not a kind of ship (`Flies: Gleaner`) gives that side no fleets
anywhere. The log names the word once for each fleet it could not make.

A side's fleets fly the side's colors: they are on that side, so a ceasefire with the side
is a ceasefire with them. An enemy system cleared completely is remembered, in the save,
and stays clear. A side the crew has a ceasefire with no longer counts against clearing
it. Measured: an enemy system nobody shot at was full again on every visit.

## A battle that waits for the story

Everything above sets odds. An enemy system is rolled again in every new game, so a
landmark in a region with `Enemy mix: 60%` is an enemy system in about six games of ten.
A **set piece** is for the one place where the story cannot take odds.

It is a card pasted at the very end of `story.mast`. The words to change are the
system's two numbers, the step's key, the kind of ship, the tier, the side's key, the
distance and the sentence.

```
#
# The Bone Pile: a Gleaner battle line waits there while "Break the Bone Pile" is open.
#
//shared/signal/universe_arrived if ARRIVE_I == -4 and ARRIVE_J == -3
    await delay_sim(1)
    ->END if not quest_is_active(universe_shared_id(), "goal_bone_pile")
    battle_at = universe_cell_origin(ARRIVE_I, ARRIVE_J)
    prefab_spawn(prefab_fleet_raider, {"race": "torgoth", "fleet_difficulty": 9, "ship_roles": "gleaners, raider", "START_X": battle_at.x + 6000, "START_Y": battle_at.y, "START_Z": battle_at.z + 6000})
    universe_info_card("A Gleaner battle line is forming up between you and the Bone Pile.", "Threat", "#f80")
    ->END
```

| Part | What it means |
|---|---|
| `//shared/signal/universe_arrived` | The game says `universe_arrived` each time it builds a system for an arriving ship. `//shared/signal` runs once, on the server. `//signal` would run once for every console: one battle line each |
| `if ARRIVE_I == -4 and ARRIVE_J == -3` | Only this system: the landmark's `At:`. Capitals, two equals signs, `and` |
| `await delay_sim(1)` | Arriving can finish the step before and reveal this one. Without the second's wait the card looks first, sees a hidden step, and makes nothing |
| `->END if not quest_is_active(...)` | Only while this step of the story is open. The word in quotes is the step's key |
| `"race"` | One of the six kinds of ship |
| `"fleet_difficulty"` | The tier, 1 to 11. Like a tier on `Guards:`, it does not move with Difficulty. `0` means the Difficulty |
| `"ship_roles": "gleaners, raider"` | The first word is the side the ships fight for. Leave `, raider` after it |
| `+ 6000`, twice | How far from the system's middle the fleet forms up. Measured about 7,000 from the arriving ship |

| When the crew arrives | Battle line |
|---|---|
| Before the story sends them (the step still hidden) | No |
| On the story's business, the step open | Yes |
| Again, after running away | One battle line, not two: the system was built new |
| After Continue, saved there with the step open | Yes: Continue builds the system the crew is in |
| After the step is done | No |

Nothing about the battle is saved; the step is. After Continue the battle line is fresh
and whole, even if the crew had destroyed half of it. The ships are on the named side, so
they count for `destroy 4 enemies`. Read and not played: a second crew jumping into a
system that already has a ship in it does not set the card off again.

## The ship budget

For each system a story sends the crew to, add up the sources. At The Bone Pile in the
Class 5 universe, an enemy system with guards and a set piece:

| At The Bone Pile, Difficulty 4 | Ships |
|---|---|
| The side's fleets (an enemy system) | 4 |
| The guards, `torgoth 7` | 3 |
| The set piece, `torgoth` tier 9 | 4 or 5 |
| All the hostile ships | 11 or 12 |

**How many is too many for the game itself?**

| Fact | Where it comes from |
|---|---|
| The ships in play are the ships in the systems crews are in. One crew: one system. Three crews in three systems: three systems at once | Counted: after a jump, no ship of the old system was left |
| The game kept full speed up to about 190 ships fighting at once | The makers' own test, with no consoles connected (`MULTI_SYSTEM_FEASIBILITY.md`) |
| Rocks and clouds are cheap: the same test held 100,000 of them at full speed | The same test |
| What a full bridge of consoles can take is not known | Nobody has measured it. Stay far below 190 |

So the budget is **the ships in your worst system, times the number of crews that can be
in different systems at once.** Set Difficulty for the crew you expect, then check the
worst system at that number. To make the end of a story lighter, lower a tier you chose,
or take a `Guards:` line off a landmark a set piece already defends.

`TERRAIN_SELECT:` in `settings.yaml` (`"none"`, `"few"`, `"some"`, `"lots"`, `"max"`) sets
how many rocks and clouds a system gets: from 16 in an empty system at `"none"` to about
4,900 at `"max"`. A nebula system holds 2,800 to 4,400 whatever it says. Any other word is
`"none"`.

## If something goes wrong

| What you see | Likely cause |
|---|---|
| No ship and no station. Nothing happens | A card in `story.mast` is indented, at the wrong place, or lost its quote marks. Lint finds the first two; `mast.runtime.log` the third |
| The game plays at Difficulty 5 whatever the file says | The `DIFFICULTY:` line lost its capitals or its space, or the file was not saved |
| Enemy fleets are still close on arrival | `ENCOUNTERS` or `"Dormant"` is misspelled. Or it is a foe's home, or guards |
| No guards, and a Threat card all the same | The word after `Guards:` is not one of the six kinds. `mast.runtime.log` names it |
| No guards and no card | The crew destroyed them earlier in this save |
| Guards are a different size from the table | The tier is missing or not a whole number, so they follow the Difficulty |
| A foe side has no ships anywhere | Its `Flies:` names something that is not a kind of ship |
| Four fighters you never wrote, at a foe's home | The foe's station launches them |
| No set piece when the story arrives | `await delay_sim(1)` is missing, the key in quotes is not the step's key, or the two numbers are not the landmark's `At:` |
| A set piece the first time the crew wanders in | The `->END if not quest_is_active` line is missing |
| The set piece is there and is not hostile | The first word of `"ship_roles"` is not the key of a `foe` side |

## Related

- [Painting the map](../writing/map.md): regions, landmarks, `Guards:` and `Terrain:`.
- [The dials](../writing/dials.md): `Enemy mix:`, `Mine chance:` and the other mixes.
- [Sides - who lives here](../writing/sides.md): `Disposition:`, `Home:`, `Flies:` and
  `Fleet:`.
- [Reputation](reputation.md): ceasefires and alliances.
- The library's
  [Fleets & raiding](https://artemis-sbs.github.io/sbs_utils/build/fleets/): the fleet
  prefab, its tiers, and the ladder files behind the table above.
