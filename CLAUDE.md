# Open Universe — Mission Guide for Claude

The **Open Universe** is a standalone Artemis Cosmos mission: a procedurally
generated, jump-between-systems sandbox (sides, trade, per-captain reputation,
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
  hangar_board). The universe's side quest pools, the bridge story, and the
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
> missing/opaque/broken.** e.g. the quest driver is now SPLIT: the generic engine is
> **`../sbs_utils/procedural/quest_driver.py`**, and its signal-route wiring (which event
> feeds which trigger, plus `game_over`) is **`../LegendaryMissions/quests/quest_driver.mast`**.
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
    ├── universe_sides.py    # sides + chatter cards + race "makeup"
    ├── universe_reputation.py    # per-captain reputation + side standing/tier/ceasefire
    ├── universe_side_quests.py   # side quest pools (jobs)
    ├── universe_systems.py  # keyed POI deck (loot/derelict/outpost/mines)
    ├── universe_standby.py  # engine-network culling (terrain/NPC/POI/fleet)
    ├── admiral.mast + universe_worldlets/_fleets/_research/_fabricator/_skirmish.py  # the Admiral console (optional; see "The Admiral console")
    ├── universe_regions.py / _landmarks.py / _goods.py  # regions, landmarks, trade goods
    ├── universe_captains.py / _lifeforms.py / _dialogue.py  # named NPCs, cast, dialogue scenes
    ├── universe_amd.py      # the "friendly fact sheet" AMD reader (data_parser)
    ├── universes.mast       # universe registry (start-screen dropdown)
    ├── universe_codex.mast  # Codex tab (lore.amd document viewer)
    ├── default.amd          # THE authored universe (capstone: sides/jobs/story/regions/...)
    ├── silver_reach.amd     # the walkthrough's worked example universe (ships registered)
    ├── jobs.amd / lore.amd  # spliced sections: generic jobs, codex lore
    └── captains/ cast/ dialogue/  # per-side captains, cast, dialogue scenes (spliced via File:)
```

Writer-facing docs live in `mkdocs/` (same structure as LegendaryMissions' docs).
It's wired into the main sbs_utils site via a multirepo `!import` line (like LM) —
so pushing OU docs to `origin/v1.4.0_dev` publishes them into the combined site.
`docs/writing/` is the author walkthrough (incl. `admiralty.md`); `docs/playing/`
is player-facing (`admiral.md`). GFM tables render by default (Material) — use them.
Keep the walkthrough + reference in sync with any AMD label changes.

`universe/__init__.mast` import order matters: helpers/sides/reputation/side_quests/
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
- A run from this folder reads and writes the REAL save
  (`missions/common_data/saves/universe_save_<universe>_<slot>.yaml`). Probe from a
  copy under `missions/_sandbox/<group>/` instead, whose saves land in
  `missions/_sandbox/<group>/common_data/saves/`.

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
  A Galaxy top tab (the `//gui/tab` framework) shows the GALAXY TILE MAP, the same GUI
  map the player Navigation console draws (`universe_core/universe_galaxy_map.py`; the
  orders are in `admiral/admiral_galaxy_map.py`). Click a unit, then a system, and the
  Orders xESS app moves it. `GALAXY_MAP_MODE = "classic"` brings back the old 2D-view
  theater (`universe_galaxy_theater.py`) until the tile map is engine-verified. The
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
  do **not** write relative sibling imports (`from .universe_sides import …`); they
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
  **capture** redraws the frontier. Side jobs are gated/scaled by standing.
- **Chatter / narrative comms use the info panel** (`comms_info_card`, the
  HereThereBeMonsters card pattern), **not the text waterfall**. Pure mechanical
  status (credits, capture) may stay on the waterfall.
- **The (future) dialogue AMD flavor must stay a sci-fi writer's movie script —
  never a scripting language.** Any new AMD syntax must be **confirmed by the user
  first** and follow **markdown-like rules** (reuse `# [text](key)`,
  `[label](target)`, `?query`, `---` data fences).

---

## Persistence
- Delta save at **`<missions>/common_data/saves/universe_save_<universe>_<slot>.yaml`**
  (beside the mission folder, keyed by `UNIVERSE_SELECT` + `SAVE_SLOT`, so the folder
  name does not matter and two missions with one title share a save). All of it is in
  `universe_core/universe_helpers.py`; the generic store is
  `sbs_utils/procedural/persistence.py`.
- **`save_version: 2`** (2026-10-09). Top-level keys: `universe_seed`,
  `current_system`, `systems`, `players`, `side_credits`, `side_admiralty`,
  `shared_quests`, `diplomacy`. `players` is keyed by a **stable ship id** (a slug of
  the name the ship had when first saved; kept on the ship as inventory
  `universe_ship_key`), and each record holds `name`, `side`, `cell`, `items`,
  `installs`, `quests`, `reputation`. On Continue a ship finds its record by name,
  then by being the only unmatched ship and record on its side (a rename in
  `settings.yaml`); a record with no ship flying is kept, never dropped.
- **Keys this build does not know are kept verbatim**, top-level and per ship, so an
  additive section needs no version bump. A breaking change bumps
  `UNIVERSE_SAVE_VERSION` and adds a step to `_MIGRATIONS`; the first load of an older
  file leaves `<file>.v<N>.bak` beside it.
- **Every write goes through `_universe_write`.** A file that is there and will not
  load (or that a newer build wrote) is never written over: it is copied aside
  (`.unreadable.bak`, or the `.v<N>.bak` when a migration raised) and the session
  plays unsaved. `universe_save_begin(START_MODE)` opens the save for a session; a New
  Game writes a whole new file and keeps the old one once as `.previous.bak`.
- **Do not call `universe_save_players()` from a quest route - call
  `universe_save_request()`.** Each save rewrites the whole file; `universe_save_loop`
  writes a requested one every 2 sim-seconds. Nothing writes `players` between
  `universe_save_reset()` and `universe_save_ready()` (the campaign is still loading).
- Tests: `python -m unittest tests.test_save_roundtrip` (fixtures in `tests/saves/`
  are generated version-1 saves; never run this mission from its real folder to make
  one - it writes slot 1 of the real saves folder. Copy it under
  `data/missions/_sandbox/<group>/` first).

## Branches & push workflow
- All three repos (OU, LM, **sbs_utils**) work on **`v1.4.0_dev`**; `main` is the
  default/release branch. (There is no `admiral_dev` anymore — its work was
  cherry-picked onto `v1.4.0_dev`.)
- **Push to origin only after the user confirms** — every push, each repo. Never
  PR/merge to `main`. (See the `feedback-branch-push-workflow` memory for state.)
