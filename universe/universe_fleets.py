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

Fleets persist: the live registry mirrors into side inventory (adm_fleets,
saved by universe_helpers) on every form/order/tick change, and
fleets_respawn re-instantiates surviving hulls on arrival in a system or
when a saved campaign continues (the navy travels with the flag).

Shared-namespace notes: universe_section from universe_clans.py; admiralty_*
pool/tuning from universe_worldlets.py.
"""
import math
from sbs_utils.mast.mast_node import MastDataObject
from sbs_utils.procedural.spawn import npc_spawn
from sbs_utils.procedural.inventory import get_inventory_value, set_inventory_value
from sbs_utils.procedural.sides import to_side_id
from sbs_utils.procedural.roles import role, all_roles
from sbs_utils.procedural.query import to_object_list, to_object
from sbs_utils.procedural.space_objects import (closest_object, target, target_pos,
                                                delete_object)
from sbs_utils.procedural.gui import gui_row, gui_text
from sbs_utils.procedural.comms import comms_info_card

# The commissionable hull roster (data - difficulty/length tuning later).
FLEET_ROSTER = [
    ("tsn_light_cruiser", "Escort"),
    ("tsn_light_cruiser", "Escort"),
    ("tsn_battle_cruiser", "Line"),
]
FLEET_COST = {"ore": 180, "gas": 40, "crew": 24}

FLEET_ORDERS = ["escort", "patrol", "strike", "hold", "salvage", "withdraw"]

_OFFICERS = {}       # key -> authored record
_OFFICER_FACES = {}  # key -> resolved face string (stable per session)
_FLEETS = {}         # fleet key ("f1"...) -> live state (MastDataObject)
_NEXT_FLEET = [1]


def _evt(officer_key, text):
    """A fleet event for the console loop: who said it + what they said."""
    return MastDataObject({"officer": officer_key, "text": text})


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
    global _OFFICERS, _OFFICER_FACES, _FLEETS, _NEXT_FLEET
    _OFFICERS = {o.get("key"): o for o in (officers or [])}
    _OFFICER_FACES = {}
    _FLEETS = {}
    _NEXT_FLEET = [1]


def officer_face(key):
    """The officer's face string, resolved once per session from the authored
    Face keyword (lifeform_face, shared namespace) and cached so the portrait
    stays stable."""
    if key not in _OFFICER_FACES:
        try:
            _OFFICER_FACES[key] = lifeform_face(_OFFICERS.get(key))
        except NameError:
            _OFFICER_FACES[key] = None
    return _OFFICER_FACES.get(key)


def officer_card(key, line, time=12):
    """Deliver an officer's line as an info-panel card (face/name/color) -
    chatter never rides the text waterfall."""
    if not line:
        return
    o = _OFFICERS.get(key)
    title = (str(o.get("name")) + ", " + str(o.get("title"))) if o is not None else "Fleet Command"
    comms_info_card(all_roles("console, comms"), line, title=title,
                    color="#8cf", face=officer_face(key), time=time)


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


def _fleets_sync(side):
    """Mirror the live fleets into side inventory (adm_fleets) - the source of
    truth the universe save persists (universe_helpers side_admiralty)."""
    recs = [{"officer": f.get("officer"), "order": f.get("order", "hold"),
             "alive": int(f.get("alive", len(FLEET_ROSTER)))}
            for f in _FLEETS.values() if f.get("side") == side]
    set_inventory_value(to_side_id(side), "adm_fleets", recs)


def _fleet_spawn_ships(side, fkey, x, z, count):
    """Spawn the first `count` roster hulls in a loose ring at (x, z)."""
    for idx, (hull, hull_name) in enumerate(FLEET_ROSTER[:count]):
        ang = idx * 2.4
        name = "Fleet " + fkey.upper() + " " + hull_name + " " + str(idx + 1)
        npc_spawn(x + 700 * math.cos(ang), 0.0, z + 700 * math.sin(ang),
                  name, side + ", adm_fleet, adm_" + fkey, hull, "behav_npcship")


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
    _fleet_spawn_ships(side, fkey, ypos.x + 1200, ypos.z + 1200, len(FLEET_ROSTER))
    _FLEETS[fkey] = MastDataObject({
        "key": fkey, "side": side, "officer": officer_key,
        "order": "hold", "alive": len(FLEET_ROSTER), "gas_starved": False})
    _fleets_sync(side)
    return None


def fleets_respawn(side):
    """Bring the navy along: after a jump (or a restored save) the system has
    no NPCs, so re-instantiate every surviving fleet's hulls near the arrival
    point. Rebuilds the live registry from side inventory when empty (fresh
    session with a saved campaign)."""
    global _FLEETS
    if not _FLEETS:
        recs = get_inventory_value(to_side_id(side), "adm_fleets", []) or []
        for rec in recs:
            if int(rec.get("alive", 0)) <= 0:
                continue
            fkey = "f" + str(_NEXT_FLEET[0])
            _NEXT_FLEET[0] += 1
            _FLEETS[fkey] = MastDataObject({
                "key": fkey, "side": side, "officer": rec.get("officer"),
                "order": rec.get("order", "hold"),
                "alive": int(rec.get("alive", 0)), "gas_starved": False})
    for n, f in enumerate(_FLEETS.values()):
        if f.get("side") != side:
            continue
        alive = int(f.get("alive", 0))
        if alive > 0 and len(fleet_ships(f.get("key"))) == 0:
            ang = n * 1.3
            _fleet_spawn_ships(side, f.get("key"),
                               4200 * math.cos(ang), 4200 * math.sin(ang), alive)
    _fleets_sync(side)


def fleet_set_order(fleet_key, order):
    """Set a fleet's order. Returns the officer's acknowledgment line (or an
    empty string if the fleet is gone)."""
    f = _FLEETS.get(fleet_key)
    if f is None or order not in FLEET_ORDERS:
        return ""
    setattr(f, "order", order)
    setattr(f, "gas_starved", False)
    _fleets_sync(f.get("side"))
    acks = {
        "escort": "Falling in on your wing.",
        "patrol": "Sweeping the system.",
        "strike": "Weapons free. Moving to engage.",
        "hold": "Holding position.",
        "salvage": "Stripping the wrecks.",
        "withdraw": "Coming home.",
    }
    return acks.get(order, "Acknowledged.")


def _fleet_home_pos(side):
    """Where withdraw goes: the HQ, else origin."""
    hqs = to_object_list(role("admiral_hq") & role(side))
    return hqs[0].pos if hqs else None


def fleet_tick(fleet_key, dt_seconds):
    """One order step for one fleet. Returns an event (officer + line) for the
    console loop to deliver (fleet lost, salvage award, gas empty), or None."""
    f = _FLEETS.get(fleet_key)
    if f is None:
        return None
    side = f.get("side")
    okey = f.get("officer")
    ships = fleet_ships(fleet_key)
    if len(ships) == 0:
        del _FLEETS[fleet_key]
        _fleets_sync(side)
        return _evt(okey, "We've lost the fleet. I'm sorry, Admiral.")
    if len(ships) != int(f.get("alive", 0)):
        setattr(f, "alive", len(ships))
        _fleets_sync(side)
    order = f.get("order", "hold")

    # Gas: every non-hold order burns fuel (per minute, officer-scaled).
    if order != "hold":
        burn = float(admiralty_tuning("fleet_gas_burn", 2)) * officer_bonus(okey, "gas")
        need = burn * float(dt_seconds) / 60.0
        if admiralty_pool_get(side, "gas") <= 0:
            setattr(f, "order", "hold")
            _fleets_sync(side)
            if not f.get("gas_starved"):
                setattr(f, "gas_starved", True)
                return _evt(okey, "Tanks are dry - holding until we get gas.")
            return None
        _pool_add_f(side, "gas", -need)

    ids = set(s.id for s in ships)
    lead = ships[0]
    engage = 6000.0 * officer_bonus(okey, "engage")
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
            _fleets_sync(side)
            return _evt(okey, "No hostiles on scope. Holding.")
    elif order == "salvage":
        wreck = closest_object(lead, role("universe_derelict"))
        if wreck is None:
            setattr(f, "order", "hold")
            _fleets_sync(side)
            return _evt(okey, "Nothing left to strip. Holding.")
        d2 = (lead.pos.x - wreck.pos.x) ** 2 + (lead.pos.z - wreck.pos.z) ** 2
        if d2 < 1500.0 ** 2:
            mult = officer_bonus(okey, "salvage")
            ore_v = int(30 * mult)
            gas_v = int(15 * mult)
            delete_object(wreck.id)
            admiralty_pool_add(side, "ore", ore_v)
            admiralty_pool_add(side, "gas", gas_v)
            return _evt(okey, "Wreck stripped - +" + str(ore_v) + " ore, +" +
                        str(gas_v) + " gas.")
        target_pos(ids, wreck.pos.x, wreck.pos.y, wreck.pos.z, 0.9, stop_dist=1000)
    elif order == "withdraw":
        home = _fleet_home_pos(side)
        if home is None:
            setattr(f, "order", "hold")
            return None
        d2 = (lead.pos.x - home.x) ** 2 + (lead.pos.z - home.z) ** 2
        if d2 < 3000.0 ** 2:
            setattr(f, "order", "hold")
            _fleets_sync(side)
            return _evt(okey, "Home and holding.")
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
