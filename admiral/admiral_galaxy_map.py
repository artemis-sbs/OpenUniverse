"""The Admiral's half of the galaxy TILE MAP: what clicking it lets an overseer DO.

The map itself is core (``universe_core/universe_galaxy_map.py``) - the player's
Navigation console draws the same one. Here are the orders, which only an Admiral gives.

CLICK, THEN CLICK. The old theater ordered by DRAG (a token onto a system) and listed the
choices in comms. A GUI map has no drag, so the gesture is two clicks: a ship or fleet
token picks the UNIT, then a system picks WHERE. The Orders app on the right-hand panel
lists what that pair can do, each line saying how far and how long - the same sentences
the drag menu used, so the two maps read alike while both exist.

The orders run through the same labels the theater used (``universe_jump_to``,
``fleet_deploy_to``, ``theater_jump_here``), so moving a crew or a fleet behaves exactly
as it did; only the way of asking changed.

Prefixed ``admiral_galaxy_map_``: every public function is a MAST global.
"""
from sbs_utils.mast.mast_node import MastDataObject
from sbs_utils.procedural.execution import get_shared_variable, task_schedule
from sbs_utils.procedural.gui import gui_row, gui_text, gui_blank
from sbs_utils.procedural.gui.listbox import gui_list_box
from sbs_utils.procedural.gui.message import gui_message_callback
from sbs_utils.procedural.gui.xess import xess_open, xess_register, gui_xess_head
from sbs_utils.procedural.query import to_object_list
from sbs_utils.procedural.roles import role

_AGM_SURFACE = "admiral_galaxy"
_AGM_DIM = "#9ab"

#: A fleet's standing orders, as the theater's fleet menu words them.
_AGM_ORDERS = (("escort", "Escort the flagship"), ("patrol", "Patrol the system"),
           ("strike", "Strike hostiles"), ("hold", "Hold position"),
           ("salvage", "Salvage wrecks"), ("withdraw", "Withdraw to base"))


def _agm_sibling(name):
    fn = globals().get(name)
    if fn is not None:
        return fn
    from sbs_utils.mast.mast_globals import MastGlobals
    return MastGlobals.globals.get(name)


def _agm_call(name, *args, **kwargs):
    fn = _agm_sibling(name)
    if fn is None:
        return None
    return fn(*args, **kwargs)


def _agm_text(s):
    """A label going into a button or list row: no style punctuation."""
    return str(s if s is not None else "").replace(";", ",").replace(":", " -") \
        .replace("{", "(").replace("}", ")").strip()


def _agm_travel(src, dst, fleet=False):
    """How far, and how long. A jump takes a wind-up and the warp screen whatever the
    distance; a fleet relocates at once."""
    d = max(abs(dst[0] - src[0]), abs(dst[1] - src[1]))
    away = "1 system away" if d == 1 else "%d systems away" % d
    if fleet:
        return away + ", deploys at once"
    secs = int(round((get_shared_variable("UNIVERSE_WARP_CHARGE_SECONDS", 3.5) or 0) + 2))
    return "%s, ~%ds jump" % (away, secs)


def _agm_side(client_id):
    return _agm_call("universe_console_side", client_id)


def _agm_hq_cell(side):
    hqs = to_object_list(role("admiral_hq") & role(side)) if side else []
    if not hqs:
        return None
    c = _agm_call("object_cell", hqs[0].id)
    return (int(c[0]), int(c[1])) if c else None


def admiral_galaxy_map_orders(client_id):
    """``[(text, data)]`` for what this console picked. ``data`` is what
    ``admiral_galaxy_map_do`` acts on - the shape the drag menu's ``galaxy_drag_do`` took,
    plus ``order`` (a standing order, no move) and ``deselect``."""
    sel = _agm_call("galaxy_map_selected", client_id)
    if sel is None:
        return []
    i, j = sel
    side = _agm_side(client_id)
    where = "(%d, %d)" % (i, j)
    unit = _agm_call("galaxy_map_selected_unit", client_id)
    out = []
    if unit:
        kind, ref = unit
        name = _agm_text(_agm_call("galaxy_map_unit_name", unit))
        at = _agm_call("galaxy_map_unit_cell", unit)
        if at is not None and kind == "ship":
            if tuple(at) != (i, j):
                out.append(("Send %s to %s - %s" % (name, where, _agm_travel(at, sel)),
                            {"act": "send", "ships": [ref], "i": i, "j": j}))
            else:
                home = _agm_hq_cell(side)
                if home is not None and home != (i, j):
                    out.append(("Recall %s to home base - %s" % (name, _agm_travel(at, home)),
                                {"act": "send", "ships": [ref], "i": home[0], "j": home[1]}))
        elif at is not None and kind == "fleet":
            if tuple(at) != (i, j):
                out.append(("Deploy %s to %s - %s" % (name, where, _agm_travel(at, sel, True)),
                            {"act": "deploy", "fleets": [ref], "i": i, "j": j, "order": None}))
                for order, verb in (("patrol", "patrol"), ("strike", "strike"),
                                    ("hold", "hold")):
                    out.append(("Deploy %s to %s and %s" % (name, where, verb),
                                {"act": "deploy", "fleets": [ref], "i": i, "j": j,
                                 "order": order}))
            else:
                current = _agm_call("admiralty_fleet_current_order", ref)
                for order, words in _AGM_ORDERS:
                    if order != current:
                        out.append(("%s - %s" % (name, words),
                                    {"act": "order", "fleets": [ref], "order": order}))
        out.append(("Deselect %s" % name, {"act": "deselect"}))
    elif side:
        for s in to_object_list(role("__player__") & role(side)) or []:
            at = _agm_call("ship_cell", s.id)
            if at and (int(at[0]), int(at[1])) != (i, j):
                at = (int(at[0]), int(at[1]))
                out.append(("Send %s here - %s" % (_agm_text(s.name), _agm_travel(at, sel)),
                            {"act": "send", "ships": [s.id], "i": i, "j": j}))
        for f in _agm_call("admiralty_fleets_of_side", side) or []:
            key = f.get("key")
            at = _agm_call("admiralty_fleet_cell", key)
            if at and (int(at[0]), int(at[1])) != (i, j):
                at = (int(at[0]), int(at[1]))
                name = _agm_text(_agm_call("admiralty_fleet_officer_name", key) or
                             ("Fleet " + str(key).upper()))
                out.append(("Deploy %s here - %s" % (name, _agm_travel(at, sel, True)),
                            {"act": "deploy", "fleets": [key], "i": i, "j": j,
                             "order": None}))
    out.append(("Go to %s (system view)" % where, {"act": "focus", "i": i, "j": j}))
    return out


def admiral_galaxy_map_do(client_id, data):
    """Carry out one order line. Moves go through ``galaxy_map_do`` (a label, because
    a jump and a deploy wait on tasks); a standing order and a deselect happen here."""
    if not data:
        return False
    act = data.get("act")
    if act == "deselect":
        return bool(_agm_call("galaxy_map_select_unit", client_id, None))
    side = _agm_side(client_id)
    if act == "order":
        for key in data.get("fleets") or []:
            ack = _agm_call("admiralty_fleet_set_order", key, data.get("order"))
            if ack:
                _agm_call("admiralty_say", side, ack)
        _agm_call("galaxy_map_select_unit", client_id, None)
        return True
    if act in ("send", "deploy"):
        # The order is given: the next click starts a new one.
        _agm_call("galaxy_map_select_unit", client_id, None)
    task_schedule("galaxy_map_do", {"GD": data, "GD_SIDE": side, "GD_CLIENT": client_id})
    return True


def admiral_galaxy_map_on_select(client_id):
    """A click on the map: show what can be done about it."""
    xess_open(client_id, "orders", _AGM_SURFACE)


def admiral_galaxy_map_order_row(item):
    gui_row("row-height: 2em; padding: 2px, 8px, 2px, 10px;")
    gui_text("$text:%s;font:gui-1;color:%s;" % (item.get("text"), item.get("color")))


def admiral_galaxy_map_orders_draw(client_id):
    """ORDERS - what the picked system (and the picked unit) can be told to do."""
    gui_xess_head(client_id, "Orders", surface=_AGM_SURFACE)
    sel = _agm_call("galaxy_map_selected", client_id)
    if sel is None:
        gui_row("row-height: 1.6em; padding: 6px, 8px, 6px, 10px;")
        gui_text("$text:Click a system on the map.;font:gui-1;color:%s;" % _AGM_DIM)
        gui_row("row-height: 1fr;")
        gui_blank()
        return
    facts = _agm_call("galaxy_map_system_facts", client_id, sel[0], sel[1]) or {}
    gui_row("row-height: 1.6em; padding: 4px, 8px, 0, 10px;")
    gui_text("$text:%s;font:gui-2;overflow:shrink;" % _agm_text(facts.get("title", "")))
    unit = _agm_call("galaxy_map_selected_unit", client_id)
    hint = ("Now click where %s should go." % _agm_text(_agm_call("galaxy_map_unit_name", unit))
            if unit else "Click a ship or fleet first to order it somewhere.")
    gui_row("row-height: content; padding: 0, 8px, 4px, 10px;")
    gui_text("$text:%s;font:gui-1;color:%s;" % (hint, _AGM_DIM))
    rows = [MastDataObject({"text": _agm_text(t), "data": d,
                            "color": "#dfe" if d.get("act") != "deselect" else _AGM_DIM})
            for t, d in admiral_galaxy_map_orders(client_id)]
    gui_row("row-height: 1fr;")
    lb = gui_list_box(rows, "row-height: 2em;", item_template=admiral_galaxy_map_order_row,
                      select=True)
    gui_message_callback(lb, lambda event, sender, _cid=client_id, _lb=lb:
                         _agm_run_row(_cid, _lb.get_value()))


def _agm_run_row(client_id, row):
    if row is None:
        return False
    return admiral_galaxy_map_do(client_id, row.get("data"))


def admiral_galaxy_map_places_draw(client_id):
    """PLACES - home, the sides' homes and your quest targets. Click one to look there."""
    gui_xess_head(client_id, "Places", surface=_AGM_SURFACE)
    places = _agm_call("galaxy_map_known_places", client_id) or []
    rows = [MastDataObject({"text": "%s  (%d, %d)" % (_agm_text(p.name), int(p.i), int(p.j)),
                            "i": int(p.i), "j": int(p.j), "color": "#dfe"}) for p in places]
    gui_row("row-height: 1fr;")
    lb = gui_list_box(rows, "row-height: 2em;", item_template=admiral_galaxy_map_order_row,
                      select=True)
    gui_message_callback(lb, lambda event, sender, _cid=client_id, _lb=lb:
                         _agm_look_at(_cid, _lb.get_value()))


def _agm_look_at(client_id, row):
    if row is None:
        return False
    return bool(_agm_call("galaxy_map_focus", client_id, row.get("i"), row.get("j"), True))


def _agm_tiles_mode(client_id=None):
    return bool(_agm_call("galaxy_map_tiles"))


def admiral_galaxy_map_register():
    """Put Orders and Places on the galaxy panel. Idempotent; the page calls it on every
    build, because a mission reset drops a mission's apps."""
    xess_register("orders", title="Orders", icon="flag", sort=5,
                  blurb="What the picked system or unit can do",
                  draw=admiral_galaxy_map_orders_draw, available=_agm_tiles_mode,
                  surface=_AGM_SURFACE)
    xess_register("places", title="Places", icon="globe-grid", sort=40,
                  blurb="Homes and quest targets - click to look",
                  draw=admiral_galaxy_map_places_draw, available=_agm_tiles_mode,
                  surface=_AGM_SURFACE)
    return True
