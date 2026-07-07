# Build a Universe - the writer's walkthrough

This walkthrough is for **science fiction writers, not programmers**. If you
can write a series bible - the factions, the places, the people, the story -
you can build a playable galaxy for the Open Universe. Everything you will
write is plain text in one file. There is no code in this walkthrough. There is
no code in your universe.

You do not need to read the whole thing. Each page adds **one** idea, the
universe is playable after **every** page, and you can stop at any point and
have a finished galaxy. When you want exact label lists instead of a tour,
see the [reference](../reference/index.md).

**What we build:** a small frontier galaxy called **The Silver Reach** - two
factions, honest work, a three-chapter story, a war to win, and a pirate
captain who holds a grudge. The finished file is on
[the complete example](silver-reach.md) page - and it ships with the mission,
playable from the Universe dropdown right now.

---

## Before you start: three ground rules

1. **Write in a plain-text editor** - Notepad, VS Code, Sublime, anything that
   saves `.amd` files as plain text. **Do not draft in Microsoft Word**: Word
   silently replaces straight quotes with curly ones and hyphens with long
   dashes, and the game can only display plain keyboard characters. If a line
   looks right but behaves wrong, this is the first thing to check.

2. **Lines starting with `//` are notes to yourself.** The game skips them.
   Use them freely.

3. **Everything is optional except the title.** Every rule, dial, and section
   you do not write falls back to a sensible built-in. You never have to
   configure anything to get started - you only write the parts you care
   about.

---

## The shape of the file (learn this once)

Your whole universe is one `.amd` file, and every piece of it - a faction, a
job, a chapter of story - has the same three-part shape:

```
### [The Red Veil](veil)         <- a heading: a NAME in [ ] and a (key)
---                              <- a fence: 3 dashes on their own line
Color: #cc2244                   <- the fact sheet: one fact per line
Disposition: foe
---                              <- the closing fence
Corsairs of the outer dark.      <- the prose: what players read
They take what the light forgets.
```

- **The heading** names the thing: the display name in `[...]`, then its **key**
  in `(...)` - a short one-word nickname, lowercase, no spaces. Other lines refer
  to it by this key, the way a screenplay refers to `INT. BRIDGE` after introducing
  it once. Keys must be unique. (The brackets are what make it a *heading*; that
  keeps `#` free to be a markdown heading in your prose - see below.)
- **The fence** holds the fact sheet: `Label: value`, one per line, like the
  header of a character sheet. Skip any fact you don't care about.
- **The prose** is yours. Everything under the fence that isn't a heading is
  description - the flavor text players actually read. It renders as **markdown**,
  so you can use `#`/`##` headings, `-` bullet lists, blank-line paragraphs, and
  inline `image://` / `ship://` / `face://` objects to make it rich.

The number of `#` marks is the outline level, exactly like headings in a
document: `#` is the universe itself, `##` is a chapter (Clans, Jobs,
Story...), `###` is one entry in that chapter.

That is the entire format. Everything from here on is just *what to write*.

**Next: [Getting started](getting-started.md)** - hang your universe on the
shelf and give it a name.
