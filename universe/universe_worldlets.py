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
from sbs_utils.mast.mast_node import MastDataObject
from sbs_utils.procedural.spawn import terrain_spawn, npc_spawn
from sbs_utils.procedural.inventory import get_inventory_value, set_inventory_value
from sbs_utils.procedural.sides import to_side_id
from sbs_utils.procedural.roles import role, has_role
from sbs_utils.procedural.query import to_object_list, to_object
from sbs_utils.procedural.gui import gui_row, gui_text
from sbs_utils.helpers import FrameContext

ADM_RESOURCES = ["ore", "gas", "crew"]

# Built-in Admiralty tuning; a universe's ## Admiralty fence overrides any knob.
_ADM_DEFAULTS = {
    "start_ore": 200, "start_gas": 100, "start_crew": 40,
    "command_points": 3, "fleet_gas_burn": 2,
    "requisition_budget": 800,
    "skirmish_pressure": "border",
    "research_pace": "campaign",
}

# Live per-load registries (reset by *_configure on universe load, mirroring
# generation_configure / regions_configure).
_WORLDLET_TYPES = {}
_ADM = dict(_ADM_DEFAULTS)
_ADM_ACTIVE = False


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


def universe_admiralty_cfg(doc):
    """The `## Admiralty` chapter's tuning dict, or None when absent. Also
    carries any generation keys authored there (Worldlet chance)."""
    section = universe_section(doc, "admiralty")
    if section is None:
        return None
    data = section.get("data") or {}
    cfg = dict(data.get("admiralty") or {})
    gen = data.get("generation") or {}
    if "worldlet" in gen:
        cfg["worldlet_chance"] = gen["worldlet"]
    return cfg


def admiralty_configure(cfg):
    """Apply a universe's Admiralty tuning (resets to defaults first). The
    Admiral game is active only when a universe authors an Admiralty chapter
    AND at least one worldlet type - legacy universes are untouched. The
    Worldlet chance dial is pushed into the generation registry so the POI
    deck sees it (generation_set lives in universe_helpers)."""
    global _ADM, _ADM_ACTIVE
    _ADM = dict(_ADM_DEFAULTS)
    _ADM_ACTIVE = cfg is not None and bool(_WORLDLET_TYPES)
    if cfg:
        for k, v in cfg.items():
            if k != "worldlet_chance":
                _ADM[k] = v
        if _ADM_ACTIVE and "worldlet_chance" in cfg:
            generation_set("worldlet", cfg["worldlet_chance"])


def admiralty_active():
    return _ADM_ACTIVE


def admiralty_tuning(name, default=None):
    return _ADM.get(name, _ADM_DEFAULTS.get(name, default))


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
    r = float(radius if radius is not None else 400)
    co.engine_object.exclusion_radius = r
    ds = co.data_set
    sim = FrameContext.sim
    if sim is not None:
        ds.set("planet_last_changed", sim.time_tick_counter, 0)
    ds.set("planet_radius", r / 2.0, 0)
    pal = wt.get("palette") or {}
    _set_planet_color(ds, "planet_baseColor", pal.get("base"))
    _set_planet_color(ds, "planet_emissiveColor", pal.get("emissive"))
    _set_planet_color(ds, "planet_upperCloudColor", pal.get("clouds"))
    if pal.get("bands") is not None:
        ds.set("planet_bandScale", float(pal.get("bands")), 0)
    py = co.py_object
    py.set_inventory_value("worldlet_type", type_key)
    py.set_inventory_value("worldlet_radius", r)
    py.set_inventory_value("worldlet_yields", dict(wt.get("yields") or {}))
    py.set_inventory_value("worldlet_reserve", wt.get("reserve"))
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
    """All live worldlet objects (the current system - only one system exists)."""
    return to_object_list(role("worldlet"))


# --- Side resource pools --------------------------------------------------------
def admiralty_pool_get(side, res):
    return int(get_inventory_value(to_side_id(side), "adm_" + res, 0))


def admiralty_pool_set(side, res, value):
    set_inventory_value(to_side_id(side), "adm_" + res, max(0, int(value)))


def admiralty_pool_add(side, res, delta):
    admiralty_pool_set(side, res, admiralty_pool_get(side, res) + int(delta))


def admiralty_pools(side):
    return {r: admiralty_pool_get(side, r) for r in ADM_RESOURCES}


def admiralty_seed_pools(side):
    """Seed a side's starting stockpiles once per campaign (guarded)."""
    sid = to_side_id(side)
    if get_inventory_value(sid, "adm_seeded", False):
        return
    set_inventory_value(sid, "adm_seeded", True)
    for res in ADM_RESOURCES:
        admiralty_pool_set(side, res, admiralty_tuning("start_" + res, 0))


def admiralty_spend(side, cost):
    """Deduct a {res: amount} cost if affordable; True on success."""
    cost = cost or {}
    for res, amt in cost.items():
        if admiralty_pool_get(side, res) < int(amt):
            return False
    for res, amt in cost.items():
        admiralty_pool_add(side, res, -int(amt))
    return True


# --- Extraction ----------------------------------------------------------------
def admiralty_extraction_tick(side, dt_seconds):
    """One economy tick: every extractor platform pulls its worldlet's Yields
    (per-minute rates) into the side pools, draining a finite Reserve. A dry
    worldlet stops producing (its extractors idle). Called from admiral.mast."""
    if not _ADM_ACTIVE:
        return
    scale = float(dt_seconds) / 60.0
    for plat in to_object_list(role("admiral_extractor")):
        if not has_role(plat.id, side):
            continue
        wid = plat.get_inventory_value("worldlet_id")
        wobj = to_object(wid) if wid is not None else None
        if wobj is None:
            continue
        yields = wobj.get_inventory_value("worldlet_yields", {}) or {}
        reserve = wobj.get_inventory_value("worldlet_reserve")
        for res, per_min in yields.items():
            amount = float(per_min) * scale
            if reserve is not None:
                if reserve <= 0:
                    break
                amount = min(amount, reserve)
                reserve -= amount
            _pool_add_f(side, res, amount)
        if reserve is not None:
            wobj.set_inventory_value("worldlet_reserve", max(0, reserve))


def _pool_add_f(side, res, amount):
    """Fractional accumulation: pools are ints, so carry the remainder."""
    sid = to_side_id(side)
    frac = float(get_inventory_value(sid, "adm_frac_" + res, 0.0)) + float(amount)
    whole = int(frac)
    set_inventory_value(sid, "adm_frac_" + res, frac - whole)
    if whole:
        admiralty_pool_add(side, res, whole)


# --- Platforms -------------------------------------------------------------------
# Slice-1 platform set: HQ + Extractor. Costs/build times are data here (an
# `## Platforms` AMD chapter can take over later without changing callers).
ADM_PLATFORMS = {
    "hq": {"name": "Headquarters", "cost": {"ore": 150, "crew": 15},
           "build_time": 30, "art": "starbase_command", "per_worldlet": False},
    "extractor": {"name": "Extractor", "cost": {"ore": 60, "crew": 5},
                  "build_time": 20, "art": "starbase_industry", "per_worldlet": True},
}


def admiralty_platform_def(kind):
    return ADM_PLATFORMS.get(kind)


def admiralty_platform_at(worldlet_obj, kind):
    """The side's platform of this kind at a worldlet, or None."""
    for plat in to_object_list(role("admiral_" + kind)):
        if plat.get_inventory_value("worldlet_id") == worldlet_obj.id:
            return plat
    return None


def admiralty_try_build(kind, side, worldlet_id):
    """Validate + pay for a build at a worldlet. Returns None on success (cost
    deducted, in-progress flag set - the caller schedules the build task), or
    a short reason string for the console to show."""
    pdef = ADM_PLATFORMS.get(kind)
    wobj = to_object(worldlet_id)
    if pdef is None or wobj is None:
        return "Nothing selected."
    if wobj.get_inventory_value("building_" + kind, False):
        return pdef["name"] + " already under construction here."
    if pdef["per_worldlet"] and admiralty_platform_at(wobj, kind) is not None:
        return "This worldlet already has an " + pdef["name"] + "."
    if not pdef["per_worldlet"] and len(to_object_list(role("admiral_" + kind) & role(side))) > 0:
        return "The " + pdef["name"] + " is already built."
    if kind != "hq" and len(to_object_list(role("admiral_hq") & role(side))) == 0:
        return "Requires a Headquarters."
    if not admiralty_spend(side, pdef["cost"]):
        return "Not enough resources (" + admiralty_cost_text(kind) + ")."
    wobj.set_inventory_value("building_" + kind, True)
    return None


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
    """The resource bar line: 'ORE 240   GAS 96   CREW 40   CMD 0/3'."""
    p = admiralty_pools(side)
    cmd_max = admiralty_tuning("command_points", 0)
    return ("ORE " + str(p["ore"]) + "   GAS " + str(p["gas"]) +
            "   CREW " + str(p["crew"]) + "   CMD 0/" + str(cmd_max))


def worldlet_list_title():
    gui_row("row-height: 1.2em;padding:6px;background:#1578;")
    gui_text("$text:Worldlets in this system;justify:left;")


def worldlet_list_template(item):
    """One listbox row: name, type, yields, reserve state."""
    wt, yields, reserve = worldlet_info(item)
    tname = wt.get("name") if wt is not None else "?"
    ytext = " ".join(k + " " + str(v) for k, v in (yields or {}).items())
    rtext = "unlimited" if reserve is None else (str(int(reserve)) if reserve > 0 else "DEPLETED")
    gui_row("row-height: 2.2em;")
    gui_text("$text:" + str(item.name) + "  (" + str(tname) + ")  " + ytext +
             " /min   reserve " + rtext + ";justify:left;font:gui-1")


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
    name = (worldlet_obj.name + " " + pdef["name"]) if worldlet_obj.name else pdef["name"]
    roles = side + ", station, admiral_platform, admiral_" + kind
    co = npc_spawn(pos.x + off, pos.y, pos.z, name, roles, pdef["art"], "behav_station")
    py = co.py_object
    py.set_inventory_value("worldlet_id", worldlet_obj.id)
    py.set_inventory_value("admiral_kind", kind)
    return py
