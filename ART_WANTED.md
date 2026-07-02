# ART_WANTED - Admiral console placeholders

The manifest `ADMIRAL_CONSOLE.md` section 9 calls for: every placeholder the
Admiral console ships with, what it should become, and how urgent. When an artist
appears they get a shopping list instead of an archaeology dig.

**How replacement works (no code changes):** every art reference lives in a data
key - a platform's `art:` in `ADM_PLATFORMS` (universe_worldlets.py), a worldlet's
`Palette:` / `Art:` in the AMD, a hull name in `FLEET_ROSTER`. Swapping art = edit
that key (or, for palettes, the AMD numbers). Nothing here needs new code, only
new assets + a one-line data edit. Placeholders are chosen to be *legible, not
pretty* - ugly is fine as long as you can tell what a thing is.

**Priority:** **P1** = blocks readability / most impactful (do first); **P2** =
clearly improves feel; **P3** = polish, current reuse is acceptable.

---

## P1 - The Admiral 2D map iconography

Section 9 says design the icon set *first* - the galaxy/system map's shape
language matters more than any 3D model. Today the galaxy map (universe.mast nav
console) draws cells as coloured text buttons; there are no dedicated icons. This
is the single highest-value art ask.

| Icon | Needs | Where it reads |
|---|---|---|
| Worldlet (by type) | A glyph per worldlet type (cinder / gas / haven), tinted to the type | Map cell + the Admiral Map tab worldlet list |
| Platform markers | HQ, Extractor, Refinery, Shipyard, Academy, Bastion, Relay - a small distinct glyph each | System view + the selected-worldlet panel |
| Fleet marker | A friendly-fleet chevron, with an order tint (escort/patrol/strike/...) | System view (Admiral overlay) |
| Foe border | A hatch / warning edge on cells bordering foe territory (skirmish pressure) | Galaxy map |
| Antimatter veil | A hazard band glyph distinct from the amber wash it already gets | Galaxy map + nav "Selected System" panel |
| Quest / requisition target | The existing amber cell wants a clearer objective pin | Galaxy map |

Reference: the engine `grid-icon-sheet.png` (128px white-on-transparent sprites,
Canvas-tinted) is the established icon substrate - a new sheet slots in the same
way.

## P2 - Console UI icons (ticker + tabs)

The ticker is text (`ORE 240/600  GAS 96/600  CREW 40/600  CMD 1/3`) and the tab
strip is text labels. Small icons would make the console scan faster.

| Icon | Needs |
|---|---|
| Resource glyphs | ore / gas / crew / command-point - one small icon each, for the ticker + cost lines |
| Tab glyphs | Map / Build / Research / Fleets / Requisition |

## P2 - MIA escape pod

A destroyed fleet's officer ejects into a pod the crews fly out to rescue - so it
has to read clearly at a glance as "a person to save," not generic debris. Today
it is a `wreck` art terrain object scaled to 0.35 with a `mia_pod` role.

- **Is:** `terrain_spawn(..., "wreck", "behav_wreck")`, `local_scale_*_coeff 0.35`
  (`universe_fleets.py` `_officer_mia_begin`).
- **Wants:** a small life-pod / escape-capsule model with a blinking distress
  beacon FX, distinct from salvage wrecks. Rescue objective legibility is the point.

## P2 - Antimatter veil

The veil is a survivable-only-briefly hazard curtain. Today it is red-tinted
nebula spheres.

- **Is:** `terrain_spawn_nebula_sphere(radius=8000, density=2, height=24000,
  cluster_color="red")` per emitter, region skybox `sky-neb2-rvb`
  (`universe.mast` enter_system).
- **Wants:** a distinct antimatter *shear* look - a vertical rainbow/plasma
  curtain rather than a red gas cloud - so it doesn't read as an ordinary nebula.
  A dedicated skybox for veil systems would sell it further.

## P3 - Admiral platforms (reused station hulls)

All seven platforms reuse existing starbase hulls, differentiated by role via a
consistent naming prefix, side colour, and (Bastion) scale. Legible today; a
dedicated model set per platform is a nice-to-have, not a blocker.

| Platform | Placeholder art | Intended |
|---|---|---|
| Headquarters | `starbase_command` | A flag/command anchor - the biggest, most fortified |
| Extractor | `starbase_industry` | A mining rig clamped to a worldlet |
| Refinery | `starbase_civil` | A processing plant (pipes/tanks), reads as "industry+" |
| Shipyard | `starbase_science` | A drydock with hulls under construction |
| Academy | `starbase_command` | A training/campus station (distinct from HQ) |
| Bastion | `starbase_command`, `local_scale 1.5` | An armed fort - turrets/ion cannon, visibly a weapon |
| Relay Gate | `starbase_science` | A jump-gate ring, reads as inter-system infrastructure |
| Depot | `starbase_industry` | A supply depot with fuel tanks / tenders - a fleet resupply anchor |
| Sensor Relay | `starbase_science` | A sensor/comms tower with dishes - reads as command + detection |
| Lab | `starbase_science` | A research lab / observatory - distinct from the Shipyard's science hull |

Art keys are the `art:` values in `ADM_PLATFORMS` (universe_worldlets.py) - an
`## Platforms` AMD chapter could move them to data later. HQ and Bastion share
`starbase_command`; a distinct Bastion silhouette is the most useful single swap.

## P3 - Worldlets

Worldlets already have *real* art via the `behav_planet` data_set surface knobs -
each type authors a palette (base / emissive / clouds / bands) in its AMD entry,
so there is visual variety now.

- **Is:** `terrain_spawn(..., "planet", "behav_planet")` + palette
  (`universe_worldlet_spawn`); Cinder `#8c2f1c`, Veiled Giant gas tones, Haven
  greens (default.amd `## Worldlets`).
- **Wants (polish):** distinct planet models or ring/asteroid-belt variants per
  type; author 3-4 palettes per type. See ADMIRAL_CONSOLE.md appendix "worldlet
  surface knobs" for the full data_set parameter list.

## P3 - Fleet hull livery

Fleets reuse real player-faction hulls (`tsn_light_cruiser` x2 as escorts,
`tsn_battle_cruiser` as the line ship in `FLEET_ROSTER`). Fine as-is; an
Admiral-fleet livery/decal to distinguish commissioned fleets from player ships
would add character. Low priority.

## P3 - Officer portraits

Officers use the authored `Face:` keyword (male/female -> a random generated
face). Works and is consistent per session (cached). Dedicated hand-drawn
portraits for the named Academy officers (Vale / Kade / Ashwell) would give the
roster more personality. Low priority.

---

## Not placeholders (no art needed)

- **Requisition items** deliver real registered item objects (the classic
  upgrades) with their existing art - nothing to replace.
- **Skybox / music** for regions use existing named assets via the AMD
  `Skybox:` / `Music:` keys.

## References

- `ADMIRAL_CONSOLE.md` section 9 (temporary art strategy) and the appendices
  ("worldlet surface knobs", "CQ nebula catalog").
- `ADMIRAL_CONSOLE_DONE.md` for what each system does, if you need context on a
  placeholder's role.
