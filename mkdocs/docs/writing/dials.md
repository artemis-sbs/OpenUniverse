# The dials (only if you want them)

Everything so far ran on default tuning. The root fence - the one at the very
top under your `#` title - accepts dials that reshape the whole galaxy.
**Skip this page freely.** Nothing here is required; this is mastering, not
writing.

## The galaxy's shape

All percentages; each line optional:

```
Station mix: 15%      // chance a system holds a station
Enemy mix: 15%        // chance a system holds hostiles
Nebula mix: 12%       // chance a system is nebula
Anomaly mix: 8%       // chance of an anomaly
Derelict chance: 40%  // chance a system hides a wreck to scan
Outpost chance: 40%   // chance of a minor outpost
Mine chance: 50%      // chance an enemy system is mined
Loot max: 2           // most loot caches per system
```

A trade-opera galaxy might run `Enemy mix: 5%` and `Station mix: 25%`; a war
story the reverse. [Regions](map.md) override any of these locally. How many
ships an enemy system then holds is Difficulty's business, and the Danger
setting multiplies every `Enemy mix:`: see
[Battles and fleets](../reference/battles.md).

## The reputation economy

How fast trust converts to access:

```
Job tiers: 20, 50        // standing needed for tier 2 / tier 3 work
Foe deals at: 20         // standing at which a foe side will deal at all
Ceasefire free at: 30    // standing at which peace costs nothing
Ceasefire per point: 20  // credits per missing point below that
Alliance at: 60          // standing at which a side becomes an ally
Max reward: 2.0          // pay multiplier at maximum standing
```

These go in the root fence, at the top of the file. Lint does not know them yet
and warns on each one ("is not a field a map has"); the game reads them all the
same. What each threshold opens is on the [Reputation](../reference/reputation.md)
page.

## Your own virtues

For a universe whose morality is genuinely different, you can replace the
seven trait pairs themselves with your own - one `Axis:` line per pair:

```
Axis: pious / heretical
Axis: loyal / faithless
```

At which point sides value, and captains are judged on, *your* virtues. That
is the deepest dial there is; most universes never need it.

## The economy (Goods)

A `## Goods` chapter renames the galaxy's trade goods and how common each is
as loot. Omit it for the built-in five (`provisions`, `ore`, `gas`, `tech`,
`contraband`).

```
## [Goods](goods)

### [Provisions](provisions)
---
Weight: 30
---
Foodstuffs and stores - common cargo on the frontier lanes.
```

Drop goods or reweight them for a different economy - a spice route versus a
tech-salvage galaxy.

## When the file gets big: splitting

One file is right for a small universe. When a chapter outgrows the page, move
its entries to their own file and leave a pointer:

```
## [Dialogue](dialogue)
---
File: dialogue/veil.amd
File: dialogue/lantern.amd
---
```

The named files contain just that chapter's entries and are spliced in, in
order. The main file stays what it should be: a readable table of contents.
(This is exactly how the shipped `default.amd` is organized - its dialogue,
captains, and cast each live in their own file.)

**Next: [The complete example](silver-reach.md)** - the whole Silver Reach in
one listing.
