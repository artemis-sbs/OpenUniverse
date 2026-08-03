# Getting started

Two one-time steps, then you never think about them again - and then a
one-heading universe that already plays.

!!! note "The finished example is already in the box"
    The universe this walkthrough builds, **The Silver Reach**, ships with the
    mission (`silver_reach.amd`) and is playable from the Universe
    dropdown right now. You can peek at it whenever a page here leaves you
    unsure - or copy it wholesale and carve your own galaxy out of it. The
    steps below build it from a blank page, using `my_reach` as your file's
    name so it never collides with the shipped copy. (Keys and display names
    must be unique across the dropdown - when you rebuild the example
    verbatim, keep your own `key:` and `display:` in the registration entry.)

## Hang your universe on the shelf

**1.** Create your file next to the existing ones:

```
OpenUniverse/my_reach.amd
```

Universes live at the mission root, not inside `universe_core/`. That addon is the
**engine** - a mission built on Open Universe loads it to get the universe machinery,
and should not inherit somebody else's universes along with it, the same way
LegendaryMissions keeps its maps out of its addons. Your `.amd` is found because the
mission's own folder is looked in first.

**2.** Add it to the game's universe list so it appears in the **Universe**
dropdown on the start screen. Open `OpenUniverse/universes.mast` and
copy an existing entry, filling in your name (this is the only file you will
touch that is not your own):

````
=== universe_my_reach
metadata:``` yaml
type: universe/my_reach
key: my_reach
display: My Reach
universe: my_reach.amd
```
    ->END
````

Think of it as the card catalog entry: the same name in three places
(`universe_my_reach`, `universe/my_reach`, `my_reach`), the display name
players see, and your filename. Copy, rename, done.

!!! tip "How to test"
    Start the Open Universe mission, pick your universe from the dropdown, and
    launch. That is the whole test loop: save the file, restart the mission,
    see your change. You will do this a lot - it is fast.

## A galaxy with a name

Put this in your file:

```
# [The Silver Reach](the_silver_reach)
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

**Next: [Sides](sides.md)** - who lives here.
