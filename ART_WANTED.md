# ART_WANTED - every placeholder, borrowed asset and wished-for piece of art

One shopping list for an artist, across all the missions: LegendaryMissions (LM),
OpenUniverse (OU), StormsBeacon (SB) and the sbs_utils library. It started as the Admiral
console's placeholder list (ADMIRAL_CONSOLE.md section 9) and grew to cover everything
built since. When an artist appears they get a list instead of an archaeology dig.

**How replacement works (almost never code):** every art reference lives in a data key -
a hull's `artfileroot` in a ship-data file, an item's `art:`, a prefab's `ship_art`, an
AMD `Art:` / `Face:` / `Palette:`, an icon name in a sheet. Swapping art = a new asset plus
a one-line data edit. Placeholders were chosen to be *legible, not pretty*.

**New hulls go through extra ship data.** A new model is a new ship-data entry in the
mission's media pack (the turret and station-kind files are the pattern). It only reaches
the engine with `EXTRA_SHIP_DATA` on, and a hull the engine never received crashes the
spawn - so art for these arrives with its ship-data entry, never as a loose file.

**Priority:** **P1** = players see it all the time, or it reads wrong; **P2** = clearly
improves feel; **P3** = polish, today's reuse is acceptable.
**Visibility:** HIGH = every player in normal play; MED = a common mode or feature;
LOW = a niche mode, a GM tool, or behind a setting.

---

## At a glance

| P | What | Today | Visibility |
|---|---|---|---|
| P1 | [Pickups and items](#p1-pickups-items-and-cargo) | ~100 pickup keys are 16 shapes x 3 glows; no 2D item icons | HIGH |
| P1 | [Fighters for Kralien, Skaraan, Torgoth](#p1-fighters-and-small-craft) | station wings fly `tsn_fighter` | HIGH vs those races |
| P1 | [StormsBeacon relic items](#p1-stormsbeacon-relic-items) | ~19 items are the `unknown` question-mark mesh | HIGH in SB |
| P1 | [Piranha rebuild](#p1-monsters) | its crash keeps 5 species switched off | HIGH once back |
| P1 | [Peacetime props](#p1-peacetime-remastered-props) | `cargo_ship` stands in for ~10 unrelated things | HIGH in that map |
| P1 | [Admiral 2D map icons](#p1-admiral-2d-map-iconography) | built-in glyph stand-ins | MED (Admiral) |
| P2 | [Turrets](#p2-turrets) | towers are a shrunken starbase; mounts and crates are a fighter | MED-HIGH when on |
| P2 | [Station kinds](#p2-station-kinds-and-missing-starbases) | a scaled copy of the race's one starbase | MED |
| P2 | [Ximni and Pirate starbases](#p2-station-kinds-and-missing-starbases) | none exist, so those races can't hold bases | MED |
| P2 | [Map markers](#p2-map-markers-and-radar-glyphs) | `generic-sphere`, default radar glyph | MED |
| P2 | [ePADD / xESS glyphs](#p2-epadd-xess-and-quest-icons) | shared glyphs, Nav on a stand-in, a "wanted" word baked into the quest icon | HIGH (quest log) |
| P2 | [Portraits](#p2-portraits) | every cast is generated faces | MED |
| P2 | [MIA pod, antimatter veil, console icons](#p2-admiral-console-icons) | wreck / red nebula / text | MED (Admiral) |
| P3 | [Typhon-style creatures](#p3-monsters-distinct-silhouettes) | 8 species on 5 shared primitives | HIGH on monster maps |
| P3 | [Relic props](#p3-relics) | procedural rock; `generic-sphere` barriers | MED in SB |
| P3 | [Admiral platforms, worldlets, Fabricator, livery](#p3-admiral-platforms-reused-station-hulls) | reused station hulls | MED (Admiral) |
| P3 | [Skyboxes](#p3-skyboxes-and-music) | 7 stock skies, 2 used by AMD regions | HIGH (ambient) |

---

## P1 - Pickups, items and cargo

**No item has its own model, and the stock pickup set is smaller than it looks.** The ship
table lists about a hundred pickup keys, but they are **16 shapes** in three families:

| Family | Shapes | What the keys really are |
|---|---|---|
| `container_*` | 6 crates | `_Na/_Nb/_Nc` are the SAME mesh and diffuse texture with a different **glow** (emissive) color; `container_small_*` are the same crates at lower detail (`container6` exists only at low detail) |
| `alien_*` | 5 artifacts | the same: 3 glow colors each, plus `alien_small_*` low-detail copies |
| `danger_*` | 5 mines | the same - and these are the **mine** meshes (`behav_mine` uses `danger_1a`) |

So the only per-item tell today is **shape x glow color**, and ~25 items and upgrades (plus
StormsBeacon's relic items) share 11 usable shapes.

- **Done in data (2026-09-19):** every LM item now has its own shape-and-glow combination -
  crates for cargo, trade, resources and kits; alien artifacts for exotic upgrades and
  beacons; mines only for mines; red glow only for the dangerous or illicit (Hacking Virus,
  contraband, the drone turret kit). The beacon, the Survey Probe, Infusion PCoil and
  Lateral Array stopped using mine meshes. It is the best the stock set allows.
- **Wants - new pickup meshes**, full + low detail, one per category that matters in play:
  **beacon**, **turret kit crate**, **tug rig**, **power cell**, **trade goods** (ore / gas /
  provisions / tech), **salvage**, **relic artifact**, **data chip / code case**. A distinct
  silhouette reads at radar and main-screen distance; a glow color does not.
- **Wants - 2D item icons.** None exist: the Cargo, Upgrades, Market and Fabricate apps are
  text lists. An icon per item (or per category) on a sheet like `media/epadd/icons.png`
  would make every one of those screens scan faster.
- **Stock data bug (not ours to fix):** `data/shipData.yaml` lists `container_small_6a`
  twice, and the first entry points at `container4lod_a` - so that key draws crate 4, not
  crate 6. LM no longer uses it.
- **Flat sprites for tethered cargo.** The grav-tether readout shows a dark panel for pickups
  and cargo pods (`consoles/tether_indicator.py` `MT_NO_ART`: `ship_art_image` returns
  nothing for them). LOW-MED.

## P1 - Fighters and small craft

- **Kralien, Skaraan and Torgoth have no fighter hull.** Their starbase wings launch
  `tsn_fighter` (`hangar/hangar_wing.py` `HANGAR_WING_FALLBACK_HULL`; one warning per
  station). Wants: a fighter, ideally a bomber, for each. Fighters are chosen by the host
  hull's `origin`, so a hull with the right origin and a `fighter` role is picked up with
  no code change.
- **Hangar variants share hulls** (`hangar/hangar_crafts.yaml`, deliberate per its line 18):
  Ximni fighter and bomber are both `xim_avenger`, Pirate both `pirate_fighter`, Arvonian
  both `arvonian_fighter`; Ximni and Arvonian shuttles are `tsn_shuttle`, Pirates have no
  shuttle. Wants: bomber hulls for those three and non-Terran shuttles. MED.

## P1 - StormsBeacon relic items

About 19 item records are `Art: unknown` - the question-mark mesh - and they spawn as relic
contents the crew has to find: `relics/ash_warren.amd`, `cipher.amd`, `false_choir.amd`,
`heart.amd`, `lens.amd`, `sink.amd`, `voice.amd`. The `unknown` art also has no interaction
radius (`sbs_utils/procedural/items.py`), so they may not even be collectable by flying over
them - unverified in the engine.

- **Wants:** a route chart / data plate, a relic artifact, deep-salvage props. HIGH in SB.

## P1 - Monsters

- **Rebuild the Piranha.** `MONSTER_NON_TYPHON` is off by default because of an engine render
  crash traced to `ships/monster2` - the only monster with a `.paxmesh` and split
  `_body`/`_jaw` geometry (MeshSilhouette / Ribbon3D path). That switch keeps **Piranha,
  Shark, Dragon, Charybdis and Insect** out of every game. A clean single-mesh Piranha is
  what brings all five back (`settings.yaml`, `prefabs/monster.mast` "HOT FIX 2026-08-27").
- **Converted 2.8 creatures** (`sbs_utils/procedural/a2x/spawn.py`): whale, tube and jelly
  have no art at all; types 1-7 all use `monster_charybdis` as a placeholder. Shark, dragon, piranha and
  bug could map to `monster4`, `monster3`, `monster2`, `monster5`. MED.
- **Biomech comms portraits** - the stage-4 hailable biomech gets a human face (`races.amd`
  falls back to terran). LOW-MED.

## P1 - Peacetime Remastered props

`maps/peacetime_remastered.mast` uses `cargo_ship` for ten things that are not freighters:

| Object | Wants |
|---|---|
| Condemned Hulk, Salvage Hulk | wreck / hulk |
| Ore Barge | ore barge |
| Lifepod, Stranded Pod, Shielded Pod | escape pod (stock `escape-pod` art exists and is unused here) |
| Comms Relay | relay buoy |
| SS Meridian (derelict) | derelict |
| Snared Grazer | should look like a Grazer |
| Drift Netting | net / debris |

The Survey Probe is `danger_4a`. Some of these (the pods) are a data swap to stock art, not
new art.

## P1 - Admiral 2D map iconography

The galaxy map's shape language matters more than any 3D model (ADMIRAL_CONSOLE.md
section 9). The Nav galaxy map is still text buttons (`universe.mast`); the Admiral galaxy
theater now has **stand-ins** from the built-in icon sheet
(`admiral/universe_galaxy_theater.py`): home = globe-grid, station = fountain, enemy =
goblin, nebula = pinwheel, anomaly = atom, empty = circle-outline, fog = square-outline,
player ship = patrol-badge, fleet = squad. Dedicated icons still wanted:

| Icon | Needs | Where it reads |
|---|---|---|
| Worldlet (by type) | a glyph per type (cinder / gas / haven), tinted | map cell + Map tab worldlet list |
| Platform markers | HQ, Extractor, Refinery, Shipyard, Academy, Bastion, Relay, Depot, Sensor Relay, Lab | system view + selected-worldlet panel |
| Fleet marker | a friendly-fleet chevron with an order tint (escort / patrol / strike...) | system view |
| Foe border | a hatch / warning edge on cells bordering foe territory | galaxy map |
| Antimatter veil | a hazard band distinct from the amber wash | galaxy map + "Selected System" |
| Quest / requisition target | a clear objective pin | galaxy map |

The engine `grid-icon-sheet.png` (128px white-on-transparent, tinted) is the substrate; a new
sheet slots in the same way.

---

## P2 - Turrets

There are **no turret models**. Every turret hull (LM `media/turrets/extraShipData_turrets.yaml`)
borrows a stock mesh:

| Hull | Borrows | Wants |
|---|---|---|
| `lm_turret_beam` | `tsn-big-base` (the command starbase) at ~41% | a defense tower / gun emplacement |
| `lm_turret_heavy` | the same, larger | a heavier fort-style emplacement |
| `lm_turret_mount` | `TSNfighter` at 1.2 | a small gun turret that bolts onto a hull - today a tiny fighter is welded on |
| `lm_turret_crate` | `TSNfighter` at 1.6 | an inert kit crate (its own file comment says so) |

Constraint: a turret must be a hull the mission declares - stock hull art never fires
(engine-measured). New art arrives as a new `artfileroot` in that file. Turrets only exist
with `EXTRA_SHIP_DATA` on.

## P2 - Station kinds and missing starbases

- **Station kinds** (LM `station_kinds/`): the Industrial, Science and Civil bases of
  Kralien, Arvonian, Skaraan and Torgoth are the race's one starbase **scaled** (0.8 / 0.6 /
  0.5). Wants: a distinct silhouette per kind per race, the way Terran has
  `starbase_industry` / `_science` / `_civil`. Swap the `artfileroot` in
  `media/stations/extraShipData_station_kinds.yaml` (regenerate with
  `station_kinds/make_station_kinds.py`, then edit). Only with `EXTRA_SHIP_DATA`.
- **Ximni and Pirates have no starbase at all** (`races/races.amd`), so station maps never
  pick them as the enemy. A starbase each opens them up.
- **OU outposts** reuse Terran starbases for every side, pirate and cult included
  (`universe_systems.py`); a landmark with no art falls back to `starbase_science` or `wreck`.

## P2 - Map markers and radar glyphs

Science's order markers (Alpha, Bravo...), job markers and nebula markers are all
`generic-sphere` with `behav_selection`: hidden on the main screen, a tint on radar, and the
default radar glyph (`sbs_utils/procedural/markers.py`, `terrain.py`). Wants radar glyphs
for: **order marker**, **point of interest / job site**, **nebula**. MED.

OU empty systems spawn an "Unknown Contact" as the `unknown` question-mark mesh
(`universe.mast`) - wants a sensor-ghost or empty-space buoy. MED-HIGH in OU.

## P2 - ePADD, xESS and quest icons

The LM sheet `media/epadd/icons.png` is 4x6 cells of 128px; all 21 named cells have art and
**3 cells are free**.

- **Stand-in:** xESS **Nav** uses the built-in `helm-wheel` glyph (it asked for an
  unregistered `epadd.helm` - see *Bugs found* below); a nav glyph on the sheet would match.
- **Sharing a glyph:** Survey = Status, Available Quests = Quests; in xESS, Scan = Status,
  Act = Quests, and Work and Fire both use Damage.
- **The quest log's job icon** is the built-in `wanted` glyph, which has the word baked into
  it (`icon_sheet.py` `ICON_ALIAS["quest.job"]`). Wants a quest/job glyph and a custom sheet
  for the other `quest.*` meanings. HIGH.
- Built-in stand-ins noted in `consoles/epadd.mast`: Help is a pointing hand, Airwing an
  unreadable blob. The host's Save / Copy / Load icons are admitted placeholders
  (`consoles/server_console.mast`). LOW.

## P2 - Portraits

There are **no hand-drawn portraits anywhere**; every cast uses generated faces by keyword.
Named recurring characters that would carry a lot more with a real portrait:

- OU: the officers - Vale, Kade, Ashwell, Serval, Voss, Orlan (`skirmish_arena.amd`,
  `default.amd`).
- StormsBeacon: its leads (`stormsbeacon.amd`).
- LM: the casino bar regulars and Crazy Eddy.

## P2 - Admiral console icons

- **Ticker and tabs** are text (`ORE 240/600  GAS 96/600  CREW 40/600  CMD 1/3`): wants
  resource glyphs (ore / gas / crew / command point) and tab glyphs (Map / Build / Research /
  Fleets / Requisition).
- **MIA escape pod** is a `wreck` scaled 0.35 (`universe_fleets.py`). Wants a small life-pod
  with a blinking distress beacon - it has to read as "a person to save". The stock
  `escape-pod` mesh exists and would already be better.
- **Antimatter veil** is red nebula spheres plus `sky-neb2-rvb`. Wants a vertical
  rainbow/plasma *shear* curtain, and a dedicated veil skybox.

---

## P3 - Monsters: distinct silhouettes

The eight Typhon-style species share five geometry primitives, pairs differing only by tint:
`typhon-big-cube` (Bulwark, Grazer), `typhon-cylinder` (Leech), `typhon-balls` (Ravener,
Warden), `typhon-needle` (Reaver), `typhon-panel` (Sparkfeeder). A silhouette per species.

## P3 - Relics

Relic interiors are procedural from asteroids and `generic-*` primitives by design
(`build/relics.md`). Optional: ancient-architecture wall / plate / pillar kits for built
relics (The Voice), and real **barrier / door** props - today the barriers crews shoot
through are `generic-sphere`.

## P3 - Admiral platforms (reused station hulls)

| Platform | Placeholder art | Intended |
|---|---|---|
| Headquarters | `starbase_command` | a flag / command anchor - the biggest, most fortified |
| Extractor | `starbase_industry` | a mining rig clamped to a worldlet |
| Refinery | `starbase_civil` | a processing plant (pipes / tanks) |
| Shipyard | `starbase_science` | a drydock with hulls under construction |
| Academy | `starbase_command` | a training / campus station, distinct from HQ |
| Bastion | `starbase_command`, scale 1.5 | an armed fort - visibly a weapon |
| Relay Gate | `starbase_science` | a jump-gate ring |
| Depot | `starbase_industry` | a supply depot with fuel tanks / tenders |
| Sensor Relay | `starbase_science` | a sensor / comms tower with dishes |
| Lab | `starbase_science` | a research lab / observatory |

Keys are `art:` in `ADM_PLATFORMS` (`universe_worldlets.py`). A distinct Bastion is the most
useful single swap.

## P3 - Worldlets, the Fabricator, fleet livery

- **Worldlets** have real art via `behav_planet` palettes. Polish: distinct models or ring /
  belt variants per type, 3-4 palettes each.
- **The Fabricator** (`FAB_ART` in `universe_fabricator.py`) is a `tsn_light_cruiser`. Wants a
  slow unarmed construction / tender hull. Only if build model B is adopted.
- **Fleet livery:** commissioned Admiral fleets reuse player hulls (`FLEET_ROSTER`); a decal
  to tell them from player ships.

## P3 - Skyboxes and music

LM picks from 7 stock skies (`basic_random_skybox.mast`); AMD regions across OU and SB only
ever use `sky-neb2-rvb` and `sky-delight`, and one music bank (`Artemis2`). More skies -
and a veil sky - would stop every region looking alike. `media/skybox/sky-local.png` ships
in LM but nothing references it.

## P3 - Docs

`sbs docs` can't show hulls - `ship://` images stay a placeholder
(`tooling/amd-docs.md`). Pre-rendered hull thumbnails would fill them. LOW.

---

## Bugs found while surveying (not art) - fixed

- **The a2x converter spelled the monster key `monster_charbdis`**, which the ship table
  does not have, so converted 2.8 monsters drew the `unknown` mesh. Now `monster_charybdis`,
  with a test that every converter art key exists.
- **The xESS Nav tile asked for `epadd.helm`**, which nothing registers. It now uses the
  built-in `helm-wheel` glyph. A dedicated nav glyph in one of the 3 free ePADD cells would
  still be nicer.
- **Docs drift:** `build/epadd.md` showed the icon sheet as 4x5 (it is 4x6); LM
  `hosting/settings.yaml.md` said `MONSTER_NON_TYPHON` defaults true (it is false).

## Not placeholders (no art needed)

- **EVA suit** - real art (`lm_eva_suit`), with `EXTRA_SHIP_DATA`; without it the suit falls
  back to `tsn_shuttle`.
- **Cockpit overlay**, **casino decks**, **console backgrounds**, **Biomech hulls** - real art.
- **Requisition items** deliver real registered items with existing art.

## References

- `ADMIRAL_CONSOLE.md` section 9 (temporary art strategy) and appendices ("worldlet surface
  knobs", "CQ nebula catalog").
- `sbs_utils/mkdocs/docs/build/turrets.md`, `build/relics.md`, `build/epadd.md`.
- The `making-a-mod` and `art-pipeline` skills: how a hull reaches the engine, and the art
  bake.
