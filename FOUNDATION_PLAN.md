# Open Universe as a Mission Foundation

**Status:** planning + Phase 1 in progress (2026-07-04).
Companion docs: `MULTI_SYSTEM_FEASIBILITY.md` (the one-sim multi-cell basis),
`ADMIRAL_CONSOLE.md` (the RTS layer). This doc is the plan for turning OU from
*one mission* into *a foundation many missions are authored on*.

---

## 1. The goal — four archetypes, one engine

We want OU to be the base for missions that vary widely in shape and length:

| # | Archetype | Length | Ships / sides | Admiral |
|---|---|---|---|---|
| A | Multi-admiral **PvP RTS skirmish** | 1–3 h | few, 2+ hostile sides | 1 per side |
| B | **Endless single-ship epic**, many sessions | 1–2 h × N | 1 ship | usually none |
| C | **Epic war** | 3 days × 6 h | many ships, 3–4 sides | ≥1 per side |
| D | **Tight story reach** | 1–2 h | 1–2 ships | none |

The bet: these are **the same engine with different content + tuning + a few
structural switches**, not four codebases.

## 2. The principle that makes it possible (already true)

OU already separates **mechanism from content**:

- **Mechanism** = the `universe/` addon (`*.py` + `*.mast`).
- **Content** = the `.amd` (clans, jobs, story, map, worldlets, tuning).

A mission is meant to be *"a new `.amd` + a thin `story.mast` that lists the
addon."* The `Economy pace` preset is the template for how *all* variation should
work: a **declarative dial**, not a fork. This plan extends that habit.

## 3. Target architecture — three layers

```
┌ Layer 3  MISSION  ────────────────────────────────────────────────┐
│  mostly .amd content + a thin story.mast + story.json (manifest)   │
├ Layer 2  OU ADDONS (mastlib)  ─────────────────────────────────────┤
│  universe_core  |  admiral  |  story helpers      (pick per mission)│
├ Layer 1  sbs_utils (sbslib)  ──────────────────────────────────────┤
│  generic substrate: cells, persistence, AMD reader, standby, quests │
└────────────────────────────────────────────────────────────────────┘
```

### 3a. Layer 1 — promote the *generic substrate* to sbs_utils
Already promoted: standby, AMD fact-reader, `PersistentStore`. Next candidates —
things that are **not universe-specific at all**:
- **multi-cell slot allocator + cell lifecycle + `objects_in_cell`** — "coexisting
  virtual systems in one sim" is a generic capability, not a universe idea;
- a **generic quest / reputation core** (reputation was already deferred as a
  promote candidate).

Rule (unchanged): *generic → sbs_utils; game framework → OU mastlib; content → AMD.*
Anything landing in sbs_utils must be truly generic and **API-stable** (backward
compat is close to sacred there), so promote one vetted piece at a time.

### 3b. Layer 2 — split the OU addon (the key move)
Today it's monolithic. Split so missions **pay only for what they use**:
- **`universe_core`** — generation, cells, exploration, POIs, quests-glue,
  dialogue, persistence wiring, the galaxy map / nav.
- **`admiral`** — the RTS economy (worldlets, platforms, fleets, officers,
  skirmish). A *game mode*, not generic.
- **`story`** — narrative helpers (chapters, scene jumps, win/lose framing).

Then `story.json` is the manifest: **D and B load `universe_core` (skip
`admiral`); A and C load both.** This split is the difference between "a
foundation" and "a big mission other missions awkwardly clone."

#### Subsystem membership (the physical-split blueprint)

Audited 2026-07-04. The file boundary is cleaner than expected — worldlets are
admiral content (the generation `worldlet` chance is `0.0` unless the admiral is
active, so no worldlets spawn without it), so an entire set of files is `admiral`:

| Belongs to | Files |
|---|---|
| **`admiral`** | `universe_worldlets.py` (economy + worldlet spawn), `universe_fleets.py`, `universe_skirmish.py`, `universe_fabricator.py`, `universe_research.py`, `admiral.mast` |
| **`universe_core`** | `universe.mast`, `universe_helpers.py`, `universe_sides.py`, `universe_clans.py`, `universe_regions.py`, `universe_systems.py`, `universe_landmarks.py`, `universe_dialogue.py`, captains/passengers/quests-glue |
| **parser (core, knows admiral vocab)** | `universe_amd.py` |

**The addon boundary = these cross-references, all already gated by
`admiralty_active()`** (which Phase 1's `Mode.admiral` folds into):
- `universe.mast` schedules the four admiralty loops + seeds pools *(gated, line 165)*,
  runs `fleets_respawn` at startup *(gated, 214)*, and restores platforms/fleets on
  arrival *(gated, 1036)*;
- `admiral.mast`'s `@console/admiral` is gated (`... and admiralty_active()`), and its
  comms routes only fire for the admiral cam, which only spawns from that console;
- `universe_amd.py` parses the admiral AMD vocab (`Mode`, `Economy pace`, `Worldlet
  chance`, the `## Admiralty`/`## Worldlets`/`## Research` chapters).

So **the runtime split already works** (Mode `campaign`/`story` → zero admiral code:
no loops, no console, no worldlets, no restore). The *physical* split (Phase 2b) is
mechanical: move the six `admiral` files into their own `.mastlib`, and turn the
core→admiral cross-refs into an optional-addon boundary (core calls the admiral entry
points only when the addon is present / `admiralty_active()`).

### 3c. Layer 3 — the mission
Content and shape authored declaratively; `story.json` picks the addons; MAST is a
thin harness. Python is touched only to invent a genuinely new mechanic.

## 4. The keystone: a `Mode` / scenario preset

Extend the `Economy pace` idea up one level — one dial that **bundles an
archetype's defaults** (relations model, victory framing, session/persistence,
economy pace, which subsystems are live). Explicit dials still override.

```
Mode: sandbox    // today's OU: full living universe, everything on
Mode: skirmish   // hostile sides, victory=raze HQ, economy=brisk, story off
Mode: war        // multi-side hostile, ≥1 admiral/side, persistent, economy=epic
Mode: campaign   // single ship, persistent, RTS off, economy=epic
Mode: story      // bounded arc, win/lose from the story, RTS off
```

`Mode` is what turns "OU the mission" into "OU the foundation": an author picks a
line, then overrides individual dials. It grows as the layers below it grow.

## 5. The one genuinely-new subsystem: relations + victory

The biggest gap across A/C is that OU is **co-op today**. Two parts:

- **Side relations** *(done, Phase 3a)* — `Mode` skirmish/war make the player sides
  mutually hostile (`universe_mode_is_pvp`); sandbox/campaign/story stay co-op.
- **Victory / defeat** *(Phase 3b — decision: express it through QUESTS, not a
  separate Rules chapter)*. The quest engine already turns `Win:`/`Lose:` goals into
  `universe_victory`/`universe_defeat`. Building blocks added:
  - **Capital tag** — a side's first HQ gets `admiral_home_hq` + a `<side>_capital`
    role, so a **decapitation quick-win is an ordinary quest** with no new syntax:
    `When: destroy 1 <enemy>_capital` + `Win: yes`.
  - **War-state watcher** (`universe_warstate.py`) — reports `side_eliminated`
    (held an HQ, now holds none = conquest) and `last_side_standing` as **signals**,
    so victory policy stays declarative. `//signal/last_side_standing` gives
    skirmish/war a built-in **last-standing** win (the Mode default); `//signal/
    quest_finished` handles authored quest wins. Both set the shared
    `UNIVERSE_GAME_OVER` and re-use the (previously dangling) victory/defeat signals.
  - **Conquest-as-quest via `on_signal` - UNBLOCKED (Doug: "did you check LM?").**
    The quest driver is **`LegendaryMissions/quests/quest_driver.{py,mast}`** (I'd
    missed it - it's an LM mastlib, not sbs_utils/OU). It hooks existing signals:
    `//signal/universe_arrived`->`on_reach`, `//damage/destroy`->`on_kill`,
    `//science`->`on_scan`, `//signal/ship_docked`->`on_dock`, and crucially a generic
    **`//signal/quest_signal`->`quest_on_signal`** escape hatch that already advances
    any quest with `on_signal {name}`/`on_comms {option}` data. So `on_reach`/`scan`
    completion works (and `derelict`->`universe_derelict` via `_ROLE_ALIASES`, so the
    "Fading Signal" scan-win is real). **`on_signal` needs NO driver change** - just
    two OU-local bits (done in Phase 3c below): an AMD `signal` verb + bridging the
    war-state milestones to `quest_signal`.

## 6. Phased plan

Each phase is independently shippable and headless-verifiable where possible;
multiplayer/PvP shapes need an in-engine playtest.

- **Phase 1 — `Mode` scaffold.** *(in progress)* The declarative dial + resolver,
  wired to the levers that already exist (economy pace, skirmish on/off, and an
  `admiral on/off` gate so `story`/`campaign` run no RTS). Establishes the keystone
  abstraction; explicit dials override; `sandbox` == today. **← starting here.**
- **Phase 2a — logical split.** *(done 2026-07-04)* Audit + document the subsystem
  seam (see §3b); confirm the `Mode.admiral` gate fully dormant-izes the admiral
  subsystem (no loops / console / worldlets / restore when off). No behaviour change
  for `sandbox`. The runtime split works today; only the packaging is still one addon.
- **Phase 2b — physical split.** Move the six `admiral` files into their own
  `.mastlib`; turn the core→admiral cross-refs into an optional-addon boundary;
  `story.json` manifests. Needs a story-mode test mission for the core-only smoke.
- **Phase 3 — relations + victory.** Player-side hostile relations + a declarative
  victory/defeat set; `Mode` picks defaults (skirmish/war → raze HQ; story →
  story goal; campaign → endless).
- **Phase 4 — promote the generic substrate** (cells/spatial, quest/reputation
  core) to sbs_utils, one vetted piece at a time.
- **Phase 5 — archetype hardening.** B: content variety for "endless." C: scale +
  multi-day-save robustness + PvP balance (rides the `perf_probe` findings).

## 7. Risks / honest read

- **C is the ambitious one** — 3 days × 6 h × 4 sides × multiplayer is a
  scale + stability + multi-day-persistence + PvP-balance problem. The foundation
  helps but this archetype *stress-tests* it.
- **PvP relations don't exist yet** (co-op today) — Phase 3 is the real new work.
- **D risks over-engineering** without the addon split (Phase 2 fixes it).
- **"Endless" (B) is a content problem**, not a mechanism one — Phase 5.
- **`Mode` now lives in a mission-level `## Scenario` chapter** *(done)* — a `story`
  universe needs no `## Admiralty` block at all (`universe_admiralty_cfg` merges the
  Scenario `Mode:`); `Mode:` inside `## Admiralty` still works for older universes.
  The first mission authored on the foundation, **`scout_signal.amd` ("The Fading
  Signal")** — a `story` universe selectable from the Universe dropdown — is the
  worked proof + the core-only consumer Phase 2b will validate against.
