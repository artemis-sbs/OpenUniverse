# Story and goals

The sandbox is now alive but directionless. A `## Narrative` chapter gives it
a spine: a chain of story beats that reveal one another, like chapters. A
`## Goals` chapter decides how the campaign ends.

## The story (Narrative)

Each beat has a trigger (`When:` - the same English phrases as job goals) and
points at the next beat (`Then: reveal ...`).

```
## [Narrative](narrative)

### [The Dimming: A Cold Lane](dimming_1)
---
Scope: shared
State: active
When: reach -4, 2
Then: reveal dimming_2
---
Three Combine convoys have gone dark in a month, and the Combine is
quietly asking for outside help. Their harbormaster waits at the home
lanterns at (-4, 2).

### [The Dimming: Ash on the Manifest](dimming_2)
---
Scope: shared
State: secret
When: scan 2 derelicts
Then: reveal dimming_3
Pays: 200 credits
---
The lost convoys did not vanish - something left the wrecks adrift off
the lanes. Find them and read what is left in the hulls.

### [The Dimming: The Long Answer](dimming_3)
---
Scope: shared
State: secret
When: destroy 5 veil
Pays: 600 credits
Earns: lantern honest 15, lantern generous 10
---
The manifests all point one way: the Red Veil is bleeding the lanes dry.
The Combine will not say the word "war" - but they will pay well for
captains who end this quietly.
```

- **Scope: shared** - the whole crew works these together; one shared story.
  Write it on every beat.
- **State** - `active` means live from the first moment; `secret` means
  hidden until an earlier beat reveals it. Your **first chapter is `active`,
  the rest are `secret`** - that's the whole pattern.
- **Then: reveal <key>** - chains to the next beat. The chain is your table
  of contents: `dimming_1 -> dimming_2 -> dimming_3`.
- **Pays / Earns** - beats can pay credits and shift reputation, exactly like
  jobs. `Earns: lantern honest 15` reads: with the *lantern* clan, along the
  *honest* trait, gain *15*.

!!! success "In play"
    The first beat is in the crew's quest log at launch; each completed
    chapter reveals the next. Your prose is the briefing text for each.

## How it ends (Goals)

A goal is written exactly like a story beat, plus one fact: `Win: true` (or
`Lose: true`) ends the campaign when it completes. The `Citation:` is the text
on the end card - write it like the closing lines of the episode.

```
## [Goals](goals)

### [Break the Veil](goal_break_veil)
---
Scope: shared
State: active
When: destroy 15 veil
Win: true
Citation: The Red Veil is broken and the lanterns burn the length of the Reach. The convoy families will tell this captain's story for a generation.
---
End the Veil's grip on the Reach for good - fifteen of their hulls, however
long it takes - and win the lanes their peace.
```

Skip this chapter entirely and your universe is an endless sandbox. That is a
legitimate choice, not a missing feature.

**Next: [Painting the map](map.md)** - regions and landmarks.
