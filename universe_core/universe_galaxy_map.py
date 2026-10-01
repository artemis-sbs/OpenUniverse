"""The galaxy map as a TILE MAP - one map for the player's Navigation console and the
Admiral's Galaxy tab.

WHY TILES. The Admiral's old map (the "theater") was real marker objects out in dead space,
watched through the engine's 2D view from a camera the console was handed to. A player's
console is bound to its ship and cannot ride a camera, so the player got a grid of buttons
instead and the two never shared anything. The tile view is plain GUI: it runs on any
console, and the galaxy is already a grid.

THE WINDOW. The galaxy has no edge, and a tile area does. So each console gets its own
finite area - ``galaxy_map:<client id>`` - regenerated around the system it is looking at.
Its own, because what a console sees is its own too: green is YOUR territory, red is YOUR
enemy, and the selection is yours. A regeneration that comes out identical repaints
nothing, so the map can be refreshed every second for free.

ONE SYSTEM IS A 3x3 BLOCK of tiles. The middle tile is the system's glyph. The eight round
it are its FRAME, tinted by what the system is to you (yours, a foe's, a region, a quest
target, where you are, what you picked), with a thin gap on the outside so neighbors stay
apart. The top row of the frame holds up to three ship tokens and the bottom row up to
three fleet tokens; a fourth gets a "+" badge. So nothing ever stacks, and the tile view
needed no fan-out code.

North (+j) is at the top. Coordinates in here: (i, j) is a SYSTEM, (x, y) is a TILE of the
window, (bx, by) is a BLOCK of the window.

Per-console state lives in the client's inventory (``GALAXY_MAP``), so a mission reset takes
it with the client and nothing here needs registering with the reset ledger.

Core, not admiral: the Navigation console must work in a mission that never loads the
Admiral, so every admiral helper is reached through ``_gm_call`` and may be missing.
"""
from sbs_utils.helpers import FrameContext
from sbs_utils.mast.mast_node import MastDataObject
from sbs_utils.procedural.execution import get_shared_variable, log
from sbs_utils.procedural.inventory import get_inventory_value, set_inventory_value
from sbs_utils.procedural.query import to_object, to_object_list
from sbs_utils.procedural.roles import role

#: Systems across, per zoom step. Three tiles each, so 39 tiles at the widest - inside
#: the tile view's 40-column cap (a wider view is thousands of widgets in one section,
#: and the engine has crashed drawing those).
GALAXY_MAP_ZOOMS = (7, 9, 11, 13)
#: How many more systems the window holds DOWN than across. The view decides how many
#: rows fit; a window shorter than that would show a black band at the bottom.
_GM_EXTRA_ROWS = 2

_GM_STATE = "GALAXY_MAP"
_GM_TILESET = "galaxy_map"

#: The map's background: the section behind it, and the middle of every frame.
GALAXY_MAP_BACKGROUND = "#0b1420"
#: A frame nobody has an interest in - just enough to show where a system is.
_GM_FRAME = "#16202c"

#: System KIND -> (glyph on the engine's icon sheet, color). The same glyphs the old
#: theater drew, so the two maps agree while both exist.
_GM_KINDS = {
    "home":    (159, "#33ff66"),
    "station": (114, "#00ccff"),
    "enemy":   (78, "#ff4444"),
    "nebula":  (8, "#cc66ff"),
    "anomaly": (0, "#aa33ff"),
    "empty":   (129, "#888888"),
    "fog":     (121, "#555555"),
}
_GM_KIND_WORD = {"home": "Home", "station": "Base", "enemy": "Threat", "nebula": "Nebula",
                 "anomaly": "Anomaly", "empty": "System", "fog": "Unknown"}

_GM_SHIP_GLYPH = 140
_GM_FLEET_GLYPH = 37
_GM_MORE_GLYPH = 156
_GM_QUEST_GLYPH = 23
_GM_DEST_GLYPH = 18

_GM_FRIENDLY = "#33ff66"
_GM_HOSTILE = "#ff4444"
_GM_OWN_SHIP = "#00e5ff"
_GM_FLEET = "#ffd24a"
_GM_QUEST = "#ffaa33"
_GM_DEST = "#8cf"

#: The frame's own tiles: (column, row) inside the block -> the tile kind. The middle
#: (1, 1) is the system.
_GM_FRAME_KINDS = {
    (0, 0): "frame_nw", (1, 0): "frame_n", (2, 0): "frame_ne",
    (0, 1): "frame_w", (2, 1): "frame_e",
    (0, 2): "frame_sw", (1, 2): "frame_s", (2, 2): "frame_se",
}

#: The icon sheet: 128px cells, 20 across. Glyph 101 is a filled square with a 6px clear
#: margin - which is exactly the gap a frame wants on its OUTSIDE edge and must not have
#: inside, so each frame tile takes a different 96px slice of it.
_GM_SHEET = "grid-icon-sheet"
_GM_CELL = 128
_GM_SQUARE = 101


def _gm_glyph_origin(index):
    return (index % 20) * _GM_CELL, (index // 20) * _GM_CELL


def _gm_frame_slice(sx, sy):
    """The slice of the square glyph a frame tile shows: flush where it meets the rest of
    its own frame, with the glyph's clear margin where it faces a neighbor."""
    x = (0, 96) if sx == 0 else (32, 128) if sx == 2 else (16, 112)
    y = (0, 96) if sy == 0 else (32, 128) if sy == 2 else (16, 112)
    return x[0], y[0], x[1], y[1]


def galaxy_map_setup():
    """Declare the map's art and tileset. Idempotent; every page that shows the map calls
    it. It asks what is THERE rather than keeping an "already done" flag: a flag would
    outlive a mission reset that took the registrations with it."""
    from sbs_utils.procedural.gui.image import (ImageAtlas, gui_image_add_atlas,
                                                gui_image_add_atlas_grid)
    from sbs_utils.procedural.tilemap import tilemap_tileset, tilemap_tileset_known
    if ImageAtlas.all.get(ImageAtlas.qualify("frame_se", _GM_TILESET)) is None:
        names = {"sys_" + k: ((g % 20), (g // 20)) for k, (g, _) in _GM_KINDS.items()}
        names.update({"ship": (_GM_SHIP_GLYPH % 20, _GM_SHIP_GLYPH // 20),
                      "fleet": (_GM_FLEET_GLYPH % 20, _GM_FLEET_GLYPH // 20),
                      "more": (_GM_MORE_GLYPH % 20, _GM_MORE_GLYPH // 20),
                      "quest": (_GM_QUEST_GLYPH % 20, _GM_QUEST_GLYPH // 20),
                      "dest": (_GM_DEST_GLYPH % 20, _GM_DEST_GLYPH // 20)})
        gui_image_add_atlas_grid(_GM_SHEET, 20, names=names, cell=_GM_CELL,
                                 domain=_GM_TILESET)
        ox, oy = _gm_glyph_origin(_GM_SQUARE)
        for (sx, sy), kind in _GM_FRAME_KINDS.items():
            l, t, r, b = _gm_frame_slice(sx, sy)
            gui_image_add_atlas(kind, _GM_SHEET, ox + l, oy + t, ox + r, oy + b,
                                domain=_GM_TILESET)
    if not tilemap_tileset_known(_GM_TILESET):
        kinds = {}
        # `space` FIRST: the view draws "nothing" with the tileset's first kind, tinted
        # black, and a filled square is the right thing to tint.
        kinds["space"] = {"cell": "galaxy_map:frame_n", "color": GALAXY_MAP_BACKGROUND}
        for kind in _GM_FRAME_KINDS.values():
            kinds[kind] = {"cell": "galaxy_map:" + kind, "color": _GM_FRAME}
        for kind, (_, color) in _GM_KINDS.items():
            # `look` names the ground a galaxy ART SET would draw it with, so a real
            # pack drops in through tilemap_art_use without touching this file.
            kinds["sys_" + kind] = {"cell": "galaxy_map:sys_" + kind, "color": color,
                                    "look": "galaxy_" + kind}
        tilemap_tileset(_GM_TILESET, kinds)
    return True


# --- siblings ------------------------------------------------------------------------

def _gm_sibling(name):
    """A sibling helper from the mission's shared namespace, or None (the Admiral is not
    loaded, or this file was imported as a plain module by a test)."""
    fn = globals().get(name)
    if fn is not None:
        return fn
    from sbs_utils.mast.mast_globals import MastGlobals
    return MastGlobals.globals.get(name)


def _gm_call(name, *args, **kwargs):
    fn = _gm_sibling(name)
    if fn is None:
        return None
    try:
        return fn(*args, **kwargs)
    except Exception as e:                               # noqa: BLE001 - a map must not die
        log(f"galaxy map: {name} failed: {e}", "galaxy_map", "warning")
        return None


def _gm_world():
    """The universe's shared settings, read once per refresh."""
    return {
        "seed": get_shared_variable("universe_seed", 0),
        "sides": get_shared_variable("UNIVERSE_SIDES", None) or [],
        "danger": get_shared_variable("DANGER", "Quiet"),
        "systems": get_shared_variable("universe_systems", None) or {},
        "reveal": get_shared_variable("MAP_REVEAL", None),
        "regions": get_shared_variable("UNIVERSE_REGIONS", None) or [],
        "landmarks": get_shared_variable("UNIVERSE_LANDMARKS", None),
    }


# --- colors --------------------------------------------------------------------------

_GM_NAMED = {
    "white": "#ffffff", "black": "#000000", "red": "#ff0000", "green": "#00ff00",
    "blue": "#0000ff", "yellow": "#ffff00", "cyan": "#00ffff", "magenta": "#ff00ff",
    "orange": "#ffa500", "purple": "#800080", "gold": "#ffd700", "grey": "#808080",
    "gray": "#808080", "pink": "#ffc0cb", "brown": "#a52a2a", "lime": "#00ff00",
    "teal": "#008080", "navy": "#000080", "silver": "#c0c0c0", "crimson": "#dc143c",
    "springgreen": "#00ff7f", "skyblue": "#87ceeb", "violet": "#ee82ee",
}


def _gm_rgba(color):
    """(r, g, b, a) from #rgb, #rgba, #rrggbb, #rrggbbaa or a common name; None if
    unreadable."""
    s = str(color or "").strip().lower()
    s = _GM_NAMED.get(s, s)
    if not s.startswith("#"):
        return None
    h = s[1:]
    try:
        if len(h) in (3, 4):
            vals = [int(c * 2, 16) for c in h]
        elif len(h) in (6, 8):
            vals = [int(h[k:k + 2], 16) for k in range(0, len(h), 2)]
        else:
            return None
    except ValueError:
        return None
    if len(vals) == 3:
        vals.append(255)
    return tuple(vals)


def galaxy_map_shade(color, strength, base=_GM_FRAME):
    """``color`` laid over ``base`` at ``strength`` (times its own alpha), as an OPAQUE
    #rrggbb. A frame wants a dark wash of a side's color, not the color itself - and the
    engine's handling of a translucent image tint is unmeasured, so nothing here relies
    on it. An unreadable color answers None, and the caller keeps what it had."""
    c, b = _gm_rgba(color), _gm_rgba(base)
    if c is None or b is None:
        return None
    a = max(0.0, min(1.0, strength * c[3] / 255.0))
    mix = [int(round(b[k] + (c[k] - b[k]) * a)) for k in range(3)]
    return "#%02x%02x%02x" % tuple(mix)


def galaxy_map_owner_is_foe(sides, owner, side):
    """A system's owner is hostile to this console's side. The Admiral's own test when it
    is loaded (ceasefire-aware); otherwise the side's authored disposition."""
    if owner is None or side is None or owner == side:
        return False
    if _gm_sibling("admiralty_side_is_foe") is not None:
        return bool(_gm_call("admiralty_side_is_foe", sides, owner, side))
    c = _gm_call("sides_get", sides, owner)
    return c is not None and c.get("diplomacy") == "foe"


def galaxy_map_marker_color(sides, owner, side, kind, controlled=False):
    """A system glyph's color by what it is TO YOU: yours green, a foe's red, a neutral
    owner's own color, otherwise the kind's. Unknown space stays grey - the map never
    tells you who owns a system you have not charted."""
    if kind == "fog":
        return _GM_KINDS["fog"][1]
    if controlled:
        return _GM_FRIENDLY
    if owner is None:
        return _GM_KINDS.get(kind, _GM_KINDS["empty"])[1]
    if galaxy_map_owner_is_foe(sides, owner, side):
        return _GM_HOSTILE
    return _gm_call("sides_color", sides, owner) or _GM_KINDS.get(kind, _GM_KINDS["empty"])[1]


def galaxy_map_unit_color(ship):
    """A ship token's health at a glance, from its shields: green, amber, red."""
    ds = ship.data_set
    cur = (ds.get("shield_val", 0) or 0) + (ds.get("shield_val", 1) or 0)
    mx = (ds.get("shield_max_val", 0) or 0) + (ds.get("shield_max_val", 1) or 0)
    frac = 1.0 if mx <= 0 else cur / mx
    if frac >= 0.66:
        return "#33ff66"
    if frac >= 0.33:
        return "#ffcc33"
    return "#ff4444"


# --- per-console state ---------------------------------------------------------------

def _gm_state(client_id):
    st = get_inventory_value(client_id, _GM_STATE, None)
    return st if isinstance(st, dict) else None


def galaxy_map_area(client_id):
    """The tile area this console's map shows."""
    return "galaxy_map:%s" % client_id


def galaxy_map_mode():
    """``tiles`` (this map) or ``classic`` (the theater on the Admiral, the button grid on
    Navigation) - the A/B knob, until the tile map has been played in the engine."""
    return str(get_shared_variable("GALAXY_MAP_MODE", "tiles") or "tiles").lower()


def galaxy_map_tiles():
    return galaxy_map_mode() == "tiles"


def galaxy_map_cols(client_id):
    """Tiles across - what the page hands the view."""
    st = _gm_state(client_id)
    zoom = st["zoom"] if st else 0
    return 3 * GALAXY_MAP_ZOOMS[zoom]


def _gm_owner_cell(client_id, st):
    """The system this console is IN: its ship's, or the overseer camera's."""
    if st["mode"] == "admiral":
        cam = get_inventory_value(client_id, "ADMIRAL_CAM", 0)
        ship = cam if cam and to_object(cam) is not None else None
    else:
        ctx = FrameContext.context
        ship = ctx.sbs.get_ship_of_client(client_id) if ctx is not None and ctx.sbs else None
        ship = ship if ship and to_object(ship) is not None else None
    if not ship:
        return None
    cell = _gm_call("ship_cell", ship)
    return (int(cell[0]), int(cell[1])) if cell else None


def galaxy_map_open(client_id, mode="nav"):
    """Get this console's map ready to draw. Call BEFORE building the page: a tile view
    whose first paint finds no area can never draw anything.

    Opening again keeps where the console was looking and what it had picked; the
    console's side is re-read, because it is whoever is sitting there now.
    """
    galaxy_map_setup()
    st = _gm_state(client_id)
    side = _gm_call("universe_console_side", client_id)
    if st is None or st.get("mode") != mode:
        st = {"mode": mode, "zoom": 1 if mode == "admiral" else 0, "ci": 0, "cj": 0,
              "sel": None, "unit": None, "owner": None, "rev": 0, "tokens": {},
              "badges": {}, "facts": None}
        set_inventory_value(client_id, _GM_STATE, st)
        owner = _gm_owner_cell(client_id, st)
        if owner is not None:
            st["ci"], st["cj"] = owner
            st["sel"] = owner
            st["owner"] = owner
    st["side"] = side
    _gm_refresh(client_id, st, force_tokens=True)
    return galaxy_map_area(client_id)


def galaxy_map_close(client_id):
    """Drop this console's map (it left the screen for good)."""
    from sbs_utils.procedural.tilemap import tilemap_unload
    tilemap_unload(galaxy_map_area(client_id))
    set_inventory_value(client_id, _GM_STATE, None)


def galaxy_map_revision(client_id):
    """What an ``on change`` watches: moves when the picked system, the picked unit, the
    focus, or what is true of the picked system changes - never on a timer, so a panel
    built on it is not torn down under a click."""
    st = _gm_state(client_id)
    return st["rev"] if st else 0


def _gm_bump(st):
    st["rev"] = st.get("rev", 0) + 1


def galaxy_map_selected(client_id):
    """The (i, j) this console picked, or None."""
    st = _gm_state(client_id)
    return tuple(st["sel"]) if st and st.get("sel") is not None else None


def galaxy_map_focus_cell(client_id):
    """The system in the middle of the map."""
    st = _gm_state(client_id)
    return (st["ci"], st["cj"]) if st else None


def galaxy_map_selected_unit(client_id):
    """``("ship", id)`` or ``("fleet", key)`` - the unit an order will move - or None."""
    st = _gm_state(client_id)
    u = st.get("unit") if st else None
    return tuple(u) if u else None


def galaxy_map_select_unit(client_id, unit):
    st = _gm_state(client_id)
    if st is None:
        return False
    st["unit"] = tuple(unit) if unit else None
    _gm_bump(st)
    _gm_refresh(client_id, st)
    return True


def galaxy_map_owner_cell(client_id):
    st = _gm_state(client_id)
    return tuple(st["owner"]) if st and st.get("owner") else None


def galaxy_map_home_cell(client_id):
    """Where this console's side calls home: its Admiral HQ, else the side's authored
    home, else (0, 0)."""
    st = _gm_state(client_id)
    side = st.get("side") if st else None
    if side:
        hqs = to_object_list(role("admiral_hq") & role(side)) or []
        if hqs:
            c = _gm_call("object_cell", hqs[0].id)
            if c:
                return (int(c[0]), int(c[1]))
        rec = _gm_call("sides_get", _gm_world()["sides"], side)
        homes = (rec.get("homes") or []) if rec is not None else []
        for h in homes:
            if len(h) == 2:
                return (int(h[0]), int(h[1]))
    return (0, 0)


# --- moving the map ------------------------------------------------------------------

def galaxy_map_pan(client_id, di, dj):
    """Look elsewhere: shift the middle of the map by (di, dj) systems. The page does
    not rebuild - the window regenerates under the same tiles."""
    st = _gm_state(client_id)
    if st is None:
        return False
    st["ci"] += int(di)
    st["cj"] += int(dj)
    _gm_bump(st)
    _gm_refresh(client_id, st)
    return True


def galaxy_map_focus(client_id, i, j, select=False):
    """Center the map on a system, and pick it when asked."""
    st = _gm_state(client_id)
    if st is None:
        return False
    st["ci"], st["cj"] = int(i), int(j)
    if select:
        st["sel"] = (int(i), int(j))
    _gm_bump(st)
    _gm_refresh(client_id, st)
    return True


def galaxy_map_zoom(client_id, step):
    """Show more systems (``step`` 1) or fewer (-1). True when the zoom changed - the
    PAGE must then be rebuilt, because the view's tiles are fixed at its build."""
    st = _gm_state(client_id)
    if st is None:
        return False
    zoom = max(0, min(len(GALAXY_MAP_ZOOMS) - 1, st["zoom"] + int(step)))
    if zoom == st["zoom"]:
        return False
    st["zoom"] = zoom
    _gm_bump(st)
    _gm_refresh(client_id, st, force_tokens=True)
    return True


def galaxy_map_zoom_text(client_id):
    st = _gm_state(client_id)
    n = GALAXY_MAP_ZOOMS[st["zoom"] if st else 0]
    return "%d across" % n


# --- the window ----------------------------------------------------------------------

def _gm_dims(st):
    wb = GALAXY_MAP_ZOOMS[st["zoom"]]
    return wb, wb + _GM_EXTRA_ROWS


def galaxy_map_cell_to_system(client_id, x, y):
    """The system a window tile belongs to, and where in its block the tile is:
    ``((i, j), (sx, sy))``."""
    st = _gm_state(client_id)
    if st is None:
        return None
    wb, hb = _gm_dims(st)
    bx, by = int(x) // 3, int(y) // 3
    return ((st["ci"] + bx - wb // 2, st["cj"] - (by - hb // 2)), (int(x) % 3, int(y) % 3))


def galaxy_map_system_to_cell(client_id, i, j):
    """The window tile in the MIDDLE of a system's block, or None when it is off the
    window."""
    st = _gm_state(client_id)
    if st is None:
        return None
    wb, hb = _gm_dims(st)
    bx = int(i) - st["ci"] + wb // 2
    by = hb // 2 - (int(j) - st["cj"])
    if not (0 <= bx < wb and 0 <= by < hb):
        return None
    return (3 * bx + 1, 3 * by + 1)


def galaxy_map_system_look(world, i, j, side, controlled):
    """``(kind, owner, glyph color)`` of a system as this side knows it."""
    known = _gm_call("universe_cell_known", world["systems"], i, j, world["reveal"])
    if not known:
        return "fog", None, _GM_KINDS["fog"][1]
    base = _gm_call("universe_system_kind", world["seed"], i, j, world["danger"]) or "empty"
    pair = _gm_call("universe_system_side", world["sides"], world["seed"], i, j, base)
    owner, kind = (pair[0], pair[1]) if pair else (None, base)
    if kind not in _GM_KINDS:
        kind = "empty"
    color = galaxy_map_marker_color(world["sides"], owner, side, kind,
                                    controlled=(i, j) in controlled)
    return kind, owner, color


def _gm_controlled(side):
    """The systems this side has built in - what makes a system YOURS."""
    if not side:
        return set()
    out = set()
    for p in to_object_list(role("admiral_platform") & role(side)) or []:
        c = _gm_call("object_cell", p.id)
        if c:
            out.add((int(c[0]), int(c[1])))
    return out


def _gm_quest_targets(side):
    """Systems an active quest of THIS side's ships is heading for."""
    return set(_gm_call("universe_quest_target_sectors", side) or ())


def _gm_frame_color(world, i, j, side, owner, known, controlled, quest, here, picked):
    """What the frame says, strongest last: a region's wash, whose it is, a quest target,
    where you are, what you picked."""
    color = _GM_FRAME
    wash = _gm_call("region_map_color", world["regions"], i, j)
    if wash:
        color = galaxy_map_shade(wash, 1.5) or color
    home = _gm_call("sides_home_owner", world["sides"], i, j)
    if (i, j) in controlled:
        color = galaxy_map_shade(_GM_FRIENDLY, 0.3) or color
    elif home is not None:
        # A side's home is common knowledge, charted or not.
        color = galaxy_map_shade(_gm_call("sides_color", world["sides"], home), 0.4) or color
    elif owner is not None and known:
        rel = _GM_HOSTILE if galaxy_map_owner_is_foe(world["sides"], owner, side) else \
            _gm_call("sides_color", world["sides"], owner)
        color = galaxy_map_shade(rel, 0.3) or color
    if quest:
        color = galaxy_map_shade(_GM_QUEST, 0.55) or color
    if here:
        color = galaxy_map_shade("#00aa66", 0.7) or color
    if picked:
        color = galaxy_map_shade("#cccc00", 0.75) or color
    return color


def _gm_units(client_id, st):
    """This side's ships and fleets: ``[(token id, (i, j), sprite, color, unit)]``."""
    side = st.get("side")
    out = []
    if not side:
        return out
    ctx = FrameContext.context
    mine = ctx.sbs.get_ship_of_client(client_id) if (ctx is not None and ctx.sbs
                                                       and st["mode"] == "nav") else 0
    for s in sorted(to_object_list(role("__player__") & role(side)) or [], key=lambda o: o.id):
        cell = _gm_call("ship_cell", s.id)
        if not cell:
            continue
        color = _GM_OWN_SHIP if s.id == mine else galaxy_map_unit_color(s)
        out.append(("gm%s:s:%s" % (client_id, s.id), (int(cell[0]), int(cell[1])),
                    "galaxy_map:ship", color, ("ship", s.id)))
    for f in sorted(_gm_call("admiralty_fleets_of_side", side) or [],
                    key=lambda r: str(r.get("key"))):
        key = f.get("key")
        cell = _gm_call("admiralty_fleet_cell", key)
        if not cell:
            continue
        out.append(("gm%s:f:%s" % (client_id, key), (int(cell[0]), int(cell[1])),
                    "galaxy_map:fleet", _GM_FLEET, ("fleet", key)))
    return out


def galaxy_map_unit_cell(unit):
    """The system a unit is in now, or None when it cannot be found."""
    if not unit:
        return None
    kind, ref = unit
    if kind == "ship":
        if to_object(ref) is None:
            return None
        cell = _gm_call("ship_cell", ref)
    else:
        cell = _gm_call("admiralty_fleet_cell", ref)
    return (int(cell[0]), int(cell[1])) if cell else None


def galaxy_map_unit_name(unit):
    if not unit:
        return ""
    kind, ref = unit
    if kind == "ship":
        obj = to_object(ref)
        return obj.name if obj is not None else "ship"
    return _gm_call("admiralty_fleet_officer_name", ref) or ("Fleet " + str(ref).upper())


def _gm_refresh(client_id, st, force_tokens=False):
    """Regenerate the window and its tokens and badges. Nothing that did not change is
    touched, so a quiet refresh sends nothing to the console."""
    from sbs_utils.procedural.tilemap import (tilemap_generate, tilemap_place, tilemap_remove,
                                              tilemap_touch, tilemap_where)
    world = _gm_world()
    side = st.get("side")
    wb, hb = _gm_dims(st)
    ci, cj = st["ci"], st["cj"]
    controlled = _gm_controlled(side)
    quests = _gm_quest_targets(side)
    here = tuple(st["owner"]) if st.get("owner") else None
    picked = tuple(st["sel"]) if st.get("sel") else None

    blocks = {}
    for by in range(hb):
        for bx in range(wb):
            i, j = ci + bx - wb // 2, cj - (by - hb // 2)
            kind, owner, glyph = galaxy_map_system_look(world, i, j, side, controlled)
            frame = _gm_frame_color(world, i, j, side, owner, kind != "fog", controlled,
                                    (i, j) in quests, (i, j) == here, (i, j) == picked)
            blocks[(bx, by)] = ("sys_" + kind, glyph, frame)

    def cell(x, y):
        kind, glyph, frame = blocks[(x // 3, y // 3)]
        sub = (x % 3, y % 3)
        if sub == (1, 1):
            return (kind, glyph)
        return (_GM_FRAME_KINDS[sub], frame)

    area = galaxy_map_area(client_id)
    tilemap_generate(area, 3 * wb, 3 * hb, cell, _GM_TILESET,
                     title="Galaxy (%d, %d)" % (ci, cj))

    # TOKENS: ships along the top of their system's frame, fleets along the bottom.
    placed, badges, rows = {}, {}, {}
    for token, (i, j), sprite, color, _unit in _gm_units(client_id, st):
        bx, by = i - ci + wb // 2, hb // 2 - (j - cj)
        if not (0 <= bx < wb and 0 <= by < hb):
            continue
        sy = 0 if sprite.endswith("ship") else 2
        k = rows.get((bx, by, sy), 0)
        rows[(bx, by, sy)] = k + 1
        if k < 3:
            placed[token] = (3 * bx + k, 3 * by + sy, sprite, color)
        else:
            badges[(3 * bx + 2, 3 * by + sy)] = ("galaxy_map:more", "white")
    old = st.get("tokens") or {}
    for token in set(old) - set(placed):
        tilemap_remove(token)
    for token, (x, y, sprite, color) in placed.items():
        if force_tokens or old.get(token) != (x, y, sprite, color) or tilemap_where(token) is None:
            tilemap_place(token, area, x, y, sprite=sprite, color=color, party=False,
                          blocks=False, fixed=True)
    st["tokens"] = placed

    # BADGES: a quest flag east of the glyph, a "headed here" mark west of it.
    for (i, j) in quests:
        c = galaxy_map_system_to_cell(client_id, i, j)
        if c is not None:
            badges[(c[0] + 1, c[1])] = ("galaxy_map:quest", _GM_QUEST)
    for s in to_object_list(role("__player__") & role(side)) if side else []:
        dest = get_inventory_value(s.id, "active_objective", None)
        if dest and len(dest) == 2:
            cur = _gm_call("ship_cell", s.id)
            if cur and (int(dest[0]), int(dest[1])) != (int(cur[0]), int(cur[1])):
                c = galaxy_map_system_to_cell(client_id, int(dest[0]), int(dest[1]))
                if c is not None:
                    badges[(c[0] - 1, c[1])] = ("galaxy_map:dest", _GM_DEST)
    if badges != st.get("badges"):
        st["badges"] = badges
        tilemap_touch(area)

    # REVISION: what is true of the picked system, so a panel showing it follows it.
    facts = (picked, here, st.get("unit"), (ci, cj), st["zoom"],
             blocks.get(_gm_block_of(st, picked)) if picked else None,
             tuple(sorted(t for t, v in placed.items()
                          if picked and _gm_block_xy(v) == _gm_block_of(st, picked))))
    if facts != st.get("facts"):
        if st.get("facts") is not None:
            _gm_bump(st)
        st["facts"] = facts


def _gm_block_of(st, cell):
    if cell is None:
        return None
    wb, hb = _gm_dims(st)
    return (cell[0] - st["ci"] + wb // 2, hb // 2 - (cell[1] - st["cj"]))


def _gm_block_xy(token):
    return (token[0] // 3, token[1] // 3)


def galaxy_map_sync(client_id):
    """The once-a-second refresh: follow the console's own ship (or camera) to a new
    system, then regenerate. Cheap when nothing moved."""
    st = _gm_state(client_id)
    if st is None:
        return False
    owner = _gm_owner_cell(client_id, st)
    if owner is not None and owner != (tuple(st["owner"]) if st.get("owner") else None):
        st["owner"] = owner
        st["ci"], st["cj"] = owner
        st["sel"] = owner
        _gm_bump(st)
    unit = tuple(st["unit"]) if st.get("unit") else None
    if unit and unit not in [u[4] for u in _gm_units(client_id, st)]:
        # The picked ship was lost, or the fleet stood down.
        st["unit"] = None
        _gm_bump(st)
    _gm_refresh(client_id, st)
    return True


# --- clicks and badges ---------------------------------------------------------------

def galaxy_map_click(client_id, area, x, y):
    """A tile click: pick the system it belongs to, and the unit when a token was hit.

    Picking a system KEEPS the picked unit, which is the whole order gesture: click a
    fleet, then click where it should go.
    """
    from sbs_utils.procedural.tilemap import tilemap_actors_at
    st = _gm_state(client_id)
    if st is None or area != galaxy_map_area(client_id):
        return False
    hit = galaxy_map_cell_to_system(client_id, x, y)
    if hit is None:
        return False
    (i, j), _sub = hit
    st["sel"] = (i, j)
    for token in tilemap_actors_at(area, x, y):
        for t, _cell, _sprite, _color, unit in _gm_units(client_id, st):
            if t == token:
                st["unit"] = unit
    _gm_bump(st)
    _gm_refresh(client_id, st)
    if st["mode"] == "admiral":
        _gm_call("admiral_galaxy_map_on_select", client_id)
    return True


def galaxy_map_hints(client_id, area):
    """The badges this console's map shows: ``{(x, y): (atlas key, tint)}``."""
    st = _gm_state(client_id)
    return dict(st.get("badges") or {}) if st else {}


# --- words ---------------------------------------------------------------------------

def galaxy_map_kind_word(kind):
    return _GM_KIND_WORD.get(kind, "System")


def galaxy_map_system_facts(client_id, i, j):
    """``{"title", "kind", "owner", "known", "veiled"}`` for a system, as this console's
    side knows it."""
    st = _gm_state(client_id)
    side = st.get("side") if st else None
    world = _gm_world()
    kind, owner, _ = galaxy_map_system_look(world, i, j, side, _gm_controlled(side))
    known = kind != "fog"
    owner_name = _gm_call("sides_name", world["sides"], owner) if (owner and known) else None
    title = _gm_call("universe_system_title", world["landmarks"], world["regions"], i, j,
                     owner_name) if known else None
    return {
        "title": (title[0] if title else "(%d, %d)" % (i, j)) if known else "Uncharted",
        "kind": galaxy_map_kind_word(kind),
        "owner": (owner_name or "Unclaimed") if known else "Unknown",
        "known": known,
        "veiled": bool(_gm_call("region_is_veiled", world["regions"], i, j)),
    }


def _gm_cell_text(text):
    return str(text if text is not None else "").replace("|", "/").replace("{", "(") \
        .replace("}", ")").replace(chr(10), " ").strip()


def galaxy_map_info_text(client_id):
    """The picked system as a short markdown grid, for a text area. No braces, ever: a
    MAST assignment of this string re-formats it as an f-string."""
    sel = galaxy_map_selected(client_id)
    if sel is None:
        return "Click a system on the map."
    i, j = sel
    f = galaxy_map_system_facts(client_id, i, j)
    here = galaxy_map_owner_cell(client_id)
    lines = ["### " + _gm_cell_text(f["title"]), "", "| | |", "|:--|:--|",
             "| Coords | (%d, %d) |" % (i, j),
             "| Type | %s |" % _gm_cell_text(f["kind"]),
             "| Owner | %s |" % _gm_cell_text(f["owner"])]
    if here is not None:
        d = abs(i - here[0]) + abs(j - here[1])
        lines.append("| Jumps away | %s |" % ("you are here" if d == 0 else str(d)))
    unit = galaxy_map_selected_unit(client_id)
    if unit:
        lines.append("| Unit | %s |" % _gm_cell_text(galaxy_map_unit_name(unit)))
    if f["veiled"]:
        lines += ["", "ANTIMATTER VEIL - unsurvivable to linger."]
    return chr(10).join(lines)


def galaxy_map_title_text(client_id):
    """The Nav header: the system this console's ship is in."""
    here = galaxy_map_owner_cell(client_id)
    if here is None:
        return "Galaxy"
    f = galaxy_map_system_facts(client_id, here[0], here[1])
    return "%s  (%d, %d)  %s" % (_gm_cell_text(f["title"]), here[0], here[1],
                                 _gm_cell_text(f["kind"]))


def galaxy_map_known_places(client_id):
    """Home, side homes and this side's quest targets - for a list a console picks from."""
    st = _gm_state(client_id)
    side = st.get("side") if st else None
    world = _gm_world()
    places = _gm_call("universe_known_locations", world["sides"], _gm_quest_targets(side))
    return list(places or [MastDataObject({"name": "Home Base", "i": 0, "j": 0})])
