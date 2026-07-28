# Sides - who lives here

Sides are your factions - the recurring characters of the galaxy. Each one is
a character sheet: what they look like on the map, where they live, what they
value, and what kind of people they are.

!!! note "These used to be called clans"
    They were always sides - the universe spawned them as sides from the first day.
    The private word bought us a private kind of record and a second vocabulary for
    standing and home systems, so it is gone. `## Clans` and `Clan:` still parse, and
    nothing you have written needs changing.

Add a `## Sides` chapter with two entries:

```
## [Sides](sides)

### [The Lantern Combine](lantern)
---
Color: #ffcc44
Character: trader
Disposition: neutral
Home: -4, 2
Values: honest 40, generous 30, peaceful 20
Flies: Arvonian
---
Convoy families who keep the freight lanes lit. Fair dealers with long
memories for a kept promise - and longer ones for a broken cargo contract.

### [The Red Veil](veil)
---
Color: #cc2244
Character: pirate
Disposition: foe
Home: 5, -4
Values: violent 40, fearsome 30, selfish 20
Flies: Torgoth
---
Corsairs of the outer dark. They take what the light forgets, and they
respect exactly one thing: a captain more dangerous than they are.
```

## Reading the fact sheet as a writer

- **Color** - the side's color on the galaxy map. Any web color like
  `#cc2244`.
- **Archetype** - the side's genre role, one word: `military`, `trader`,
  `settler`, `mercenary`, `pirate`, or `cult`. This flavors their chatter,
  their stations, and their fleets.
- **Disposition** - `neutral` (will talk) or `foe` (shoots first). A `foe`
  side can still be won over in play - through reputation, ceasefires, even
  alliance. You are writing their opening attitude, not their fate.
- **Home** - their home system as map coordinates, `column, row`. The galaxy
  is a grid of systems centered on `0, 0`, where the players start; a home at
  `5, -4` is five columns and four rows away in the other direction. Give
  sides some distance from each other (and from `0, 0`) so their territories
  read on the map.
- **Values** - the side's moral leanings, as traits with weights. These are
  the seven built-in trait pairs a captain is measured on:

    | | |
    |---|---|
    | `honest` / `liar` | `fearsome` / `cowardly` |
    | `peaceful` / `violent` | `generous` / `selfish` |
    | `kind` / `cruel` | `resourceful` / `by-the-book` |
    | `intellectual` / `foolish` | |

    Pick two or three poles that define the side and weight them (they need
    not add to 100). A side warms to captains who act like it - the Veil
    respects `fearsome` deeds, the Combine respects `honest` ones. This one
    line is the engine of the whole reputation game, and it is pure
    characterization.

- **Flies** - the ships they fly: one race (`Torgoth`), an even mix
  (`Kralien, Torgoth`), or weighted (`60% Kralien, 40% Arvonian`). Races:
  `Kralien`, `Torgoth`, `Arvonian`, `Ximni`. Skip it for a random mix.

!!! success "In play"
    Your sides now hold home systems, their colors mark the map, their fleets
    fly their colors, and every captain has a personal standing with each of
    them that moves with how the captain behaves.

**Next: [Jobs](jobs.md)** - the work they offer.
