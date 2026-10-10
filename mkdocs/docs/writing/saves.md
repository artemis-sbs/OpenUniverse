# 10. What the game remembers

A universe is played over many evenings. The crew picks **Continue**, and the
galaxy is as they left it. This page says what "as they left it" means, and
what you may change in your file between evenings without breaking a campaign
that is already under way.

You do not write anything to make saving happen. There is one save per
universe title and slot, in `data/missions/common_data/saves/`, and the game
writes it as things happen - not only when the crew jumps.

## What is kept

| Kept between evenings | Notes |
|---|---|
| Where each ship is | Each ship comes back in its own system, not the last jumper's |
| Credits, cargo, upgrades | Per side and per ship |
| Standing with every side | Per ship |
| Every story beat and goal | Done, running, hidden or failed - and a running count (`destroy 4 of 6`) |
| Jobs in hand | Whole, including ones taken after the last jump |
| A clock that is running | It comes back with the time that was **left**, give or take half a minute |
| A beat that had started | A `Starts when: signal x` beat that started is not made to wait for `x` again |
| What the crew has learned | `; learn` in a hail and `Then: learn` on a beat |
| What was done in a ruin | Opened barriers, finished repairs, the piece that was taken |
| What was done at a site the party walks | Opened doors, things picked up, people put down, and what was learned there |
| Charted locations, cleared guards, captured stations, market stock | As before |
| That the campaign was won | See the end of this page |

| Not kept | So |
|---|---|
| A hail nobody answered | A beat whose `Action:` calls the crew does not call again on Continue. End an evening at a point where nothing is waiting on the comms |
| Ordinary loot in a ruin | It is there again on the next visit |
| A hidden thing at a walked site that was revealed and not picked up | A prop with `Hidden until:` is hidden again on Continue. Send its signal again (the scene that told the crew about it can be read again), or do not hide what the crew must be able to come back for |
| What a party member was carrying | A key in a pack is gone on Continue. The door it opened stays open |
| Enemies that were not destroyed | They are there again |
| Where a ship was inside its system | It arrives at the system's edge |

## Changing your file between evenings

A saved campaign and your file are two halves of one thing: the save holds
what the crew **did**, your file holds what there **is** to do. The save keeps
no copy of your beats' titles or text - only each beat's key and its state -
so whatever your file says tonight is what plays.

| You do this | A campaign already under way |
|---|---|
| Reword a title, the prose, an objective, a reward | Sees the new words. Nothing is lost |
| Add a beat, a job, a landmark, a scene | Gets it. A new beat is in the state your file gives it |
| Change a beat's `Done when:` | Uses the new trigger from now on |
| **Delete** a beat | It is gone from the quest log. Its state is *parked* in the save - not deleted - and comes back if you put the record back |
| **Rename** a beat's key | Starts again as a new beat - unless you add `Was:` (below) |
| Rename a ship in `settings.yaml` | Keeps its jobs and standing |
| Change the universe's **title** | Is a different campaign with a new save. The old one is untouched |

### `Was:` - renaming a beat

The key in the round brackets is how the save knows a beat. Change it and the
save no longer recognizes the record. `Was:` says what it used to be called:

```amd
### [The Cold Trail](cold_trail)
---
Scope: shared
State: secret
Was: signal_2
Done when: reach 3, -2
---
```

On the next Continue, everything the crew had done on `signal_2` belongs to
`cold_trail`. Remember to change the `Then: reveal signal_2` that pointed at
it. Leave the `Was:` line in for as long as anybody might still have an old
save; it does nothing once it has been used. A record renamed twice lists
both: `Was: signal_2, the_trail`.

`Was:` works on story beats and goals. It names a sibling: for a step inside
an arc, write the step's own old key. (Write the whole old path, `arc/step`,
only if the step also moved to a different arc.)

!!! warning "A beat that was already revealed"
    A deleted beat takes its place in the chain with it. If `a` reveals `b`
    and `b` reveals `c`, deleting `b` from a campaign that has finished `a`
    leaves `c` hidden with nothing to reveal it. Point `a` at `c`
    (`Then: reveal c`) before the crew finishes `a` - or, if they already
    have, give `c` `State: active` so it is simply there.

## Facts: `learn` and `learned`

The game keeps one more thing you can write to: what the crew **knows**.

```amd
- [Log it.]() ; learn the manifest was altered
```

```amd
- [We know about the manifest.](quill_confession) if learned the manifest was altered
%{learned the manifest was altered} So you saw it too.
```

```amd
### [Read the Ledger](read_ledger)
---
Scope: shared
State: active
Done when: scan 1 derelict
Then: learn the ledger page
---
```

A fact is a few plain words. It is known or it is not; it belongs to the
whole crew, not one ship; and it is kept between evenings. Use it for
"they only get this answer once they have heard that one". It is what a
reputation trait was being bent into doing, and it does not move anybody's
standing.

`sbs lint` checks the spelling. Once your mission teaches anything at all,
an `if learned ...` that no `; learn` or `Then: learn` in any of its files
can make true is reported.

## Save slots

A universe can hold several campaigns side by side. The start screen's
**Save Slot** dial picks one; **Start** says whether to Continue it or begin a
New Game in it. A New Game keeps the campaign that was in the slot once, as
`<save>.previous.bak`.

## When a campaign is won

A goal with `Win:` ends the game the evening it is finished. After that the
save remembers it. The next Continue shows one card - *This campaign has been
won* - and then the crew can fly on: jobs, trade and the galaxy are all still
there, and nothing ends the game again. To start the story over, pick New
Game.

## When a save will not load

If the save file is damaged, or was written by a newer build of the game, the
evening still plays - as a new game that is **not saved** - and the crew is
told so on a card. The file is left exactly as it was, with a copy beside it.
Nothing is ever written over a save the game could not read.

**Next: [The complete example](silver-reach.md).**
