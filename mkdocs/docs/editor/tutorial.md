# Get started: build a character and a scene

This is a hands-on tour. In a few minutes you'll use the editor to build a
**character with a face** and a **short branching conversation** — and watch the
map, graph, and form stay in sync the whole way. You'll barely type any AMD
syntax; the tools write it for you.

!!! note "You need two things"
    - VS Code with the **Artemis AMD** extension installed — see
      [Install it](index.md#install-it).
    - A mission open. Use **your universe file** (the `my_reach.amd` from the
      [writing walkthrough](../writing/getting-started.md)), or make a throwaway
      one to experiment in — Command Palette → **Artemis AMD: New Content File**,
      which scaffolds a complete `.amd` with every section stubbed and opens the
      Map and Graph next to it.

---

## 1. Meet the safety net

Open your `.amd` file. Within a second or two you get **syntax colors** and, a
moment later, **error-checking**.

Try it: in any `# [Name](key)` heading, delete the closing `)`. A **red squiggle**
appears, and the Problems panel (**View → Problems**) explains it. That broken
heading would have made the whole node silently vanish in-game — the editor
catches it before you ever launch.

!!! tip "This is the whole reason to use the extension"
    AMD fails quietly. A typo'd link or a dropped bracket doesn't crash — it just
    makes content not show up, and you spend twenty minutes wondering why. The
    squiggles turn those silent failures loud. Put the `)` back and the squiggle
    clears.

---

## 2. See your story as a graph

Click the **branch icon** in the top-right of the editor toolbar (or Command
Palette → **Artemis AMD: Show Story Graph**). Your content appears as
**swimlanes — one horizontal band per section** (Dialogue, Lifeforms, Goals…),
with links flowing left to right.

A fresh file is nearly empty. Let's fill it.

---

## 3. Add a character — without typing syntax

**Double-click an empty spot** in the graph. Pick **Lifeform (cast)** from the
menu. Two things happen:

1. A new character node is scaffolded into the **Lifeforms** section of your
   `.amd` — the heading, a `Face:`, `Roles:`, `Scene:`, and `Color:` are written
   for you.
2. The **Inspector** opens on it.

Look at your text file: the new `### [New Character](character_1)` block is there.
You didn't type it.

---

## 4. Fill the character in the Inspector

The **Inspector** is your node as a form. It lives in three places — use whichever
you like:

- the **AMD** icon on the left **Activity Bar** (a panel that follows your cursor
  through the file),
- the pop-out tab you got from **Edit…**, or
- a **drawer right inside the graph** (click any node).

Change the **Display** to your character's name — say `Quartermaster Vane`. Set
**Roles** to something like `advisor`. As you type, the change is written into the
`.amd` **live** — no Save, no Apply button. Flip to the text file and watch it
update; edit the text and watch the form follow. It's the same node, three views.

!!! note "Dropdowns where it helps"
    Common fields (`State`, `Kind`, `Scope`, …) show as dropdowns with the valid
    choices, so you don't have to remember them. Use **+ add field** for anything
    else.

---

## 5. Give them a face

A lifeform has a **`Face:`** field, and the Inspector shows a **live portrait**
next to it (as long as the extension can find your Cosmos install — that's where
the face art lives).

**Click the face preview.** The **Face Builder** opens: pick a **race** from the
dropdown, then move the **sliders** — eyes, mouth, hair, and so on — with a
checkbox to toggle the optional features. The portrait updates as you drag, **and
so does your character's `Face:` field** — the changes apply live. When it looks
right, you're done; there's nothing to press.

!!! tip "Already have a face string?"
    The builder **starts from whatever's already in the field**, so you can open
    it to tweak an existing face instead of starting over. And the **Face…**
    button offers quick options too: a random face per race, the `female`/`male`
    keywords, or paste a string from the in-game Avatar Editor.

---

## 6. Add two scenes and connect them

Double-click empty graph space again, twice, choosing **Dialogue scene** each
time. You get two scene nodes in the **Dialogue** lane, each with a `Speaker:` and
a `%` dialogue line ready to fill.

Now wire them together three ways — all without touching link syntax:

- **Character → opening scene.** In the character's Inspector, set the **`Scene:`**
  field to the first scene's key (start typing and let completion help). That's
  who they talk to first.
- **Scene → scene choice.** In the graph, **drag from the first scene node onto the
  second**. The editor writes a choice — `- [New Scene](scene_2)` — into the first
  scene's body. Open that scene in the Inspector and rename the choice's label in
  the **Body** to what the player should see, e.g. `Ask about the cargo`.
- Fill each scene's `%` line with what the character says.

Your conversation now exists, and the graph shows the character in the Lifeforms
lane linking down to the Dialogue lane, with the two scenes joined by a choice.

---

## 7. Read the graph like a map of your story

Now that there's something to see, the graph's tools earn their keep:

- **Collapse a branch.** A node with children shows a **±** badge — click it to fold
  the conversation below it, so a big story stops being a wall.
- **Filter sections.** Uncheck **Lifeforms** in the toolbar and that lane drops out
  and the rest **recompact** — handy for focusing on just the dialogue.
- **Focus one thread.** Right-click a node → **Focus here** to see only the flow
  reachable from it; widen or narrow with the direction/hops controls.
- **Back-links are chips.** A choice that loops back to an earlier scene shows as a
  small **↩ chip** on the source instead of a line running backward — click it to
  jump to the target.

---

## 8. Place it on the map

Some content is physical, not conversational. Open the **Mission Map** (the map
icon in the toolbar, or Command Palette → **Artemis AMD: Show Mission Map**).

- **Right-click empty space → New landmark here** to drop a point (a station, a
  derelict), or **New region here** for a tinted zone (`Center` / `Radius` /
  `Color` are written for you).
- **Drag** a landmark to move it — its `At:` is rewritten; **drag a region's dots**
  to move or resize it.
- **Click** any landmark or region to edit it in the Inspector drawer, right there
  on the map.

Everything you do here edits the same `.amd` your graph and text are showing.

---

## 9. Test it in the game

The editor never runs your mission — it edits the files. To see your character and
scene for real, use your normal loop: **save, restart the mission, and look.**
(For a universe, that's picking it from the Universe dropdown and launching; see
[How to test](../writing/getting-started.md).)

---

## What you learned

You built a character with a portrait and a branching conversation, placed a
landmark, and never fought AMD syntax — the map, graph, inspector, and face tools
wrote it for you, kept each other in sync, and flagged mistakes before they cost
you a launch. From here, the rest of the [writing walkthrough](../writing/index.md)
gives you the *ideas* to fill a universe with; this editor is how you build them
comfortably.
