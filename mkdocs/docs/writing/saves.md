# 10. What the game remembers

A universe is played over many evenings. The crew picks **Continue**, and the
galaxy is as they left it. This page says what "as they left it" means, and
what you may change in your file between evenings without breaking a campaign
that is already under way.

You do not write anything to make saving happen. There is one save per
universe title and slot, in `data/missions/common_data/saves/`, and the game
writes it as things happen - not only when the crew jumps. A finished or failed
step, and what it paid or cost, is in the file within seconds.

## The save file

The file is named for the universe's title and the slot:
`universe_save_the_kestrel_verge_1.yaml` is *The Kestrel Verge* in slot 1. The title is
lower-cased, and every run of spaces and punctuation becomes one `_`. The title is the
one your mission's `story.mast` gives `UNIVERSE_SELECT`.

It is plain text, and it is safe to open (do not change it while the game is running).
What is inside:

| Under | What it holds |
|---|---|
| `players:` | One record per ship: where it is, its jobs, its items, and its standing with every side (`reputation:`) |
| `shared_quests:` | Every step of your story, by **key** only: its state, how far along it is, and a clock's time left |
| `state:` | What the crew has learned (`boarding_facts:`), and what was done in ruins and sites |

A step's `state:` is a number:

| `state:` | The step is |
|---|---|
| `1` | Open. The crew can see it |
| `2` | Hidden, waiting to be revealed |
| `99` | Done |
| `98` | Failed |

**There is no story text in the save** - no title, no description. The save holds the key
of each step and how far the crew has got with it; the words are only in your file. So
the save is no spoiler, and a rewrite between evenings reaches a campaign in progress. A
**job** is different: a job the ship has taken is saved whole, title and all, under the
ship, because the game made that job up and your file cannot make it again.

## What is kept

| Kept between evenings | Notes |
|---|---|
| Where each ship is | Each ship comes back in its own system, not the last jumper's |
| Credits, cargo, upgrades | Per side and per ship |
| Standing with every side | Per ship |
| Every story beat and goal | Done, running, hidden or failed - and a running count (`destroy 4 of 6`) |
| Jobs in hand | Whole, including ones taken after the last jump |
| A clock that is running | It comes back with the time that was **left**. The game writes a running clock down every half minute, so a clock can gain up to that much |
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
| Enemies that were not destroyed | They are there again. Guards destroyed to the last ship, and an enemy system cleared completely, stay gone |
| A set-piece battle | Nothing about it is saved; the step it waits for is. After Continue it is fresh and whole |
| Where a ship was inside its system | It arrives at the system's edge |

On Continue the game builds the system each ship was in, and announces that arrival
only **after** the save is restored. So a step still open that waits for reaching that
system finishes, and a step that is already Done - a `Win:` included - stays done and
does not fire again.

## Changing your file between evenings

A saved campaign and your file are two halves of one thing: the save holds
what the crew **did**, your file holds what there **is** to do. The save keeps
no copy of your beats' titles or text - only each beat's key and its state -
so whatever your file says tonight is what plays.

| You do this | A campaign already under way |
|---|---|
| Reword a title, the prose, an objective, a reward | Sees the new words. Nothing is lost |
| Add a beat, a job, a landmark, a scene | Gets it. A new beat is in the state your file gives it |
| Add steps after the step the crew is on | Has them when it gets there. This is how a campaign is written |
| Add a step behind one that is **finished** | Never shows it: the step that would reveal it was done last week, and a finished step does not reveal again. Add it after the open step, or make it a lead that starts `at once` |
| Change a beat's `Done when:` | Uses the new trigger from now on |
| Change `Starts when:` or `State:` on a beat the save has seen | Nothing. The save keeps the state it has (see the rule below) |
| Move a chapter into a file of its own (`File:`) | Unchanged |
| **Delete** a finished beat | It is gone from the quest log. Its state is *parked* in the save - not deleted - and comes back if you put the record back. The game's report says so: "parked ... story step(s) the universe file no longer has (kept in the save, not shown)" |
| **Delete** the beat the crew is on | Everything after it is **stranded**: hidden, with nothing left to reveal it. The campaign has no next lead. See the warning below |
| **Rename** a beat's key | Starts again as a new beat - unless you add `Was:` (below) |
| Rename a ship in `settings.yaml` | Keeps its jobs and standing - one ship at a time. The game pairs it with the one saved record nobody claimed on its side, and says so: "ship 'Kittiwake' continues the saved record of 'Artemis'". Rename two in one week and both start clean |
| Change the universe's **title** | Is a different campaign with a new save, starting from nothing. The old one is untouched |

**The rule.** The save decides the state of every key it has seen. Your file decides the
state of a key the save has never seen. Every row above follows from it.

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
    (`Then: reveal c`) before the crew finishes `a`.

    If they already have, writing `State: active` or `Starts when: at once` on
    `c` does **not** bring it back: the save has `c` as hidden, and the save wins.
    Give `c` a **new key**, with no `Was:` line, and `Starts when: at once`, and
    change every `Then: reveal` that named the old key. The old key is parked,
    and the new one starts from your file. Lint saw the cut coming: "waits to be
    revealed, and nothing reveals it" (`never-revealed`).

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
whole crew, not one ship; and it is kept between evenings, at the end of the
save under `boarding_facts:`. Nothing takes a fact back once it is learned. A
fact learned on the bridge (in a hail, or by `Then: learn`) is known everywhere;
one learned in the scenes of a site the crew beams down to belongs to that site,
and another site cannot ask for it. Use it for
"they only get this answer once they have heard that one". It is what a
reputation trait was being bent into doing, and it does not move anybody's
standing.

`sbs lint` checks the spelling. Once your mission teaches anything at all,
an `if learned ...` that no `; learn` or `Then: learn` in any of its files
can make true is reported.

## Save slots

A universe can hold several campaigns side by side. The start screen's
**Save Slot** dial picks one, from 1 to 6, and the slot is the number at the end
of the file's name. **Start** says whether to **Continue** it or begin a
**New Game** in it. Use a slot for each table that plays the universe, and one
for yourself, so that walking your own story never touches a crew's save.

**New Game does not ask.** It replaces the campaign in the chosen slot, and keeps
the one it replaced, once, as `<save>.previous.bak`. A second New Game replaces
that copy too. To get the campaign back, close the game, delete the save, and take
`.previous.bak` off the end of the copy's name.

A mission folder made before the dial existed has no **Save Slot** on its start
screen and plays in slot 1. To add the dial, put this line under the `Start:` line
of the `@map` in `story.mast`, with the same indentation:

```
    Save Slot: 'gui_int_slider("$text:int;low: 1.0;high:6.0;", var="SAVE_SLOT")'
```

### Rehearsing a change on a crew's save

Make a copy of your mission folder (a "lab"), and pin it to a slot of its own with
one line in its `story.mast`, under the `UNIVERSE_SELECT` line:

```
default shared SAVE_SLOT = 6
```

The lab has the same title, so without that line the two would share one save. Ask
the host for a copy of the crew's save, name it for slot 6
(`universe_save_the_kestrel_verge_6.yaml`), put your changed file in the lab, and
continue there. The crew's own file is not touched.

## When a campaign is won

A goal with `Win:` ends the game the evening it is finished. After that the
save remembers it. The next Continue shows one card, titled **Campaign won**:
"This campaign has been won (Break the Bone Pile). The story is finished and the
galaxy is still here - fly on." The words in brackets are the title of the step
that won it. Then the crew can fly on: jobs, trade and the galaxy are all still
there, and nothing ends the game again. To start the story over, pick New
Game.

## When a save will not load

If the save file is damaged, **Continue does not start the game**. The start
screen comes back, and where it shows its text it says which file could not be
loaded, why, and where the copy is. The file is left exactly as it was, with a
copy beside it (`<save>.unreadable.bak`, or the `<save>.v1.bak` taken before an
upgrade that failed). Nothing is ever written over a save the game could not
read.

From there the operator chooses:

| To | Do this |
|---|---|
| Start over in the same slot | Set **Start** to **New Game** and press Start. The damaged file is kept once more as `<save>.previous.bak` |
| Play another campaign | Turn the **Save Slot** dial to another slot |
| Get the campaign back | Close the game and put a good copy of the file back under its own name (`<save>.previous.bak` is the campaign as it was before the last New Game) |

A save written by a **newer** build of the game is different: it loads, the
evening plays from it, and nothing is saved over it. The crew is told so on a
card.

**Next: [The complete example](silver-reach.md).**
