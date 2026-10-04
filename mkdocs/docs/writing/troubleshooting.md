# Troubleshooting - the five classic mistakes

1. **Curly quotes and long dashes** from drafting in Word. The game draws
   plain keyboard characters only. It swaps a curly quote or a long dash for
   the plain one as it reads your file, so the crew sees clean text, and
   `sbs lint` names each one so you can fix it. Better, draft in a
   plain-text editor from the start.

2. **A key that doesn't match.** `Offers: bounty` needs a job whose heading
   ends in `(bounty)`; `Then: reveal dimming_2` needs a beat keyed
   `(dimming_2)`; `Scene: quill_hail` needs a scene keyed `(quill_hail)`.
   Misspelled keys don't error - the connection just quietly never happens.
   When something is silently missing in play, check its key first.

3. **A heading that is not quite a heading.** `### [Name](key)` works. These
   do not, and the entry they were meant to start is simply not there:
   `###[Name](key)` (no space after the `#`), `### Name (key)` (no square
   brackets), `### [Name] (key)` (a space before the round bracket), and
   anything with spaces in front of the `#`. Same for the fence: it must be
   a line of exactly three dashes, `---`, and nothing else. `sbs lint` names
   each of these.

4. **A fact outside the fence** (or prose inside it). Facts go between the
   `---` lines; story goes below them. If a `Color:` line is showing up in
   your description text, it's outside the fence.

5. **Two things with the same key.** Keys are nicknames, and nicknames must
   be unique across the file.

## The file at a glance

When you're lost, this is the whole shape of a universe file - every chapter
optional, every entry the same heading / fact sheet / prose shape:

```
# [The Silver Reach](the_silver_reach)    <- the title and the world's prose
## [Sides](sides)                         <- the factions (character sheets)
### [The Lantern Combine](lantern)
### [The Red Veil](veil)
## [Jobs](jobs)                           <- the work sides offer
### [Convoy Escort](escort)
## [Narrative](narrative)                 <- the story, chapter by chapter
### [The Dimming: A Cold Lane](dimming_1)
## [Goals](goals)                         <- how the campaign ends
### [Break the Veil](goal_break_veil)
## [Regions](regions)                     <- the map's moods
### [The Veilfall](veilfall)
## [Landmarks](landmarks)                 <- the legendary places
### [The Pale Ark](pale_ark)
## [Captains](captains)                   <- the named people
### [Mara Dusk](mara)
## [Lifeforms](lifeforms)                 <- the comms cast and passengers
### [Harbormaster Quill](quill)
## [Dialogue](dialogue)                   <- the words
### [Veil Hail](veil_hail)
```

Every heading, chapters included, is written `[Name](key)`. (The arrows and
the words after them are notes on this page, not part of the file.)

The rest is world-building - and that part was always your job, not the
computer's.
