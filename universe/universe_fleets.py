"""Officers + Admiral fleets for the Open Universe (slice 3 - see
ADMIRAL_CONSOLE.md section 6).

Officers are the Academy roster (`## Officers` in the universe AMD): named
captains whose reputation-pole Values grant fleet bonuses - by-the-book runs
leaner (gas), resourceful salvages richer, fearsome engages farther. This is
CQ's six-admirals pattern transplanted onto the reputation poles.

A fleet = one officer + a small hull roster, commissioned at a Shipyard and
capped by command points. Orders are a fixed verb set (escort / patrol /
strike / hold / salvage / withdraw); each order is executed by fleet_tick
(called on a cadence from admiral.mast) using the target/target_pos
primitives - deliberately NOT a brain tree, so slice 3 stays self-contained.
Every non-hold order burns gas (Fleet gas burn per minute, officer-scaled);
an empty tank forces hold.

Fleets are per-session (not persisted) - a jump clears NPCs, so fleets live
in the current system only for now (carried gap).

Shared-namespace notes: universe_section from universe_clans.py; admiralty_*
pool/tuning from universe_worldlets.py.
"""
import math
from sbs_utils.mast.mast_node import MastDataObject
from sbs_utils.procedural.spawn import npc_spawn
from sbs_utils.procedural.inventory import get_inventory_value, set_inventory_value
from sbs_utils.procedural.sides import to_side_id
from sbs_utils.procedural.roles import role
from sbs_utils.procedural.query import to_object_list, to_object
from sbs_utils.procedural.space_objects import (closest_object, target, target_pos,
                                                delete_object)
from sbs_utils.procedural.gui import gui_row, gui_text

# The commissionable hull roster (data - difficulty/length tuning later).
FLEET_ROSTER = [
    ("tsn_light_cruiser", "Escort"),
    ("tsn_light_cruiser", "Escort"),
    ("tsn_battle_cruiser", "Line"),
]
FLEET_COST = {"ore": 180, "gas": 40, "crew": 24}

FLEET_ORDERS = ["escort", "patrol", "strike", "hold", "salvage", "withdraw"]

_OFFICERS = {}     # key -> authored record
_FLEETS = {}       # fleet key ("f1"...) -> live state (MastDataObject)
_NEXT_FLEET = [1]


# --- Officers (## Officers) ---------------------------------------------------
def universe_parse_officers(doc):
    """Officer records from the `## Officers` chapter (empty if none)."""
    section = universe_section(doc, "officers")
    out = []
    if section is not None:
        for n in section.get("children", []):
            data = n.get("data") or {}
            out.append(MastDataObject({
                "key": n.get("key"),
                "name": n.get("display_text"),
                "title": data.get("title") or "",
                "desc": (n.get("description") or "").strip(),
                "leans": data.get("leans") or {},
                "face": data.get("face"),
            }))
    return out


def officers_configure(officers):
    global _OFFICERS, _FLEETS, _NEXT_FLEET
    _OFFICERS = {o.get("key"): o for o in (officers or [])}
    _FLEETS = {}
    _NEXT_FLEET = [1]


def officer_def(key):
    return _OFFICERS.get(key)


def officer_list():
    return list(_OFFICERS.values())


def officer_fleet(key):
    """The fleet this officer commands, or None (available)."""
    for f in _FLEETS.values():
        if f.get("officer") == key:
            return f
    return None


def officer_bonus(key, kind):
    """A trait-derived multiplier. Linear in the pole weight, so the authored
    Values ARE the tuning: by_the_book 40 -> gas x0.8; resourceful 40 ->
    salvage x1.5; fearsome 40 -> engage range x1.4."""
    o = _OFFICERS.get(key)
    leans = (o.get("leans") if o else None) or {}
    if kind == "gas":
        return max(0.5, 1.0 - leans.get("by_the_book", 0) * 0.005)
    if kind == "salvage":
        return 1.0 + leans.get("resourceful", 0) * 0.0125
    if kind == "engage":
        return 1.0 + leans.get("fearsome", 0) * 0.01
    return 1.0


# --- Fleets ---------------------------------------------------------------------
def fleet_list():
    return list(_FLEETS.values())


def fleet_get(key):
    return _FLEETS.get(key)


def fleet_count():
    return len(_FLEETS)


def fleet_ships(fleet_key):
    return to_object_list(role("adm_" + fleet_key))


def fleet_cost_text():
    return ", ".join(str(v) + " " + k for k, v in FLEET_COST.items())


def fleet_try_form(side, officer_key):
    """Validate + pay for a fleet. Returns None on success (hulls spawned at
    the Shipyard, officer assigned) or a short reason string."""
    o = _OFFICERS.get(officer_key)
    if o is None:
        return "No such officer."
    if officer_fleet(officer_key) is not None:
        return o.get("name") + " already commands a fleet."
    if len(to_object_list(role("admiral_academy") & role(side))) == 0:
        return "Requires an Academy."
    yards = to_object_list(role("admiral_shipyard") & role(side))
    if len(yards) == 0:
        return "Requires a Shipyard."
    if fleet_count() >= int(admiralty_tuning("command_points", 0)):
        return "No command points free."
    if not admiralty_spend(side, FLEET_COST):
        return "Not enough resources (" + fleet_cost_text() + ")."
    fkey = "f" + str(_NEXT_FLEET[0])
    _NEXT_FLEET[0] += 1
    ypos = yards[0].pos
    for idx, (hull, hull_name) in enumerate(FLEET_ROSTER):
        ang = idx * 2.4
        name = "Fleet " + fkey.upper() + " " + hull_name + " " + str(idx + 1)
        npc_spawn(ypos.x + 1200 + 700 * math.cos(ang), ypos.y,
                  ypos.z + 1200 + 700 * math.sin(ang),
                  name, side + ", adm_fleet, adm_" + fkey, hull, "behav_npcship")
    _FLEETS[fkey] = MastDataObject({
        "key": fkey, "side": side, "officer": officer_key,
        "order": "hold", "gas_starved": False})
    return None


def fleet_set_order(fleet_key, order):
    """Set a fleet's order. Returns the officer's acknowledgment line (or an
    empty string if the fleet is gone)."""
    f = _FLEETS.get(fleet_key)
    if f is None or order not in FLEET_ORDERS:
        return ""
    setattr(f, "order", order)
    setattr(f, "gas_starved", False)
    o = _OFFICERS.get(f.get("officer")) or {}
    acks = {
        "escort": "Falling in on your wing.",
        "patrol": "Sweeping the system.",
        "strike": "Weapons free. Moving to engage.",
        "hold": "Holding position.",
        "salvage": "Stripping the wrecks.",
        "withdraw": "Coming home.",
    }
    return str(o.get("name", "Fleet")) + ": " + acks.get(order, "Acknowledged.")


def _fleet_home_pos(side):
    """Where withdraw goes: the HQ, else origin."""
    hqs = to_object_list(role("admiral_hq") & role(side))
    return hqs[0].pos if hqs else None


def fleet_tick(fleet_key, dt_seconds):
    """One order step for one fleet. Returns an event string for the console/
    comms (fleet lost, salvage award, gas empty), or None."""
    f = _FLEETS.get(fleet_key)
    if f is None:
        return None
    side = f.get("side")
    ships = fleet_ships(fleet_key)
    o = _OFFICERS.get(f.get("officer")) or {}
    if len(ships) == 0:
        del _FLEETS[fleet_key]
        return str(o.get("name", "A fleet officer")) + ": we've lost the fleet. I'm sorry, Admiral."
    order = f.get("order", "hold")

    # Gas: every non-hold order burns fuel (per minute, officer-scaled).
    if order != "hold":
        burn = float(admiralty_tuning("fleet_gas_burn", 2)) * officer_bonus(f.get("officer"), "gas")
        need = burn * float(dt_seconds) / 60.0
        if admiralty_pool_get(side, "gas") <= 0:
            setattr(f, "order", "hold")
            if not f.get("gas_starved"):
                setattr(f, "gas_starved", True)
                return str(o.get("name", "Fleet")) + ": tanks are dry - holding until we get gas."
            return None
        _pool_add_f(side, "gas", -need)

    ids = set(s.id for s in ships)
    lead = ships[0]
    engage = 6000.0 * officer_bonus(f.get("officer"), "engage")
    hostiles = role("raider")

    if order == "escort":
        players = to_object_list(role("__player__"))
        if not players:
            return None
        ward = players[0]
        threat = closest_object(ward, hostiles, max_dist=engage)
        if threat is not None:
            target(ids, threat.id, True, 1.0)
        else:
            target_pos(ids, ward.pos.x + 900, ward.pos.y, ward.pos.z + 900,
                       1.0, stop_dist=800)
    elif order == "patrol":
        threat = closest_object(lead, hostiles, max_dist=engage * 1.5)
        if threat is not None:
            target(ids, threat.id, True, 1.0)
        else:
            # Walk a wide ring around the system origin.
            leg = f.get("patrol_leg", 0)
            wx = 20000.0 * math.cos(leg * math.pi / 3.0)
            wz = 20000.0 * math.sin(leg * math.pi / 3.0)
            if ((lead.pos.x - wx) ** 2 + (lead.pos.z - wz) ** 2) < 4000.0 ** 2:
                setattr(f, "patrol_leg", (leg + 1) % 6)
            target_pos(ids, wx, 0.0, wz, 0.8, stop_dist=500)
    elif order == "strike":
        threat = closest_object(lead, hostiles)
        if threat is not None:
            target(ids, threat.id, True, 1.0)
        else:
            setattr(f, "order", "hold")
            return str(o.get("name", "Fleet")) + ": no hostiles on scope. Holding."
    elif order == "salvage":
        wreck = closest_object(lead, role("universe_derelict"))
        if wreck is None:
            setattr(f, "order", "hold")
            return str(o.get("name", "Fleet")) + ": nothing left to strip. Holding."
        d2 = (lead.pos.x - wreck.pos.x) ** 2 + (lead.pos.z - wreck.pos.z) ** 2
        if d2 < 1500.0 ** 2:
            mult = officer_bonus(f.get("officer"), "salvage")
            ore_v = int(30 * mult)
            gas_v = int(15 * mult)
            delete_object(wreck.id)
            admiralty_pool_add(side, "ore", ore_v)
            admiralty_pool_add(side, "gas", gas_v)
            return (str(o.get("name", "Fleet")) + ": wreck stripped - +" +
                    str(ore_v) + " ore, +" + str(gas_v) + " gas.")
        target_pos(ids, wreck.pos.x, wreck.pos.y, wreck.pos.z, 0.9, stop_dist=1000)
    elif order == "withdraw":
        home = _fleet_home_pos(side)
        if home is None:
            setattr(f, "order", "hold")
            return None
        d2 = (lead.pos.x - home.x) ** 2 + (lead.pos.z - home.z) ** 2
        if d2 < 3000.0 ** 2:
            setattr(f, "order", "hold")
            return str(o.get("name", "Fleet")) + ": home and holding."
        target_pos(ids, home.x + 1500, home.y, home.z, 1.0, stop_dist=1200)
    # hold: leave the ships where they are.
    return None


def fleet_status_text(fleet_key):
    """One console line: officer, order, hulls alive."""
    f = _FLEETS.get(fleet_key)
    if f is None:
        return ""
    o = _OFFICERS.get(f.get("officer")) or {}
    n = len(fleet_ships(fleet_key))
    return (fleet_key.upper() + "  " + str(o.get("name", "?")) + "  -  " +
            f.get("order", "hold") + "  -  " + str(n) + " ships")


# --- Console listbox templates (admiral.mast) ------------------------------------
def officer_list_title():
    gui_row("row-height: 1.2em;padding:6px;background:#1578;")
    gui_text("$text:Officers")


def officer_list_template(item):
    f = officer_fleet(item.get("key"))
    status = ("commanding " + f.get("key").upper() + " (" + f.get("order") + ")"
              if f is not None else "available")
    line = str(item.get("name")) + ", " + str(item.get("title")) + "  -  " + status
    gui_row("row-height: 2.2em;")
    gui_text("$text:" + line + ";font:gui-1")
