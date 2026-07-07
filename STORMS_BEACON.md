# Storm's Beacon — Design Doc (draft)

**Status:** draft for iteration (2026-07-06). A *rough* plan — expect to cut and simplify.
**Genre:** episodic stealth-archaeology. "Tomb Raider in space."
**Home:** authored as a `Mode: story` universe on the **OpenUniverse** foundation
(the `scout_signal.amd` / "The Fading Signal" pattern, scaled to episodes).

---

## 1. The pitch

Prof. Storm is chasing an ancient **beacon**. You captain her ship — a small, fast,
under-gunned **Warpster/escort**, *not* a warship. You survive by cleverness: science
scans that read ruins and reveal weaknesses, engineering that crafts countermeasures
and exploration missiles, comms that negotiates, bribes, and **gets other people to
fight your battles** while you slip away. Each episode follows a clue toward a
candidate beacon site, with **XORN** — a superior enemy ship — closing in behind you.

**Tone:** less epic fleet battle, more tense skirmish and escape. Fights are against
**fighter squads and bounty hunters**. The player's edge is non-combat: *know more,
prepare better, and never fight fair.*

**Backstory hook (the dungeon justification):** Torgoth and Kralien, in an earlier
evolutionary phase, were physically **much larger** — and built the **massive stations**
that now drift derelict across the frontier. Those giant ancient hulks are the "tombs"
you raid; the beacon is a relic of that lost era. One idea buys us the ruins, the
relics, and the beacon's origin.

---

## 2. Feasibility & architecture — the honest current state

You asked: *"standalone mission using the Open Universe, if that's possible yet."*
Here's the real answer from surveying the OU working tree.

| Capability | State today | Storm's Beacon uses it by… |
|---|---|---|
| **Multi-system jump** (single ship, per-cell) | Real, engine-verified (`universe_jump_to`, per-ship `ship_cell`) | authoring systems in `.amd`; `When: reach i,j` chapters drive the jump |
| **`Mode: story`** (RTS/economy OFF) | Shipped; cleanly gates off the whole Admiral economy | set `Mode: story` in `## Scenario` |
| **Quest driver** (clue-chaining) | Shipped in LM `quest_driver` (`on_reach`/`on_scan`/`on_dock`/`on_signal`/`on_comms`) | episodes = narrative chapters + goals |
| **Reputation** | **Already exists** in OU (`universe_reputation.py`) — per-captain, signed axes vs clans, persisted | configure clans + rep rules; **do not build from scratch** |
| **Persistence** | `PersistentStore` in sbs_utils; OU saves per-ship + credits + quests | inherited for free (rep, credits, progress persist across episodes) |
| **OU as a `.mastlib` dependency** | **Not built** (Phase 2b) — `universe/` has no `__lib__.json` | — |

**STATUS (2026-07-06): OU Phase 2b DONE + StormsBeacon standalone slice landed** (headless
`--test` PASS, core-only, on the fully-packaged path; browser jump/scan-win verification is
the user's step). See FOUNDATION_PLAN Phase 2b for the split details. What exists now: the
`universe_core`/`admiral` mastlib split, a mission-relative `.amd` loader, an sbs_utils
shared-per-lib-namespace fix, and `data/missions/StormsBeacon/` (a `Mode: story` mission
loading `universe_core` only, with a vertical-slice `stormsbeacon.amd`). The full campaign
below (comms-with-Storm loop, episodes, reputation, XORN, Eddy) is the next content layer.

**DECISION (2026-07-06): do OU Phase 2b now, and make Storm's Beacon the example case.**
Rather than author inside OU, we're building the `universe_core` / `admiral` mastlib
split (Phase 2b) so Storm's Beacon can be a **true separate sibling mission folder**
(`data/missions/StormsBeacon/`) that loads `universe_core` the way missions load
LegendaryMissions. This is exactly the "story-mode test mission for the core-only smoke"
that FOUNDATION_PLAN Phase 2b says it needs — so the two goals reinforce each other:
2b makes the standalone folder possible, and Storm's Beacon validates 2b.

Consequences:
- **New target folder:** `data/missions/StormsBeacon/` (sibling), not a universe inside OU.
- **`story.json` loads `universe_core` only** (admiral mastlib omitted) + the LM addons
  it needs (quests, comms, consoles, docking, science_scans, prefabs).
- The split's invariant: `admiralty_active()` becomes **core** and is False unless the
  `admiral` addon is loaded — so a core-only mission never references a missing admiral
  symbol. See the OU Phase 2b execution notes (tracked separately during the refactor).

> The `.amd` campaign content is identical regardless — so this reorganizes *where the
> engine lives*, not *what the campaign is*.

---

## 3. The core loop — Prof. Storm as episode dispatcher

Storm is **virtual crew** (a Lifeform comms contact reachable anywhere), not a ship you
fly to. Hailing her **is** the start-of-episode beat. This is the campaign's heartbeat:

```
        ┌─────────────────────────────────────────────────────────────┐
        │                                                             │
        ▼                                                             │
  ┌───────────┐   lead not ready    ┌──────────────────────┐          │
  │ HAIL PROF │────────────────────▶│ "still cross-        │          │
  │  STORM    │                     │  referencing…" +      │          │
  │ (comms)   │                     │  nudge: go scan/dock  │──────────┘
  └─────┬─────┘                     │  X to feed research"  │   investigate feeds
        │ lead ready                └──────────────────────┘   Storm the next fragment
        ▼
  ┌──────────────────────┐   emits quest signal   ┌────────────────────────┐
  │ Storm names the next │──────────────────────▶ │ REVEAL next Narrative   │
  │ candidate location   │  (on_comms / on_signal)│ chapter  → When: reach   │
  └──────────────────────┘                        │           i,j            │
                                                  └───────────┬────────────┘
                                                              │ Nav "Engage" jump
                                                              ▼
                                              ┌──────────────────────────────┐
                                              │ EPISODE: arrive → investigate │
                                              │ (scan relics / dock stations /│
                                              │ comms locals) → complication  │
                                              │ (bounty hunters / squad / XORN│
                                              │ closes in) → resolve → clue    │
                                              └──────────────┬───────────────┘
                                                             │ back to Storm
                                                             ▼  (loop)
```

**How it maps to existing machinery (little new code):**
- Storm's "lead ready" comms option is a **plain comms button that emits a quest
  signal** — the quest driver's `on_comms {option}` / `//signal/quest_signal` hook
  advances the quest and `reveal`s the next chapter. **No driver change needed.**
- The revealed chapter carries `When: reach i,j`; the Nav galaxy map's **"Engage"**
  button (`//signal/quest_engage → universe_jump_to`) performs the jump. Already wired.
- "Investigate feeds Storm's research" = the *complication/clue* chapter completes on
  `scan`/`dock`/`comms`, emitting a signal that flips Storm's dialogue to "lead ready."

---

## 4. Episode structure — spine + procedural filler

Goal was 7–10 episodes, *or* begin-middle-end + procedural. Recommended shape:

- **3 hand-authored tentpoles:** **Opening** (meet Storm, first ruin, first XORN
  sighting), **Midpoint** (Crazy Eddy's Emporium — a turn), **Finale** (the beacon).
- **A pool of procedural clue-chase episodes** between them, assembled from the **one
  episode template** below by shuffling: system (i,j), relic/ruin type, which
  station/ship holds the clue, and which antagonist shows up.

This hits "beginning-middle-end + procedurally generated" and keeps authoring sane.

### The episode template (the repeatable unit)

1. **Arrive** — jump into the system Storm named.
2. **Investigate** — get the clue by one of: **scan an ancient relic**, **dock a
   station/ship**, or **comms an NPC** out of what they know.
3. **Complication** — bounty hunters, a fighter squad, or **XORN's trail** catches up.
4. **Resolve** — stealth away, win the skirmish, or **recruit a third party** (bribe/
   provoke a nearby faction to engage while you escape). Reputation gates who'll help.
5. **Clue** — the fragment points to the next system → back to Storm.

### Build order (simplify — do not build all 10 up front)

1. **Vertical slice:** the Opening tentpole as a single `.amd`, end-to-end (hail Storm
   → jump → scan a derelict relic → one fighter-squad complication → clue → hail Storm).
   Prove the loop + tone headless (`--test`) then in-browser.
2. **Reputation wiring:** configure OU's clans + rep rules; make one gate real (a
   faction that will/won't fight for you).
3. **Procedural generator:** the episode template as a parameterized chapter factory.
4. **Tentpoles:** author Eddy's Emporium (midpoint) and the Finale.
5. **Polish pass:** XORN pursuit tuning, crafting depth, more relic/clue variety.

---

## 5. Reputation (consume OU's module — do not rebuild)

OU already has `universe_reputation.py`: per-captain reputation vs **clans**, **7 signed
axes**, with `reputation_configure / get / adjust / apply`, persisted per-ship. Storm's
Beacon **configures and consumes it** rather than inventing one.

**Design (kept simple):**
- **Factions (clans):** the ancient civs (**Torgoth**, **Kralien**), a **Merchant/Salvage
  guild**, a **Bounty-Hunter guild**, and **XORN's crew**. (Fewer is fine — start with 3.)
- **Bands:** map a signed axis to 5 readable bands — **Hostile ▸ Wary ▸ Neutral ▸
  Friendly ▸ Allied** — so the player can read where they stand at a glance.
- **What rep *does* (the point — it must be legible and matter):**
  - **Comms:** low rep → a faction won't talk, refuses clues, or sells your position to
    XORN; high rep → shares clues, warns you of ambushes.
  - **Recruit-a-third-party:** only **Friendly+** factions will fight XORN/hunters for you.
  - **Crazy Eddy:** rep sets his **prices** and the quality of his black-market **leads**.
  - **Bounty hunters:** low rep raises the bounty (more/harder squads); high rep can
    call them *off* — or hire them.
- **What *moves* rep:** helping/defending a faction's ships or stations (+), attacking
  them (−), bribes (spend credits to nudge +), fencing relics through the wrong channel
  (−), and story choices. Persisted across episodes for free.

> **Open design question for you:** do you want reputation to mostly gate **who fights
> for you** (tactical) — or to also branch the **story/dialogue** (narrative)? That
> choice sets how much authored dialogue variance we sign up for. See §11.

---

## 6. Crew — Lifeforms

Created at top level as `lifeform_spawn`, used for comms faces + dialogue; the ones
aboard can be `host`-attached to the player ship for interior/crew presence.

| Character | Role | Function in play |
|---|---|---|
| **Prof. Storm** | Archaeologist, expedition lead | Episode dispatcher (§3); lore/science voice; reads relics |
| **You (Captain)** | Player | Flies the ship, makes the calls |
| **Chief Engineer** | Crafting/countermeasures voice | Fronts the crafting UI (§8); banter on damage |
| **Crazy Eddy** | Ship-dealer, comic relief | His own episode (§9); **joins as virtual crew** after — a comms contact for black-market leads + fencing relics |

Keep the *speaking* cast small (3–4). Everyone else is a station/ship NPC surfaced via
comms.

---

## 7. Antagonists

- **XORN** — the recurring **pursuer**. Superior to your ship; **not** a boss you
  out-gun early. Appearances are **chases and escapes** — a rising dread that closes the
  gap if you dawdle. Mechanically likely a small new MAST piece: a ship that arrives in
  (or trails you into) systems and forces a "get out or get help" decision. *(New work —
  see §10.)*
- **Bounty hunters** — mercenaries who can be **out-run, bribed, turned, or hired**
  (rep-driven). The tunable pressure valve.
- **Fighter squads** — the bread-and-butter skirmish; small, beatable with prep +
  countermeasures.

---

## 8. Crafting (science / weapons / engineering as *tools*, not war)

Keep it **light** — 3–4 craftable items at first, framed as expedition gear:

| Item | Console | Effect |
|---|---|---|
| **Sensor decoy** | Engineering | Drops a false contact; breaks XORN/hunter lock so you can slip away |
| **Probe / scan missile** | Weapons | Fired at a relic/ruin/derelict to scan it from range (exploration, not damage) |
| **EMP countermeasure** | Engineering | Briefly disables a fighter squad's weapons/engines — a stealth opener |
| **Relic-scan booster** | Science | Temporarily extends scan range/resolution to read a ruin's glyphs |

Crafting is a **resource sink** (salvage/credits/relic fragments) that turns science +
engineering into the *real* toolkit. Depends on whether OU already has a crafting
substrate to lean on — **to be scoped** (see §10). `sbs_utils` has torpedo/launch and
upgrade plumbing we can likely build the missiles on.

---

## 9. Crazy Eddy's Spaceship Emporium (the midpoint tentpole)

A recurring **hub** and the campaign's turning-point episode. A ramshackle bazaar
station where you: buy upgrades + crafting materials + decoy drones, **fence relics**
for credits, and buy **intel/leads**. Eddy is comic relief; his **prices and lead
quality scale with reputation**. After his episode he **joins as virtual crew** — a
comms contact you can call for black-market leads or to sell relics without hauling them
home. (Spawns from an ancient starbase art → strip art-derived `station` roles you don't
want, per the detached-console / spawn-role note in `MAST_CLAUDE.md`.)

---

## 10. What we reuse vs. what's genuinely new

**Reused (inherited from OU + LM + sbs_utils — little/no code):**
- Multi-system jump (`universe_jump_to`, `reach i,j` chapters, Nav galaxy map "Engage").
- `Mode: story` (RTS off), quest driver (clue-chaining), reputation module, persistence,
  comms, docking, science scan, Lifeforms.

**Genuinely new (the short list — this is the real work):**
1. **The `.amd` campaign content** — episodes, chapters, landmarks (ancient ruins),
   Prof. Storm's dispatcher dialogue, clans + rep rules, Crazy Eddy.
2. **XORN pursuit** — a scripted pursuer that raises tension across systems (§7).
3. **Crafting mini-system** — the 3–4 expedition items (§8), if OU has no substrate to
   reuse. *(Scope check pending.)*
4. **Recruit-a-third-party** verb — bribe/provoke a faction to fight for you (may lean
   on existing relations + a comms option + a brain retarget).

---

## 11. Open questions (for our next pass)

1. **Placement:** ~~confirm path A vs B~~ **DECIDED** — path B: doing OU Phase 2b, Storm's
   Beacon ships as a sibling `data/missions/StormsBeacon/` loading `universe_core`. (§2)
2. **Reputation's job:** ~~tactical only or also narrative branching?~~ **DECIDED
   (2026-07-07)** — **tactical AND narrative branching.** Rep gates who fights for you,
   Eddie's prices/leads, and bounty pressure *and* branches what characters say / which
   narrative paths open. This is the richer choice; it commits us to authored dialogue
   variance per episode, so the episode template (§12) must bake rep-branch slots in from
   the start. (§5)
3. **Crafting depth:** is 3–4 items the right ceiling, and does OU already have a crafting
   substrate to build on, or is this net-new? *(Still open — scope during Phase 3 polish.)* (§8)
4. **XORN cadence:** ~~trailing dread or scripted set-piece?~~ **DECIDED (2026-07-07)** —
   **both:** a light ever-trailing pressure (arrives if you linger) PLUS 2–3 hand-authored
   confrontations (first sighting, midpoint, finale). Most work of the options; richest
   feel. XORN is the campaign's single largest new mechanic. (§7)
5. **Episode count for v1:** ship the 3 tentpoles + how many procedural episodes? Suggest
   proving the slice + 2 procedural before authoring all three tentpoles.
6. **Ancient-station relics:** are ruins *scannable derelicts* (like The Fading Signal's
   Meridian) or *dockable/boardable* interiors? The former is nearly free today; the
   latter is more authoring.
7. **Eddie's up/downgrades:** ~~real stat effects or narrative flavor?~~ **DECIDED
   (2026-07-07)** — **real ship-stat effects.** Buying applies to the ship (turn rate, top
   speed, scan range, shields…) and downgrades genuinely hurt; the gamble matters. Requires
   resolving the deferred *apply-owned-upgrades-on-launch* TODO (casino Pilot Market). (§9)

---

## 12. Build plan (2026-07-07) — mechanics once, then mass-author

**The discipline:** episode *content* is cheap (`.amd` headings + a landmark); what makes
episodes good is a small set of mechanics built ONCE and reused. Do NOT author 7–10
episodes on the current scan-a-derelict spine and retrofit — build the enablers first, lock
the template, then fill in. The three richer decisions above (§2, §4, §7) raise the
authoring bar, so the template must bake in rep-branch slots, a complication slot, and a
terrain hint from day one.

**What `universe_core` already gives us for free** (confirmed in the working tree — do not
rebuild): per-system terrain by `kind` (nebula/asteroid/black-hole/mines, `universe.mast`
~994–1145), POI decks (loot/derelict/outpost/mines, `universe_systems.py`), the full
reputation module (`universe_reputation.py` + `reputation:` `.amd` block), `## Regions`
(per-area skybox/music/**generation-mix override**/tint + antimatter veil), and a
buy-market substrate (LM `casino/market.mast`, `items/item_market.mast`).

### Phase 0 — Enablers (build once, before any bulk content) — **DONE 2026-07-07**

1. **Episode complication hook** — ✅ DONE. A landmark authors `Guards: <race> [difficulty]`;
   `universe_core` spawns a `prefab_fleet_raider` contesting it on arrival, **one-shot** via a
   persisted `guards_cleared` flag (mirrors the `enemy`-kind `enemy_cleared` pattern). New
   `universe_landmark_guards()` + spawn + `universe_watch_guards_cleared` watch label.
2. **Terrain control** — ✅ DONE. Two layers: a **`## Regions`** block (skybox/music/map-tint/
   nebula-biased generation mix) gives the episode cluster geography, AND a per-landmark
   **`Terrain: <kind> [color]`** hint (`nebula`/`asteroids`) *guarantees* the ruin sits in
   cover regardless of the cell's rolled kind. New `universe_landmark_terrain()` + spawn.
3. **Lock the episode template** — ✅ DONE. The Storm dispatcher is now **data-driven** (an
   ordered `_eps` list; adding an episode = author its go/scan chapters + landmark, then
   append one row — no bespoke `if/elif`). Proven by adding **episode 3** (the win moved to
   it). Copy-ready pattern doc: `StormsBeacon/EPISODE_TEMPLATE.md`.

> **Status:** all three verified headless (`--test` PASS, no runtime errors; parser helpers
> unit-checked). Dispatcher logic traced across all quest states. **Browser-verify pending**
> (jump to 2,-1 / 4,1 / 6,-2: ruin-in-terrain + guards + scan-advances-Storm). The
> `universe_core` primitives (`Guards:`/`Terrain:`) are generic — any universe can use them.

### Phase 1 — The two new mechanics

4. **XORN pursuit** (§7 decision: both) — start minimal: XORN arrives in the episode system
   after a dwell timer (the light trail), forcing escape-or-get-help; then layer the 2–3
   authored confrontations. The one piece with real design risk — tune cadence in browser.
5. **Crazy Eddy's Emporium** (§7 decision: real stats) — market surface reusing the
   casino/items substrate + **resolve the apply-upgrade-on-launch TODO** so purchases hit
   ship stats + the up/downgrade gamble. Wire rep → prices + lead quality.

### Phase 2 — Cast & reputation

6. **Cast** (cheap `.amd`): add Lifeforms + Dialogue for Chief Engineer, Eddy-as-virtual-
   crew, and 1–2 faction voices. Small.
7. **Reputation** (§2 decision: tactical + narrative) — `reputation_configure` 3 clans to
   start (Salvage guild, Bounty-Hunter guild, XORN's crew); make ONE tactical gate real
   (a faction that will/won't fight for you) AND one dialogue branch real, as the pattern
   the rest of the episodes copy.

### Phase 3 — Content build-out (now fast, because the template + mechanics exist)

8. Author the **3 tentpoles** (Opening / Eddy midpoint / Beacon finale) + **4–6 procedural
   episodes** from the template = **7–9 episodes**.
9. **Polish:** XORN tuning, crafting depth (the 3–4 expedition items, §8 — scope here), more
   relic/clue variety, save/continue verification across the full quest tree.
```
