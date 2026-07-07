# The Admiral Console - design brainstorm

A new console for Artemis Cosmos: one player runs an RTS-flavored strategic
game **on the same side as the player ships**, overseeing friendly fleets,
building infrastructure, researching upgrades the bridge crews can actually
receive, and feeding the war effort. The bridge crews play Artemis; the
Admiral plays the war *around* them.

Reference game: **Conquest: Frontier Wars** (2001) - "CQ" below. The manual is
at `f:\a\Conquest Frontier Wars - Manual.pdf`. We mine CQ for patterns, we
don't ape it. Section 2 is the full inventory of what CQ has and what we take.

Cosmos used to have an Admiral console; this is different and closer to the
original intent: an Admiral is a *player on a side*, not a game master. (The
GM/operator consoles stay what they are.)

---

## 1. The core fantasy and the loop

**Bridge crews** feel: "someone has our back - reinforcements, resupply, and
new toys come from somewhere real, and we can ask for them."

**The Admiral** feels: "I run the navy. I decide where the fleets go, what we
research, what gets built, and which crews get the good hardware. When the
players win a fight I set up, it was my plan too."

The Admiral's loop (one sitting):
1. **Claim** - plant infrastructure at resource bodies (worldlets, section 4).
2. **Extract** - harvest and refine resources.
3. **Research** - walk a small tech tree; unlock upgrades and hulls.
4. **Project** - form fleets, assign captains, give orders that support the
   player ships (escort, picket, strike, salvage, supply).
5. **Deliver** - push upgrades/torpedoes/consumables to player ships through
   the existing upgrade/item system; subsidize their stations.

The loop must *touch the bridge game* at every step - an Admiral turtling in
a corner playing solitaire RTS is a design failure. Every build/research
choice should have a visible effect a bridge crew can feel or receive.

**Interface reality check:** the Admiral console is a GUI console (2D map +
panels + queues), not a 3D flythrough. That's good news for art (section 9)
and puts the build effort in `gui_*` layout work, where we're strong.

---

## 2. CQ pattern inventory - mine, simplify, or skip

Everything in the CQ manual worth a decision, so nothing is left unmined.

| CQ pattern | What it is | Verdict |
|---|---|---|
| Three resources: Ore / Gas / Crew | Ore = build, Gas = fuel, Crew = operate | **Mine.** Three is the right count. See section 3. |
| Command Points | Fleet cap that grows with HQ/sensor infrastructure | **Mine.** The single best anti-snowball lever - caps fleet spam and gives infrastructure a purpose beyond economy. |
| System Supply (binary in/out of supply) | A system is "in supply" only if connected by jump gates to an HQ system | **Simplify.** In OU, adjacency chains to a supplied system; in a one-system Siege game it collapses to supply *radius* around platforms. Powerful with our engine-network culling: out-of-supply = degraded, not dead. |
| Jump Gates lock wormholes | Supply line + traffic control; destructible from both sides | **Simplify (OU only).** A "Relay" platform makes a neighboring system reachable-in-supply; foe clans can raid it. Siege games skip it. |
| Resupply radius; Supplyship; Repair Platform; repair costs resources | Logistics as gameplay | **Mine minimally.** Docking already refuels/rearms players. Admiral logistics applies to NPC fleets: a fleet out of supply fights at a penalty. One mobile Tender ship class. |
| Fabricator (builder ship) | Construction is a vulnerable unit, not a menu click | **Mine.** One Fabricator ship the Admiral orders around. Killing it hurts. It's also the natural "temporary art" ship (any freighter hull). |
| Harvester (off-planet mining) | Gathers from asteroid fields/nebulae | **Phase 2.** Start with platform-based extraction only; add Harvesters when asteroid/nebula mining matters. OU already scatters loot in fields - keep that as the *player* version of harvesting. |
| Platform tech tree (HQ -> Refinery -> Academy -> Shipyards -> Labs) | Prereq chains gate progress | **Simplify hard.** CQ has ~17 platforms/race; we start with 6 (section 5). |
| Naval Academy trains 6 named admirals with personality bonuses | Halsey (battleships/supplies/shields), Hawkes (speed), Takei (carriers/sensors), Steele (damage), Smirnoff (vs platforms), Benson (evasion/range) | **Mine enthusiastically - as captains.** This IS our captains system: named characters, trait weights, per-fleet bonuses. Author them in AMD like OU captains; the traits reuse reputation poles. Section 6. |
| Admiral boards largest ship, bails when it dies, transferable | The commander is a physical object in the world | **Mine for captains.** A captain lifeform hosted on the flag ship; if it dies, she ejects to another fleet ship (or is lost - drama). Do NOT put the human Admiral player in the world. |
| Fleet commands: Form/Disband/Repair fleet/Resupply fleet/Assault | One-click fleet-level orders | **Mine.** Maps directly onto our brains: each command = a brain label with the fleet's blackboard. Small fixed verb set (section 6). |
| Fleet special-weapon buttons; admiral picks best executor | Fleet-level ability use | **Skip initially.** NPC brains already fire their own weapons. Maybe later: one "doctrine" button per fleet (aggressive/defensive/screen). |
| Planet types yield different resources (earth=all, moon=ore, gas giant=gas, swamp=crew) | Geography drives economy | **Mine.** Our worldlet types, defined in universe AMD (section 4). |
| Planet popup: current / original / harvest rate | Depletion is visible | **Mine.** Worldlets deplete. Forces expansion, ends turtling, and in OU makes territory worth fighting over. |
| Nebula effect catalog (Helios amplifies damage, Celsius locks supplies, Ion kills shields, Cygnus speeds up...) | Terrain as tactical modifiers | **Phase 2, but keep the list.** OU nebulae are currently scenery; typed nebula effects are a whole feature by themselves and benefit the bridge game even without an Admiral. |
| Antimatter ribbon: impassable terrain | Absolute movement wall | **Mine, adapted for 3D.** Section 8. |
| Black holes | Gravity death trap | Already exists in OU prefabs. No action. |
| Diplomacy screen: alliances + gifting resources | Inter-player relations | **Mine the gift, skip the screen.** OU diplomacy already exists clan-side. Admiral-to-players resource flow is section 7. Multi-Admiral alliance games are far future. |
| Salvage (Mantis Dissection Chamber refunds resources from wrecks) | Wreck recycling | **Mine.** Wrecks/derelicts already exist in OU. A Salvage fleet order that converts wrecks to resources is cheap to build and very on-theme. |
| Rally points, idle-worker button, research-platform cycle button | UI quality of life | **Mine the ideas** when the GUI is built - rally = default station for new hulls; an "idle" indicator on the Admiral panel. |
| Fog of war / LR Sensor Tower | Information warfare | **Simplify.** OU already has Fog of War on the galaxy map. A Sensor platform extends what the Admiral (and science!) can see. Feeds the bridge game: Admiral sensors light up science contacts. |
| Troopship assault / boarding | Capture mechanics | **Skip.** OU already has space-dock capture for players; don't duplicate it in fleet AI yet. |

---

## 3. Resources

Three gathered resources + one cap, straight CQ shapes with our names:

| Resource | From | Spent on |
|---|---|---|
| **Ore** | rocky worldlets, (later) asteroid fields | hulls, platforms |
| **Gas** | gas worldlets, (later) nebulae | fleet operations: every fleet order burns gas; research reactors |
| **Crew** | inhabited worldlets (recruiting) | commissioning ships, staffing platforms; captains |
| **Command** (cap, not stock) | HQ + each Relay/Sensor platform | max simultaneous fleets/ships under Admiral command |

Design intents:
- **Crew is the emotional resource.** Losing a fleet loses people; the number
  going down should sting. It also ties to lifeforms/captains naturally.
- **Gas as an *operations* cost** (not just build cost) is the throttle on
  Admiral aggression: you can hold a big navy (ore) but running it hard costs
  gas. This keeps the Admiral making choices instead of A-moving.
- **Command points prevent super-navies** independent of economy balance -
  the cheapest and most robust balancing tool we can steal.
- Stored amounts have silo caps (build more silos = another early platform
  choice), so hoarding for one giant spike is bounded.

All numbers live in the **universe AMD** (a `## Admiralty` chapter or the
worldlet entries) so a Siege game and an Open Universe can tune the same
engine differently - see section 10.

## 4. Worldlets (the resource bodies)

`behav_planet` draws small planet/gas-giant terrain (see appendix for the
data_set surface knobs). They're too small to be planets and they're not all
gas giants, so they need their own word.

**Proposed name: worldlet.** Reads instantly, covers rocky and gaseous kinds,
singular/plural are clean, and it doesn't collide with an astronomy term the
science console might want later. Runners-up, in case worldlet doesn't sing:
- *planetoid* - familiar, but astronomers use it for asteroids; collides with
  our asteroid terrain.
- *dwarf world* - accurate but two words, awkward in UI labels.
- *protoworld* - implies "still forming"; wrong flavor for settled ones.
- *orb / mote / kernel* - too cute by half.

Worldlet **types** are authored in the universe AMD (same friendly fact-sheet
shape as everything else), so each universe can define its own geology:

```
## Worldlets

### Cinder World (cinder)
---
Yields: ore 8
Reserve: 4000
Art: behav_planet
Base color: #8c2f1c
---
A cracked, mineral-rich ember of a world. Miners love it; nobody else does.

### Veiled Giant (veiled_giant)
---
Yields: gas 10
Reserve: 6000
Base color: #2c4a8c
---
A banded gas giant, its high winds rich in fuel-grade volatiles.

### Haven World (haven)
---
Yields: crew 2, ore 2, gas 2
Reserve: unlimited
---
A small settled world. People, modest industry, and somewhere to come from.
```

- `Yields:` = per-minute extraction *per extractor platform* (CQ: different
  planets, different resources; earth-type yields all three).
- `Reserve:` = depletion pool (CQ's current/original popup). `unlimited` for
  inhabited worlds so crew never hard-zeroes.
- Generation: worldlets join the POI deck (`Worldlet chance:` dial) and
  regions can override the mix - an ore-rich region is a war objective now.
- The galaxy-map popup shows yields/reserve exactly like CQ's planet popup.

## 5. Platforms (built around worldlets)

CQ builds platforms *at planets*; we do the same around worldlets, authored
as **prefabs** so missions/universes can reskin or extend them. Launch set of
six - CQ's seventeen, folded:

| Platform | Folds in (CQ) | Does |
|---|---|---|
| **Headquarters** | HQ | Anchor of supply; awards command points; prereq for everything. One per side to start. |
| **Extractor** | Refinery-on-planet | Harvests the worldlet's `Yields:` into stores. The minimum viable Admiral game is HQ + Extractor. |
| **Refinery** | Refinery upgrades + silos | Boosts extraction, raises storage caps, unlocks tier-2 build costs. |
| **Academy** | Marine Training Facility + Naval Academy | Recruits crew from inhabited worldlets; trains **captains**; researches crew/officer tech. |
| **Shipyard** | Light+Heavy Shipyards + Fabricator's build role | Commissions fleet hulls; the research site for hull/weapon tech. |
| **Bastion** | Laser Turret / Space Station / Ion Cannon | Defense platform; protects a worldlet or a jump point. |

Phase 2 platforms, when the base loop is proven: **Depot** (supply radius +
Tender ships; CQ Supply/Repair Platforms), **Sensor Relay** (fog of war +
command points; CQ LR Sensor Tower), **Relay Gate** (OU inter-system supply;
CQ Jump Gate), **Lab** (splits research off the Shipyard/Academy).

Prefab shape (mission-local or LM addon, same metadata pattern we already
use for `prefab_side_generic` and station prefabs):

````
=== prefab_admiral_extractor
metadata: ``` yaml
display: Extractor
cost: { ore: 300, crew: 20 }
build_time: 45
requires: hq
art: starbase_industry     # placeholder art, see section 9
```
````

A **Fabricator ship** (one, cheap, slow, unarmed) does the physical building:
the Admiral clicks the worldlet + platform type, the Fabricator flies there
and builds it over time. It's a target, which makes early expansion a real
decision. (CQ pattern kept on purpose - build-by-menu feels like a spreadsheet;
build-by-vulnerable-ship feels like a navy.)

## 6. Fleets and captains (simplified hard)

CQ: recruit a named admiral at the Academy, form a fleet around them, issue
fleet-level commands, the admiral grants personality bonuses. Replace "CQ
admiral" with **our captain system** and the whole thing lands on machinery
that already exists:

- A **captain** is a lifeform + AMD record (exactly like OU clan captains):
  name, face, `Values:` trait weights, a voice via dialogue scenes.
- **Traits reuse the reputation poles** and grant fleet bonuses:
  `fearsome` -> damage, `by-the-book` -> supply efficiency, `resourceful` ->
  salvage yield, `peaceful` -> escort/defense bonuses, `intellectual` ->
  sensors... one mapping table, authored, not hardcoded. (This is CQ's
  Halsey/Hawkes/Takei/Steele/Smirnoff/Benson roster - Halsey's
  supplies/shields bonus is literally `by-the-book`; Benson's evasion is
  `resourceful`; Steele's damage is `fearsome`. The pattern transplants
  1:1 onto poles we already have.)
- The Academy offers a small roster (3 at launch, authored in the universe
  AMD - a `## Officers` chapter, or reuse `## Captains` with `Clan: <player
  side>`). In OU their *personal standing* with bridge crews can even move -
  captains the crews fly with get better. That's free depth from the
  reputation engine.
- A **fleet** = captain + hulls commissioned at the Shipyard, driven by the
  LM `ai`/brains addon. **Fleet orders are a fixed verb set**, each one brain
  label with a blackboard target:

  `escort <player ship>` · `patrol <system/region>` · `strike <target>` ·
  `hold <position>` · `salvage <field>` · `withdraw`

  That's it at launch. Every order burns gas (section 3); command points cap
  the number of fleets. The captain lifeform is hosted on the flag hull and
  ejects to another fleet ship if it dies (CQ's bail mechanic - cheap to do
  with `host =` and dramatic).
- **Comms is the Admiral's voice.** Fleet acknowledgments, captain
  personality lines, and distress calls run through dialogue scenes - the
  bridge crews hear the Admiral's navy talk. This is the glue that keeps the
  two games one game.

## 7. The Admiral <-> player economy bridge

Player ships deal in **credits**; the Admiral deals in ore/gas/crew. The
bridge should be *narrow, rate-limited, and one purpose per direction* - a
wide-open exchange collapses the two economies into one and invites super
ships (the thing we must not build).

Note the hook that already exists: `universe_helpers.py` keeps credits as a
**shared per-side pool** with the comment "the future admiral / RTS console
will own more of this economy." This console is that future.

Proposed bridges (each individually toggleable in AMD):
1. **Procurement (credits -> resources).** The Admiral posts a standing
   order; player-side credits buy resource deliveries *with lead time* (a
   freighter NPC actually flies in - interceptable, on-theme, and the delay
   is the rate limit).
2. **Subsidy (resources -> player prices).** The Admiral spends resources to
   discount station services/torpedoes/upgrades for the crews. Indirect,
   impossible to snowball into a super ship, and it *feels* like a navy
   quartermaster.
3. **Requisition (research -> upgrades).** Researched tech doesn't teleport
   onto player ships: it becomes an **upgrade item at a station** (existing
   item/upgrade system), and the crew still has to dock and take it. One
   hull-visit per upgrade is a natural absorption limit.
4. **Prize money (fleets -> credits).** Salvage operations pay a cut into
   the side credit pool. The Admiral funding the crews' shopping by cleaning
   up their battlefields is a lovely loop.

Anti-super-ship rails (apply to all bridges): per-session requisition budget;
upgrade tiers gated by research *milestones* (section 10) not raw stockpile;
diminishing returns on repeat purchases of the same upgrade; and everything
priced in the AMD so a tournament Siege can lock it down.

## 8. Antimatter (impassable terrain in a 3D engine)

CQ: a rainbow ribbon / yellow clouds, "lovely to look at but utterly
impassable." In a 2D game a wall works because there is no over/under. In
Cosmos, a true wall fights the engine (no navmesh; ships steer by pursuit)
and fights 3D itself (players will just fly over).

**Proposal: don't make it impassable - make it *unsurvivable*, and make it
volumetric.**

- **Form:** a vertical **curtain** - a ribbon of nebula-like emitters with
  real height (say 20-40k up/down), not a flat patch. Crossing is possible
  in theory; over/under means a long, fuel/time-expensive climb, so at
  strategic scale it shapes movement exactly like CQ's wall. (Embrace the
  third dimension as the *cost* rather than pretending it isn't there.)
- **Effect inside:** heavy continuous hull damage (heat damage channel) +
  drive dampening (speed clamp) + shields offline. Fast ships with a death
  wish can thread it; fleets and freighters never will. AI: fleet brains get
  a cheap `avoid_role("antimatter")` check - no pathfinding needed since
  brains already steer point-to-point and orders route around named zones.
- **On the maps:** hard hatched band on the galaxy/system map with a clear
  edge - the *information* is the wall as much as the damage is.
- **In OU generation:** a region-level line, e.g. `Antimatter: veil from -2,6
  to 4,6` or a `## Regions` entry with `Kind: antimatter`, so authors can
  fence off part of a galaxy (story gates: "the Reach beyond the Veil").
- **Name:** keep *antimatter* for the substance, call the terrain a
  **veil** or **shear**. ("The antimatter veil" reads well on a science scan.)
- Engine-honesty check: all of the above is data_set damage + speed knobs +
  art we already have (nebula emitters, tinted); no engine changes needed.

## 9. Temporary art strategy

Principles: never block design on art; make placeholders *systematically
replaceable*, not scattered hacks.

1. **All art references live in the prefabs/AMD** (`Art:` / `art:` keys) -
   already our pattern. Replacing art later = editing data, zero code.
2. **Platforms:** reuse existing starbase/station hulls, differentiated by
   role via `local_scale_*` coeffs + side color + a consistent naming prefix
   (`[EXT] Cinder Extractor`). Ugly is fine; *legible* is mandatory.
3. **Worldlets:** `behav_planet` + the data_set surface parameters (appendix)
   give us real visual variety NOW - author 3-4 palettes per worldlet type
   (base/emissive/cloud colors, band scale, wind) in the AMD entry itself.
   This is the one place we already have "real" art knobs - lean on it.
4. **The Admiral console itself is GUI** - panels, queues, list boxes, the
   galaxy map. The 2D map iconography (icon_index + color + shape language)
   matters far more than any 3D model. Design the icon set first.
5. Keep an `ART_WANTED.md` manifest as we go: every placeholder, what it
   should become, priority. When an artist appears, they get a shopping
   list instead of an archaeology dig.
6. Antimatter veil: tinted existing nebula emitters in a line. Done.

## 10. Balancing one engine across two game lengths

The requirement: an Admiral in a 40-60 minute Siege must *feel like the same
role* as an Admiral in a many-session Open Universe - but the pacing math
can't be the same, or one of the two breaks.

**Same engine, same verbs, different clocks - via three ideas:**

1. **Milestone research, not point research.** The tech tree is a fixed
   ladder of ~6-10 *milestones* per branch (hulls / weapons / logistics /
   officers). A game mode declares how many milestones are *reachable* and
   at what pace:
   - *Siege (45 min):* tree capped at milestone 3; costs tuned so a focused
     Admiral hits their last unlock around minute 30. Research feels like
     picking a **doctrine** (which branch), not climbing a tree.
   - *Open Universe:* full ladder, costs an order of magnitude higher,
     **progress persists in the save** (alongside side credits). Sessions
     end mid-tree and that's fine - it's a campaign.
   One tree definition, two pacing profiles - both authored in AMD
   (`Research pace: siege` vs explicit per-milestone costs).
2. **Session flattening (OU).** Persistent progress must not make session 5
   trivial: costs *within* a branch escalate steeply (late milestones are
   generational projects), and the *requisition budget* (section 7) resets
   per session - long-run tech raises what's *available*, not how much can
   be absorbed per sitting. An Admiral joining session 5 has more options
   than session 1, not a super navy.
3. **Rate caps over price walls.** Prefer per-minute extraction rates,
   build times, lead times, and command points (all time-shaped) to giant
   price tags (stockpile-shaped). Time-shaped limits scale automatically
   with session length; price walls have to be re-tuned per mode. This is
   the single most important tuning principle for making one engine serve
   both clocks.

Sanity targets: Siege Admiral makes their first meaningful delivery to a
player ship by ~minute 8; OU Admiral by end of first session has one fleet,
one extractor chain, and one requisition delivered.

## 11. What we already have (build on, don't rebuild)

- **Sides + clans + diplomacy** (OU) - the Admiral is a side member; foe
  clans are the opposition; capture already redraws territory.
- **Reputation poles** - captain traits and their fleet bonuses (section 6).
- **Captains/lifeforms/dialogue AMD** - the officer roster and its voice.
- **Quests/objectives** - Admiral "operations" could literally be quests
  granted to the side (reuse triggers: destroy/reach/dock).
- **prefab system + fleets + brains (LM)** - fleet spawning and orders.
- **Markets/commerce (LM)** - the station side of subsidy/requisition.
- **Side credits pool** (`universe_helpers.py`) - explicitly reserved for
  this console.
- **Universe AMD** - every number above gets authored, not hardcoded; an
  `## Admiralty` chapter (+ `## Worldlets`, `## Officers`) keeps the
  writer-not-programmer promise even for the RTS layer.
- **Engine-network culling / standby** (OU) - Admiral infrastructure in
  other systems can go dormant exactly like everything else.
- **Old LM `admiral`/`admiral_comms` addons** - salvage the console shell
  and comms wiring for parts, but this design supersedes them.

## 12. MVP slices (strawman)

1. **Slice 1 - the economy exists:** worldlets spawn with yields; HQ +
   Extractor prefabs; resource ticker on an Admiral GUI panel; galaxy-map
   popup shows yields/reserve. No fleets yet.
2. **Slice 2 - the war effort reaches the players:** Refinery + Shipyard;
   milestone research (one branch); requisition -> an upgrade item appears
   at a station; subsidy toggle.
3. **Slice 3 - the navy:** Academy + 3 authored captains; fleets with the
   six orders; gas burn; command points; captain comms chatter.
4. **Slice 4 - the frontier:** Bastion, salvage order, depletion pressure,
   antimatter veil, (OU) Relay Gate + persistent research.

Each slice is testable headless (the mock already drives NPC steering and
the GUI) and each slice ships something a bridge crew notices.

## 13. Decisions (first pass)

- **Multiple Admirals per side: yes.** Any number of Admiral consoles can
  join a side; they share the side's resource pools, research, and fleets
  (co-op at one faction, like two hands on one RTS). No per-Admiral
  ownership at launch - if order conflicts ever hurt in play, the cheap fix
  later is soft claims (a fleet shows who last commanded it), not hard
  partitioning. This also solves the Admiral going to the bathroom.

- **Fog of war: sensor-based, like the science console.** The Admiral does
  NOT get side-wide omniscience; they see what the side's coverage sees -
  platforms, Sensor Relays, their fleets, and (nice consequence) whatever
  player ships' science is lighting up. Engine networking limits push the
  same direction, so the honest implementation and the good design agree.
  Information asymmetry becomes gameplay: crews scout for the Admiral, the
  Admiral builds sensors for the crews.

- **Crew vs. captains, explained.** Two separate things are at stake:
  - *Crew* is a pooled number. Commissioning a hull spends crew; losing the
    hull loses them. It is the resource that makes fleet losses sting and it
    never needs names. (Decided by section 3 already.)
  - *Captains* are named characters, so their deaths are a design choice:
    1. **Immortal** - always ejects, returns to the Academy after a
       cooldown. Safe, flat, no stories.
    2. **Permadeath** - flag dies with no fleet ship to eject to, she's
       gone; the Academy offers a fresh recruit with weaker traits.
       Veterans become precious; roster churn is real drama but can feel
       brutal in a 45-minute Siege.
    3. **Missing in action (recommended)** - she ejects into a pod/wreck
       and becomes a *rescue objective the bridge crews can fly*: reach the
       pod, or dock it home, before a timer (or a foe clan) claims her.
       Rescued = returns with a scar and maybe a trait shift; unclaimed =
       permadeath. Admiral drama becomes bridge content - exactly the
       loop-touching rule from section 1. Siege can tune the timer short
       or default this off; OU makes it a signature event.

- **Raids: border skirmishes.** Extraction doesn't summon raids globally;
  pressure comes from *proximity to foe territory*. Platforms inside or
  bordering a foe clan's region draw periodic skirmish raids (scaled by
  that clan's strength/standing); deep-core mining is safe but the rich
  worldlets are seeded near borders and contested regions. Result: the
  frontier is where the Admiral's game and the crews' game meet - defense
  requests become escort orders become quests.

- **Where the Admiral exists: Siege (and the Open Universe).** The other LM
  missions are small, special-purpose recreations of Artemis 2.8 games and
  stay Admiral-free. Siege is the mode we keep upgrading, so the Admiral is
  built as: engine in sbs_utils/addon form, tuned by AMD, mounted first in
  Siege, mounted persistently in OU. Nothing binds it to either map.

- **AMD shape: reuse the location machinery we already have.** Correct
  instinct - the universe AMD already places things:
  - *Hand-placed worldlets* are **Landmarks** (`Kind: worldlet`,
    `Type: cinder`, `At: i, j`) - the Drifting-Cathedral pattern, no new
    chapter needed for placement.
  - *Procedural worldlets* ride the existing POI deck + region overrides
    (`Worldlet chance:`, per-region mixes), like derelicts/outposts today.
  - *Worldlet types* (yields, reserve, palette) and officer rosters do need
    defining somewhere: keep them as top-level `## Worldlets` and
    `## Officers` chapters, matching how `## Goods` defines types that other
    entries reference. `## Admiralty` (if we need it at all) shrinks to just
    the tuning fence (research pace, budgets).

- **Player-facing name: Admiral.** The console is "Admiral"; "the
  Admiralty" stays available as flavor for the infrastructure/tech side in
  prose and lore.

## 14. Decisions (second pass)

- **Multi-Admiral etiquette: last command wins.** No claim system, no locks -
  the humans at the consoles are a command staff and are expected to talk.
  (If a venue proves this wrong, soft claims remain the later fix.)

- **Captain capture: OU yes, Siege no.** In Siege an MIA captain is just a
  timer (rescue or lose her - keep the mode lean). In the Open Universe a foe
  clan can *claim* the pod: the captain becomes a prisoner, and getting her
  back is content - ransom through the clan's comms (priced by standing, a
  genuine use for the diplomacy/reputation economy) or a rescue raid at the
  clan's station. A captured captain is a better story than a dead one, and
  it gives foe clans something to want.

- **Border defense: `patrol` first.** Fleets are the answer to skirmish
  pressure at launch; the Bastion platform stays in slice 4 as the later,
  static alternative. Consequence for pacing: border skirmishes shouldn't
  turn on until fleets exist (slice 3) - slices 1-2 get economy peace.

- **Sensor model: any side ship feeds the map, via `extra_scan_sources`.**
  The existing mechanism (`link(ship, "extra_scan_source", obj)`) already
  defines "what a ship's sensors are allowed to see beyond itself" - reuse
  that same linkage/pattern to aggregate the Admiral's map: every side ship
  (players included) is a sensor source, plus platform and Sensor Relay
  radii. One mechanism serves science and Admiral consistently, so what the
  crews can scan and what the Admiral can see never contradict each other.

## 15. Decisions (third pass)

- **Code lives in OU for now.** Build the Admiral inside OpenUniverse where
  the friendly-AMD reader, worldlets, and captains already live; assume an
  LM backport later *if it makes sense*. (Practical consequence: Siege gets
  the Admiral only after the backport - OU is the proving ground, which
  also matches "OU is exempt from the code lock" today.)

- **Siege worldlets: one.** A single worldlet near the player station -
  and it can be an all-yields Haven type (CQ's earth-planet pattern: one
  body, all three resources), so the Siege Admiral plays the full economy
  without a map redesign. *(Interpreting "maybe one / I'd be OK if all
  worldlets" as: one body, all yields - correct me if you meant all
  worldlet TYPES may spawn.)*

- **Requisition catalog: include the originals.** The existing LM upgrade
  items are the tier-1 deliverables from day one; Admiral-flavored new
  items come later as research milestones want them.

- **Research branches: Engineering / Ordnance / Logistics / Officers.**
  Strawman milestones for slice 2:

  | Branch | I | II | III |
  |---|---|---|---|
  | **Engineering** | Escort hulls (light escorts commissionable) | Line hulls (line ship + Tender) | Heavy hulls + a player hull-plating upgrade item |
  | **Ordnance** | Munitions contracts (cheaper torpedo restock at stations) | Fleet gunnery (fleet damage bonus) | Special ordnance (a player special-torpedo item) |
  | **Logistics** | Silos & rates (storage caps + extraction rate) | Tenders & supply radius (fleet endurance; unlocks Subsidy) | Rapid requisition (lead times cut; unlocks Procurement) |
  | **Officers** | Academy roster (first captains) | Veteran training (trait bonuses grow with sorties) | Flag staff (+command points, +1 fleet) |

  Note the shape: every branch's milestone I-III includes at least one
  thing a bridge crew receives - the section-1 rule enforced structurally.

- **Fleet hull roster: escort / line ship / tender at launch** - but the
  roster is *data, tuned by difficulty and game length* (a longer OU
  campaign unlocks deeper rosters; higher difficulty may restrict them).
  Roster lives in the AMD, not code, so this costs nothing to honor.

- **Admiral GUI: tabbed, with a 2D view for selection.** Reuse the
  `gui_screen_tabs` pattern (console top tabs / game-results board) for the
  major modes, and embed a 2D view widget so the Admiral clicks worldlets/
  fleets/platforms spatially instead of hunting lists. Slice-1 screen:
  resource ticker (top bar, CQ-style), 2D system view (center), worldlet/
  build panel (side), build queue (bottom).

## 16. Decisions (fourth pass)

- **Fourth research branch: Engineering.** (Table in section 15 updated.)
- **Tabs confirmed: Map / Build / Research / Fleets / Requisition.** ASCII
  mock in section 17.
- **AMD strawman: go.** Drafted as the second appendix - the authored data
  slice 1 loads.
- Siege-worldlet reading (one body, all yields) stands unless corrected.

## 17. Slice-1 GUI mock (the Map tab)

Resource ticker top (CQ's resource bar), tab strip (`gui_screen_tabs`),
2D view center for spatial selection, context panel right (CQ's context
window, reborn), queue bottom. The right panel is *contextual*: it shows
whatever the 2D view selection is - a worldlet offers Build, a fleet offers
orders, a platform offers its queue.

```
+--------------------------------------------------------------------------+
| ORE 1240/2000   GAS 380/1000   CREW 62/80   CMD 3/5          ALERTS (2)  |
+--------------------------------------------------------------------------+
|  [ MAP ]  [ BUILD ]  [ RESEARCH ]  [ FLEETS ]  [ REQUISITION ]           |
+-----------------------------------------------------------+--------------+
|                                                           | SELECTED     |
|                    2D SYSTEM VIEW                         | Cinder World |
|                                                           | (5, -4)      |
|     [HQ]                                                  | Ore 8/min    |
|       \            o Haven World                          | Reserve 3120 |
|        \                                                  |              |
|      F1 >---escort---> PLR Artemis                        | + Extractor  |
|                                                           | + Refinery   |
|              o Cinder World   <-- selected                | + Bastion    |
|                                                           |--------------|
|                     ~ ~ antimatter veil ~ ~               | F1 Mara Dusk |
|                                                           | escort:      |
|              o Veiled Giant   !! foe border               |  PLR Artemis |
|                                                           | gas 2/min    |
+-----------------------------------------------------------+--------------+
| QUEUE: Extractor @ Cinder 0:45 > Escort hull 1:20   [Fabricator: IDLE]   |
+--------------------------------------------------------------------------+
```

Notes: the ticker line and the IDLE indicator are the two CQ UI-QoL mines
from section 2 (resource bar; idle-worker button). ALERTS collects skirmish
warnings and MIA events. The 2D view reuses the console 2D-view widget with
Admiral-only overlays (yields popup, supply radii, border hatching).

## 18. Status: shipped work and open items

The Admiral is **feature-complete against this document.** Everything under
*Shipped* landed on the `admiral_dev` branch (OpenUniverse, with the market
subsidy hook in LegendaryMissions), now merged to `v1.4.0_dev`. Each entry is what
shipped plus its verification/commit; the design rationale for each piece is in
the numbered sections above.

Verification note: 2026-07-01 items were browser-verified as they landed; the
2026-07-02 items are test-verified (in-process suite) + headless PASS; the overseer
(below) is partially browser-verified, with a full browser pass still pending.

### Shipped

**AMD strawman moved into default.amd** - `## Worldlets` + `## Admiralty` live in
default.amd (Officers followed in slice 3).

**Slice 1 - the economy exists** (browser-verified 2026-07-01) - Worldlet
types/tuning parse via the friendly reader (universe_amd.py); worldlets spawn via
the POI deck (authored 30%, home system guaranteed a settled type) and as
`Kind: worldlet` landmarks; side ore/gas/crew pools ride the side agent like
credits; the Admiral console has the ticker, tabs (Map live), worldlet
select/inspect, HQ + Extractor builds with costs/prereqs/build-times, a build
queue line, and the extraction tick. Inert for universes with no Admiralty chapter.

**Slice 2 - the war effort reaches the players** (browser-verified 2026-07-01) -
Refinery (boosts its worldlet 1.5x, +400 storage) + Shipyard (research site);
stockpile caps; the Engineering ladder authored as a `## Research` AMD chapter
(Costs/Time/Requires/Unlocks in plain English), researched one-at-a-time; the
Requisition tab - upgrade items bought with resources and delivered as REAL items
beside the player ships with a comms notice.

**Slice 3 - the navy** (browser-verified 2026-07-01) - the Academy trains the
`## Officers` roster; fleets (2 escorts + 1 line ship) form at the Shipyard for
resources + one command point; the six orders run as a per-fleet tick
(target/target_pos, not brains); every non-hold order burns officer-scaled gas and
dry tanks force hold; salvage strips wrecks; officer trait bonuses derive linearly
from authored Values; acknowledgments reach the crews as comms; CMD is live. UI
pattern settled: every repeating list is a scrollable gui_list_box + a
context/detail panel acting on the selection.

**Consolidation pass** (committed 2ae8540, 2026-07-02) - officer chatter rides
info-panel cards with cached faces; fleets persist (adm_fleets + fleets_respawn on
every arrival - the navy travels with the flag); per-system worldlet depletion +
platforms snapshot into the sectors delta and re-apply on arrival; baseline save at
map start; pool seeding retried until the side agent exists.

**Slice 4 - the frontier** (f1ea629, 2026-07-02) - **Bastion** (per-worldlet armed
fort; skirmish raids prefer it); **border skirmishes** (pressure = foe-owned cells
in the Chebyshev ring; raids once the first fleet exists; `Skirmish pressure: off`
disables); **MIA captains** (a destroyed fleet drops its officer in a pod; a player
ship within 1500 rescues before `MIA timer:` lapses; fates persist); **antimatter
veil** (a `Kind: antimatter` region is survivable only briefly - continuous heat +
system_damage, tinted nebula, amber chart wash); **Relay Gate** (a gated system
feeds income at `Relay rate:` while the flag is elsewhere; remote depletion
simulated).

**Captain capture + ransom; HQ campaign uniqueness** (f6c1e3f, 2026-07-02) - a
lapsed MIA pod is claimed by a hostile foe clan; the officer becomes their prisoner
(ransom priced by standing at a captor station, or break them out by
destroying/capturing a captor station). The HQ is campaign-unique;
Shipyard/Academy/Relay stay per-system.

**Officer voices** (a02ab16, 2026-07-02) - an officer with a `Scene:` rides their
flag hull as a hailable cast character (lifeform + //comms/universe_cast); select
the flag, hail the officer, and their voice is a dialogue scene. The lifeform
follows the lead hull (dead flag -> next ship) and parks while
podside/captured/between fleets; their Values are the leans, so crews build
personal reputation with the captains they fly with.

**Authorable fleet chatter** (eed4545, 2026-07-02) - fleet event lines (order acks,
gas/salvage blips, pod-away/rescue/capture/lost) are built-in pools with a random
pick and {ore}/{gas}/{rescuer}/{officer}/{clan} fields; a `## Fleet Chatter` AMD
section overrides any pool; zero authoring keeps the defaults.

**NPC veil avoidance** (d8ca036, 2026-07-02) - the navy will not operate inside an
antimatter veil; fleet_tick forces any active fleet to hold and warns once. Same
commit fixed a QuestState-in-MAST-eval engine error (compare quest state against
the int 0).

**Subsidy - the resources-to-prices bridge** (LM f219a11 + OU ac6d00f, 2026-07-02)
- bridge #2 from section 7: one number `market_subsidy` on the side agent that LM
`items.market_price` reads (backward-compatible ship_id param discounts the buyer
side's price); the Requisition tab cycles the tier (0/10/20/30%). Every econ tick
pays the rate's upkeep; a dry pool suspends it (the anti-snowball rail). The LM
change is generic.

**Lab - concurrent research** (2026-07-02) - research is a list; the side researches
up to `research_slots(side)` = 1 + each Lab at once. Each Lab (per-worldlet,
stackable) adds a slot; legacy single-key saves coerce to a list.

**Sensor Relay - command-point expansion** (2026-07-02) - each Sensor Relay
(per-worldlet, stackable) adds SENSOR_COMMAND_POINTS to the fleet cap via
`admiralty_command_points(side)`; both the ticker and the fleet-form cap read it.

**Fog of war - Sensor Relay reveal** (2026-07-02) - finishing a Sensor Relay marks
its system + the 8 neighbours 'sensed' in the sectors delta persistently; the
galaxy map + nav panel treat a cell as known if visited OR sensed OR Full Chart
(universe_cell_known). Carried gap: in-system reveal + a visual sensed-vs-visited
mark.

**Officer veterancy** (2026-07-02) - an officer on an active order accrues service
each fleet_tick; every VETERAN_STEP is a level (capped) that adds VETERAN_BUMP to
the Values they were built for and ONLY those. Persists and survives MIA/capture in
place, so a lost veteran stings.

**Depot - fleet supply anchor** (2026-07-02) - a fleet on an active order within a
Depot's radius (DEPOT_SUPPLY_RADIUS) burns no gas; extends patrol range on the
frontier. Per-worldlet build; persists like the others.

**Relay Gate remote depletion** (2026-07-02) - the econ tick snapshots a
per-worldlet relay plan into the sectors delta; admiralty_relay_tick draws that
income against the SAME worldlet_reserves arrival re-applies - a gated finite
worldlet really drains, unlimited (Haven) ones pay on.

**Build menu = scrollable listbox** (browser-verified 2026-07-02) - the Map build
panel is a scrollable gui_list_box of buildable platforms
(`admiralty_buildable_items`) + a Build button; only prereq-met platforms list
(`admiralty_buildable_kinds`), so it unlocks as you build. Validation split into a
check-only `admiralty_can_build` shared by the list and the action.

**Fabricator - build model B** (2026-07-02) - behind `Build model:` (menu default,
fabricator = B): one slow unarmed Fabricator ship physically flies to each queued
worldlet and builds it (universe_fabricator.py); death penalty is TIME not
resources (the queue survives on adm_fab_queue). Placeholder hull (ART_WANTED).

**Terrain no longer proximity-culls in a system** (a614293, 2026-07-02) - terrain
stays loaded for the whole visit (no network pop in/out), torn down only on a jump.
Brained raider fleets still cull as a formation park.

**Overseer console - detached 2D command surface** (23812c8 step 1; 0ea2146 +
70f8ef8 step 2; 2026-07-02; step 1 + build/order/pan browser-verified) - the
signature UI shift (section 17 realized as a live command surface). Now the only
Admiral UI - the old tabbed `bridge` console and the `Admiral view:` A/B knob were
retired (2026-07-04) once the overseer reached economy parity (build, fleet orders,
research, requisition, subsidy). The Admiral rides a private
detached camera over the system (GM cambot pattern) with a comms 2D view and
**commands by selecting objects**: click a worldlet to build, a fleet hull to order
(the six orders), a platform for its actions - **Shipyard** to commission an
officer, **Lab** to research, **HQ** to cycle subsidy. Click empty space to pan,
an object to recenter; a radar zoom control. Supporting work: the building side is
threaded from the selecting Admiral (`COMMS_ORIGIN.side` -> BUILD_SIDE), not
hard-coded (multi-side groundwork); a side-wide theatre scan
(`admiralty_scan_theatre`) so comms enables on the side's own worldlets/platforms/
fleets; platforms stripped of the engine-derived `station` role so only the Admiral
menus show; a live resource ticker + a build-queue/action status panel (no info
panel on this console) + a "no extractors yet" income hint; in-place comms refresh
on build start/complete (`comms_navigate_override`); start-ore raised 200->300 (the
HQ+Extractor soft-lock); nebula dialed down for transmit cost; the console named
`gamemaster_overseer_comms` for the engine's optimized detached-console network.
Player + author docs shipped (mkdocs `playing/admiral.md` + `writing/admiralty.md`).

### Open

1. Confirm/correct the Siege-worldlet reading (section 15).
2. Full browser pass of the 2026-07-02 features and the overseer economy loop
   (commission a fleet -> order it; research at a Lab). Most are test-verified
   (in-process) + headless PASS; build/order/pan are browser-verified.
3. **Multi-side:** the server economy loops still assume `"tsn"` as the player
   side; the overseer build path is the reference for deriving side from context.
   Generalize when rival/co-op Admirals on different sides become real.
4. Carried polish (non-blocking):
   - **Build queue LIST** (playtest 2026-07-04). DONE off-engine (7d5d19f): `ADM_BUILDS`
     entries are now records (`admiralty_build_record`: name + worldlet + eta);
     `admiralty_build_queue_text` shows "Building N: name - where (Ns), ..." with each
     build's time remaining, and `admiralty_status_change_key` ticks the countdown
     live each second (idle = no repaint). REMAINING (wants an eye on the render):
     swap the status `gui_text` for a `gui_list_box`/`gui_text_area` so many builds
     stack as real rows instead of one line, and fold in the Fabricator queue
     (`fabricator_queue`) as a second source.
   - NPC veil *pathing* - fleets route around a veil vs today's refuse-and-hold
     (marginal: the veil is whole-system, so refuse-and-hold is arguably correct).
   - Event dialogue *scenes* - richer than the authorable canned chatter pools.
   - Distinct Admiral-platform art (see `ART_WANTED.md`).

---

## 19. Back to Conquest - divergence audit and the way to the expand loop

Section 18 calls the Admiral "feature-complete against this document" - and it is.
But the document it's complete against describes a **contested-frontier brawl**:
extract at home, hold one frontier, defend against border raids, field a small navy,
go crack the enemy HQ. Conquest: Frontier Wars - the "CQ" this whole design ports -
is a bigger thing: a **reveal -> contest -> secure -> build -> hold -> repeat**
expansion loop. The pieces we built are faithful CQ *features*; what we haven't built
is the CQ *loop*. This section is the honest audit and the sequenced way back.
(Prompted by playtest: the economy felt glacial and the loop didn't "go anywhere" -
the tuning + admiral self-jump fixes shipped alongside this were the first response.)

### Where we stayed faithful to CQ (keep)

Solid ports, unchanged: **ore / gas / crew** and **Command Points** (CQ minerals/gas/
crew + admiral command capacity; CP stays the fleet cap); **worldlet types +
depletion** and the planet-popup read; **captains-as-officers** with trait bonuses +
veterancy; the **six fleet orders**; **Bastion / Relay Gate / Depot / Sensor Relay /
Lab**; the **subsidy** resources->prices bridge; **fog + Sensor reveal**. All mined
per section 2, all shipped.

### Where we forked or fell short of the CQ *loop* (the gap)

Not the individual features - the loop between them:

1. **Expansion is capped, so you can't settle.** The HQ is campaign-unique; the
   Shipyard/Academy are single-instance (the code gates non-per-worldlet platforms
   side-wide - section 18 describes them as per-system, a discrepancy worth
   reconciling). Either way you can extend Extractors outward but can't root a
   *self-sustaining base* in a new system. Expansion is tenant-mining, not settling -
   the loop caps out after your second system instead of repeating.
2. **Fleets don't claim ground.** They're purely military (patrol/strike/defense,
   CP-capped). A worldlet is claimed by *building* on it (needs your flag present),
   not *secured* by a fleet - so "send the fleet out to take the next system" isn't a
   verb.
3. **The Fabricator exists but off to the side.** Section 2 mined it; section 18
   shipped it as build-model *B* (an optional slow builder ship). But the default is
   menu-build, and the CQ-defining verb - convoy a builder to the frontier and found a
   base - is neither the default nor wired into an expand loop.
4. **No economic AI opponent.** Clans are scripted raiders; they harass but don't run
   an economy or expand. The "others doing the same" half of the loop is PvP-only.
5. **Held-but-unattended territory doesn't produce.** The multi-cell model keeps only
   *occupied* cells live; an empty system despawns and freezes into its sectors delta.
   A captured system you aren't sitting in earns nothing (the offline-economy revisit).

### The way back - decided principles

From the realignment discussion (user-confirmed where noted):

- **CQ is the north star** - already the stated reference; finish the port, don't
  change games.
- **One Capital, many colonies (CONFIRMED).** Keep the HQ as a single campaign-unique
  Capital (losing it loses you). Expansion is *controlling worldlets*, NOT replicating
  HQs - so the singleton stops being a wall and becomes the thing you defend. Dissolves
  the "can't settle" fork with no new capital structures.
- **The worldlet IS the build site; DROP the Fabricator (user's call).** Simpler than a
  mobile builder and one less unit to micro. Retire build-model B (or keep it dark) in
  favour of build-on-the-controlled-worldlet.
- **The fleet establishes control.** A fleet *secures* a worldlet (clears hostiles +
  holds); control unlocks building there; an Extractor + **Bastion** make it stick after
  the fleet moves on. Gives fleets an economic purpose and makes the worldlet the atomic
  unit you fight over. This is the missing verb - it replaces the Fabricator run.
- **Anti-snowball is positional overextension, layered on Command Points.** You can only
  secure what your fleets can clear and hold only what your navy + Bastions can defend;
  spread too thin and the frontier picks you apart. CP caps the navy; overextension is
  its territorial twin. Lean on organic limits, not more price walls / hard caps.

### Open decisions to lock (recommendation in bold)

- **#4 Which artificial rails to retire?** The singleton HQ *stays* (it's the Capital),
  CP *stays*. **Recommend** relaxing the storage cap and letting the Shipyard/Academy
  limits follow "control, not replication" as needed; lean on overextension for the
  snowball. Decide per-rail during Phase C.
- **#5 What grants "control"? DECIDED - clear-and-build, fleet-anchored** (per-system;
  control is binary + structure-based). Claim an uncontrolled system: clear any
  contesting hostiles, then build an anchor with your fleet PRESENT for the whole build
  (the fleet is pinned/vulnerable while it goes up - the CQ Fabricator tension without a
  Fabricator; leaving or dying mid-build aborts). Empty systems have nothing to clear, so
  you just build an anchor - fly-through space with no structure is NOT held. Light anchor
  = REUSE the Relay Gate (waypoint / supply / reveal); heavy = Bastion or forward
  starbase. Once controlled, build freely (the gate applies only to the first, claiming
  structure). Abort refund = PERCENT-COMPLETE (refund the unbuilt fraction via `build_left`;
  the built portion is sunk). A RAZED structure DROPS SALVAGE (reuse the derelict/salvage
  system) so taking enemy territory is rewarding. Revert to contested when a foe destroys
  your anchors.
- **#6 Do fleets reveal the fog? Recommend yes** - a fleet lifts fog as it flies, so
  "build fleets to explore" is literally true (today only the static Sensor Relay
  reveals; keep it as the *persistent* reveal).
- **#7 PvE economic AI admiral? Recommend PvP-first** - prove the loop with two human
  admirals (Skirmish already does this); an AI admiral that builds + expands is a later
  phase.

### Phased roadmap (each phase playable + verified in-engine before the next)

- **Phase A - Economy legibility (mostly done).** Playtest speed knob + self-jump fix
  landed so the loop is watchable. OWED: replace `_PLAYTEST_SPEED` with a real tuned
  curve (fast-but-balanced), remove the debug pace tag. *Deliverable: a Skirmish economy
  that ramps in minutes, not an hour.*
- **Phase B - The control verb.** Fleet-secures-worldlet (#5) as the gate to building in
  a not-yet-yours system; Bastion = the hold; reversion on raid. Drop the Fabricator
  default. *Deliverable: reveal -> secure -> build -> hold works for one forward system.*
- **Phase C - Repeat + overextension.** Fleets reveal fog (#6); relax the rails that
  block a second/third forward base (#4); tune so holding more frontier genuinely strains
  the navy. *Deliverable: the rinse-and-repeat expand loop; an admiral can chain 3-4
  systems.*
- **Phase D - Held-territory economy.** Resolve the offline-economy revisit: unattended
  held systems keep producing (keep select cells live, or a timestamped catch-up on the
  delta at re-entry). *Deliverable: territory is worth holding even when you leave.*
- **Phase E - The opponent.** A PvE economic AI admiral (#7) that runs the same loop back
  at you. *Deliverable: single-player CQ, not just PvP.*

### Deploy UX - the galaxy theater + popup command model (proposed, spike first)

The fleet-deploy verb (Phase B/C) needs a way to point a fleet at a system the admiral
isn't in. Direction: build the galaxy map as a 2D-VIEW "theater" of real selectable
marker objects placed in the DEAD SPACE far from the play slots (~+50M, where float
precision is fine because the markers never move and the camera parks among them),
viewed through the engine 2D view - so the engine's right-click / long-hold popup
(//popup, the LM friendly_give_orders pattern) works on systems directly.

- **Markers = real objects, so the MESH is the icon:** kind -> mesh, owner/control ->
  data_set color, importance/strength -> scale (+ name_tag). Three channels = a board
  that reads at a glance. Fog/unscanned uses the `unknown` shipData art (same art the
  empty-system marker uses). Spawn every marker (and the fleet icons) as TERRAIN
  (passive tick_type via terrain_spawn), NOT npc_spawn - the whole board then stays OUT
  of the engine's active sim calcs (passive is ~free, perf_probe: 100k flat; active
  ships have a ~190 ceiling), and terrain is still selectable on the 2D view (the
  empty-system marker already proves a terrain object scans + selects). Terrain isn't
  proximity-culled either, so the board stays loaded for the whole session. Windowed + virtual-scrolled (~15x15 pool relabels on pan;
  the galaxy is infinite so we never spawn all of it); reuses every per-cell
  kind/owner/fog computation + control state; fleets show as side-colored ship icons at
  their current systems. Icon->mesh mapping is a small table (later AMD-authorable, a
  `## Galaxy Icons` chapter, per the declarative preference).
- **Regions as nav-areas:** draw each named region (Ashen Reach, Verdant Belt, the
  antimatter veil) as a `sim.add_navarea` quad in theater space, colored by
  `region_map_color` (veil = amber), so the geographic backdrop is a real SHADED ZONE on
  the 2D view - the layered strategic-map look (region territories underneath, mesh
  system/fleet icons on top), reusing the existing region logic verbatim
  (region_for_system / region_map_color / region_is_veiled). Nav-areas are navpoints, so
  a region could even carry its own popup later.
- **Command grammar:** left-click SELECTS, right-click (popup) COMMANDS. So "select
  fleet, right-click system X, Send fleet here" is ONE gesture, feeding
  `fleet_deploy`/`universe_admiral_jump`. Crucially the popup carries BOTH the selected
  object AND the clicked target (COMMS_SELECTED + COMMS_POPUP/_POINT) - the "do X to Y"
  grammar single-selection //comms can't express. This is the real reason to move to
  popups, not just consistency.
- **ONE COMMON map, per-console popups.** The player Navigation console and the Admiral
  already SHARE one galaxy map (`universe_galaxy_map_gui` today); keep that - the theater
  REPLACES the shared grid for BOTH, it is not an admiral-only surface. The `//popup`
  routes gate on the origin's role, so the SAME markers offer the Admiral its commands
  (jump / send fleet / build) and the player Nav its own (set course / jump) with zero
  duplication. Common rendering, divergent commands.
- **DECIDED (reversed 2026-07-06): KEEP the admiral's system-view commands on //comms +
  the comms_control widget; do NOT migrate them to //popup.** Reason: the comms button
  panel SCROLLS when there are many buttons (buildable platforms, "Send fleet here" per
  fleet, fleet orders); the hold-menu popup has limited space and no scroll. So popups
  are for the theater MAP gesture (right-click a marker/empty space), and //comms stays
  the surface for command LISTS. (Watch: a very long theater fleet list could overflow
  the hold menu - route that one through comms if it bites.)
- **Spike FIRST** - two engine unknowns the headless mock can't answer: do
  far-coordinate static markers render + select on the 2D view, and does the popup fire
  on them? Prove with a theater camera + a few mesh markers + one //popup route in the
  browser before committing to the full theater.

Guiding constraint throughout: **every step must still touch the bridge game**
(section 1) - securing, holding, and losing systems should be things the crews feel,
not a solitaire RTS in the corner.

---

## Appendix - AMD strawman (slice-1 authored data)

Drops into `default.amd` (or an `admiralty.amd` spliced via `File:`). Same
friendly fact-sheet rules as every other chapter; all numbers provisional.

```
## Worldlets

The resource bodies of this galaxy. Each type names what it yields per
minute per extractor, how much it holds before running dry, and its look
(the behav_planet surface palette). Placement: procedural via the POI deck
(Worldlet chance dial), or hand-placed as a Landmark with Kind: worldlet.

### Cinder World (cinder)
---
Yields: ore 8
Reserve: 4000
Palette: #8c2f1c, emissive #48180c, clouds #776655
---
A cracked, mineral-rich ember of a world. Miners love it; nobody else does.

### Veiled Giant (veiled_giant)
---
Yields: gas 10
Reserve: 6000
Palette: #2c4a8c, clouds #b8c4e0, bands 3.7
---
A banded gas giant, its high winds rich in fuel-grade volatiles.

### Haven World (haven)
---
Yields: crew 2, ore 2, gas 2
Reserve: unlimited
Palette: #2f6e3a, clouds #ffffff
---
A small settled world. People, modest industry, and somewhere to come from.

## Officers

The Academy roster - named fleet captains for the player side. Values use
the reputation poles and drive each officer's fleet bonuses (fearsome ->
damage, by-the-book -> supply, resourceful -> salvage/evasion...). Their
voice is a dialogue scene (Speaker = the officer key).

### Commodore Ansel Vale (vale)
---
Title: the Quartermaster
Values: by-the-book 40, honest 30, kind 10
Face: male
Scene: vale_hail
---
Ran the academy's logistics course for a decade and the lanes know it.
Fleets under Vale come home fueled, patched, and on schedule.

### Captain Iris Kade (kade)
---
Title: Old Thunder
Values: fearsome 40, violent 20, generous 10
Face: female
Scene: kade_hail
---
Leads from the front and shoots first. Kade's fleets hit harder and
scare easier prey off the board before a shot is fired.

### Captain Juno Ashwell (ashwell)
---
Title: the Magpie
Values: resourceful 40, intellectual 20, selfish 10
Face: female
Scene: ashwell_hail
---
Never met a wreck she could not strip or a sensor shadow she could not
slip through. Ashwell's fleets salvage more and die less.

## Admiralty
---
// Research pacing: siege (capped ladder, minutes-scale costs) or
// campaign (full ladder, save-persisted, generational costs).
Research pace: campaign
Requisition budget: 800 credits
Skirmish pressure: border
Worldlet chance: 30%
Command points: 3
Command per relay: 1
Fleet gas burn: 2
---
The war effort behind the player fleet - dials for the Admiral console.
```

Open AMD questions the strawman surfaces: does `Palette:` carry the whole
behav_planet knob set or a named preset list; do officer bonuses need an
explicit `Grants:` line or stay derived from Values (derived preferred -
one less thing to author); is `## Admiralty` per-universe or can Siege's
settings.yaml override it (both, probably: AMD authors, settings tunes).

## Appendix - worldlet surface knobs (engine `behav_planet` data_set)

Radius cannot get larger than 3000.

```python
co.data_set.set("planet_radius", co.engine_object.exclusion_radius/2.0, 0)
co.data_set.set("planet_baseColorR", 0.55)
co.data_set.set("planet_baseColorG", 0.16)
co.data_set.set("planet_baseColorB", 0.28)
co.data_set.set("planet_emissiveColorR", 0.48)
co.data_set.set("planet_emissiveColorG", 0.24)
co.data_set.set("planet_emissiveColorB", 0.16)
co.data_set.set("planet_upperCloudColorR", 1.19)
co.data_set.set("planet_upperCloudColorG", 1.18)
co.data_set.set("planet_upperCloudColorB", 1.2)
co.data_set.set("planet_fresnel", 11.96)
co.data_set.set("planet_fresnelBias", 0.42)
co.data_set.set("planet_bandScale", 3.72, 0)
co.data_set.set("planet_windSpeed1", 1000)
co.data_set.set("planet_windSpeed2", 1000)
co.data_set.set("planet_upperCloudStrength", 3.12)
co.data_set.set("planet_upperCloudExponent", 3.96)
```

## Appendix - CQ nebula catalog (phase-2 terrain ideas)

Mined for later; each is a cheap data_set/damage-channel effect:

| CQ nebula | Effect | Cosmos translation |
|---|---|---|
| Helios | attacks inside do extra damage | damage multiplier zone - duels *in* it are deadly |
| Lithium | slows ships, harvestable gas | speed clamp + gas yield |
| Hyades | rich gas but damage over time | risk/reward mining zone |
| Celsius | locks supplies/special weapons | torpedo/consumable lockout zone |
| Cygnus | speeds ships up | highway - route fights around it |
| Ion | disables shields | shields-off knife-fight zone |
