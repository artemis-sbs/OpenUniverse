"""Worldlets + the Admiralty economy for the Open Universe (Admiral console,
slice 1 - see ADMIRAL_CONSOLE.md).

Worldlets are small resource bodies (behav_planet terrain) whose types are
authored in the universe AMD (`## Worldlets`: Yields / Reserve / Palette).
They spawn procedurally via the POI deck (`Worldlet chance`, an Admiralty
dial) or hand-placed as Landmarks (Kind: worldlet). The Admiralty chapter
tunes the side economy: starting stockpiles, command points, budgets.

Resources (ore / gas / crew) are pooled per side on the side agent's
inventory - the same home as the shared `credits` pool. Extraction platforms
(admiral.mast prefabs) drain a worldlet's reserve into the side pools on a
tick driven from admiral.mast.

Shared-namespace notes (like the other universe_*.py files): universe_section
comes from universe_clans.py; no relative sibling imports.
"""
import math
from sbs_utils.mast.mast_node import MastDataObject
from sbs_utils.procedural.spawn import terrain_spawn, npc_spawn
from sbs_utils.procedural.inventory import get_inventory_value, set_inventory_value
from sbs_utils.procedural.sides import to_side_id, side_enemy_members_set
from sbs_utils.procedural.roles import role, has_role, remove_role, add_role
from sbs_utils.procedural.query import to_object_list, to_object
from sbs_utils.procedural.science import science_set_scan_data
from sbs_utils.procedural.gui import gui_row, gui_text
from sbs_utils.helpers import FrameContext

ADM_RESOURCES = ["ore", "gas", "crew"]

# Built-in Admiralty tuning; a universe's ## Admiralty fence overrides any knob.
_ADM_DEFAULTS = {
    # Ore must cover the bootstrap: HQ (150) + first Extractor (60) = 210 before any
    # income exists, so start above that with a buffer (a soft-lock otherwise).
    "start_ore": 300, "start_gas": 100, "start_crew": 40,
    "storage": 600,
    "command_points": 3, "fleet_gas_burn": 2,
    "requisition_budget": 800,
    "skirmish_pressure": "border",
    "skirmish_interval": 240,   # seconds between border raids (pressure-scaled)
    "mia_timer": 300,           # the MIA rescue window (seconds)
    "relay_rate": 0.5,          # Relay Gate remote income fraction
    "subsidy_max": 0.3,         # cap on the crew price subsidy (fraction off)
    "subsidy_step": 0.1,        # tier size the console cycles through
    "build_model": "menu",      # "menu" (instant/parallel) or "fabricator" (A/B)
    "research_pace": "campaign",
    "economy_pace": "standard", # brisk | standard | epic (scales the dials below)
    "mode": "sandbox",          # mission-shape preset (see MODE_PRESETS / FOUNDATION_PLAN.md)
}

# The Mission-shape `Mode` dial (MODE_PRESETS) moved to universe_mode.py (core) in
# Phase 2b so a core-only mission has it without this admiral economy addon. This addon
# reads MODE_PRESETS / mission_mode() from there (shared MAST namespace).

# Economy pace presets: one authored line ("Economy pace: brisk") scales the four
# throughput/longevity dials together, instead of hand-tuning Yields/Reserve/Storage/
# Start separately. Multipliers on the AUTHORED base values (so an author can still
# set explicit numbers AND pick a pace - the pace scales whatever they set):
#   yield   - per-minute extraction + relay throughput
#   reserve - how long a FINITE worldlet lasts before drying up (unlimited stays so)
#   storage - the pool ceiling
#   start   - the opening stockpile
# brisk = a punchy ~1h session; standard = today's balance; epic = a long/persistent
# game (same per-hour ramp, but worldlets last far longer and you can bank much more).
ECONOMY_PACE = {
    "brisk":    {"yield": 2.0, "reserve": 2.0, "storage": 1.5, "start": 1.5},
    "standard": {"yield": 1.0, "reserve": 1.0, "storage": 1.0, "start": 1.0},
    "epic":     {"yield": 1.0, "reserve": 5.0, "storage": 3.0, "start": 1.5},
}

# TEMP PLAYTEST KNOB: a blanket multiplier on every economy-pace dial (yield / start
# pool / reserve / storage), applied in economy_pace_mult AFTER the pace lookup - so
# it speeds the loop unconditionally, even if the Mode->brisk wiring isn't taking.
# Purpose is OBSERVABILITY (make the build/fleet/expand loop fast enough to watch and
# verify it works), not final balance. Set to 1 to disable; remove once tuned.
_PLAYTEST_SPEED = 8.0

# Per-minute resource upkeep of a FULL (100%) subsidy - the actual drain scales
# with the active rate, so a 30% subsidy costs 30% of this each minute. This is
# the anti-snowball rail: the upkeep competes with fleets/builds/research.
SUBSIDY_UPKEEP_PER_MIN = {"ore": 180, "gas": 60}

# Live per-load registries (reset by *_configure on universe load, mirroring
# generation_configure / regions_configure).
_WORLDLET_TYPES = {}
_ADM = dict(_ADM_DEFAULTS)


# --- AMD parsing + load-time configuration -----------------------------------
def universe_parse_worldlets(doc):
    """Worldlet type records from the `## Worldlets` chapter (empty if none)."""
    section = universe_section(doc, "worldlets")
    out = []
    if section is not None:
        for n in section.get("children", []):
            data = n.get("data") or {}
            out.append(MastDataObject({
                "key": n.get("key"),
                "name": n.get("display_text"),
                "desc": (n.get("description") or "").strip(),
                "yields": data.get("yields") or {},
                "reserve": data.get("reserve"),   # None = unlimited
                "palette": data.get("palette") or {},
            }))
    return out


def worldlets_configure(types):
    """Register the authored worldlet types for this universe load."""
    global _WORLDLET_TYPES
    _WORLDLET_TYPES = {t.get("key"): t for t in (types or [])}


# universe_admiralty_cfg + the Mode gate (MODE_PRESETS / mission_mode / admiralty_active)
# moved to universe_mode.py (core) in Phase 2b, so a core-only mission has them without
# this admiral economy addon. Below keeps only the economy tuning + activation report.


def admiralty_configure(cfg):
    """Apply a universe's Admiralty economy tuning (resets to defaults first) and
    enable the RTS for this load. Mode resolution lives in universe_mode.py (core);
    this fills the economy dials, then reports admiral-content presence back to the
    Mode gate via universe_mode_set_admiral_active. The Worldlet chance dial is pushed
    into the generation registry so the POI deck sees it (generation_set, universe_helpers)."""
    global _ADM
    _ADM = dict(_ADM_DEFAULTS)
    if cfg:
        for k, v in cfg.items():
            if k != "worldlet_chance":
                _ADM[k] = v
    # Mission Mode preset: fill in DEFAULTS for any economy dial the author did not set
    # explicitly (explicit cfg value wins). The Mode itself is resolved in universe_mode.py.
    preset = MODE_PRESETS.get(mission_mode())
    if preset is not None:
        for k, v in preset.items():
            if k == "admiral":
                continue
            if cfg is None or k not in cfg:
                _ADM[k] = v
    # Active iff the Mode allows the RTS AND the universe authored worldlet types.
    # universe_mode_set_admiral_active folds in the Mode gate + the admiral-present flag.
    universe_mode_set_admiral_active(cfg is not None and bool(_WORLDLET_TYPES))
    if admiralty_active() and cfg and "worldlet_chance" in cfg:
        generation_set("worldlet", cfg["worldlet_chance"])


def admiralty_tuning(name, default=None):
    return _ADM.get(name, _ADM_DEFAULTS.get(name, default))


def economy_pace_mult(dim):
    """The active Economy pace preset's multiplier for one dial (yield / reserve /
    storage / start); 1.0 for an unknown pace or dial. Applied at the read sites
    (extraction, reserve spawn, pool cap, seed) so it scales the authored base."""
    preset = ECONOMY_PACE.get(str(admiralty_tuning("economy_pace", "standard")).strip().lower(),
                              ECONOMY_PACE["standard"])
    # _PLAYTEST_SPEED is a TEMP blanket accelerator (see its definition) - multiplied
    # in after the pace lookup so it applies regardless of the Mode->pace wiring.
    return float(preset.get(dim, 1.0)) * _PLAYTEST_SPEED


def worldlet_type(key):
    return _WORLDLET_TYPES.get(key)


def worldlet_type_keys():
    return list(_WORLDLET_TYPES.keys())


def universe_worldlet_pick(r):
    """A worldlet type key for the POI deck's draw (deck's own seeded rng)."""
    keys = worldlet_type_keys()
    return r.choice(keys) if keys else None


def universe_worldlet_home_pick():
    """The home system's guaranteed worldlet: the first unlimited-reserve type
    (a settled Haven-style world) so the Admiral's opening economy never runs
    dry at base - else the first authored type."""
    for k, t in _WORLDLET_TYPES.items():
        if t.get("reserve") is None:
            return k
    keys = worldlet_type_keys()
    return keys[0] if keys else None


# --- Spawning -----------------------------------------------------------------
def universe_worldlet_spawn(type_key, x, y, z, radius=None):
    """Spawn one worldlet of an authored type: behav_planet terrain + palette +
    the yields/reserve inventory the extraction tick reads. Returns the
    SpawnData (None for an unknown type). Pattern follows LM's
    prefab_planetoid (planet_last_changed tick flag, then the planet_* knobs)."""
    wt = worldlet_type(type_key)
    if wt is None:
        return None
    co = terrain_spawn(x, y, z, wt.get("name"), "#,worldlet", "planet", "behav_planet")
    r = float(radius if radius is not None else 2000)
    co.engine_object.exclusion_radius = r
    ds = co.data_set
    sim = FrameContext.sim
    if sim is not None:
        ds.set("planet_last_changed", sim.time_tick_counter, 0)
    # planet_radius IS the 3D-view size. Use the full worldlet radius (not r/2 like
    # LM's decorative prefab_planetoid) so the body reads at a distance - a worldlet
    # is the whole point of the Admiral's map. r is ~2000 (see universe_systems.py),
    # matching exclusion_radius above and clearing the platform offset (r + 900).
    ds.set("planet_radius", r, 0)
    # A worldlet is the whole point of the Admiral's map, so make it read from a
    # distance on the 2D command view: a larger icon + a warm radar tint. (These are
    # 2D-view knobs; the 3D planet keeps its palette above. Tune icon_scale to taste -
    # needs an in-engine eye, per object_data_documentation.txt.)
    ds.set("icon_scale", 2.5, 0)
    ds.set("radar_color_override", "#ffcf8c", 0)
    pal = wt.get("palette") or {}
    _set_planet_color(ds, "planet_baseColor", pal.get("base"))
    _set_planet_color(ds, "planet_emissiveColor", pal.get("emissive"))
    _set_planet_color(ds, "planet_upperCloudColor", pal.get("clouds"))
    if pal.get("bands") is not None:
        ds.set("planet_bandScale", float(pal.get("bands")), 0)
    else:
        ds.set("planet_bandScale", 3.72, 0)              # LM planetoid default
    # The engine's planet needs its full shader model set or the body can read as
    # INVISIBLE in the 3D view (colors alone aren't enough). These are the values LM's
    # working prefab_planetoid uses; the palette above tints on top. Without them the
    # worldlet spawns but never draws - the "worldlets don't show in 3D" bug.
    ds.set("planet_fresnel", 11.96)
    ds.set("planet_fresnelBias", 0.42)
    ds.set("planet_windSpeed1", 1000)
    ds.set("planet_windSpeed2", 1000)
    ds.set("planet_upperCloudStrength", 3.12)
    ds.set("planet_upperCloudExponent", 3.96)
    py = co.py_object
    py.set_inventory_value("worldlet_type", type_key)
    py.set_inventory_value("worldlet_radius", r)
    py.set_inventory_value("worldlet_yields", dict(wt.get("yields") or {}))
    # Finite reserves scale with the Economy pace (epic worldlets last far longer);
    # an unlimited (None) reserve stays unlimited.
    base_reserve = wt.get("reserve")
    if base_reserve is not None:
        base_reserve = int(round(float(base_reserve) * economy_pace_mult("reserve")))
    py.set_inventory_value("worldlet_reserve", base_reserve)
    return co


def _set_planet_color(ds, prefix, hexstr):
    """'#8c2f1c' -> planet_*ColorR/G/B floats (0-1). None -> leave engine default."""
    if not hexstr:
        return
    s = str(hexstr).lstrip("#")
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    if len(s) < 6:
        return
    try:
        rgb = [int(s[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    except ValueError:
        return
    ds.set(prefix + "R", rgb[0])
    ds.set(prefix + "G", rgb[1])
    ds.set(prefix + "B", rgb[2])


def worldlet_info(obj_or_id):
    """(type record, yields dict, reserve) for a spawned worldlet - the map
    popup / Admiral panel read. reserve None = unlimited."""
    obj = to_object(obj_or_id)
    if obj is None:
        return None, {}, None
    wt = worldlet_type(obj.get_inventory_value("worldlet_type"))
    return (wt,
            obj.get_inventory_value("worldlet_yields", {}) or {},
            obj.get_inventory_value("worldlet_reserve"))


def worldlets_in_system():
    """All live worldlet objects across every live cell, in creation order (sorted
    ids). Multi-cell: prefer worldlets_in_cell(i, j) for per-cell persistence -
    this bare form spans cells (fine only when one cell is live)."""
    return sorted(to_object_list(role("worldlet")), key=lambda o: o.id)


def worldlets_in_cell(i, j):
    """Live worldlets physically inside cell (i, j), in creation order (sorted ids)
    so a per-cell snapshot lines up with that cell's deterministic spawn order.
    objects_in_cell is a sibling helper (shared MAST namespace)."""
    return sorted(objects_in_cell(to_object_list(role("worldlet")), i, j), key=lambda o: o.id)


# --- Per-system persistence (the universe_systems delta) --------------------------
# A system regenerates from the seed, so only player-made changes are stored:
# worldlet depletion and the platforms built there. Snapshotted on the economy
# tick (admiral.mast) into universe_systems; re-applied on arrival
# (universe.mast enter_system). Order-based: spawn order is deterministic.
def worldlets_snapshot_reserves(i, j):
    """[reserve or None per worldlet, creation order] for cell (i, j)'s delta."""
    return [w.get_inventory_value("worldlet_reserve") for w in worldlets_in_cell(i, j)]


def worldlets_apply_reserves(saved, i, j):
    """Re-apply saved depletion to cell (i, j)'s freshly regenerated worldlets."""
    if not isinstance(saved, list):
        return
    for w, r in zip(worldlets_in_cell(i, j), saved):
        if r is not None:
            w.set_inventory_value("worldlet_reserve", r)


def admiralty_snapshot_platforms(side, i, j):
    """[{k: kind, w: worldlet index}] for cell (i, j)'s delta. Both the worldlet
    index map and the platform list are confined to the cell, so a second live
    system's platforms never bleed into this cell's save."""
    order = {w.id: idx for idx, w in enumerate(worldlets_in_cell(i, j))}
    out = []
    for plat in objects_in_cell(to_object_list(role("admiral_platform") & role(side)), i, j):
        widx = order.get(plat.get_inventory_value("worldlet_id"))
        kind = plat.get_inventory_value("admiral_kind")
        if widx is not None and kind:
            out.append({"k": kind, "w": widx})
    return out


def admiralty_restore_platforms(side, saved, i, j):
    """Respawn cell (i, j)'s platforms from the systems delta (arrival)."""
    if not isinstance(saved, list):
        return
    worldlets = worldlets_in_cell(i, j)
    for rec in saved:
        widx = rec.get("w")
        kind = rec.get("k")
        if widx is None or kind not in ADM_PLATFORMS or widx >= len(worldlets):
            continue
        wobj = worldlets[widx]
        if admiralty_platform_at(wobj, kind) is None:
            universe_platform_spawn(kind, side, wobj)


# --- Side resource pools --------------------------------------------------------
def admiralty_pool_get(side, res):
    return int(get_inventory_value(to_side_id(side), "adm_" + res, 0))


def admiralty_pool_cap(side, res):
    """Stockpile cap: the Storage tuning + each Refinery's silos + research
    ('storage N' unlocks; research_storage_bonus is a shared-namespace call
    into universe_research.py)."""
    cap = int(admiralty_tuning("storage", 600) * economy_pace_mult("storage"))
    cap += REFINERY_STORAGE_BONUS * len(to_object_list(role("admiral_refinery") & role(side)))
    cap += int(research_storage_bonus(side))
    return cap


def admiralty_pool_set(side, res, value):
    capped = min(int(value), admiralty_pool_cap(side, res))
    set_inventory_value(to_side_id(side), "adm_" + res, max(0, capped))


def admiralty_pool_add(side, res, delta):
    admiralty_pool_set(side, res, admiralty_pool_get(side, res) + int(delta))


def admiralty_pools(side):
    return {r: admiralty_pool_get(side, r) for r in ADM_RESOURCES}


def admiralty_seed_pools(side):
    """Seed a side's starting stockpiles once per campaign (guarded). Returns
    True when the seed happened on this call. Safe to retry: the side agent
    may not exist yet at map start (to_side_id -> None early in some start
    orders), so the economy tick retries until it lands."""
    sid = to_side_id(side)
    if sid is None or get_inventory_value(sid, "adm_seeded", False):
        return False
    set_inventory_value(sid, "adm_seeded", True)
    start_mult = economy_pace_mult("start")
    for res in ADM_RESOURCES:
        admiralty_pool_set(side, res, int(admiralty_tuning("start_" + res, 0) * start_mult))
    return True


def admiralty_can_afford(side, cost):
    """True if the side's pools cover a {res: amount} cost (no deduction)."""
    for res, amt in (cost or {}).items():
        if admiralty_pool_get(side, res) < int(amt):
            return False
    return True


def admiralty_spend(side, cost):
    """Deduct a {res: amount} cost if affordable; True on success."""
    if not admiralty_can_afford(side, cost):
        return False
    for res, amt in (cost or {}).items():
        admiralty_pool_add(side, res, -int(amt))
    return True


# --- Extraction ----------------------------------------------------------------
def admiralty_extraction_tick(side, dt_seconds):
    """One economy tick: every extractor platform pulls its worldlet's Yields
    (per-minute rates) into the side pools, draining a finite Reserve. A dry
    worldlet stops producing (its extractors idle). A Refinery at the same
    worldlet multiplies the pull; 'extraction N%' research speeds everything.
    Called from admiral.mast."""
    if not admiralty_active():
        return
    scale = float(dt_seconds) / 60.0 * float(research_extraction_mult(side)) * economy_pace_mult("yield")
    for plat in to_object_list(role("admiral_extractor")):
        if not has_role(plat.id, side):
            continue
        wid = plat.get_inventory_value("worldlet_id")
        wobj = to_object(wid) if wid is not None else None
        if wobj is None:
            continue
        wscale = scale
        if admiralty_platform_at(wobj, "refinery") is not None:
            wscale *= REFINERY_EXTRACT_MULT
        yields = wobj.get_inventory_value("worldlet_yields", {}) or {}
        reserve = wobj.get_inventory_value("worldlet_reserve")
        for res, per_min in yields.items():
            amount = float(per_min) * wscale
            if reserve is not None:
                if reserve <= 0:
                    break
                amount = min(amount, reserve)
                reserve -= amount
            _pool_add_f(side, res, amount)
        if reserve is not None:
            wobj.set_inventory_value("worldlet_reserve", max(0, reserve))


def admiralty_relay_snapshot(side, i, j):
    """Per extractor-fed worldlet in cell (i, j): {w: creation-order index, rate:
    {res: per_min}} - the income a Relay Gate keeps pulling after the flag leaves.
    Stored in the systems delta each econ tick, keyed by worldlet index (same order
    as worldlets_snapshot_reserves) so the relay draws it against that system's
    stored worldlet_reserves list - the one arrival re-applies - and a gated FINITE
    worldlet really runs dry while unlimited ones pay on."""
    order = {w.id: idx for idx, w in enumerate(worldlets_in_cell(i, j))}
    # Include the pace yield multiplier so relay income matches live extraction.
    mult = float(research_extraction_mult(side)) * economy_pace_mult("yield")
    out = []
    for plat in objects_in_cell(to_object_list(role("admiral_extractor")), i, j):
        if not has_role(plat.id, side):
            continue
        wid = plat.get_inventory_value("worldlet_id")
        widx = order.get(wid)
        wobj = to_object(wid) if wid is not None else None
        if widx is None or wobj is None:
            continue
        wmult = mult
        if admiralty_platform_at(wobj, "refinery") is not None:
            wmult *= REFINERY_EXTRACT_MULT
        rate = {res: float(per_min) * wmult
                for res, per_min in (wobj.get_inventory_value("worldlet_yields", {}) or {}).items()}
        if rate:
            out.append({"w": widx, "rate": rate})
    return out


# --- Per-side persistence wrappers (multi-side in one cell) ----------------------
# admiral_platforms / adm_relay are stored PER SIDE ({side: [...]}) so a second
# player side's infrastructure in the same cell is never clobbered by the primary
# side's (empty) snapshot. Both readers accept the legacy FLAT LIST too (= the
# primary side's), so a dev save written before this still loads.
def _adm_platforms_for_side(stored, side):
    if isinstance(stored, dict):
        return stored.get(side) or []
    if isinstance(stored, list):
        return stored if side == universe_primary_side() else []
    return []


def _adm_relay_for_side(stored, side):
    if isinstance(stored, dict):
        return stored.get(side)
    if isinstance(stored, list):
        return stored if side == universe_primary_side() else None
    return None


def admiralty_snapshot_platforms_all(i, j):
    """{side: [{k,w}]} for every player side with platforms in cell (i, j)."""
    out = {}
    for s in universe_player_sides():
        p = admiralty_snapshot_platforms(s, i, j)
        if p:
            out[s] = p
    return out


def admiralty_relay_snapshot_all(i, j):
    """{side: [{w,rate}]} for every player side's extractors in cell (i, j)."""
    out = {}
    for s in universe_player_sides():
        r = admiralty_relay_snapshot(s, i, j)
        if r:
            out[s] = r
    return out


def admiralty_restore_platforms_all(saved, i, j):
    """Respawn cell (i, j)'s platforms for EVERY side in the per-side save (accepts
    the legacy flat list = the primary side)."""
    if isinstance(saved, dict):
        for s, plats in saved.items():
            admiralty_restore_platforms(s, plats, i, j)
    elif isinstance(saved, list):
        admiralty_restore_platforms(universe_primary_side(), saved, i, j)


def admiralty_relay_tick(side, systems, cur_i, cur_j, dt_seconds):
    """Remote income (slice 4): every OTHER system whose systems delta shows a
    Relay Gate feeds the pools at the Relay rate, drawn against that system's
    stored worldlet reserves - so a gated FINITE worldlet depletes and stops,
    while unlimited worldlets pay on. Mutates the stored reserves in place, so
    the depletion is exactly what arrival re-applies on the next visit. A legacy
    delta (adm_income, no adm_relay) falls back to the frozen aggregate."""
    if not admiralty_active() or not isinstance(systems, dict):
        return
    rate = float(admiralty_tuning("relay_rate", 0.5))
    if rate <= 0:
        return
    scale = float(dt_seconds) / 60.0 * rate
    for skey, sval in systems.items():
        if not isinstance(sval, dict):
            continue
        # Skip any LIVE cell, not just the flag's current one: a live system pays via
        # its own extraction tick, so relaying it too would double-pay it. With
        # several cells live at once, cur_i/cur_j alone would miss the others.
        _sc = skey.split(",")
        if len(_sc) == 2 and universe_cell_live(int(_sc[0]), int(_sc[1])):
            continue
        # This SIDE's platforms/relay in the stored cell (per-side dict, or legacy
        # flat list = primary side). A side only earns from relays IT built.
        side_plats = _adm_platforms_for_side(sval.get("admiral_platforms"), side)
        if not any(isinstance(p, dict) and p.get("k") == "relay" for p in side_plats):
            continue
        relay = _adm_relay_for_side(sval.get("adm_relay"), side)
        if not isinstance(relay, list):
            # Pre-depletion save: pay the frozen aggregate, no drawdown (legacy
            # single-side saves only - gated to the primary side).
            if side == universe_primary_side():
                for res, per_min in (sval.get("adm_income") or {}).items():
                    _pool_add_f(side, res, float(per_min) * scale)
            continue
        reserves = sval.get("worldlet_reserves")
        have_res = isinstance(reserves, list)
        for entry in relay:
            if not isinstance(entry, dict):
                continue
            widx = entry.get("w")
            reserve = (reserves[widx] if (have_res and isinstance(widx, int)
                                          and 0 <= widx < len(reserves)) else None)
            for res, per_min in (entry.get("rate") or {}).items():
                amount = float(per_min) * scale
                if reserve is not None:
                    if reserve <= 0:
                        break
                    amount = min(amount, reserve)
                    reserve -= amount
                _pool_add_f(side, res, amount)
            if reserve is not None and have_res:
                reserves[widx] = max(0, reserve)


# --- Subsidy (resources -> crew prices; ADMIRAL_CONSOLE.md section 7) -----------
# The Admiral spends the side's stockpiles to discount station prices for the
# crews. The rate lives on the side agent as `market_subsidy` (0..subsidy_max) -
# the same value LM's items.market_price reads - so the console and the market
# are one number. Every econ tick pays the rate's resource upkeep; a dry pool
# drops the subsidy (the anti-snowball rail: no free-goods pipeline).
def admiralty_subsidy_rate(side):
    """The side's active crew subsidy (0..subsidy_max)."""
    sid = to_side_id(side)
    if sid is None:
        return 0.0
    try:
        rate = float(get_inventory_value(sid, "market_subsidy", 0.0) or 0.0)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(float(admiralty_tuning("subsidy_max", 0.3)), rate))


def admiralty_subsidy_cycle(side):
    """Advance the subsidy to the next tier (0 -> step -> ... -> max -> 0),
    the console's one-button control. Returns the new rate."""
    step = float(admiralty_tuning("subsidy_step", 0.1))
    cap = float(admiralty_tuning("subsidy_max", 0.3))
    if step <= 0:
        return 0.0
    rate = admiralty_subsidy_rate(side) + step
    if rate > cap + 1e-6:
        rate = 0.0
    set_inventory_value(to_side_id(side), "market_subsidy", round(rate, 4))
    return rate


def admiralty_subsidy_upkeep_text(side):
    """The current subsidy's per-minute upkeep as 'NN ore, NN gas' (console)."""
    rate = admiralty_subsidy_rate(side)
    if rate <= 0:
        return "none"
    parts = [str(int(round(v * rate))) + " " + r
             for r, v in SUBSIDY_UPKEEP_PER_MIN.items()]
    return ", ".join(parts) + " / min"


def admiralty_subsidy_upkeep(side, dt_seconds):
    """Pay this tick's subsidy upkeep. Returns a reason string if the subsidy
    lapsed (a pool ran dry -> dropped to 0), else None."""
    rate = admiralty_subsidy_rate(side)
    if rate <= 0:
        return None
    for res, per_min in SUBSIDY_UPKEEP_PER_MIN.items():
        if per_min > 0 and admiralty_pool_get(side, res) <= 0:
            set_inventory_value(to_side_id(side), "market_subsidy", 0.0)
            return "The stockpiles can't sustain the crew subsidy - discounts suspended."
    scale = rate * float(dt_seconds) / 60.0
    for res, per_min in SUBSIDY_UPKEEP_PER_MIN.items():
        _pool_add_f(side, res, -float(per_min) * scale)
    return None


def _pool_add_f(side, res, amount):
    """Fractional accumulation: pools are ints, so carry the remainder."""
    sid = to_side_id(side)
    frac = float(get_inventory_value(sid, "adm_frac_" + res, 0.0)) + float(amount)
    whole = int(frac)
    set_inventory_value(sid, "adm_frac_" + res, frac - whole)
    if whole:
        admiralty_pool_add(side, res, whole)


# --- Platforms -------------------------------------------------------------------
# Slice 1-2 platform set. Costs/build times are data here (an `## Platforms`
# AMD chapter can take over later without changing callers).
ADM_PLATFORMS = {
    "hq": {"name": "Headquarters", "cost": {"ore": 150, "crew": 15},
           "build_time": 30, "art": "starbase_command", "per_worldlet": False},
    "extractor": {"name": "Extractor", "cost": {"ore": 60, "crew": 5},
                  "build_time": 20, "art": "starbase_industry", "per_worldlet": True},
    # Refinery: boosts ITS worldlet's extraction and adds storage (slice 2).
    "refinery": {"name": "Refinery", "cost": {"ore": 100, "gas": 20},
                 "build_time": 30, "art": "starbase_civil", "per_worldlet": True},
    # Shipyard: the research site (universe_research.py); fleets form here.
    "shipyard": {"name": "Shipyard", "cost": {"ore": 200, "crew": 20},
                 "build_time": 45, "art": "starbase_science", "per_worldlet": False},
    # Academy: trains the officer roster (universe_fleets.py).
    "academy": {"name": "Academy", "cost": {"ore": 120, "crew": 10},
                "build_time": 35, "art": "starbase_command", "per_worldlet": False},
    # Bastion (slice 4): the static border answer - an armed fort at a
    # worldlet. Skirmish raids hit the Bastion first (universe_skirmish.py),
    # so the fight happens at the fort instead of the extractors.
    "bastion": {"name": "Bastion", "cost": {"ore": 220, "crew": 12},
                "build_time": 40, "art": "starbase_command", "per_worldlet": True},
    # Relay Gate (slice 4, OU): inter-system supply. A gated system keeps
    # feeding the pools while the flag is elsewhere (admiralty_relay_tick),
    # at the Relay rate. One per system (the live-object check's scope).
    "relay": {"name": "Relay Gate", "cost": {"ore": 400, "gas": 120, "crew": 20},
              "build_time": 60, "art": "starbase_science", "per_worldlet": False},
    # Depot (phase-2): a fleet supply anchor. Fleets within its supply radius
    # burn no gas (resupplied locally, universe_fleets.fleet_tick) - place them
    # to extend patrol range on the frontier without draining the stockpile.
    "depot": {"name": "Depot", "cost": {"ore": 160, "gas": 40, "crew": 10},
              "build_time": 35, "art": "starbase_industry", "per_worldlet": True},
    # Sensor Relay (phase-2): each one raises the side's command-point cap, so
    # the navy grows through infrastructure (admiralty_command_points). One per
    # worldlet, so they stack across the system. (Fog-of-war coverage - the
    # other CQ Sensor Tower role - is a carried gap.)
    "sensor": {"name": "Sensor Relay", "cost": {"ore": 200, "crew": 20},
               "build_time": 40, "art": "starbase_science", "per_worldlet": True},
    # Lab (phase-2): each Lab adds a concurrent research slot, so tech advances
    # in parallel (universe_research.research_slots). One per worldlet, stackable.
    "lab": {"name": "Lab", "cost": {"ore": 180, "crew": 20},
            "build_time": 40, "art": "starbase_science", "per_worldlet": True},
}

REFINERY_EXTRACT_MULT = 1.5   # a Refinery speeds its own worldlet's extraction
DEPOT_SUPPLY_RADIUS = 15000.0  # fleets within this of a friendly Depot burn no gas
SENSOR_COMMAND_POINTS = 1     # command points each Sensor Relay adds to the cap
REFINERY_STORAGE_BONUS = 400  # ...and adds silo capacity to the side
# Each Bastion mans a small squad of player-orderable defenders (LM prefab_npc_defender +
# friendly_give_orders) - the fort's living garrison, replenished by admiralty_bastion_-
# garrison_loop. NOT counted against fleet command points (static system defence, not the
# mobile navy).
BASTION_GARRISON_SIZE = 2


def admiralty_platform_def(kind):
    return ADM_PLATFORMS.get(kind)


def admiralty_platform_at(worldlet_obj, kind):
    """The side's platform of this kind at a worldlet, or None."""
    for plat in to_object_list(role("admiral_" + kind)):
        if plat.get_inventory_value("worldlet_id") == worldlet_obj.id:
            return plat
    return None


def admiralty_in_supply(side, x, z):
    """True if (x, z) is within a friendly Depot's supply radius - a fleet there
    is resupplied locally and burns no gas (universe_fleets.fleet_tick)."""
    r2 = DEPOT_SUPPLY_RADIUS * DEPOT_SUPPLY_RADIUS
    for depot in to_object_list(role("admiral_depot") & role(side)):
        dp = depot.pos
        if (x - dp.x) ** 2 + (z - dp.z) ** 2 <= r2:
            return True
    return False


def admiralty_platform_elsewhere(systems, kind, here_key, side):
    """The sector key ("i,j") of another system whose persistence delta already holds a
    platform of `kind` FOR `side`, or None. The HQ's campaign-uniqueness check - live
    objects only exist in LIVE systems, so uniqueness across the campaign must consult the
    systems delta (a despawned home still counts). Reads the PER-SIDE platform delta via
    _adm_platforms_for_side (the delta is {side: [...]}, with a legacy flat list = primary
    side); the old flat-list-only read silently missed every per-side save, so a second HQ
    could be founded anywhere."""
    if not isinstance(systems, dict):
        return None
    for skey, sval in systems.items():
        if skey == here_key or not isinstance(sval, dict):
            continue
        plats = _adm_platforms_for_side(sval.get("admiral_platforms"), side)
        if any(isinstance(p, dict) and p.get("k") == kind for p in plats):
            return skey
    return None


def admiralty_platform_location(side, kind, systems, here_key=None):
    """The system ("i,j") where `side` already has a `kind` platform - live in a system now,
    OR persisted in another system's delta - else None. This is the campaign-wide uniqueness
    reader for EVERY single-instance platform (HQ / Shipyard / Academy / Relay Gate): a
    live-only check breaks in the multi-cell model, where the system holding the platform
    despawns when the overseer leaves it. The live match ignores here_key (any live one
    blocks); the delta match excludes here_key (the current system's live platforms aren't
    in its delta)."""
    for p in to_object_list(role("admiral_" + kind) & role(side)):
        c = object_cell(p.id)
        return str(c[0]) + "," + str(c[1])
    return admiralty_platform_elsewhere(systems, kind, here_key, side)


def admiralty_side_has_hq(side, systems=None):
    """True if `side` has its Headquarters ANYWHERE in the campaign - live now or persisted
    in a delta. Multi-cell: home DESPAWNS when the overseer leaves it, so a live-only check
    wrongly reports 'no HQ' and blocks every build away from home."""
    return admiralty_platform_location(side, "hq", systems) is not None


# --- System control (Phase B: fleet-establishes-control) -------------------------
# Control is DERIVED, not stored: a side controls a system once it owns any admiral
# structure there. Structures already persist in the systems delta, so control
# survives save/load for free, and home is controlled the moment its HQ stands.
def admiralty_side_controls_cell(side, i, j):
    """True if `side` owns any admiral structure in cell (i, j) - i.e. controls it."""
    return len(objects_in_cell(to_object_list(role("admiral_platform") & role(side)), i, j)) > 0


def admiralty_cell_has_hostiles(side, i, j):
    """True if an armed foe HOSTILE TO `side` is contesting cell (i, j). Uses the
    raider foe-fleet tag intersected with the side's LIVE enemy set, so a clan you
    have ceasefired (now NEUTRAL, but still raider-tagged) no longer blocks a claim.
    `raider` scopes to actual combat fleets; side_enemy_members_set is the allegiance
    test. (PvP: a RIVAL admiral's adm_fleet doesn't count yet - a later refinement.)"""
    foes = role("raider") & side_enemy_members_set(side)
    return len(objects_in_cell(to_object_list(foes), i, j)) > 0


def admiralty_side_fleet_in_cell(side, i, j):
    """True if one of the side's own fleets is present in cell (i, j) - the fleet that
    holds a system while its first (claiming) structure is built."""
    return len(objects_in_cell(to_object_list(role("adm_fleet") & role(side)), i, j)) > 0


def admiralty_can_build(kind, side, worldlet_id, systems=None, here_key=None, need_cost=True):
    """Why a build is (None) or isn't (a reason string) allowed at a worldlet,
    WITHOUT spending. systems/here_key drive the HQ's campaign-wide uniqueness
    check. need_cost=False skips the affordability test - the build menu uses
    that so it lists everything currently UNLOCKED (prereqs met), and the button
    label carries the cost."""
    pdef = ADM_PLATFORMS.get(kind)
    wobj = to_object(worldlet_id)
    if pdef is None or wobj is None:
        return "Nothing selected."
    if wobj.get_inventory_value("building_" + kind, False):
        return pdef["name"] + " already under construction here."
    if pdef["per_worldlet"] and admiralty_platform_at(wobj, kind) is not None:
        return "This worldlet already has an " + pdef["name"] + "."
    # Single-instance platforms (HQ / Shipyard / Academy / Relay Gate) are campaign-unique:
    # blocked if the side already has one ANYWHERE - live now OR persisted in a despawned
    # system's delta (a live-only check wrongly allowed a second once its system despawned).
    if not pdef["per_worldlet"]:
        at = admiralty_platform_location(side, kind, systems, here_key)
        if at is not None:
            return "The " + pdef["name"] + " is already established in system (" + at.replace(",", ", ") + ")."
    if kind != "hq" and not admiralty_side_has_hq(side, systems):
        return "Requires a Headquarters."
    # Control gate (Phase B): in a system your side does not yet control, the first
    # structure IS the claim - it requires the system CLEARED of hostiles and one of
    # your FLEETS present to hold it while it builds. Once you own any structure here
    # the cell is controlled and you build freely. The HQ is exempt: it's the capital,
    # founded in your start system (which has no fleet yet).
    if kind != "hq":
        wc = object_cell(worldlet_id)
        if not admiralty_side_controls_cell(side, wc[0], wc[1]):
            if admiralty_cell_has_hostiles(side, wc[0], wc[1]):
                return "Clear the hostile forces before you can claim this system."
            if not admiralty_side_fleet_in_cell(side, wc[0], wc[1]):
                return "Bring a fleet here to hold the system while you build."
    if kind == "refinery" and admiralty_platform_at(wobj, "extractor") is None:
        return "Requires an Extractor at this worldlet."
    if need_cost and not admiralty_can_afford(side, pdef["cost"]):
        return "Not enough resources (" + admiralty_cost_text(kind) + ")."
    return None


def admiralty_buildable_kinds(side, worldlet_id, systems=None, here_key=None):
    """Platform kinds whose prereqs are met at a worldlet right now (ignoring
    cost), in ADM_PLATFORMS order - the console build menu. The list shrinks as
    you build (HQ drops out once placed; a per-worldlet platform drops once this
    worldlet has it), so the menu guides rather than dumping every button."""
    return [kind for kind in ADM_PLATFORMS
            if admiralty_can_build(kind, side, worldlet_id, systems, here_key,
                                   need_cost=False) is None]


def admiralty_buildable_items(side, worldlet_id, systems=None, here_key=None):
    """Buildable platforms as listbox items (key/name/cost) for the Map-tab build
    list - a scrollable list beats a stack of buttons when many are unlocked."""
    out = []
    for kind in admiralty_buildable_kinds(side, worldlet_id, systems, here_key):
        pdef = ADM_PLATFORMS.get(kind) or {}
        out.append(MastDataObject({"key": kind, "name": pdef.get("name"),
                                   "cost": admiralty_cost_text(kind)}))
    return out


def build_list_title():
    gui_row("row-height: 1.2em;padding:6px;background:#1578;")
    gui_text("$text:Build here")


def build_list_template(item):
    gui_row("row-height: 2.2em;")
    gui_text("$text:" + str(item.get("name")) + "   (" + str(item.get("cost")) + ");font:gui-1")


def admiralty_try_build(kind, side, worldlet_id, systems=None, here_key=None):
    """Validate + pay for a build at a worldlet. Returns None on success (cost
    deducted, in-progress flag set - the caller schedules the build task), or a
    short reason string. Shares its checks with admiralty_can_build."""
    reason = admiralty_can_build(kind, side, worldlet_id, systems, here_key, need_cost=True)
    if reason is not None:
        return reason
    admiralty_spend(side, ADM_PLATFORMS[kind]["cost"])
    to_object(worldlet_id).set_inventory_value("building_" + kind, True)
    return None


def admiralty_command_points(side):
    """The side's fleet cap: the base `command_points` tuning plus each Sensor
    Relay's grant. The navy grows through infrastructure - build Sensor Relays
    to field more fleets. Read by the ticker and the fleet-form cap check."""
    base = int(admiralty_tuning("command_points", 0))
    relays = len(to_object_list(role("admiral_sensor") & role(side)))
    return base + relays * SENSOR_COMMAND_POINTS


def admiralty_build_record(kind, worldlet_id, side=None):
    """A build-queue entry the overseer can read cleanly: name + where + eta (sim
    seconds at completion). Replaces the old bare 'Name at Where' string so the queue
    can show per-build progress with several builds running at once. kind/side/
    worldlet_id + the `cancel` flag let the console cancel a queued build: the build
    task polls `cancel` and refunds via admiralty_build_cancel."""
    pdef = ADM_PLATFORMS.get(kind) or {}
    wobj = to_object(worldlet_id)
    where = str(wobj.name) if (wobj is not None and wobj.name) else "the works"
    return MastDataObject({"name": pdef.get("name", kind), "where": where,
                           "eta": FrameContext.sim_seconds + float(pdef.get("build_time", 0)),
                           "kind": kind, "side": side, "worldlet_id": worldlet_id,
                           "cancel": False})


def admiralty_build_cancel(kind, side, worldlet_id):
    """Undo a cancelled build: refund its full cost to the side pools and clear the
    worldlet's in-progress flag so the platform can be rebuilt. The build task itself
    removes the queue record and stops; this just reverses the spend + reservation."""
    pdef = ADM_PLATFORMS.get(kind) or {}
    for res, amt in (pdef.get("cost") or {}).items():
        admiralty_pool_add(side, res, int(amt))
    wobj = to_object(worldlet_id)
    if wobj is not None:
        wobj.set_inventory_value("building_" + kind, False)


def admiralty_build_queue_text(builds, now):
    """A clear multi-build queue readout - 'Building 2: Extractor - Cinder World
    (12s), Refinery - Veiled Giant (5s)' - with each build's name, worldlet, and
    time remaining. Pure (now = sim seconds passed in) so it unit-tests; the panel
    reads FrameContext.sim_seconds. Tolerates legacy bare-string entries."""
    rows = []
    for b in builds:
        if isinstance(b, str):
            rows.append(b)
            continue
        rem = int(max(0, float(b.get("eta", now)) - now))
        rows.append(b.get("name", "?") + " - " + b.get("where", "?") + " (" + str(rem) + "s)")
    return "Building " + str(len(rows)) + ": " + ", ".join(rows)


def admiralty_status_change_key(builds, last_msg):
    """The overseer status panel's `on change` key. Changes every SECOND while builds
    are queued (so the countdown ticks live), and only on build count / last-message
    otherwise (no idle repaints). Keep the panel's `on change` and its repaint reading
    the same admiralty_status_line, so what triggers the repaint and what it shows agree."""
    base = str(len(builds)) + "|" + str(last_msg)
    if builds:
        return base + "|" + str(int(FrameContext.sim_seconds))
    return base


def admiralty_status_line(builds, last_msg):
    """The overseer's status/queue line. Active builds take priority (a live queue -
    what the yards are working on); else the last action result (a build/commission
    confirmation or a rejection reason); else idle. `builds` is the shared ADM_BUILDS
    list, `last_msg` the shared ADM_LAST_MSG - passed in so this stays pure Python."""
    if builds:
        return admiralty_build_queue_text(builds, FrameContext.sim_seconds)
    # No income source is worth flagging over a stale last-action line: the HQ is
    # only a hub, the Extractor is what actually produces (the discoverability gap
    # that had ore/gas going nowhere). Clears itself once an extractor exists.
    if not to_object_list(role("admiral_extractor")):
        return "No extractors yet - build an Extractor on a worldlet to produce ore and gas."
    if last_msg:
        return last_msg
    return "Shipyards standing by - select a worldlet or platform to command."


def admiralty_build_queue_area(builds, last_msg):
    """Multi-line queue readout for a gui_text_area: ONE build per line (a scrollable
    list instead of one cramped string), so the overseer sees everything in flight.
    Active builds take priority; otherwise the same idle / last-action text as
    admiralty_status_line. Reads FrameContext.sim_seconds for the live countdown."""
    now = FrameContext.sim_seconds
    if builds:
        lines = ["$t Build Queue (" + str(len(builds)) + ")", ""]
        for b in builds:
            if isinstance(b, str):
                lines.append("- " + b)
                continue
            rem = int(max(0, float(b.get("eta", now)) - now))
            lines.append("- " + b.get("name", "?") + " - " + b.get("where", "?") + " (" + str(rem) + "s)")
        return "\n".join(lines)
    if not to_object_list(role("admiral_extractor")):
        return "No extractors yet - build an Extractor on a worldlet to produce ore and gas."
    if last_msg:
        return str(last_msg)
    return "Shipyards standing by - select a worldlet or platform to command."


# --- Selectable build-queue listbox (cancel a queued build) --------------------
def admiralty_build_title():
    gui_row("row-height: 1.2em; padding:6px; background:#1578;")
    gui_text("$text:Build Queue")


def admiralty_build_row(item):
    """One queue row: name - worldlet. No live countdown - updating it would force a
    listbox repaint each tick, which made the list un-clickable. Tolerates legacy
    string entries (research runs), which aren't cancellable here."""
    gui_row("row-height: 1.8em;")
    if isinstance(item, str):
        gui_text("$text:" + item + ";font:gui-1")
        return
    gui_text("$text:" + item.get("name", "?") + " - " + item.get("where", "?") + ";font:gui-1")


def admiralty_build_count_key(builds, last_msg):
    """Repaint key for the selectable queue listbox: changes ONLY when a build is
    added or removed (or the last-action message changes) - never on a timer, so the
    list stays clickable. (A periodic countdown repaint rebuilt the list mid-click and
    made it unusable.)"""
    return str(len(builds)) + "|" + str(last_msg)


def admiralty_status_hint(builds, last_msg):
    """The action/idle line ABOVE the queue list (the list itself shows active
    builds). Last action result, else the no-extractor nudge, else an idle prompt."""
    if not to_object_list(role("admiral_extractor")):
        return "No extractors yet - build an Extractor on a worldlet to produce ore and gas."
    if last_msg:
        return str(last_msg)
    return "Select a worldlet or platform to command."


def admiralty_scan_theatre(side):
    """Mark the side's own theatre - the worldlets it can develop, its stations,
    its fleets - as scanned for the WHOLE side, so the Admiral's overseer can open
    comms on them (the engine won't enable comms on an object the origin holds no
    science data for). science_set_scan_data keys the data on the origin's side
    (universe: side-wide scan), so ONE pass here covers every console on the side -
    no per-client loop. Any tsn object serves as origin; the home starbase always
    qualifies. Stopgap until the engine can mark a side's own objects known."""
    # role(side) also contains console clients (base Agents that carry the side
    # role but have no .side - e.g. the server, Agent 0). Don't assume origins[0]
    # is a sided space object; use the first member that actually has a side.
    origin = None
    for _o in to_object_list(role(side)):
        if getattr(_o, "side", None) is not None:
            origin = _o
            break
    if origin is None:
        return
    targets = to_object_list(role("worldlet"))
    targets += to_object_list(role("adm_fleet") & role(side))
    targets += to_object_list(role("admiral_platform") & role(side))
    targets += to_object_list(role("station") & role(side))
    for t in targets:
        science_set_scan_data(origin, t.id, "Admiralty Scan")


def admiralty_build_done(kind, side, worldlet_id):
    """Finish a build: clear the in-progress flag and spawn the platform.
    Called by admiral.mast's build task after the build_time delay."""
    wobj = to_object(worldlet_id)
    if wobj is None:
        return None
    wobj.set_inventory_value("building_" + kind, False)
    return universe_platform_spawn(kind, side, wobj)


def admiralty_cost_text(kind):
    """'60 ore, 5 crew' for a platform's cost line."""
    pdef = ADM_PLATFORMS.get(kind) or {}
    return ", ".join(str(v) + " " + k for k, v in (pdef.get("cost") or {}).items())


# --- Console GUI helpers (admiral.mast) -------------------------------------------
def admiralty_ticker_text(side):
    """The resource bar line: 'ORE 240/600   GAS 96/600   CREW 40/600   CMD 1/3'.
    CMD used = live fleets (fleet_count is a shared-namespace call into
    universe_fleets.py)."""
    p = admiralty_pools(side)
    cmd_max = admiralty_command_points(side)
    parts = []
    for res in ADM_RESOURCES:
        parts.append(res.upper() + " " + str(p[res]) + "/" + str(admiralty_pool_cap(side, res)))
    return "   ".join(parts) + "   CMD " + str(fleet_count()) + "/" + str(cmd_max)


def admiralty_debug_pace_text(side):
    """TEMP DIAGNOSTIC (remove after verifying): the mode + economy pace actually in
    effect at runtime, with the yield/start multipliers. Brisk should read
    '[skirmish/brisk y2.0 s1.5]'; a fallback to '[.../standard y1.0 s1.0]' means the
    Mode->brisk wiring didn't take, which doubles every economy timer."""
    pace = str(admiralty_tuning("economy_pace", "standard"))
    return ("[" + mission_mode() + "/" + pace
            + " y" + str(economy_pace_mult("yield"))
            + " s" + str(economy_pace_mult("start")) + "]")


def admiralty_platform_status_text(obj):
    """A one-line status readout for a platform, shown when the Admiral hails it.
    Every platform answers a hail (no dead clicks); passive infrastructure has no
    action menu, so this IS its interaction. Kind-specific detail where it helps."""
    if obj is None:
        return "Platform not found."
    kind = obj.get_inventory_value("admiral_kind", None) or "platform"
    pdef = ADM_PLATFORMS.get(kind) or {}
    name = pdef.get("name", kind)
    wid = obj.get_inventory_value("worldlet_id", None)
    wobj = to_object(wid) if wid is not None else None
    wname = wobj.name if (wobj is not None and wobj.name) else "the worldlet"
    if kind == "extractor" and wobj is not None:
        yields = wobj.get_inventory_value("worldlet_yields", {}) or {}
        reserve = wobj.get_inventory_value("worldlet_reserve", None)
        ytxt = ", ".join(str(v) + "/min " + k for k, v in yields.items()) or "nothing"
        rtxt = "unlimited" if reserve is None else str(int(reserve))
        return name + " online. Mining " + wname + " (" + ytxt + "). Reserve: " + rtxt + "."
    if kind == "refinery":
        return name + " online at " + wname + ". Boosting extraction and adding storage."
    if kind == "academy":
        return name + " online. Training the officer roster for the shipyard."
    if kind == "bastion":
        return name + " standing watch over " + wname + ". Raids strike here first."
    if kind == "depot":
        return name + " online. Fleets in range resupply and burn no gas."
    if kind == "sensor":
        return name + " online. Sensor coverage extended; command-point cap raised."
    if kind == "relay":
        return name + " online. Relaying this system's income while the flag is away."
    return name + " online and operational."


def worldlet_list_title():
    gui_row("row-height: 1.2em;padding:6px;background:#1578;")
    gui_text("$text:Worldlets in this system")


def worldlet_list_template(item):
    """One listbox row: name, type, yields, reserve state."""
    wt, yields, reserve = worldlet_info(item)
    tname = wt.get("name") if wt is not None else "?"
    ytext = " ".join(k + " " + str(v) for k, v in (yields or {}).items())
    rtext = "unlimited" if reserve is None else (str(int(reserve)) if reserve > 0 else "DEPLETED")
    gui_row("row-height: 2.2em;")
    gui_text("$text:" + str(item.name) + "  (" + str(tname) + ")  " + ytext +
             " /min   reserve " + rtext + ";font:gui-1")


def worldlet_sel_text(worldlet_id, side):
    """The selected-worldlet context panel body (one string, ^-separated lines
    for $text)."""
    wobj = to_object(worldlet_id)
    if wobj is None:
        return "Nothing selected."
    wt, yields, reserve = worldlet_info(wobj)
    lines = [str(wobj.name)]
    if wt is not None:
        lines.append(str(wt.get("name")))
    lines.append("Yields " + " ".join(k + " " + str(v) for k, v in (yields or {}).items()) + " per min per extractor")
    lines.append("Reserve " + ("unlimited" if reserve is None else str(int(reserve))))
    plats = []
    for kind in ADM_PLATFORMS:
        if wobj.get_inventory_value("building_" + kind, False):
            plats.append(ADM_PLATFORMS[kind]["name"] + " (building)")
        elif admiralty_platform_at(wobj, kind) is not None:
            plats.append(ADM_PLATFORMS[kind]["name"])
    lines.append("Platforms " + (", ".join(plats) if plats else "none"))
    return "^".join(lines)


def universe_platform_spawn(kind, side, worldlet_obj):
    """Spawn a finished platform of `kind` beside a worldlet for `side`.
    (Build cost/time are handled by the caller - admiral.mast's build task.)"""
    pdef = ADM_PLATFORMS.get(kind)
    if pdef is None or worldlet_obj is None:
        return None
    pos = worldlet_obj.pos
    off = float(worldlet_obj.get_inventory_value("worldlet_radius", 400)) + 900
    # Orbit: space platforms evenly around the worldlet in its XZ plane at radius `off`,
    # instead of stacking them all at one point. The slot is the count already orbiting
    # this worldlet (any side); the golden angle (~137.5 deg) fills the largest gap each
    # time, so the ring stays nicely spread no matter how many build.
    slot = 0
    for o in to_object_list(role("admiral_platform")):
        if o.get_inventory_value("worldlet_id", 0) == worldlet_obj.id:
            slot += 1
    ang = slot * 2.399963229728653   # golden angle (radians)
    px = pos.x + off * math.cos(ang)
    pz = pos.z + off * math.sin(ang)
    name = (worldlet_obj.name + " " + pdef["name"]) if worldlet_obj.name else pdef["name"]
    # No `station` role: it would pull in LM's default station comms (docking/market
    # /hail) on top of the Admiral's own platform menus. These are Admiral
    # infrastructure, commanded only through the admiral_* routes, so we tag them
    # admiral_platform + admiral_<kind> and leave `station` off. (behav_station still
    # gives them station physics/behaviour - the role is only a query/comms tag.)
    roles = side + ", admiral_platform, admiral_" + kind
    co = npc_spawn(px, pos.y, pz, name, roles, pdef["art"], "behav_station")
    # The engine also derives `station` from the starbase ART's ship data, so the
    # role string alone won't keep it off - strip it explicitly after the spawn.
    remove_role(co, "station")
    if kind == "bastion":
        # Legible-over-pretty (section 9): the fort reads bigger than the works.
        for ax in ("x", "y", "z"):
            co.data_set.set("local_scale_" + ax + "_coeff", 1.5)
    py = co.py_object
    py.set_inventory_value("worldlet_id", worldlet_obj.id)
    py.set_inventory_value("admiral_kind", kind)
    # The side's FIRST HQ is its capital (FIXED - decapitation targets this one):
    # tag it admiral_home_hq + a side-specific <side>_capital role so a victory quest
    # can target it directly (`destroy 1 orion_capital` = the quick-win shortcut).
    # The watcher's elimination is a separate, HQ-count-based conquest condition, so
    # losing the capital is only decisive if an author wrote a decapitation quest.
    if kind == "hq" and len(to_object_list(role("admiral_home_hq") & role(side))) == 0:
        add_role(py, "admiral_home_hq")
        add_role(py, side + "_capital")
    # Mark the finished platform known to its OWN side immediately, so the Admiral
    # console can open comms on it right away instead of waiting up to a full econ
    # tick for the next admiralty_scan_theatre pass (the engine won't open comms on
    # an object the side holds no science data for). Origin = any sided object of the
    # side (the HQ that gated this build always qualifies).
    for _sorg in to_object_list(role(side)):
        if getattr(_sorg, "side", None) is not None:
            science_set_scan_data(_sorg, co.id, "Admiralty Scan")
            break
    return py
