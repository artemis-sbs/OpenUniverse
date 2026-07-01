# Getting started

Two one-time steps, then you never think about them again - and then a
one-heading universe that already plays.

## Hang your universe on the shelf

**1.** Create your file next to the existing one:

```
OpenUniverse/universe/silver_reach.amd
```

**2.** Add it to the game's universe list so it appears in the **Universe**
dropdown on the start screen. Open `OpenUniverse/universe/universes.mast` and
copy the existing entry, filling in your name (this is the only file you will
touch that is not your own):

````
=== universe_silver_reach
metadata:``` yaml
type: universe/silver_reach
key: silver_reach
display: The Silver Reach
universe: silver_reach.amd
```
    ->END
````

Think of it as the card catalog entry: the same name in three places
(`universe_silver_reach`, `universe/silver_reach`, `silver_reach`), the
display name players see, and your filename. Copy, rename, done.

!!! tip "How to test"
    Start the Open Universe mission, pick your universe from the dropdown, and
    launch. That is the whole test loop: save the file, restart the mission,
    see your change. You will do this a lot - it is fast.

## A galaxy with a name

Put this in your file:

```
# The Silver Reach
---
Display: The Silver Reach
---
A ribbon of frontier stars beyond the last patrol line. Freight moves by
lantern-light convoys, and the dark between systems belongs to whoever
claims it.
```

**That is a complete, playable universe.** Launch it and you get a full
procedural sandbox: stations, nebulae, enemies, derelicts, trade goods, and a
working reputation system - all running on the built-in defaults. Your prose
is its description.

Everything after this page is you replacing defaults with authorship.

**Next: [Clans](clans.md)** - who lives here.
