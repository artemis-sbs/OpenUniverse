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
- **Relay Gate** - one per system; a gated system feeds its last-known income
  (adm_income in the sectors delta) into the pools at `Relay rate:` while the
  flag is elsewhere. Carried: remote depletion not simulated (income freezes at
  last visit).

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

## Terrain no longer proximity-culls in a system (a614293, 2026-07-02)
Not an Admiral feature but landed alongside: parking/retrieving terrain to
standby is expensive network traffic, so terrain now stays loaded for the whole
visit (no pop in/out) and is torn down only on a jump (universe_clear_system).
Raider fleets - brained NPCs - still cull as a whole-formation park.
