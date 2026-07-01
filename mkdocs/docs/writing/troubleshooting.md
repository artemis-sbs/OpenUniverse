# Troubleshooting - the five classic mistakes

1. **Curly quotes and long dashes** from drafting in Word. The game speaks
   plain keyboard characters only. Fix the quotes, or better, draft in a
   plain-text editor from the start.

2. **A key that doesn't match.** `Offers: bounty` needs a job whose heading
   ends in `(bounty)`; `Then: reveal dimming_2` needs a beat keyed
   `(dimming_2)`; `Scene: quill_hail` needs a scene keyed `(quill_hail)`.
   Misspelled keys don't error - the connection just quietly never happens.
   When something is silently missing in play, check its key first.

3. **No space after the `#`.** `### Name (key)` works; `###Name (key)` does
   not. Same for the fence: it must be a line of *only* dashes.

4. **A fact outside the fence** (or prose inside it). Facts go between the
   `---` lines; story goes below them. If a `Color:` line is showing up in
   your description text, it's outside the fence.

5. **Two things with the same key.** Keys are nicknames, and nicknames must
   be unique across the file.

## The file at a glance

When you're lost, this is the whole shape of a universe file - every chapter
optional, every entry the same heading / fact sheet / prose shape:

```
# The Silver Reach              <- the title and the world's prose
## Clans                        <- the factions (character sheets)
### The Lantern Combine (lantern)
### The Red Veil (veil)
## Jobs                         <- the work clans offer
### Convoy Escort (escort)
## Narrative                    <- the story, chapter by chapter
### The Dimming: A Cold Lane (dimming_1)
## Goals                        <- how the campaign ends
### Break the Veil (goal_break_veil)
## Regions                      <- the map's moods
### The Veilfall (veilfall)
## Landmarks                    <- the legendary places
### The Pale Ark (pale_ark)
## Captains                     <- the named people
### Mara Dusk (mara)
## Lifeforms                    <- the comms cast and passengers
### Harbormaster Quill (quill)
## Dialogue                     <- the words
### Veil Hail (veil_hail)
```

The rest is world-building - and that part was always your job, not the
computer's.
