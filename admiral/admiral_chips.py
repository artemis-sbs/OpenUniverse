"""Filter chips for the Admiral's two maps - the system view and the galaxy theater.

Same idea as LM's comms chips, but the console rides a detached CAM rather than a ship,
so the lens is written to the cam's own `comms_map_filter` (`comms_map_filter_set`): the
2D view then draws only what the lens holds. Each board has its own vocabulary:

- **system** (the Admiral console): Worldlets, Platforms, Ships, Fleets, Threats. This is
  the build board, so worldlets - the sites a platform can go on - are a lens of their own.
- **galaxy** (the theater board): the ship and fleet PROXIES, and the system markers split
  into Known and Unknown. Unknown is the fog: a marker the overseer has not revealed. It is
  a lens on the board's own tokens, not on contacts - the board is entirely proxies.

The chips replace the zoom control that used to sit in the band above each map.

A chip's ids are what the SCRIPT knows (roles, sides, cells, reveal state) and the engine
does not. Counts are recounted at most every couple of seconds.

Galaxy note: `galaxy_theater_map_filter` re-writes the cam's filter after every board sync,
and it asks this module for the lens, so a synced board keeps the chip selection.

Prefixed `admiral_chips_` because every top-level function here is a MAST global in one
flat, mission-wide namespace.
"""
from sbs_utils.helpers import FrameContext
from sbs_utils.procedural.comms import comms_map_filter_set, comms_map_filter_clear
from sbs_utils.procedural.inventory import get_inventory_value, set_inventory_value
from sbs_utils.procedural.query import object_exists, to_object, to_object_list
from sbs_utils.procedural.roles import role
from sbs_utils.procedural.sides import side_are_enemies

#: board -> [(key, label)] in rail order. "all" is first on both and clears the lens.
_CHIPS = {
    "system": [
        ("all", "All"),
        ("worldlets", "Worldlets"),
        ("platforms", "Platforms"),
        ("ships", "Ships"),
        ("fleets", "Fleets"),
        ("threats", "Threats"),
    ],
    # The board's own vocabulary, in the order an overseer asks the questions: where are
    # my forces, where are they going, who is in the way, and where is there anything
    # worth going to. "Known" is deliberately absent - it was the whole board minus the
    # fog, which is what All already shows.
    "galaxy": [
        ("all", "All"),
        ("ships", "Ships"),
        ("fleets", "Fleets"),
        ("orders", "Orders"),
        ("threats", "Threats"),
        ("yours", "Yours"),
        ("worldlets", "Worldlets"),
        ("bases", "Bases"),
        ("anomalies", "Anomalies"),
        ("nebulae", "Nebulae"),
        ("unknown", "Unknown"),
    ],
}

#: Seconds between recounts - a count a couple of seconds old is fine, and both boards
#: walk every object of a side to build one.
_RECOUNT_SECONDS = 2.0

# (cam_id, board) -> (sim_seconds, {key: set(ids)})
_SETS = {}

# (cam_id, board) -> the chip KEYS last applied to that cam, so a board sync that
# re-writes the cam's filter can narrow it to the same lens (see
# admiral_chips_lens_for_cam). Keyed by cam because a cam belongs to one console.
_LENS = {}

_SELECTED_KEY = "admiral_chips"


def _labels(board):
    return dict(_CHIPS.get(board, ()))


def _sibling(name):
    """A sibling helper from the mission's shared namespace, or None.

    In the game every mission .py execs into ONE dict, so `object_cell` and
    `admiralty_side_controls_cell` are simply in scope. Imported as a plain package (a
    unit test, a tool) they are not, and a bare call raises NameError - which stops the
    command that was computing a chip. Looked up rather than imported, so this module
    keeps the no-sibling-imports rule the other universe_*.py files follow.
    """
    fn = globals().get(name)
    if fn is not None:
        return fn
    from sbs_utils.mast.mast_globals import MastGlobals
    return MastGlobals.globals.get(name)


def admiral_chips_items(board):
    """The listbox's items: "<board>:<key>" strings, in rail order. The board travels in
    the item because the template gets only the item."""
    return [board + ":" + k for k, _ in _CHIPS.get(board, ())]


def _split(item):
    board, _, key = str(item).partition(":")
    return board, key


def _cell_of(obj_id):
    """The system an object is in, as (i, j), or None."""
    cell_of = _sibling("object_cell")
    if cell_of is None or to_object(obj_id) is None:
        return None
    c = cell_of(obj_id)
    return (int(c[0]), int(c[1])) if c else None


def _compute_system(cam_id, side):
    """The system board's lenses: what the Admiral commands, and what threatens it, in
    the cam's OWN cell (Model A - sides can be in different systems at once)."""
    sets = {k: set() for k, _ in _CHIPS["system"]}
    cell = _cell_of(cam_id)
    if cell is None:
        return sets

    def here(objs):
        return [o for o in objs
                if o is not None and o.id != cam_id and _cell_of(o.id) == cell]

    for o in here(to_object_list(role("worldlet"))):
        sets["worldlets"].add(o.id)
    for o in here(to_object_list(role("admiral_platform") & role(side))):
        sets["platforms"].add(o.id)
    for o in here(to_object_list(role("__player__") & role(side))):
        sets["ships"].add(o.id)
    # A fleet's SHIPS are what the map draws, so the lens is the escorts themselves -
    # the NPCs of this side, which is what a fleet deploys.
    for o in here(to_object_list(role("__npc__") & role(side))):
        sets["fleets"].add(o.id)
    for o in here(to_object_list(role("__npc__") | role("__player__"))):
        if o.id not in sets["ships"] and side_are_enemies(cam_id, o.id):
            sets["threats"].add(o.id)
    sets["all"] = set().union(*[v for k, v in sets.items() if k != "all"]) if sets else set()
    return sets


def _ordered_cells(side):
    """The systems this side's ships have been SENT to (active_objective), as cells. The
    Orders lens marks those systems, so "where did I send everyone" is one tap."""
    cells = set()
    for o in to_object_list(role("__player__") & role(side)):
        dest = get_inventory_value(o.id, "active_objective", None)
        if dest and len(dest) == 2:
            cells.add((int(dest[0]), int(dest[1])))
    return cells


def _compute_galaxy(cam_id, side):
    """The theater board's lenses: this cam's own tokens.

    The unit tokens are Ships and Fleets. Every other lens is a lens on the SYSTEM
    markers, read off what the board already stored on each one when it built it - its
    kind, its cell, and how many worldlets the cell has.

    A fogged cell is in NO lens but Unknown: its kind, its owner and its worldlets are
    exactly what the overseer has not charted yet, so a count of them would hand over
    what the fog is hiding. Unknown itself is safe - the board already draws the fog.
    """
    sets = {k: set() for k, _ in _CHIPS["galaxy"]}
    for o in to_object_list(role("galaxy_unit")):
        if get_inventory_value(o.id, "board_cam", 0) == cam_id:
            sets["ships"].add(o.id)
    for o in to_object_list(role("galaxy_fleet")):
        if get_inventory_value(o.id, "board_cam", 0) == cam_id:
            sets["fleets"].add(o.id)
    ordered = _ordered_cells(side) if side else set()
    for o in to_object_list(role("galaxy_marker")):
        if get_inventory_value(o.id, "board_cam", 0) != cam_id:
            continue
        kind = get_inventory_value(o.id, "marker_kind", "")
        if kind == "fog":
            sets["unknown"].add(o.id)
            continue
        cell = (get_inventory_value(o.id, "marker_i", 0), get_inventory_value(o.id, "marker_j", 0))
        if kind == "enemy":
            sets["threats"].add(o.id)
        elif kind in ("station", "home"):
            sets["bases"].add(o.id)
        elif kind == "anomaly":
            sets["anomalies"].add(o.id)
        elif kind == "nebula":
            sets["nebulae"].add(o.id)
        if get_inventory_value(o.id, "marker_worldlets", 0):
            sets["worldlets"].add(o.id)
        controls = _sibling("admiralty_side_controls_cell")
        if side and controls is not None and controls(side, cell[0], cell[1]):
            sets["yours"].add(o.id)
        if cell in ordered:
            sets["orders"].add(o.id)
    sets["all"] = set().union(*[v for k, v in sets.items() if k != "all"])
    return sets


def admiral_chips_sets(cam_id, board, side=None, force=False):
    """{chip key: set of ids} for one cam's board, recounted at most every couple of
    seconds. Empty sets when the cam is gone."""
    now = FrameContext.sim_seconds or 0
    cached = _SETS.get((cam_id, board))
    # `0 <=`: sim time restarts with a mission, so a clock that went BACKWARDS is stale.
    if not force and cached is not None and 0 <= now - cached[0] < _RECOUNT_SECONDS:
        return cached[1]
    if not cam_id or not object_exists(cam_id):
        # A cam that is gone is not cached - the next one to answer should be the board.
        return {k: set() for k, _ in _CHIPS.get(board, ())}
    # The cam carries the overseer's side, so a caller that has not got it (the chip
    # TEMPLATE, which is handed only an item) still gets the side-aware lenses.
    side = side or getattr(to_object(cam_id), "side", None)
    if board == "galaxy":
        sets = _compute_galaxy(cam_id, side)
    else:
        sets = _compute_system(cam_id, side)
    _SETS[(cam_id, board)] = (now, sets)
    return sets


def admiral_chips_revision(cam_id, board, side=None):
    """What an `on change` watches: the lens MEMBERS, not just the counts - a token
    swapped for another keeps every count the same and must still re-apply the filter."""
    sets = admiral_chips_sets(cam_id, board, side)
    return tuple(sorted((k, tuple(sorted(v))) for k, v in sets.items() if k != "all"))


def admiral_chips_template(item):
    """One chip: its label and live count, centered. All carries no count - it is the
    absence of a lens, and a number on it would just be the sum of the others."""
    from sbs_utils.procedural.gui import gui_row, gui_text
    board, key = _split(item)
    # The chip's WIDTH is the listbox's `col-width`; this row just fills it.
    gui_row("row-height: 1fr;")
    label = _labels(board).get(key, key)
    if key == "all":
        gui_text(f"$text:{label};justify:center;font:gui-2;")
        return
    cam_id = get_inventory_value(FrameContext.client_id, _cam_key(board), 0)
    n = len(admiral_chips_sets(cam_id, board).get(key, ()))
    gui_text(f"$text:{label} {n};justify:center;font:gui-2;")


def _cam_key(board):
    return "GALAXY_CAM" if board == "galaxy" else "ADMIRAL_CAM"


def admiral_chips_selected(client_id, board):
    """The chips this console has selected on this board (defaults to All)."""
    sel = get_inventory_value(client_id, _SELECTED_KEY + ":" + board, None)
    return list(sel) if sel else [board + ":all"]


def admiral_chips_ids(client_id, cam_id, board, side=None):
    """(mode, ids) for this console's selection: ("show", ids), or ("all", None) for no
    filter."""
    sets = admiral_chips_sets(cam_id, board, side)
    lenses = [_split(k)[1] for k in admiral_chips_selected(client_id, board)]
    lenses = [k for k in lenses if k != "all"]
    if not lenses:
        return "all", None
    ids = set()
    for k in lenses:
        ids |= sets.get(k, set())
    return "show", ids


def admiral_chips_apply(client_id, cam_id, board, side=None):
    """Write this console's lens to its cam's map filter - cleared for All. The cam is
    what the console is assigned to, so the filter is the cam's, not a ship's."""
    if not cam_id or not object_exists(cam_id):
        return False
    mode, ids = admiral_chips_ids(client_id, cam_id, board, side)
    _LENS[(cam_id, board)] = [_split(k)[1] for k in admiral_chips_selected(client_id, board)]
    if mode == "all":
        comms_map_filter_clear(cam_id)
    else:
        comms_map_filter_set(cam_id, ids)
    return True


def admiral_chips_normalize(client_id, cam_id, board, lb, side=None):
    """Keep the selection sensible after a tap, then apply it. All is exclusive with the
    lenses: tapping All clears them, tapping a lens clears All, clearing every lens
    brings All back."""
    before = set(admiral_chips_selected(client_id, board))
    picked = set(lb.get_selected() or [])
    now = [k for k in admiral_chips_items(board) if k in picked]
    all_key = board + ":all"
    lenses = [k for k in now if k != all_key]
    if all_key in now and all_key not in before:
        lenses = []                                      # All was just tapped
    keep = lenses or [all_key]
    if keep != now:
        lb.selected = list(keep)
        lb.mark_visual_dirty()
    set_inventory_value(client_id, _SELECTED_KEY + ":" + board, keep)
    admiral_chips_apply(client_id, cam_id, board, side)
    return keep


def admiral_chips_refresh(client_id, cam_id, board, lb, side=None):
    """Counts moved: redraw the chips' own rows (not the page) and re-apply the lens,
    since the ids behind a lens change with them."""
    lb.items = admiral_chips_items(board)
    admiral_chips_apply(client_id, cam_id, board, side)


def admiral_chips_lens_for_cam(cam_id, board, ids):
    """Narrow `ids` (everything the board would show) to the lens any console watching
    this cam has picked. Used by galaxy_theater_map_filter, which re-writes the filter
    after every board sync and would otherwise undo the chips.

    A cam belongs to ONE console, so the lens last applied to it is that console's."""
    keys = [k for k in _LENS.get((cam_id, board), ()) if k != "all"]
    if not keys:
        return ids
    sets = admiral_chips_sets(cam_id, board)
    keep = set()
    for k in keys:
        keep |= sets.get(k, set())
    return [i for i in ids if i in keep]


def admiral_chips_clear():
    """Forget every cached count and lens (reset_mission_state / tests)."""
    _SETS.clear()
    _LENS.clear()
