# Reputation - how a side sees a ship

Every side in your universe keeps a private opinion of every player ship. That opinion
is one number, called **standing**. It decides what work a side offers, what the work
pays, how a station greets the ship, what a ceasefire costs, and whether an old enemy
will take the crew as an ally.

This page is the whole of it: every line you can write, what moves standing, and what
the game does at each number. The walkthrough introduces it in
[Sides](../writing/sides.md) (the `Values:` line) and [The dials](../writing/dials.md)
(the thresholds).

| Word | Meaning |
|---|---|
| Trait | One way of behaving a side can care about: `honest`, `fearsome`, `generous` |
| Value | A trait a side cares about, with a weight for how much |
| Deed | Something the crew does that a side hears about |
| Score | How the ship rates on one trait with one side, from -100 to 100. It starts at 0 |
| Standing | What one side thinks of one ship, from -100 to 100. It starts at 0 |
| Threshold | A standing at which something changes |

## What you write

All of it is in your `.amd` files. Nothing here needs a line of script.

| Where | Line | Example |
|---|---|---|
| A side | `Values:` | `Values: honest 40, generous 30` |
| A job | `Tier:` | `Tier: 2` |
| A story step or goal | `Standing:` | `Standing: hollin honest 15, hollin generous 10` |
| An answer in a hail | `earns` after the `;` | `- [Pay the levy](paid) ; costs 100 credits, earns hollin honest 20` |
| A line or an answer | a guard on `standing`, or on a trait | `%{standing >= 20} Welcome back.` / `if standing >= 20` |
| A captain | `Values:` of their own | `Values: honest 40, kind 30` |
| The title record | the six thresholds, and `Axis:` | `Alliance at: 60` |

## What a side values

The game measures a ship on seven pairs of traits. Neither end of a pair is the good one:
a navy may value `by-the-book`, a band of wreckers `fearsome`.

| One end | The other end |
|---|---|
| `honest` | `liar` |
| `fearsome` | `cowardly` |
| `peaceful` | `violent` |
| `generous` | `selfish` |
| `kind` | `cruel` |
| `resourceful` | `by-the-book` |
| `intellectual` | `foolish` |

A side's `Values:` line names the traits it cares about, each with a weight. The weights
say how much each one counts beside the others. They do not have to add up to anything.

```
### [Hollin Compact](hollin)
---
Values: honest 40, generous 30
---
```

**How standing is worked out.** For each trait a side values, the game keeps a score for
the ship. Standing is the average of those scores, with the weights deciding how much
each one counts. For Hollin, who value `honest 40, generous 30`:

| The ship's scores with Hollin | Standing |
|---|---|
| honest 20, generous 20 | 20 |
| honest 35, generous 0 | 20 |
| honest 0, generous 20 | 8 |
| honest 100, generous 0 | 57 |
| honest 20, generous -20 | 2 |

So a deed that touches only one of a side's values moves standing part of the way, and a
crew that pleases a side in one thing only can never reach the top. With Hollin, honesty
alone stops at 57.

A score moves toward the other end of its pair when a deed names that end. A deed worth
`selfish 20` takes 20 off the ship's generous score with that side. Scores stop at -100
and 100.

| You write | What the game does |
|---|---|
| No `Values:` line on a side | Standing is the plain average of every score the ship has with that side, and finishing its jobs earns nothing |
| A trait misspelled in `Values:` (`honset 40`) | The side values a trait no deed can name. Lint warns (`values-unknown-trait`) and lists the fourteen |
| A trait with no number (`Values: honest, generous`) | That trait counts for nothing. Lint warns (`values-no-weight`) |
| `Value:` for `Values:` | The side values nothing. Lint warns (`unknown-field`) |

## What moves standing

There are three kinds of deed. Standing with one side is no business of another: nothing
the crew does for one side is heard by the others, unless a deed names both.

### Finishing a side's job

When a ship finishes a job a side offered, the game adds `5 x tier` to the ship's score
on **every** trait that side values. So the standing moves by exactly that much:

| The job | Standing with the side that offered it |
|---|---|
| Tier 1 (no `Tier:` line) | +5 |
| Tier 2 | +10 |
| Tier 3 | +15 |

You write nothing for this. A `Standing:` line on a job does nothing: a job's worth to
standing is always 5 for each tier. A side with no `Values:` gets nothing from its jobs.

### An answer in a hail

An answer can carry a deed after its `;`:

```
- [Pay the relay levy](hollin_levy) ; costs 100 credits, earns hollin honest 20, earns hollin generous 20
- [Call the levy a racket](hollin_cold) ; earns hollin selfish 20
```

`earns` takes three things: a side's key, a trait, and a number. Separate several
outcomes with commas. The deed goes to the ship whose Comms gave the answer.

**An answer can be given again.** The crew can hail a station as often as they like, and
each time the answer does its deed again. An answer that earns standing and costs nothing
can be pressed until the side adores the ship. Give a deed in talk a `costs`, or expect it
to be farmed. `costs` that the crew cannot pay refuses the answer, and the same buttons
stay.

### A step of the story

A step in your Narrative or Goals chapter can carry a deed on its fence:

```
### [The Long Count](long_count)
---
Scope: shared
Done when: reach 3, 1
Standing: gleaners fearsome 70
---
```

`Standing:` takes the same three things as `earns`, comma-separated (`Earns:` is its
older spelling). A shared step's deed reaches **every** player ship flying when it is
done: played with two ships, both had the same new standing. A step is finished once, so
its deed happens once. That makes a step the place to award standing when you want to
choose the evening it happens.

A `Penalty:` can carry an `earns` too. Its number is applied exactly as written, so a
penalty that should cost standing needs a minus: `earns hollin honest -10`.

When a finished job or step moves anybody's standing, the game shows a card titled
**Comms Chatter**: "Word of your deeds spreads among the sides."

### Deeds that do nothing

| You write | What the game does |
|---|---|
| A deed in a trait the side does not value (`earns hollin fearsome 20`) | The score is kept. Standing does not move |
| A side's key misspelled (`earns holin honest 20`) | The score is kept for a side that does not exist. Lint warns (`earns-unknown-side`) |
| A deed with no number (`earns hollin honest`) | Nothing. Any `costs` beside it is still charged. Lint warns (`earns-shape`) |
| Two traits joined with `and` (`earns hollin honest 20 and generous 20`) | Neither deed happens. Lint warns (`outcome-run-together`). Write two `earns`, with a comma |
| No comma between `costs 100 credits` and `earns` | The credits are taken. No deed. Lint warns (`outcome-run-together`) |
| No `;` in front of the outcomes | Nothing at all. Lint warns (`choice-tail-ignored`) |

## Reading standing in a line

A guard, in curly brackets right after the `%`, decides whether a line can be said. The
same comparison after `if` on an answer decides whether the answer is offered.

```
%{standing >= 20} Kestrel Relay knows your ship, captain. What do you need?
%{standing < 20} Hollin Compact. State your business, captain.

- [Ask who keeps the Gleaners' books](edda_tip) if standing >= 20
```

| The word | What it reads |
|---|---|
| `standing` | The ship's standing with the speaker's side. With a captain who has `Values:` of their own, the ship's standing with that captain |
| A trait (`fearsome`) | The ship's score on that one trait with the same side |
| `credits` | The crew's credits |
| `learned <fact>` | Whether the crew knows a fact. See [What the game remembers](../writing/saves.md) |

A guard is one comparison: a word, one of `>=`, `>`, `<=`, `<`, and a number. An answer's
`if` goes after the key and before the `;`.

**Guard every line, or none.** When more than one line can be said, the game picks one
of them **at random**. A line with no guard can always be said, so beside a guarded line
it is heard by everybody some of the time.

**A door closes as soon as standing falls.** An answer's `if` is read each time the hail
opens. There is no "you had it once". The game does not tell the crew a door has closed:
if the story needs them to know, say it in a guarded greeting.

| You write | What the game does |
|---|---|
| Two comparisons: `%{standing >= 0 and standing < 20}` | The line is never said. Lint warns (`unreadable-guard`, `guard-joined`) |
| The curly brackets left off: `%standing < 20 Hollin Compact.` | No guard. The station says the words `standing < 20` out loud, to everybody. Lint warns (`guard-no-braces`) |
| A word misspelled in a guard: `%{standng >= 20}` | The line is never said. Lint does not see it |
| Words for a sign: `%{standing at least 20}` | The same |

## What standing changes: the thresholds

Standing does nothing by itself. It matters where it crosses a line. These are the lines
the game uses when you write none:

| Standing with a side | What changes |
|---|---|
| 20 or more | The side offers tier 2 jobs |
| 50 or more | The side offers tier 3 jobs |
| 20 or more, with a `foe` | A foe offers work at all. Below 20 a foe's station has no jobs |
| Above 0 | Jobs pay more: 1 percent more for each point. At 20 a 250 credit job pays 300. At 100 it pays double |
| Below 30, with a `foe` the crew is at war with | A ceasefire costs 20 credits for each point short of 30: 600 at 0, 400 at 10, 200 at 20 |
| 30 or more, with a `foe` | A ceasefire is free |
| 60 or more | A side the crew has a ceasefire with will accept an alliance |

Standing below 0 counts as 0 for prices. A side that despises the crew charges 600 for a
ceasefire, the same as a side that has never heard of them. It pays no bonus and offers
nothing above tier 1. There is no tier above 3: a job with `Tier: 4` is never offered.

**No screen shows the number.** The crew learns their standing from what changes: a
greeting, a price, a job on offer. Write lines that tell them.

### On a station's Comms

All of it shows on the buttons of a side's station, when Comms selects it:

| Button | When it is there |
|---|---|
| **Hail** and the side's name (**Hail Hollin Compact**) | The side has a Dialogue record with `Speaker:` its key and `When: comms` |
| The job's title and its pay (**Escort (300 cr)**) | One for each job in the side's `Offers:` whose tier the standing has reached. The pay already includes the bonus |
| **Negotiate Ceasefire** and its price (**Negotiate Ceasefire (600 cr)**) | The crew is at war with this side and has the credits for the price. It takes the credits and ends the war: "We have an understanding. Hostilities are suspended (tribute: 600 cr)." |
| **Propose Alliance** | The crew has a ceasefire with this side and standing 60 or more. "Then we stand together. The side is honored to call you ally." |
| **Ransom** and an officer's name and price | Only with the Admiral: this side holds one of the Admiralty's officers. The price is 400, plus 15 credits for each point of standing short of 30 (850 at 0) |

**An alliance is offered only after a ceasefire.** A side written `Disposition: neutral`
never offers one, however high the standing. Only an old enemy becomes an ally. A
ceasefire and an alliance are kept in the save.

While the crew is at war with a side, its stations also carry buttons of the game's own,
**Hail** and **Taunt** among them. Yours is the one with the side's name in it.

## Changing the thresholds

Each threshold is a dial. You do not have to write any. To move one, put its line in the
title record at the very top of the file (under `Display:`). These are the game's own
numbers:

```
Job tiers: 20, 50
Foe deals at: 20
Ceasefire free at: 30
Ceasefire per point: 20
Alliance at: 60
Max reward: 2.0
```

| Dial | What it sets |
|---|---|
| `Job tiers: 20, 50` | The standing for tier 2, then for tier 3. It needs both numbers |
| `Foe deals at: 20` | The standing at which a foe offers work |
| `Ceasefire free at: 30` | The standing at which a ceasefire costs nothing. A ransom's price counts from the same line |
| `Ceasefire per point: 20` | Credits for each point short of that |
| `Alliance at: 60` | The standing for an alliance |
| `Max reward: 2.0` | How many times the pay at standing 100. `2.0` is double, `1.5` is half again |

!!! warning "Lint does not know these six lines"
    Write one and lint warns: "`Job tiers` is not a field a map has". The game reads the
    line and uses it all the same. Because lint warns on every dial line, right or
    wrong, check these by eye:

    | The mistake | What the game does |
    |---|---|
    | A dial misspelled: `Aliance at: 60` | Ignored. The game's own number stands |
    | A dial in the Scenario record, not the title record | Ignored |
    | `Job tiers: 20`, with one number | Ignored |
    | `Max reward: 200%` | The mission stops working the first time a job's pay is worked out. Write `2.0` |

### Your own virtues: `Axis:`

For a universe whose morality is different, the title record can replace the seven
pairs with your own, one `Axis:` line per pair:

```
Axis: pious / heretical
Axis: loyal / faithless
```

Writing **any** `Axis:` line replaces **all seven**: sides then value, and deeds then
name, only your words. This one was read from the game's code and has not been played
for this page.

## Standing with a captain

A captain with `Values:` of their own is regarded personally. In a record whose
`Speaker:` is that captain, `standing` is the ship's standing with **that captain**, not
with their side, and a deed with the captain names the captain's key after `earns`:

```
- [Give her the news from down the lanes](edda_news) ; earns edda honest 20, earns edda kind 20
```

| Fact | What it means for your story |
|---|---|
| Personal standing and a side's standing never touch | If a deed should count with both, write two deeds in one answer: `earns sable honest 20, earns gleaners fearsome 10` |
| A captain with no `Values:` and a `Side:` is read against the side's `Values:` | Deeds in traits the side does not value leave the captain's standing at 0 |
| A captain's key and a side's key go in the same place after `earns` | The game tells them apart only by the word. Never give a captain the same key as a side |
| A rival is a captain whose standing has fallen below a line your guards choose | There is no switch for it. Write the cold greeting, and withhold what a friend would be told |
| `Rival when:` and `Flies:` on a captain do nothing today | Lint accepts them. Nothing happens when `Rival when:` comes true, and a captain has no ship. A rival does not come after the crew |

[Captains and the cast](../writing/people.md) has the captain's other lines.

## Where standing is kept

| Fact | What it means |
|---|---|
| Standing belongs to a ship | Two ships in one game each have their own. A deed in an answer goes only to the ship that gave it. A shared story step's deed goes to every ship flying |
| It is saved in the ship's record | Close the game and Continue: it is still in force. In the save file it is under the ship, as `reputation:`, by side |
| A ship renamed in `settings.yaml` keeps it | One ship at a time. The game pairs the renamed ship with the one saved record nobody claimed on its side. Rename two in one week and both start at 0 |
| **New Game**, or a changed universe title, starts at 0 | Both start a new campaign. See [What the game remembers](../writing/saves.md) |
| Standing is not war and peace | Whether a side shoots the crew is diplomacy, and it is side-wide: a ceasefire or an alliance is for the whole crew. Standing is each ship's own |

## If something goes wrong

| What you see | Likely cause |
|---|---|
| No **Hail** button on a side's station | The record has no `When: comms`, its `Speaker:` is not that side's key, or the chapter's key is not `dialogue` |
| The station says nothing when hailed | No line can be said. A guard is misspelled, or has two comparisons in it |
| The station says `standing < 20` out loud | The curly brackets are missing from that guard |
| A deed changes nothing | The side's key or the trait after `earns` is misspelled, or there is no number, or the side does not value that trait |
| Standing rises more slowly than you worked out | A trait in that side's `Values:` is misspelled, or the deed touches only one of its values |
| A tier 2 job never appears | Standing with that side is below 20. Or the job is not in the side's `Offers:` |
| The mission stops working when Comms selects a station | A `Tier:` that is not a number (`Tier: two`), or a `Max reward:` with a percent sign. Read `mast.runtime.log` |
| A side already greets the ship as a friend at the start | The game continued an old save. Delete the save, or choose **New Game** |
| The standing is 0 this week | **New Game** was chosen, the title changed, or two ships were renamed at once |

## Related

- [Sides - who lives here](../writing/sides.md): the side record and its `Values:`.
- [Jobs - the work they offer](../writing/jobs.md): `Tier:` and `Offers:`.
- [Dialogue](../writing/dialogue.md): calls, answers and guards.
- [The dials](../writing/dials.md): the thresholds beside the galaxy's other dials.
- [What the game remembers](../writing/saves.md): standing in the save.
- Outside a universe, a mission's sides can value deeds too: see "Reputation: a side that
  values deeds" in the library's
  [Sides, lifeforms & faces](https://artemis-sbs.github.io/sbs_utils/build/sides-lifeforms/).
  Tiers, prices and ceasefires are Open Universe's.
