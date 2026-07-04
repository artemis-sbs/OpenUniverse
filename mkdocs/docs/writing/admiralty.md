# The Admiralty (a side to command)

Everything so far built a galaxy to travel through. The Admiralty adds a galaxy
to **command**: it turns the player's own side into a small strategy game -
worldlets to mine, platforms to build, fleets to raise and order, a tech ladder
to climb - all run from a console on the bridge.

**Skip this page freely.** A pure trade-and-story universe never needs it. And
like every chapter, you add it **one piece at a time**, and it is playable after
each step. You never write it all at once.

## What the player does (read this once)

So you know what you are building: the Admiral rides a camera high over the
system - a god's-eye 2D map of everything on their side - and commands by
**clicking things on it**.

- **Click a worldlet** to build on it. First an **HQ**, then an **Extractor** -
  and ore and gas start flowing.
- **Click a platform** to run it (raise a fleet at the Shipyard, research at the
  Lab).
- **Click a fleet** to order it (escort, patrol, strike, hold, salvage, withdraw).

The galaxy you wrote is the board. Now let's put a game on it, one step at a time.

---

## Step 1 - give them something to mine

Nothing to mine, no economy. So start with a `## Worldlets` chapter holding one
resource world. Use the **same three-part shape as everything else** - a heading
with a `(key)`, a `---` fence of facts, and a line of prose:

```
## Worldlets

### Cinder World (cinder)
---
Yields: ore 8
Reserve: 4000
---
A cracked, mineral-rich ember of a world. Miners love it; nobody else does.
```

- **Yields** is per minute, per Extractor: `ore 8` means one Extractor here pulls
  8 ore a minute.
- **Reserve** is the total before it runs dry. Leave it off (or write
  `unlimited`) for a world that never empties.

That's it for step 1. There is no Admiral console yet - just a world waiting.

## Step 2 - switch the game on, and play it

Add an `## Admiralty` chapter. You can leave its fence **completely empty** -
every setting has a sensible default:

```
## Admiralty
---
---
```

**Now play it.** Pick your universe from the dropdown and look at the bridge:
the **Admiral** console is there. Open it and you will see your home system from
above, your worldlet out on the ring, and a resource ticker reading zero.

Try the loop:

1. Click the worldlet, click **Build HQ**. Wait for it to finish.
2. Click the worldlet again - now **Build Extractor** is offered. Build it.
3. Watch the ticker: **ore starts climbing.**

That is the entire foundation. Everything below just gives it more to do.

!!! warning "The one rule that will bite you"
    An HQ plus the first Extractor costs more ore than the player has income to
    replace at the start. If your starting ore can't buy **both**, they get
    stuck with no way to earn more. The shipped default (300) clears it - if you
    lower `Start ore` (in step 6), keep it above the cost of HQ + Extractor.

## Step 3 - more worlds to mine

One world is thin. Add a couple more types - a gas giant, a settled world - so
different systems feel different:

```
### Veiled Giant (veiled_giant)
---
Yields: gas 10
Reserve: 6000
Palette: base #2c4a8c, clouds #b8c4e0, bands 3.7
---
A banded gas giant, its high winds rich in fuel-grade volatiles.

### Haven World (haven)
---
Yields: crew 2, ore 2, gas 2
Reserve: unlimited
---
A small settled world. People, modest industry, and somewhere to come from.
```

- **Palette** is optional - it paints the planet (base colour, cloud colour,
  and `bands` for a gas giant's stripes). Skip it and you get an engine default.
- The **home system always gets one** worldlet so the player can always start.
  Elsewhere they appear by chance (the `Worldlet chance` dial in step 6), or you
  pin one to a place as a [Landmark](map.md) with `Kind: worldlet`.

## Step 4 - give the fleets captains

Fleets need someone to command them. Add an `## Officers` chapter - the Academy
roster. Their **Values** use the **same reputation poles as your clans**
([people](people.md)), and they shape the fleet: `by-the-book` burns less fuel,
`resourceful` salvages richer, `fearsome` fights farther out.

```
## Officers

### Commodore Ansel Vale (vale)
---
Title: the Quartermaster
Values: by-the-book 40, honest 30, kind 10
Face: male
Scene: off_vale_hail
---
Ran the academy's logistics course for a decade and the lanes know it.
Fleets under Vale come home fueled, patched, and on schedule.
```

- **Title** is the honorific; **Face** picks a portrait; **Scene** (optional)
  names a [dialogue](dialogue.md) hail so players can talk to the captain.
- Captains **grow with service** - one kept in the field deepens the strengths
  you wrote them for. Which is why losing one hurts: a fleet's flagship can fall,
  and its captain's escape pod has only a short window to be rescued before they
  are captured or lost.

**Play it again:** build an Academy and a Shipyard, then click the Shipyard -
your officers are offered to commission. Raise a fleet, then click its ships to
give orders.

## Step 5 - add a tech ladder

A `## Research` chapter gives the Admiralty something to work toward at a Lab.
Each milestone names its **Branch**, what it **Costs**, its **Time**, any
milestone it **Requires** first, and what it **Unlocks** in plain English:

```
## Research

### Expanded Silos (eng_silos)
---
Branch: engineering
Costs: ore 120, gas 40
Time: 40
Unlocks: storage 500
---
Bigger tanks and deeper bunkers - the stockpiles hold more.

### Refined Extraction (eng_refining)
---
Branch: engineering
Costs: ore 180, gas 90
Time: 60
Requires: eng_silos
Unlocks: extraction 25%
---
Better drills, hotter crackers. Every extractor works a quarter again as fast.
```

`Unlocks` understands three phrases: `storage N` raises the caps, `extraction N%`
speeds every extractor, and `requisition <item>` adds hardware to the catalog.
Chain milestones with `Requires:` to build a ladder climbed one rung at a time.

## Step 6 - tune the dials (only if you want to)

The whole game above ran on defaults. When you want to reshape it, the
`## Admiralty` fence takes dials - **all optional, each line skippable**:

```
Economy pace: standard    // brisk | standard | epic - scales the dials below together
Worldlet chance: 30%      // chance a NON-home system holds a worldlet
Start ore: 300            // opening stockpiles (mind the warning in step 2)
Start gas: 100
Start crew: 40
Storage: 600              // per-resource cap; Refineries and Research raise it
Command points: 3         // how many fleets at once; Sensor Relays add more
Fleet gas burn: 2         // gas per minute a fleet burns on an active order
Requisition budget: 800 credits   // starting funds for the Requisition catalog
Build model: menu         // menu (instant) or fabricator (a builder ship flies out)
Skirmish pressure: border // where border raids come from (border, or none)
Skirmish interval: 240    // seconds between border raids
MIA timer: 300            // rescue window for a downed captain's pod, in seconds
Relay rate: 50%           // income a Relay Gate keeps paying from a system you left
Research pace: campaign   // how quickly the tech ladder is meant to be climbed
```

The Admiral commands from the **overseer**: a detached camera over a system-wide 2D
map where you select objects to act (worldlet build, fleet orders, platform actions).
The older tabbed "bridge" console has been retired.

### Mode — one dial for the mission's shape

`Mode` picks the **kind** of mission and sets sensible defaults for the dials below
(any dial you set explicitly still wins). It's the keystone the Open Universe
foundation grows on (see `FOUNDATION_PLAN.md`). Author it in a mission-level
**`## Scenario`** chapter — so a `story` universe needs no `## Admiralty` block at all:

```
## Scenario
---
Mode: story
---
```

(`Mode:` is still accepted inside `## Admiralty` for older universes.)

| Mode | Admiral RTS | Economy | Skirmish | For |
|---|---|---|---|---|
| `sandbox` | on | standard | border | today's living universe (default) |
| `skirmish` | on | brisk | border | a punchy 1–3 h RTS |
| `war` | on | epic | border | a long, multi-side war |
| `campaign` | **off** | epic | off | a persistent single-ship epic |
| `story` | **off** | standard | off | a bounded 1–2 h narrative |

`campaign`/`story` switch the **admiral economy off entirely** even if a Worldlets
chapter is present — so a story mission can reuse the universe without the RTS. An
unknown or omitted mode is `sandbox`. (More of the mission shape — hostile side
relations, victory/defeat conditions, which subsystems load — folds into `Mode` in
later phases; today it drives the admiral/economy/skirmish switches.)

### Victory & defeat (via quests + the Mode default)

Victory conditions are **authored as quests**, not a separate config block — a quest
with `Win: yes` that completes ends the game in victory (`Lose: yes` in defeat). The
war Modes also come with a built-in default so a PvP match ends on its own.

- **Last side standing** *(skirmish/war default)* — a player side is eliminated when
  it holds no Headquarters (conquest); when one side remains it wins. No authoring
  needed; it just works in `skirmish`/`war`.
- **Decapitation quick-win** — a side's **first HQ is its capital**, tagged with a
  `<side>_capital` role. Capturing/destroying it is a normal quest:

  ```
  # [Take the Orion capital](win_decap)
  When: destroy 1 orion_capital
  Win: yes
  ```

- **Conquest as a quest** — to make "wipe out a *specific* side" an authored objective
  (not just the automatic last-standing), hook the war-state milestone signal:

  ```
  # [Break the Orion Concord](win_conquest)
  When: signal eliminated_orion
  Win: yes
  ```

  The war-state watcher fires `eliminated_<side>` when a side loses its last HQ (and
  `last_side_standing` when one remains); `When: signal <name>` completes the quest via
  the quest driver's generic `on_signal` hook.
- **Story / objective wins** — any quest with `Win:`/`Lose:` (reach a sector, recover
  an item, etc.) ends the game, so a `story` mission's victory is just its final quest.

Under the hood a war-state watcher emits `side_eliminated` / `last_side_standing`
(and mirrors them to the quest `quest_signal` hook); game end sets the shared
`UNIVERSE_GAME_OVER`.

### Economy pace — one dial for game length

Base resources accumulate slowly on purpose (an anti-snowball economy: single-digit
per-minute yields against 60–400-ore platforms, capped by Storage). Rather than
hand-tune Yields, Reserve, Storage and Start separately, pick a **pace** — it scales
all four together (as multipliers on whatever you authored):

| Pace | Yield | Reserve | Storage | Start | For |
|---|---|---|---|---|---|
| `brisk` | ×2.0 | ×2.0 | ×1.5 | ×1.5 | a punchy ~1-hour session |
| `standard` | ×1.0 | ×1.0 | ×1.0 | ×1.0 | today's balance (default) |
| `epic` | ×1.0 | ×5.0 | ×3.0 | ×1.5 | a long / persistent game |

`brisk` speeds the whole curve; `epic` keeps the same per-hour ramp but makes finite
worldlets last far longer and lets you bank much more for late infrastructure. You can
still set explicit `Yields` / `Reserve` / `Storage` / `Start` values — the pace scales
those. An unknown pace (or omitting the line) is `standard`.

!!! note "It's multi-side, for free"
    Everything on this page is written **once** and runs for **every**
    player-commanded side your universe fields. Field two player sides and each
    gets its **own** Admiral, stockpiles, fleets, and research off these same
    chapters - you don't duplicate anything, and you don't name a side anywhere in
    them. Whether those sides are **allies** (a co-op war) or **rivals** is set
    where the universe defines its sides, not here.

## The platforms (the fixed kit)

You don't write the platforms - they are the standard set the Admiral builds
from. Knowing what each does helps you tune your yields and dials around them:

| Platform | What it does |
|---|---|
| **HQ** | The hub. The first build; unlocks the rest. |
| **Extractor** | Pulls a worldlet's Yields into the pools. The income. |
| **Refinery** | Boosts its worldlet's extraction and adds storage. |
| **Academy** | Lets you commission officers into fleets. |
| **Shipyard** | Where fleets form; also the research site. |
| **Lab** | Research slots - one project per Lab at a time. |
| **Sensor Relay** | Adds a command point and charts the neighbouring systems. |
| **Depot** | Supplies fleets operating away from home. |
| **Bastion** | Draws and holds border raids - where the fight lands. |

---

**Next: [The complete example](silver-reach.md)** - the whole Silver Reach in
one listing.
