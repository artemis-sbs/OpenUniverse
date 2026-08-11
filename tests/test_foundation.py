"""Open Universe foundation regression test - the off-engine safety net for the
multi-cell + Mode/Scenario + PvP/victory + economy-pace + build-queue work.

Execs the OU universe_*.py into ONE shared namespace (mimicking MAST's `import
file.py` merge), then asserts the per-cell scope/snapshot helpers, the Mode/Economy
presets, the war-state watcher, the capital tag, the build-queue readout, the AMD
signal verb, and that the example universes (scout_signal / skirmish_arena) parse.
Also proves the cross-module free globals (objects_in_cell, universe_cell_live, ...)
resolve at call time, the way the real MAST merged namespace does.

DEPENDENCY: needs `../../sbs_utils` (the mock sbs + procedural API) as a sibling.

Run:  python tests/test_foundation.py     (from the OpenUniverse dir; exits 0/1)
"""
import os, sys

# Portable paths (a test file may use __file__ - reliable; the fs.py caveat is about
# production script.py only). OU universe + the sibling sbs_utils.
_HERE = os.path.dirname(os.path.abspath(__file__))
# Phase 2b split the monolithic universe/ into two addons: the core .py + all the
# .amd content in universe_core, the RTS .py in admiral. This test execs BOTH into one
# namespace (mimicking the runtime per-lib merge) and reads .amd from universe_core.
OU_CORE = os.path.join(_HERE, "..", "universe_core")
ADMIRAL = os.path.join(_HERE, "..", "admiral")
OU  = os.path.join(_HERE, "..")  # .amd files moved to the mission root in f18845e
                                 # ("universes are mission content, not engine")
SBS = os.path.abspath(os.path.join(_HERE, "..", "..", "sbs_utils"))
sys.path.insert(0, SBS)

from sbs_utils.fs import test_set_exe_dir
test_set_exe_dir()

# story_nodes first (memory: avoids a comms circular import), then the mock sim.
import sbs_utils.mast_sbs.story_nodes  # noqa: F401
from cosmos_dev.mock import sbs as mock_sbs
from sbs_utils.helpers import FrameContext, Context
from sbs_utils.spaceobject import SpaceObject


class FakeEvent:
    client_id = 0
    tag = sub_tag = value_tag = extra_tag = extra_extra_tag = ""
    origin_id = selected_id = parent_id = 0
    sub_float = 0.0
    source_point = None
    event_time = 0


mock_sbs.create_new_sim()
FrameContext.context = Context(mock_sbs.sim, mock_sbs, FakeEvent())
SpaceObject.clear()

# --- exec the OU modules into ONE shared namespace (the MAST merge) --------------
# Exec every .py from BOTH addons (core then admiral). Bodies only define functions +
# constants; cross-module free globals (objects_in_cell, admiralty_active, ...) resolve
# at CALL time, the way the merged runtime namespace does - so load order is safe.
import glob as _glob
NS = {"__name__": "ou_merged", "__builtins__": __builtins__}
for _dir in (OU_CORE, ADMIRAL):
    for _path in sorted(_glob.glob(os.path.join(_dir, "*.py"))):
        with open(_path, "r", encoding="utf-8") as f:
            exec(compile(f.read(), os.path.basename(_path), "exec"), NS)

# Phase 2b split the setup into two calls: core resolves the Mode
# (universe_mode_configure), then the admiral addon fills the economy
# (admiralty_configure). The runtime always does both in that order (universe.mast).
# Wrap admiralty_configure to mirror that, so the test's `admiralty_configure({mode:..})`
# calls set the Mode too, and initialize defaults before the worldlet checks below.
_ou_mode_configure = NS["universe_mode_configure"]
_ou_adm_configure = NS["admiralty_configure"]
def _ou_configure(cfg):
    _ou_mode_configure(cfg)
    _ou_adm_configure(cfg)
NS["admiralty_configure"] = _ou_configure
# _PLAYTEST_SPEED is a TEMP blanket economy accelerator (universe_worldlets.py) that
# economy_pace_mult multiplies in. Pin it to 1.0 so this test verifies the PURE pace
# presets + reserve scaling, independent of that debug knob's current value.
NS["_PLAYTEST_SPEED"] = 1.0
_ou_configure({})   # sandbox / standard defaults, like the runtime's setup pass

# Pull what we need out of the merged namespace.
universe_cell_enter   = NS["universe_cell_enter"]
universe_cell_origin  = NS["universe_cell_origin"]
universe_live_cells   = NS["universe_live_cells"]
universe_cell_live    = NS["universe_cell_live"]
objects_in_cell       = NS["objects_in_cell"]
worldlets_configure   = NS["worldlets_configure"]
worldlets_in_cell     = NS["worldlets_in_cell"]
worldlets_snapshot_reserves = NS["worldlets_snapshot_reserves"]
universe_worldlet_spawn = NS["universe_worldlet_spawn"]
MastDataObject = NS["MastDataObject"]

# One authored worldlet type with a finite reserve.
worldlets_configure([MastDataObject({
    "key": "rock", "name": "Rock", "desc": "", "yields": {"ore": 10}, "reserve": 500, "palette": {},
})])

# Two live cells at different galaxy coords -> different world slots.
CA = (0, 0)
CB = (3, 1)
universe_cell_enter(*CA, 0x1001)   # a fake occupant id each
universe_cell_enter(*CB, 0x1002)
oa = universe_cell_origin(*CA)
ob = universe_cell_origin(*CB)

# Spawn one worldlet at each cell's origin.
wa = universe_worldlet_spawn("rock", oa.x + 1000, oa.y, oa.z + 1000)
wb = universe_worldlet_spawn("rock", ob.x - 800,  ob.y, ob.z + 500)
# Deplete B's reserve so the snapshots are distinguishable.
wb.py_object.set_inventory_value("worldlet_reserve", 123)

fails = []
def check(name, cond):
    print(("  ok  " if cond else " FAIL ") + name)
    if not cond:
        fails.append(name)

print("Phase 2e.3 per-cell scope:")
lc = set(universe_live_cells())
check("universe_live_cells() has both cells", CA in lc and CB in lc)
check("universe_cell_live(A) and (B)", universe_cell_live(*CA) and universe_cell_live(*CB))
check("universe_cell_live(unknown) is False", not universe_cell_live(9, 9))

wa_cell = worldlets_in_cell(*CA)
wb_cell = worldlets_in_cell(*CB)
check("worldlets_in_cell(A) == [A's worldlet only]", [o.id for o in wa_cell] == [wa.id])
check("worldlets_in_cell(B) == [B's worldlet only]", [o.id for o in wb_cell] == [wb.id])

ra = worldlets_snapshot_reserves(*CA)
rb = worldlets_snapshot_reserves(*CB)
check("snapshot_reserves(A) == [500] (full)", ra == [500])
check("snapshot_reserves(B) == [123] (depleted)", rb == [123])

# objects_in_cell confines an all-cells role list to one cell.
allw = wa_cell + wb_cell  # stand in for to_object_list(role('worldlet'))
check("objects_in_cell(all, A) -> only A", [o.id for o in objects_in_cell(allw, *CA)] == [wa.id])
check("objects_in_cell(all, B) -> only B", [o.id for o in objects_in_cell(allw, *CB)] == [wb.id])

# --- Phase 2e.4: fleet cell awareness -------------------------------------------
# (Exec'ing universe_fleets.py / universe_skirmish.py above already proves they load
# and their new free-global refs are defined in the merged namespace.)
print("\nPhase 2e.4 fleet cell:")
npc_spawn        = NS["npc_spawn"]
admiralty_fleet_cell       = NS["admiralty_fleet_cell"]
universe_cell_at_pos = NS["universe_cell_at_pos"]

# A lead hull for fleet 'ftest' parked in cell B; admiralty_fleet_cell must report B.
npc_spawn(ob.x + 500, 0.0, ob.z - 300, "Lead", "tsn, adm_fleet, adm_ftest",
          "tsn_light_cruiser", "behav_npcship")
check("admiralty_fleet_cell('ftest') == cell B", admiralty_fleet_cell("ftest") == CB)
check("admiralty_fleet_cell('none') == (0,0) when no ships", admiralty_fleet_cell("nope") == (0, 0))
check("universe_cell_at_pos at B origin == B", universe_cell_at_pos(ob.x, ob.z) == CB)
check("universe_cell_at_pos far away == (0,0) default", universe_cell_at_pos(9_000_000, 9_000_000) == (0, 0))

# --- per-side snapshot readers (multi-side in one cell) --------------------------
print("\nPer-side platform/relay readers:")
_adm_platforms_for_side = NS["_adm_platforms_for_side"]
_adm_relay_for_side = NS["_adm_relay_for_side"]
snapshot_platforms_all = NS["admiralty_snapshot_platforms_all"]
universe_register_player_side = NS["universe_register_player_side"]

universe_register_player_side("tsn")
universe_register_player_side("orion")

# per-side dict: each side sees only its own list.
pdict = {"tsn": [{"k": "hq", "w": 0}], "orion": [{"k": "relay", "w": 1}]}
check("_adm_platforms_for_side(dict, tsn)", _adm_platforms_for_side(pdict, "tsn") == [{"k": "hq", "w": 0}])
check("_adm_platforms_for_side(dict, orion)", _adm_platforms_for_side(pdict, "orion") == [{"k": "relay", "w": 1}])
check("_adm_platforms_for_side(dict, unknown) == []", _adm_platforms_for_side(pdict, "zzz") == [])
# legacy flat list == the primary side (tsn, registered first), empty for others.
legacy = [{"k": "hq", "w": 0}]
check("_adm_platforms_for_side(legacy list, primary)", _adm_platforms_for_side(legacy, "tsn") == legacy)
check("_adm_platforms_for_side(legacy list, non-primary) == []", _adm_platforms_for_side(legacy, "orion") == [])
check("_adm_relay_for_side(legacy, primary) == list", _adm_relay_for_side(legacy, "tsn") == legacy)
check("_adm_relay_for_side(legacy, non-primary) is None", _adm_relay_for_side(legacy, "orion") is None)
check("_adm_relay_for_side(None) is None", _adm_relay_for_side(None, "tsn") is None)
# _all resolves universe_player_sides (free global) and returns a per-side dict;
# no admiral platforms exist here, so it's empty - but it must not crash.
check("snapshot_platforms_all(A) == {} (no platforms, resolves sides)", snapshot_platforms_all(*CA) == {})

# --- Economy pace presets -------------------------------------------------------
print("\nEconomy pace presets:")
admiralty_configure = NS["admiralty_configure"]
economy_pace_mult = NS["economy_pace_mult"]

admiralty_configure({"economy_pace": "standard"})
check("standard yield/reserve/storage/start all 1.0",
      (economy_pace_mult("yield"), economy_pace_mult("reserve"),
       economy_pace_mult("storage"), economy_pace_mult("start")) == (1.0, 1.0, 1.0, 1.0))
admiralty_configure({"economy_pace": "brisk"})
check("brisk yield == 2.0", economy_pace_mult("yield") == 2.0)
check("brisk storage == 1.5", economy_pace_mult("storage") == 1.5)
admiralty_configure({"economy_pace": "epic"})
check("epic reserve == 5.0", economy_pace_mult("reserve") == 5.0)
check("epic storage == 3.0", economy_pace_mult("storage") == 3.0)
check("epic yield == 1.0 (same per-hour ramp)", economy_pace_mult("yield") == 1.0)
admiralty_configure({"economy_pace": "bogus"})
check("unknown pace falls back to standard (1.0)", economy_pace_mult("yield") == 1.0)
admiralty_configure({})  # no pace key -> default standard
check("no pace key -> standard", economy_pace_mult("storage") == 1.0)

# --- Mode preset (mission shape) ------------------------------------------------
print("\nMode presets:")
admiralty_active = NS["admiralty_active"]
mission_mode = NS["mission_mode"]
admiralty_tuning = NS["admiralty_tuning"]

# sandbox == today: admiral on, standard economy, border skirmish.
admiralty_configure({"mode": "sandbox"})
check("sandbox: admiral active", admiralty_active() is True)
check("sandbox: economy_pace default standard", admiralty_tuning("economy_pace") == "standard")
check("sandbox: skirmish border", admiralty_tuning("skirmish_pressure") == "border")
# skirmish: brisk economy + raids, admiral on.
admiralty_configure({"mode": "skirmish"})
check("skirmish: economy brisk (mode default)", admiralty_tuning("economy_pace") == "brisk")
check("skirmish: admiral active", admiralty_active() is True)
# story/campaign: admiral OFF even with worldlet types configured.
admiralty_configure({"mode": "story"})
check("story: admiral gated OFF", admiralty_active() is False)
check("story: skirmish off", admiralty_tuning("skirmish_pressure") == "off")
admiralty_configure({"mode": "campaign"})
check("campaign: admiral OFF", admiralty_active() is False)
check("campaign: economy epic", admiralty_tuning("economy_pace") == "epic")
# explicit dial beats the mode default.
admiralty_configure({"mode": "skirmish", "economy_pace": "epic"})
check("explicit economy_pace beats mode default", admiralty_tuning("economy_pace") == "epic")
check("mission_mode() reports the active mode", mission_mode() == "skirmish")
# unknown mode -> no preset applied, plain defaults; admiral stays on.
admiralty_configure({"mode": "bogus"})
check("unknown mode: admiral still active (no gate)", admiralty_active() is True)

# --- Phase 3: Mode-driven PvP relations -----------------------------------------
print("\nMode-driven PvP relations:")
universe_mode_is_pvp = NS["universe_mode_is_pvp"]
for m, want in (("sandbox", False), ("skirmish", True), ("war", True),
                ("campaign", False), ("story", False)):
    admiralty_configure({"mode": m})
    check(f"{m}: pvp == {want}", universe_mode_is_pvp() is want)

# --- Phase 3b: war-state watcher (elimination -> last standing) ------------------
print("\nWar-state watcher:")
warstate_reset = NS["warstate_reset"]
warstate_tick = NS["warstate_tick"]
warstate_done = NS["warstate_done"]
delete_object = NS["delete_object"]
# tsn + orion are registered player sides (from the Mode tests above).
warstate_reset()
check("no HQs yet: no events", warstate_tick() == [])
hq_t = npc_spawn(oa.x, 0, oa.z, "T HQ", "tsn, admiral_hq", "starbase_command", "behav_station")
hq_o = npc_spawn(oa.x + 3000, 0, oa.z, "O HQ", "orion, admiral_hq", "starbase_command", "behav_station")
check("both have an HQ: established, no elimination", warstate_tick() == [])
delete_object(hq_o.id)   # orion loses its last HQ
_ev = warstate_tick()
_types = [(e.type, e.side) for e in _ev]
check("orion eliminated", ("eliminated", "orion") in _types)
check("tsn last standing", ("last_standing", "tsn") in _types)
check("watcher now done", warstate_done() is True)
check("after done: no more events", warstate_tick() == [])

# --- Phase 3b: capital tag (the decapitation quick-win target) ------------------
print("\nCapital tag:")
universe_platform_spawn = NS["universe_platform_spawn"]
has_role = NS["has_role"]
to_object = NS["to_object"]
wa_obj, wb_obj = to_object(wa.id), to_object(wb.id)
# tsn has raw HQs from the warstate test but no admiral_home_hq yet -> first one
# built via universe_platform_spawn becomes the capital.
cap = universe_platform_spawn("hq", "tsn", wa_obj)
check("first tsn HQ tagged admiral_home_hq", has_role(cap.id, "admiral_home_hq"))
check("first tsn HQ tagged tsn_capital (quest target)", has_role(cap.id, "tsn_capital"))
cap2 = universe_platform_spawn("hq", "tsn", wb_obj)
check("second tsn HQ is NOT a capital", not has_role(cap2.id, "admiral_home_hq"))
orion_cap = universe_platform_spawn("hq", "orion", wa_obj)
check("orion's first HQ tagged orion_capital", has_role(orion_cap.id, "orion_capital"))
check("non-HQ platform gets no capital tag", not has_role(
    universe_platform_spawn("extractor", "tsn", wb_obj).id, "admiral_home_hq"))

# --- Archetype D: The Fading Signal (a Mode: story universe) --------------------
print("\nArchetype D - The Fading Signal (Mode: story):")
universe_doc = NS["universe_doc"]
universe_admiralty_cfg = NS["universe_admiralty_cfg"]
universe_section = NS["universe_section"]
with open(os.path.join(OU, "scout_signal.amd"), "r", encoding="utf-8") as f:
    _sig_doc = universe_doc(f.read())
_sig_adm = universe_admiralty_cfg(_sig_doc)
# scout_signal carries Mode in a ## Scenario chapter and has NO ## Admiralty block.
check("scout_signal: Mode==story from ## Scenario (no Admiralty chapter)", (_sig_adm or {}).get("mode") == "story")
# Worldlet types are still configured (rock) from earlier - Mode: story must STILL
# gate the admiral off (the whole point of the story mission).
admiralty_configure(_sig_adm)
check("scout_signal: admiral gated OFF despite worldlet types", admiralty_active() is False)
check("scout_signal: not PvP (co-op/solo)", universe_mode_is_pvp() is False)
check("scout_signal has a Goals (win) section", universe_section(_sig_doc, "goals") is not None)
check("scout_signal has a Narrative section", universe_section(_sig_doc, "narrative") is not None)
# No ## Sides chapter - the load path must handle an empty side list, not crash.
_sig_sides = NS["universe_sides_from_doc"](_sig_doc)
check("scout_signal: sides parse to a list (0 sides ok)", isinstance(_sig_sides, list))
# default.amd: Mode migrated to ## Scenario; economy dials stay in ## Admiralty.
with open(os.path.join(OU, "default.amd"), "r", encoding="utf-8") as f:
    _def_adm = universe_admiralty_cfg(universe_doc(f.read()))
check("default.amd: Mode==sandbox from ## Scenario (Admiralty also present)", (_def_adm or {}).get("mode") == "sandbox")
check("default.amd: worldlet_chance still read from ## Admiralty", "worldlet_chance" in (_def_adm or {}))

# --- Archetype A: The Broken Accord (a Mode: skirmish universe) -----------------
print("\nArchetype A - The Broken Accord (Mode: skirmish):")
with open(os.path.join(OU, "skirmish_arena.amd"), "r", encoding="utf-8") as f:
    _sk_doc = universe_doc(f.read())
_sk_adm = universe_admiralty_cfg(_sk_doc)
check("skirmish_arena: Mode==skirmish from ## Scenario", (_sk_adm or {}).get("mode") == "skirmish")
check("skirmish_arena: worldlet_chance authored", (_sk_adm or {}).get("worldlet_chance") is not None)
# Configure its OWN worldlets, then admiralty -> admiral ON, brisk, PvP.
worldlets_configure(NS["universe_parse_worldlets"](_sk_doc))
admiralty_configure(_sk_adm)
check("skirmish_arena: admiral ON (worldlets present + Mode admiral)", admiralty_active() is True)
check("skirmish_arena: PvP True (player sides hostile)", universe_mode_is_pvp() is True)
check("skirmish_arena: economy brisk (Mode default)", admiralty_tuning("economy_pace") == "brisk")
check("skirmish_arena: 3 worldlet types parsed", len(NS["universe_parse_worldlets"](_sk_doc)) == 3)

# --- Overseer build-queue readout (name + worldlet + time remaining) ------------
print("\nBuild-queue text:")
admiralty_build_queue_text = NS["admiralty_build_queue_text"]
MDO = NS["MastDataObject"]
_q = [MDO({"name": "Extractor", "where": "Cinder World", "eta": 112.0}),
      MDO({"name": "Refinery", "where": "Veiled Giant", "eta": 105.0})]
_txt = admiralty_build_queue_text(_q, 100.0)
check("queue counts builds", _txt.startswith("Building 2:"))
check("queue shows name+where+remaining #1", "Extractor - Cinder World (12s)" in _txt)
check("queue shows name+where+remaining #2", "Refinery - Veiled Giant (5s)" in _txt)
check("past-eta clamps to 0s (no negatives)",
      "HQ - Haven (0s)" in admiralty_build_queue_text([MDO({"name": "HQ", "where": "Haven", "eta": 90.0})], 100.0))
check("legacy bare-string entry tolerated", "old label" in admiralty_build_queue_text(["old label"], 100.0))
# Live-tick change key: no time component when idle, a per-second one when building.
admiralty_status_change_key = NS["admiralty_status_change_key"]
_active = [MDO({"name": "X", "where": "Y", "eta": 10.0})]
check("idle change-key has no time component", admiralty_status_change_key([], "hi").count("|") == 1)
_k1 = admiralty_status_change_key(_active, "hi")
check("active change-key adds a time component", _k1.count("|") == 2)
# The time component is the LIVE sim clock (int seconds) - so it advances each second
# in-engine, ticking the countdown. (Mock time_tick_counter has no setter to advance.)
check("active change-key carries the live sim clock", _k1.endswith("|" + str(int(NS["FrameContext"].sim_seconds))))

# --- Phase 3c: the AMD `signal` verb (conquest-as-quest via on_signal) -----------
print("\nAMD signal verb (on_signal):")
# The trigger verbs moved to the shared library (sbs_utils.procedural.amd_quest);
# universe passes its own role aliases (derelict -> universe_derelict).
from sbs_utils.procedural.amd_quest import amd_trigger
_aliases = NS["_ROLE_ALIASES"]
check("`signal eliminated_orion` -> on_signal {name}",
      amd_trigger("signal eliminated_orion") == ("on_signal", {"name": "eliminated_orion"}))
check("`signal Eliminated Orion` normalizes case+spaces",
      amd_trigger("signal Eliminated Orion") == ("on_signal", {"name": "eliminated_orion"}))
check("existing `scan 1 derelict` still aliases to universe_derelict",
      amd_trigger("scan 1 derelict", _aliases) == ("on_scan", {"role": "universe_derelict", "count": 1}))


# --- the jump wind-up: which look a side's drives use ----------------------------
print("\nJump wind-up (universe_charge_look):")
from sbs_utils.procedural import particles as _P
from sbs_utils.procedural import amd_effects as _E
from sbs_utils.procedural.amd_doc import amd_document, amd_section
from sbs_utils.procedural.inventory import set_inventory_value

_sr_text = open(os.path.join(OU, "silver_reach.amd"), "r", encoding="utf-8").read()
_sr = amd_document(_sr_text)
_sr_sides = NS["universe_sides_from_doc"](_sr)
_E.amd_effects(amd_section(_sr, "effects"))

check("silver_reach declares both looks",
      _E.effect_amd_names() == ["lantern_charge", "veil_charge"])
check("a look name resolves, and says which layer it came from",
      _E.effect_amd_look("lantern_charge") == "amd"      # authored
      and _E.effect_amd_look("smoke") == "preset"        # the attachable table
      and _E.effect_amd_look("coil") == "charge"         # a built-in build-up
      and _E.effect_amd_look("no_such_look") is None)

_lan = NS["sides_get"](_sr_sides, "lantern")
_vei = NS["sides_get"](_sr_sides, "veil")
check("`Jump Charge:` reached the side record",
      _lan.get("jump_charge", None) == "lantern_charge"
      and _vei.get("jump_charge", None) == "veil_charge")

# A ship on each side, plus one on a side that declares nothing at all.
_ships = {}
for _key, _side in (("lantern", "lantern"), ("veil", "veil"), ("stray", "nobody")):
    _o = NS["to_object"](NS["npc_spawn"](0, 0, 0, _key, _side, "tsn_light_cruiser", "behav_npcship"))
    _o.side = _side
    _ships[_key] = _o

_look = NS["universe_charge_look"]
_color = NS["universe_charge_color"]
check("a side's own `Jump Charge:` wins",
      _look(_sr_sides, _ships["lantern"].id) == "lantern_charge")
check("...per side, not globally",
      _look(_sr_sides, _ships["veil"].id) == "veil_charge")
# The Combine is a trader and the Veil a pirate, so DROPPING Jump Charge: must still
# tell them apart - that is the free half, and it is what an unauthored universe gets.
_lan_no = NS["MastDataObject"]({"key": "lantern", "archetype": "trader", "color": "#ffcc44",
                                "jump_charge": None, "diplomacy": "neutral"})
_vei_no = NS["MastDataObject"]({"key": "veil", "archetype": "pirate", "color": "#cc2244",
                                "jump_charge": None, "diplomacy": "foe"})
_bare = [_lan_no, _vei_no]
check("with no Jump Charge:, Character: still separates them",
      _look(_bare, _ships["lantern"].id) == "preburn"
      and _look(_bare, _ships["veil"].id) == "arc")
check("a side with no record at all still winds up",
      _look(_sr_sides, _ships["stray"].id) == "coil")
check("the tint is the side's own Color:",
      _color(_sr_sides, _ships["lantern"].id) == "#ffcc44"
      and _color(_sr_sides, _ships["veil"].id) == "#cc2244")

# A prefab or quest can pin a look on one hull, over its side's.
set_inventory_value(_ships["lantern"].id, "charge", "implode")
check("a per-ship `charge` overrides the side",
      _look(_sr_sides, _ships["lantern"].id) == "implode")

# And every look a side can name has to actually resolve, or the jump goes silent.
_all_looks = ["lantern_charge", "veil_charge", "coil", "arc", "preburn", "implode", "pulse"]
check("every nameable look resolves",
      all(_E.effect_amd_look(k) is not None or k in _P.particle_charge_looks()
          for k in _all_looks))

print("\n" + ("ALL PASS" if not fails else f"{len(fails)} FAILED: {fails}"))
sys.exit(1 if fails else 0)
