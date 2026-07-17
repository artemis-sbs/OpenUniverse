# Jobs - the work they offer

Jobs are the work a clan posts at its stations. Two steps: write the job, then
put it in a clan's offer list.

Add a `## Jobs` chapter:

```
## [Jobs](jobs)

### [Convoy Escort](escort)
---
Tier: 1
Goal: dock station
Pays: 260 credits
---
A lantern convoy needs a shepherd through the dark miles. See it safe to
port and the Combine settles up.

### [Veil Bounty](bounty)
---
Tier: 1
Goal: destroy 3 raiders
Pays: 300 credits
---
The Veil has been working the lanes again. There is a standing price on
their hulls - three will do for a start.

### [Quiet Cargo](smuggle)
---
Tier: 2
Goal: recover 2 contraband
Pays: 480 credits
---
Sealed crates, no manifest, no questions. Bring them in quietly and be
paid the same way.
```

Then give each clan its offerings - add an `Offers:` line to the clan fact
sheets from the [Clans page](clans.md):

```
// in the Lantern Combine's fence:
Offers: escort, bounty

// in the Red Veil's fence:
Offers: smuggle, bounty
```

The words in `Offers:` are the job **keys** from your `## Jobs` headings -
that's how the two connect.

## About the facts

- **Goal** is the whole mechanic, and you write it as an order to the captain,
  in English. The first verb picks the objective type:

    | You write... | The game tracks... |
    |---|---|
    | `destroy 4 raiders` | kills |
    | `recover 3 provisions` | cargo collected |
    | `scan 2 derelicts` | science scans |
    | `dock station` | a docking |
    | `reach 5, -4` | traveling to a system |

    The same line is shown to players as the objective, so write it well.

- **Tier** is how trusted a captain must be before the clan offers this work:
  `1` is offered to anyone the clan will talk to, `2` to captains in good
  standing, `3` to proven friends. Higher-tier work should pay better and read
  more sensitive - you are writing the clan's inner circle.
- **Pays** - the reward. Standing quietly scales it up for captains a clan
  likes.
- **Accept On** / **Engage On** (optional) - which bridge station may take on or
  travel to *this* job, e.g. `Accept On: comms`. Leave them off and the job uses
  the ship's usual stations (in Open Universe, command accepts work at comms while
  the helm flies to it); add one only for a task that belongs to a single console.

!!! note "Where the cargo names come from"
    `recover` goals name trade goods. Five exist out of the box:
    `provisions`, `ore`, `gas`, `tech`, and `contraband`. You can reshape the
    economy with a `## Goods` chapter later - see [The dials](dials.md).

!!! success "In play"
    Hail a clan station and its work is on offer, gated by standing.
    Completing a clan's job earns standing along the traits that clan values -
    do the Combine's honest work and the Combine starts to love you.

**Next: [Story and goals](story.md)** - give the sandbox a spine.
