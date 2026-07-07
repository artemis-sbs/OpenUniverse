# Open Universe — Mission Guide for Claude

The **Open Universe** is a standalone Artemis Cosmos mission: a procedurally
generated, jump-between-systems sandbox (clans, trade, per-captain reputation,
diplomacy, space-dock capture). It was extracted from **LegendaryMissions** into
its own repo. This file is the working guide for an agent focused on this mission.

> Roadmap + design history + status: **`UNIVERSE_CHANGES.md`** (in this repo).

---

## How it relates to the other repos (read this first)

This mission is **content**; it stands on two other repos that live as **siblings**
in the same `missions/` folder:

```
missions/
├── sbs_utils/         # the library + engine API (Python). The mission RUNTIME.
├── LegendaryMissions/ # reusable addons (mastlibs) the universe loads
└── OpenUniverse/      # THIS repo — the mission
```

- **sbs_utils** — the `sbs` engine API + the `procedural/` functions the universe
  calls (`terrain_spawn*`, `comms_info_card`/`comms_broadcast`, `quest_*`,
  `side_set_relations`, `prefab_spawn`, `market_*`, `scatter`, `Vec3`, …). Loaded
  via `story.json`'s `sbslib`. For dev, run against the **working tree** with
  `--use-working-tree` (see below).
- **LegendaryMissions** — the universe loads these LM **mastlibs** via
  `story.json` (`prefabs`, `fleets`, `docking`, `commerce`, `consoles`, `comms`,
  `ai`, `damage`, `science_scans`, `hangar`, `upgrades`, **`quests`**,
  `documents`, `data_panels`, `basic_player_destroy`, `basic_random_skybox`). They
  provide `prefab_side_generic`, `prefab_fleet_raider`, `spawn_players`,
  `docking_standard_player_station`, `market_*`, the **quest driver** (`quests`),
  the **quest-log tab** (`documents`), the console layouts + info panel
  (`consoles`/`data_panels`), etc.
- **The quest system is the LM `quests` mastlib** (quest_driver + bridge_story +
  hangar_board). The universe's clan quest pools, the bridge story, and the
  on_reach cargo runs all ride it. `quests` was packaged as a mastlib specifically
  so this mission could load it.

**Cross-repo rule of thumb**
- Gameplay / mission content / universe data → **here** (`OpenUniverse`).
- Library API or procedural helpers → **sbs_utils**.
- Reusable addon behavior (consoles, comms, prefabs, quests, …) → **LegendaryMissions**, then **rebuild the mastlibs** (below).
- **Concurrency:** other agents may be editing sbs_utils / LM at the same time.

> **SEARCH DISCIPLINE — check dependencies first (learned the hard way):** this
> mission's **`story.json`** lists everything it loads (`sbslib` + the LM `mastlib`
> list) — that's the map of where its mechanics live. When a mechanic isn't found
> here, **search the dependencies it declares**, especially **LegendaryMissions** (the
> shared drivers — quest completion, docking, fleets, comms, consoles — live in LM
> mastlibs, NOT here or in sbs_utils). **Grep all of `story.json`'s deps
> (`../sbs_utils`, `../LegendaryMissions`, here) before concluding a mechanic is
> missing/opaque/broken.** e.g. the quest driver is
> `../LegendaryMissions/quests/quest_driver.{py,mast}`.
  Keep edits to those repos minimal and coordinated; one owner per sbs_utils push
  at a time (a branch+tag name collision once broke pushes). Stay inside this repo
  when you can.

---

## Repo layout

```
OpenUniverse/
├── script.py            # standard Cosmos boilerplate (story_file = story.mast)
├── story.mast           # empty entry; content is the universe/ addon
├── story.json           # sbslib + the LM mastlibs this mission loads
├── settings.yaml        # difficulty / player list / docking defaults
├── description.yaml     # mission-browser entry
├── __lib__.json         # {"version": "v1.4.0"} (packaging tag)
├── UNIVERSE_CHANGES.md  # roadmap + status (the plan)
├── mkdocs/              # docs site (writer's walkthrough + AMD label reference)
│   └── docs/writing/        # "Build a Universe" walkthrough for non-programmer authors
└── universe/            # the mission's local addon (auto-loaded like any addon)
    ├── __init__.mast        # imports the files below, in order
    ├── universe.mast        # @map/universe + comms/science/damage routes + Navigation console + system generation
    ├── universe_helpers.py  # generation, delta save + migration, quest-target sectors
    ├── universe_clans.py    # clans + chatter cards + race "makeup"
    ├── universe_reputation.py    # per-captain reputation + clan standing/tier/ceasefire
    ├── universe_clan_quests.py   # clan quest pools (jobs)
    ├── universe_systems.py  # keyed POI deck (loot/derelict/outpost/mines)
    ├── universe_standby.py  # engine-network culling (terrain/NPC/POI/fleet)
    ├── admiral.mast + universe_worldlets/_fleets/_research/_fabricator/_skirmish.py  # the Admiral console (optional; see "The Admiral console")
    ├── universe_regions.py / _landmarks.py / _goods.py  # regions, landmarks, trade goods
    ├── universe_captains.py / _lifeforms.py / _dialogue.py  # named NPCs, cast, dialogue scenes
    ├── universe_amd.py      # the "friendly fact sheet" AMD reader (data_parser)
    ├── universes.mast       # universe registry (start-screen dropdown)
    ├── universe_codex.mast  # Codex tab (lore.amd document viewer)
    ├── default.amd          # THE authored universe (capstone: clans/jobs/story/regions/...)
    ├── silver_reach.amd     # the walkthrough's worked example universe (ships registered)
    ├── jobs.amd / lore.amd  # spliced sections: generic jobs, codex lore
    └── captains/ cast/ dialogue/  # per-clan captains, cast, dialogue scenes (spliced via File:)
```

Writer-facing docs live in `mkdocs/` (same structure as LegendaryMissions' docs).
It's wired into the main sbs_utils site via a multirepo `!import` line (like LM) —
so pushing OU docs to `origin/v1.4.0_dev` publishes them into the combined site.
`docs/writing/` is the author walkthrough (incl. `admiralty.md`); `docs/playing/`
is player-facing (`admiral.md`). GFM tables render by default (Material) — use them.
Keep the walkthrough + reference in sync with any AMD label changes.

`universe/__init__.mast` import order matters: helpers/clans/reputation/clan_quests/
systems/standby, then `universes.mast`, then `universe.mast` last.

---

## Running & testing (dev)

From the **sbs_utils** directory (that's where `cosmos_dev` lives):

```bash
cd ../sbs_utils

# Headless conformance run (verdict + coverage):
python -m cosmos_dev.mission_runner ../OpenUniverse --test 30 --map universe --use-working-tree

# Browser GUI (open http://localhost:8765/):
python -m cosmos_dev.mission_runner ../OpenUniverse --gui --map universe --use-working-tree
```

- **`--use-working-tree`** runs against the live `sbs_utils` checkout (so local
  library edits take effect). Without it the packaged `.sbslib` shadows your edits.
- The `sbslib not found ...v1.4.0.sbslib` warning in dev is **expected** —
  `--use-working-tree` supplies sbs_utils; only a `v1.4.0_dev` sbslib exists locally.
- Clean the shared save between probes: `rm missions/common_data/universe_save.yaml*`.

### Rebuilding LM mastlibs (when LM addons change)
The universe loads LM addons from `missions/__lib__/` as **mastlibs**, not from
LM's working tree. After editing LegendaryMissions, rebuild:

```bash
cd missions
python sbs.pyz lib LegendaryMissions   # builds v1.4.0 mastlibs (incl. quests) into __lib__/
```

---

## The Admiral console (overseer)

A strategic, RTS-flavored console **on the player side** (worldlets -> ore/gas/crew
economy -> platforms -> fleets -> research), layered on the universe. **Optional:**
it only wakes up when the universe has an `## Admiralty` chapter (+ `## Worldlets`);
Silver Reach has none, so it's inert there. Full design + shipped status:
**`ADMIRAL_CONSOLE.md`** (section 18 = status/commits). Player + author docs:
`mkdocs/docs/playing/admiral.md` and `mkdocs/docs/writing/admiralty.md`.

Files (`universe/`): **`admiral.mast`** (the console GUIs + every Admiral `//comms`
route + the server econ/fleet/skirmish/fabricator loops), `universe_worldlets.py`
(economy, pools, `ADM_PLATFORMS`, build/scan), `universe_fleets.py` (officers,
fleets, the six orders, veterancy), `universe_research.py` (tech ladder),
`universe_fabricator.py` (build model B), `universe_skirmish.py` (border raids),
`universe_regions.py` (antimatter veil).

- **The overseer is the Admiral UI** (the old tabbed `bridge` console was retired).
  It's a detached camera + comms 2D view where
  you **select objects to act**: worldlet -> build; fleet hull -> orders; platform
  -> its actions (Shipyard = commission, Lab = research, HQ = subsidy + requisition).
  A Galaxy top tab (the `//gui/tab` framework) reuses the player Navigation console's
  galaxy map for jumping between systems. The
  detached-console / comms-refresh / side-wide-scan / role-from-art patterns live in
  `../sbs_utils/MAST_CLAUDE.md` ("Detached command consoles").
- **Multi-side rule (will bite you):** derive the side from context
  (`COMMS_ORIGIN.side`, a platform's `.side`), **never a `"tsn"` literal.** The
  build path already does; the **server econ loops still assume `"tsn"`** — the one
  remaining single-side assumption to generalize. Don't add new `"tsn"` literals.

---

## Conventions & gotchas (will bite you)

- **`.mast` comments use `#`.** `//` at column 0 starts a **route** (`//comms`),
  not a comment. (`.amd` files use `//` for comments — the opposite. `.py` uses `#`.)
- **`import file.py` merges all mission helpers into ONE shared MAST namespace** —
  do **not** write relative sibling imports (`from .universe_clans import …`); they
  fail in-engine. Cross-helper functions are already global once `__init__.mast`
  imported that sibling earlier. Only absolute `sbs_utils...` imports are valid.
- **Engine-rendered text is ASCII-only** (GUI text, console names, comms,
  objectives) — no emoji / smart quotes / em-dashes. Comments & docs are exempt.
- The **engine MAST compiler is stricter than the headless mock** — a mission can
  pass `--test` and still fail to compile in Cosmos. Watch comms button labels with
  `:` in them, and identifiers starting with `jump`.
- Full MAST/AMD references live in the sibling repo — read when needed:
  `../sbs_utils/CLAUDE.md`, `../sbs_utils/MAST_CLAUDE.md`,
  `../sbs_utils/MAST_MISSION_CLAUDE.md`, **`../sbs_utils/GUI.md`** (GUI best
  practices + gotchas), and `../AMD_AUTHORS_GUIDE.md`.

---

## Design north-star & guardrails (from UNIVERSE_CHANGES.md)

- **Feel:** a living-frontier sandbox — Elite/EVE bones (seeded galaxy, mission-
  board loop, contestable territory) + **Mount & Blade reputation** (standing is a
  *character* meter), with a Star Trek bridge/scan skin. Principle: **"the galaxy
  reacts to who you are,"** not "follow the scripted hero."
- **Reputation** is per-captain across 7 signed axes; **diplomacy** is side-wide;
  **capture** redraws the frontier. Clan jobs are gated/scaled by standing.
- **Chatter / narrative comms use the info panel** (`comms_info_card`, the
  HereThereBeMonsters card pattern), **not the text waterfall**. Pure mechanical
  status (credits, capture) may stay on the waterfall.
- **The (future) dialogue AMD flavor must stay a sci-fi writer's movie script —
  never a scripting language.** Any new AMD syntax must be **confirmed by the user
  first** and follow **markdown-like rules** (reuse `# [text](key)`,
  `[label](target)`, `?query`, `---` data fences).

---

## Persistence
- Delta save at **`missions/common_data/universe_save.yaml`** (a *shared* location,
  not per-mission). Versioned with a `save_version` + `_MIGRATIONS` ladder — bump +
  add a migration when you change the save shape.

## Branches & push workflow
- All three repos (OU, LM, **sbs_utils**) work on **`v1.4.0_dev`**; `main` is the
  default/release branch. (There is no `admiral_dev` anymore — its work was
  cherry-picked onto `v1.4.0_dev`.)
- **Push to origin only after the user confirms** — every push, each repo. Never
  PR/merge to `main`. (See the `feedback-branch-push-workflow` memory for state.)
