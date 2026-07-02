# Admiral Console - Completed Work

Shipped Admiral-console work, moved out of `ADMIRAL_CONSOLE.md` section 18 to
keep the design doc's action list short. Each entry is what shipped plus its
verification/commit. Everything here is on the `admiral_dev` branch (OpenUniverse,
with the market subsidy hook in LegendaryMissions). Design rationale for each
piece still lives in the numbered sections of `ADMIRAL_CONSOLE.md`.

Verification note: items dated 2026-07-01 were browser-verified as they landed;
the 2026-07-02 items are test-verified (in-process suite) + headless PASS, with a
full browser pass still pending (see the open list in the design doc).

---

## AMD strawman moved into default.amd
`## Worldlets` + `## Admiralty` live in default.amd (Officers followed in slice 3).

## Slice 1 - the economy exists (browser-verified 2026-07-01)
Worldlet types/tuning parse via the friendly reader (universe_amd.py); worldlets
spawn via the POI deck (authored 30%, home system guaranteed a settled type) and
as `Kind: worldlet` landmarks (universe_worldlets.py + universe_systems.py); side
ore/gas/crew pools ride the side agent like credits; the Admiral console
(admiral.mast) has the ticker, the five tabs (Map live), worldlet select/inspect,
HQ + Extractor builds with costs/prereqs/build-times, a build queue line, and the
extraction tick feeding the ticker. Inert for universes with no Admiralty chapter
(Silver Reach unchanged).

## Slice 2 - the war effort reaches the players (browser-verified 2026-07-01)
Refinery (boosts its worldlet 1.5x, +400 storage) + Shipyard (the research site);
stockpile caps (Storage tuning + refineries + research); the Engineering ladder
authored as a `## Research` AMD chapter (Costs/Time/Requires/Unlocks in plain
English - storage N / extraction N% / requisition <item>), researched
one-at-a-time at a Shipyard, persisted with effects derived from the completed
set; the Requisition tab - three classic upgrade items (+ two research-unlocked)
bought with resources and delivered as REAL items beside the player ships with a
comms notice. GUI style rule learned: $text first, justify:left never.

## Slice 3 - the navy (browser-verified 2026-07-01)
The Academy trains the `## Officers` AMD roster (Vale / Kade / Ashwell); fleets
(2 escorts + 1 line ship) form at the Shipyard for resources + one command point;
the six orders run as a per-fleet tick using target/target_pos primitives
(deliberately not brains - self-contained); every non-hold order burns gas
(officer-scaled) and dry tanks force hold; salvage strips wrecks into the
stockpiles; officer trait bonuses derive linearly from the authored Values
(by-the-book 40 -> gas x0.8, resourceful 40 -> salvage x1.5, fearsome 40 ->
engage x1.4) - writers tune officers by writing character; officer
acknowledgments reach the crews as comms; CMD in the ticker is live. UI pattern
settled (user): every repeating list is a scrollable gui_list_box + a
context/detail panel acting on the selection - Map, Research, Fleets, Requisition
all use it.

## Consolidation pass (browser-verified + committed 2ae8540, 2026-07-02)
Officer chatter rides info-panel cards with cached faces (comms_info_card);
fleets persist (adm_fleets side inventory + fleets_respawn on every
arrival/Continue - the navy travels with the flag); per-system worldlet depletion
+ platforms snapshot into the sectors delta each econ tick and re-apply on
arrival; baseline save at map start; pool seeding retried until the side agent
exists.

## Slice 4 - the frontier (f1ea629, 2026-07-02; browser check pending)
- **Bastion** - per-worldlet armed fort (1.5x scale for legibility); skirmish
  raids prefer it, so the fight happens at the fort.
- **Border skirmishes** (universe_skirmish.py) - pressure = foe-owned cells in
  the Chebyshev ring (2 for the cell itself); raids on the side's platforms once
  the FIRST fleet exists (economy peace before that); countdown runs faster under
  pressure; `Skirmish pressure: off` disables; negotiated ceasefire lifts the
  pressure. Alert is an Admiralty Operations info card.
- **MIA captains** - a destroyed fleet drops its officer in an escape pod at the
  loss site; a player ship within 1500 rescues them before the `MIA timer:`
  lapses, else they are lost. Fates persist (adm_officers). Roster shows
  MISSING/lost; MIA officers can't take fleets.
- **Antimatter veil** - a region with `Kind: antimatter` is survivable only
  briefly: continuous system_cur_heat + system_damage across all engineering
  systems (region_veil_tick); tinted red nebula volume on arrival; hard amber
  wash on the chart (shown unexplored) + a nav-panel warning. Optional `Heat:` /
  `Damage:` per-second overrides. default.amd ships one at (0,7) r1.
- **Relay Gate** - one per system; a gated system feeds income into the pools at
  `Relay rate:` while the flag is elsewhere. Remote depletion IS simulated (see
  below): the relay draws against the system's stored worldlet reserves, so a
  gated finite worldlet runs dry and unlimited ones pay on.

## Captain capture + ransom; HQ campaign uniqueness (f6c1e3f, 2026-07-02; browser check pending)
A lapsed MIA pod is claimed by a currently hostile foe clan (ceasefire respected;
no foe clans -> lost as before). The officer becomes their PRISONER (persisted
with the captor): buy them back at any captor-clan station - ransom priced by
standing (clan_ransom_cost: base 400 + 15/pt below the ceasefire line, so friends
sell cheap) - or break them out by destroying OR capturing a captor-clan station
(both hooks free every prisoner the clan holds). Roster shows PRISONER; prisoners
can't take fleets. The HQ is now campaign-unique (admiralty_try_build checks the
sectors delta, names the system that has it); Shipyard/Academy/Relay stay
per-system by design.

## Officer voices (a02ab16, 2026-07-02; browser check pending)
An officer with an authored `Scene:` rides their flag hull as a hailable cast
character - the same lifeform + //comms/universe_cast substrate as passengers /
comms NPCs; select the flag, hail the officer, and their voice is a dialogue
scene (dialogue/officers.amd: Vale/Kade/Ashwell each have one). The lifeform
follows the lead hull (CQ's bail mechanic: dead flag -> officer answers from the
next ship) and parks - unhailable, not beamable - while podside/captured/between
fleets. dialogue_speaker resolves officer keys (officer_speaker; their Values are
the leans, so crews build PERSONAL reputation with the captains they fly with).
Same commit fixed a create_sides ->END engine error.

## Authorable fleet chatter (eed4545, 2026-07-02; browser check pending)
The fleet's event lines - order acks, gas/salvage/no-target blips,
pod-away/rescue/capture/lost - are no longer hardcoded. Built-in pools (fleet_line
+ _FLEET_LINES_DEFAULT in universe_fleets) with a per-event random pick and
{ore}/{gas}/{rescuer}/{officer}/{clan} fields; a `## Fleet Chatter` AMD section
overrides any pool (### <key> body lines = the pool), zero authoring keeps the
defaults. default.amd ships a small example (strike ack, salvage haul, rescue).

## NPC veil avoidance (d8ca036, 2026-07-02; browser check pending)
The navy will not operate inside an antimatter veil - a whole veiled system is
lethal, so fleet_tick(fleet, dt, veiled) forces any active fleet to hold and
warns once (veil_warn chatter), reset on leaving or a new order. The Admiral must
clear a lane or jump the flag out; lingering feeds the MIA/capture loop.
admiral.mast passes region_is_veiled. Same commit fixed a QuestState-in-MAST-eval
engine error (compare quest state against the int 0, not QuestState.IDLE).

## Subsidy - the resources-to-prices bridge (LM f219a11 + OU ac6d00f, 2026-07-02; browser check pending)
Bridge #2 from section 7 - the Admiral spends stockpiles to discount station
prices for the crews. One number, `market_subsidy` (0..subsidy_max) on the side
agent: LM items.market_price reads it (a backward-compatible ship_id param
discounts the buyer side's price - shown, checked, and charged coherently in
item_market.mast), and the Admiral console's Requisition tab cycles the tier
(0/10/20/30%). Every econ tick pays the rate's resource upkeep
(SUBSIDY_UPKEEP_PER_MIN, scaled by rate); a dry pool suspends it - the
anti-snowball rail (upkeep competes with fleets/builds/research; discount capped;
sells never subsidised). Persists in side_admiralty. Closes the Admiral bridge
set; the LM items.py change is generic (any mission can set a side subsidy).

## Lab - concurrent research (2026-07-02; browser check pending)
Phase-2 platform. Research was single-slot (adm_researching held one key). It is
now a list, and the side researches up to `research_slots(side)` = 1 + each Lab
milestones at once - so tech advances in parallel through infrastructure. Each
Lab (per-worldlet, stackable) adds a slot. research_try_start gates on the slot
count (was "already researching X"); research_complete frees a slot; research_
state reads the list. Legacy single-key saves coerce to a list (in-progress
research is session-only anyway; only the done set persists). The Research tab
shows "Research slots: used/total". Slots into the dynamic build menu with no UI.

## Overseer console - detached 2D command view, STEP 1 (2026-07-02; PROTOTYPE, browser check needed)
Direction: turn the Admiral from a tab+list console into an RTS command surface -
a detached overseer (GM cambot pattern) with a system-wide 2D view where you
select objects for popup actions + comms. The engine/LM already anticipate it:
the give-orders //popup/comms routes guard on `admiral` role, and the console
dispatcher has admiral+2dview handling. Behind an A/B knob `Admiral view:`
(bridge = the tab console, default; overseer = this). STEP 1 (shell only): the
overseer console spawns a private camera per client (player_spawn invisible +
has_science_scan, __player__ stripped, all friendlies linked as
extra_scan_source, big scan range), assigns the client to it, and lays a
full-system science_2d_view + the resource ticker. NOT YET: object-select popups
(worldlet->build, fleet->orders), comms, the economy panels alongside. Verified
no-crash headless/exercise; the RENDER (does the detached 2D view show the system
in the browser?) needs user eyes before step 2. Also fixed the vestigial Build
tab -> renamed to a System tab holding gui_layout_widget("2dview") for the bridge
console (browser-verified separately: "looks great").

## Fabricator - build model B, A/B toggle (2026-07-02; browser A/B pending)
An A/B alternative to instant menu building (design section 5), behind the
Admiralty `Build model:` knob (menu = default, fabricator = B). universe_
fabricator.py: one slow unarmed Fabricator ship per side physically flies to
each queued worldlet and constructs it - serial, travel takes time, the ship is
a target. Auto-queue (not a micro chore): the Admiral queues builds
(fabricator_enqueue, cost paid up front), the driver loop (fabricator_tick, 2s)
flies + builds through them. Death penalty is TIME, not resources: the queue
lives on adm_fab_queue and survives the ship, so a lost Fabricator relaunches
from the yards after FAB_RESPAWN_DELAY and resumes the (restarted) job; a jump
that clears the system drops jobs whose worldlet is gone, like a menu build.
admiral_build branches on the model; the Map bottom bar shows the FABRICATOR
queue. Placeholder hull tsn_light_cruiser (ART_WANTED). Purpose: playtest A/B -
does menu building feel too spreadsheet-y vs. build-by-vulnerable-ship? Flip the
AMD knob to compare. Carried: multiple fabricators, per-cell safe/vulnerable
routing, resource-loss-on-death variant.

## Fog of war - Sensor Relay reveal (2026-07-02; browser check pending)
The Sensor Relay's second CQ role (it already did command points). Finishing a
Sensor Relay marks its system + the 8 neighbours 'sensed' in the sectors delta
(universe_reveal_neighbors), persistently. The galaxy map + the nav info panel
now treat a cell as known if it's visited OR sensed OR Full Chart
(universe_cell_known, one helper wired into the cell text, the cell background,
and sel_known) - so a sensor network reveals nearby systems' contents (kind,
owner) without a visit. Build sensors along the frontier to grow the strategic
map. Persisted (universe_save on build). This is the galaxy-scale intel slice of
the fog-of-war decision; a full sensor-coverage / in-system reveal remains a
carried gap, as does a visual mark distinguishing sensed intel from a real visit.

## Officer veterancy (2026-07-02; browser check pending)
"Captains the crews fly with get better" (design section 6). An officer
commanding a fleet on an active (non-hold) order accrues service time each
fleet_tick; every VETERAN_STEP seconds is a veteran level (capped at
VETERAN_MAX_LEVEL). Each level adds VETERAN_BUMP to the Values they were built
for - and ONLY those (officer_effective_lean grows an authored pole, never
grants a new one), so a fearsome captain grows more fearsome (engage range), a
resourceful one salvages richer, a by-the-book one burns less gas. officer_bonus
reads the grown leans. Veterancy persists (vet field in adm_officers) and
survives MIA/capture in place, so a lost veteran genuinely stings - it raises
the stakes of the MIA/rescue loop. Roster shows "[Vet N]".

## Sensor Relay - command-point expansion (2026-07-02; browser check pending)
Phase-2 platform: the navy grows through infrastructure. Each Sensor Relay
(per-worldlet, so they stack across a system) adds SENSOR_COMMAND_POINTS to the
side's fleet cap via `admiralty_command_points(side)` = base tuning + relay
count, which both the ticker and the fleet-form cap check now read. Build Sensor
Relays to field more fleets. Slots into the dynamic build menu with zero UI work.
Carried gap: fog-of-war coverage (the CQ Sensor Tower's other role) is not
implemented - this is the command-point half only.

## Build menu = scrollable listbox of buildable platforms (2026-07-02; BROWSER-VERIFIED)
The Map-tab build panel was a stack of platform buttons (8+), which overflowed /
went wonky at small screen sizes. It is now the settled UI pattern: a scrollable
`gui_list_box` of buildable platforms (`admiralty_buildable_items`) + a "Build
[name]" action button for the selection. Only prereq-met platforms are listed
(`admiralty_buildable_kinds`), so the list unlocks as you build (HQ first, then
the rest) and stays short. Selecting a worldlet resets the build selection. This
also dropped the per-button `data={"bk":...}` loop injection - the build now
flows select->BUILD_SEL->one button, no loop-variable capture.

Refactor for one source of truth: the validation half of `admiralty_try_build`
moved to a check-only `admiralty_can_build` (need_cost toggles affordability);
`admiralty_can_afford` split out of `admiralty_spend`. Shared by the list and the
build action. Verified with the --exercise pass (two listboxes on the Map tab
drive clean) and browser-confirmed (user, 2026-07-02 - "looks great").

## Depot - fleet supply anchor (2026-07-02; browser check pending)
Phase-2 platform closing the gas-starvation gap: a fleet on any active order
within a Depot's supply radius (DEPOT_SUPPLY_RADIUS, universe_worldlets) burns no
gas - it's resupplied locally (admiralty_in_supply, checked in fleet_tick against
the lead hull). Place Depots to extend patrol range on the frontier without
draining the central stockpile; pairs with the Bastion (defend + sustain). A
per-worldlet build (ADM_PLATFORMS "depot"), so it persists and restores via the
existing platform snapshot like the others. Build button on the Map tab.

## Relay Gate remote depletion (2026-07-02; browser check pending)
A gated system's remote income is no longer infinite. The econ tick snapshots a
per-worldlet relay plan (adm_relay: {w: creation-order index, rate: {res: per
min}} per extractor) into the sectors delta, and admiralty_relay_tick draws that
income against the SAME worldlet_reserves list that arrival re-applies - so a
gated finite worldlet really drains and stops, while unlimited (Haven) worldlets
pay on. Single source of truth: the relay mutates the stored reserves in place,
so the depletion is exactly what the player sees on their next visit. Old saves
(adm_income, no adm_relay) fall back to the frozen aggregate.

## Terrain no longer proximity-culls in a system (a614293, 2026-07-02)
Not an Admiral feature but landed alongside: parking/retrieving terrain to
standby is expensive network traffic, so terrain now stays loaded for the whole
visit (no pop in/out) and is torn down only on a jump (universe_clear_system).
Raider fleets - brained NPCs - still cull as a whole-formation park.
