# Open Universe

An endless, procedurally generated **sandbox** mission for **Artemis Cosmos** —
jump between star systems, trade and take work from rival clans, build (or burn)
your reputation, negotiate or wage war, and seize space docks on a shifting
frontier. The whole galaxy is grown from a single **seed**, so the same seed
always produces the same stars, fields, and factions.

> Originally part of *LegendaryMissions*; now its own mission.

---

## What it plays like

Think a bridge-crew take on **Elite Dangerous** and **EVE Online**, with the
faction-and-reputation feel of **Mount & Blade** — wrapped in a Star Trek-style
exploration skin. The galaxy reacts to *who you are and what you've done*, rather
than walking you through a scripted story.

**The loop:**
- **Explore** the galaxy map — scout systems before you jump, scroll the chart,
  jump to coordinates, or pick from your known locations.
- **Jump** between systems on the Navigation console. Only the system you're in
  exists at any moment (rebuilt around you on arrival), so the universe is
  effectively limitless.
- **Trade & take jobs** — station markets buy and sell; clans offer work (bounties,
  supply runs, salvage, raids…) drawn from their character and **gated by your
  standing** with them.
- **Build reputation** — every captain earns a personal standing with each clan
  across seven traits (honest/violent/generous/…). Do a clan's work and they warm
  to you; better standing unlocks better jobs and cheaper peace.
- **Diplomacy** — negotiate a ceasefire (buy your way in when standing is low, earn
  it when they respect you), then propose an alliance once you've truly won them.
- **Capture & hold** — clear a foe clan's space dock and hold its space to take the
  station; clans mount counter-assaults to retake it. The frontier is yours to
  redraw.
- **Richer systems** — loot caches, scannable derelicts, secondary clan outposts,
  and mine fields lurking in hostile space.

Distant, irrelevant objects are quietly **culled** from the engine network as you
travel, so the galaxy stays light no matter how far you roam.

---

## Running it

### In Artemis Cosmos
Place this folder in your Cosmos `missions/` directory alongside the libraries it
needs (it loads the `sbs_utils` library and several *LegendaryMissions* addons —
see `story.json`). Then pick **Open Universe** from the mission browser.

### For developers (offline dev runner)
From the sibling `sbs_utils` checkout:

```bash
cd ../sbs_utils

# Play it in the browser (then open http://localhost:8765/):
python -m cosmos_dev.mission_runner ../OpenUniverse --gui --map universe --use-working-tree

# Quick headless check (plays ~30s, prints a pass/fail verdict):
python -m cosmos_dev.mission_runner ../OpenUniverse --test 30 --map universe --use-working-tree
```

---

## How it's built

This mission is **content** that stands on two sibling repos:

| Repo | Provides |
|---|---|
| **sbs_utils** | The library + engine API the mission runs on (loaded via `story.json` `sbslib`). |
| **LegendaryMissions** | Reusable addons (mastlibs) the universe loads: prefabs, fleets, docking, commerce, consoles, comms, AI, damage, science scans, hangar, **quests**, documents, and more. |

The actual universe — the map, clans, quests, systems, reputation, and economy —
lives in the local **`universe/`** addon. The galaxy itself is **authored as
data** in `universe/default.amd` (clans, jobs, story, regions, captains, cast,
and dialogue in one plain-text file), so a writer can reshape — or replace —
the galaxy without touching code.

**Want to write your own universe?** See the writer's walkthrough in
[`mkdocs/docs/writing/`](mkdocs/docs/writing/index.md) — it builds a complete
example universe from a blank page, no programming required.

If you change a *LegendaryMissions* addon, rebuild its mastlibs so this mission
picks them up:

```bash
cd ..            # the missions/ folder
python sbs.pyz lib LegendaryMissions
```

---

## Project notes

- **Roadmap & design rationale:** see [`UNIVERSE_CHANGES.md`](UNIVERSE_CHANGES.md).
- **Branches:** `main` (stable) and `v1.4.0_dev` (active development).
- **Saves:** progress is stored as a small delta file under the shared
  `missions/common_data/` folder, so your universe persists between sessions.
- Contributors: there's a `CLAUDE.md` with the technical conventions (MAST/AMD
  rules, how the repos fit together, testing commands) if you're working with an
  AI assistant.
