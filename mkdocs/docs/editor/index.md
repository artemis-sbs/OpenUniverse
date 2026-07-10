# The AMD editor for VS Code

You can write a whole universe in Notepad — everything is plain text. But if you
use [Visual Studio Code](https://code.visualstudio.com/) (it's free), the
**Artemis AMD** extension turns that plain text into a living authoring surface:
it catches mistakes as you type, draws your story as a graph and your systems as
a map, and lets you edit any node in a form — faces and all — without hand-typing
AMD syntax.

It's optional. Nothing here changes your `.amd` files' format; the extension just
makes them easier to see and safer to edit.

!!! tip "In a hurry?"
    Jump to the [**Get started tutorial**](tutorial.md) — it installs the
    extension and builds a character with a face and a scene in a few minutes.

---

## Install it

1. **Get VS Code** if you don't have it: <https://code.visualstudio.com/>.
2. **Download the extension.** Go to the
   [sbs_cli releases page](https://github.com/artemis-sbs/sbs_cli/releases) and
   grab the `amd-language-*.vsix` from the newest **"Artemis AMD (VS Code)"**
   release.
3. **Install the `.vsix`.** In VS Code, open the Command Palette
   (`Ctrl+Shift+P`), run **Extensions: Install from VSIX…**, and pick the file
   you downloaded.
4. **Open your mission folder** (the one with your `.amd` files) and open any
   `.amd` file. Colors appear immediately; the smart features come online a
   moment later.

!!! note "It finds Cosmos on its own"
    The smart features (error-checking, the map/graph, face previews) are powered
    by a language server that ships with your Cosmos install. Because your `.amd`
    files live **inside** the Cosmos folder, the extension auto-detects the
    install and starts it for you. If you keep `.amd` files somewhere else, set
    **`amd.cosmosPath`** in VS Code settings to your Cosmos folder (the one with
    `PyRuntime/` and `data/`).

---

## What it gives you

| Feature | What it does |
|---|---|
| **Live error-checking** | Red/yellow squiggles for broken headings, dangling links, unfired signals, non-ASCII text — the mistakes that otherwise make a node silently vanish in-game. |
| **Navigation** | `F12` to jump to a link's target, `Shift+F12` to find every reference, `F2` to rename a key across the whole mission, hover to preview, `Ctrl+Space` to complete node keys. |
| **Mission Map** | Your landmarks and regions on a grid — drag to move/resize, right-click empty space to add one, click to edit. |
| **Story Graph** | Your nodes and their links as swimlanes by section — collapse branches, filter sections, focus one conversation, drag between nodes to link them. |
| **Inspector** | Edit any node as a **form** (display, fields, body) that saves live and stays in sync with the text — in a side panel, a pop-out tab, or a drawer right inside the map/graph. |
| **Faces** | A live face preview and a **Face Builder** with a slider per feature — build a character's portrait without memorizing face codes. |
| **Formatter** | Tidy a `.amd` file's whitespace and fences (optionally on save) without touching your words. |

The [tutorial](tutorial.md) uses most of these to build something real. Everything
here is also summarized in the extension's own **Help** (`HELP.md` in the
`editors/vscode/` folder).

---

## The two views, in one picture

- The **Mission Map** answers *"where is everything?"* — the physical layout of a
  system: stations, derelicts, regions.
- The **Story Graph** answers *"how does it connect?"* — who talks to whom, which
  choice leads where, which quest reveals what.

Open both from the icons in the top-right of the editor toolbar when a `.amd`
file is focused, or from the Command Palette (**Artemis AMD: Show Mission Map** /
**Show Story Graph**). Click a thing in either one and it opens in the Inspector,
ready to edit — your text, map, graph, and form all stay in lockstep.
