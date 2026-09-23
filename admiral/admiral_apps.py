"""The Admiral's right-hand panel: the xESS shell, with this console's content as apps.

Both Admiral views - the system overseer and the galaxy theater - used to spend their right
column on `comms_face` + `comms_control` and one hard-coded list underneath. The comms
buttons now draw in the 2D view itself, so the column is free, and what was pinned there
becomes tiles: Info, Build, Forces, Log.

WHERE AM I. The bar above the tiles names the SYSTEM - "The Ossuary", "Home Port",
"Uncharted (9, 9)" - because neither view said so anywhere, and an overseer who cannot
name the place they are looking at cannot talk about it either. It uses
`universe_system_title`, the same function the crew's arrival card uses, so both consoles
call a system by the same name.

TWO SURFACES, NOT ONE. The system view and the theater are different places with different
questions, so an app opened on one does not follow you to the other (xESS keys its open-app
state per surface). Forces and Log are registered on both; Build belongs to the economy.

The bar carries the live status line and the app area carries the tiles, and the shell
repaints those two separately - which is why the build countdown can tick every second
without replacing the queue row under a cursor.

Prefixed `admiral_app_` because every public function here is a MAST global in one flat,
mission-wide namespace.
"""
from sbs_utils.helpers import FrameContext
from sbs_utils.procedural.execution import get_shared_variable, set_shared_variable, task_schedule
from sbs_utils.procedural.gui import gui_row, gui_text, gui_blank
from sbs_utils.procedural.gui.listbox import gui_list_box
from sbs_utils.procedural.gui.text import gui_text_area
from sbs_utils.procedural.gui.button import gui_button
from sbs_utils.procedural.gui.message import gui_message_callback
from sbs_utils.procedural.gui.xess import (xess_register, xess_surface, xess_focus,
                                           xess_set_focus, gui_xess_head)
from sbs_utils.procedural.inventory import get_inventory_value
from sbs_utils.procedural.query import object_exists, to_object, to_object_list
from sbs_utils.procedural.roles import role

#: The system overseer's panel, and the galaxy theater's.
SURFACE_SYSTEM = "admiral"
SURFACE_GALAXY = "admiral_galaxy"

#: Kind -> the word the board already uses for it, so the bar and the map agree.
_KIND_WORD = {
    "home": "Home", "station": "Base", "enemy": "Threat", "nebula": "Nebula",
    "anomaly": "Anomaly", "empty": "System", "fog": "Unknown",
}

#: How wide the panel is, in PIXELS on every display. Wide enough for a tile's icon,
#: title and blurb, and for a system name beside its coordinates - measured at 1024x768,
#: the narrowest screen anyone plays on, where 28% was 287px and everything wrapped.
ADMIRAL_PANEL_PX = 360

_DIM = "#9ab"
_ACCENT = "#8cf"


def _sibling(name):
    """A sibling helper from the mission's shared namespace, or None.

    In the game every mission .py execs into ONE dict, so `ship_cell` and the `admiralty_*`
    family are simply in scope. Imported as a plain package (a unit test, a tool) they are
    not, and a bare call raises NameError - which stops whichever command was drawing.
    Same lookup `admiral_chips.py` uses, for the same reason.
    """
    fn = globals().get(name)
    if fn is not None:
        return fn
    from sbs_utils.mast.mast_globals import MastGlobals
    return MastGlobals.globals.get(name)


def _call(name, *args, **kwargs):
    """Call a sibling global if it exists; None when the addon that owns it is not loaded."""
    fn = _sibling(name)
    if fn is None:
        return None
    try:
        return fn(*args, **kwargs)
    except Exception:                                    # noqa: BLE001 - a panel must not die
        return None


def _cam(client_id, surface):
    """The camera this panel's view rides: the command cambot, or the galaxy board's."""
    return get_inventory_value(client_id,
                               "GALAXY_CAM" if surface == SURFACE_GALAXY else "ADMIRAL_CAM", 0)


def admiral_app_cell(client_id, surface=SURFACE_SYSTEM):
    """The (i, j) this panel is ABOUT.

    The system view is about where the overseer's camera is. The theater is about the
    centre of the board on screen - the cam parks among its markers out in dead space, so
    its own position says nothing about which part of the galaxy is being shown.
    """
    cam = _cam(client_id, surface)
    if not cam or not object_exists(cam):
        return None
    if surface == SURFACE_GALAXY:
        i = get_inventory_value(cam, "board_ci", None)
        j = get_inventory_value(cam, "board_cj", None)
        if i is None or j is None:
            return None
        return (int(i), int(j))
    cell = _call("ship_cell", cam)
    return (int(cell[0]), int(cell[1])) if cell else None


def admiral_app_side(client_id):
    """The side this console commands."""
    return _call("universe_console_side", client_id)


def _system_of(i, j):
    """(kind, owner) for a cell, the way the galaxy board derives them."""
    seed = get_shared_variable("universe_seed", 0)
    sides = get_shared_variable("UNIVERSE_SIDES", None)
    danger = get_shared_variable("DANGER", "Quiet")
    kind = _call("universe_system_kind", seed, i, j, danger) or "empty"
    pair = _call("universe_system_side", sides, seed, i, j, kind)
    if pair is None:
        return kind, None
    owner, kind = pair
    return kind, owner


def admiral_app_system_title(client_id, surface=SURFACE_SYSTEM):
    """`(name, subtitle)` for the system this panel is about - the arrival card's words.

    An unnamed cell answers "Uncharted (i, j)" rather than blank: not knowing a system's
    name is ordinary, and a blank bar reads as a broken one.
    """
    cell = admiral_app_cell(client_id, surface)
    if cell is None:
        return ("No system", "")
    i, j = cell
    _, owner = _system_of(i, j)
    sides = get_shared_variable("UNIVERSE_SIDES", None)
    owner_name = _call("sides_name", sides, owner) if owner else None
    title = _call("universe_system_title",
                  get_shared_variable("UNIVERSE_LANDMARKS", None),
                  get_shared_variable("UNIVERSE_REGIONS", None), i, j, owner_name)
    if not title:
        return ("(%d, %d)" % (i, j), "")
    return (title[0], title[1])


def _control_word(client_id, i, j):
    """Yours / Contested / the owner's name / Unclaimed - in that order, because that is
    the order an overseer cares about."""
    side = admiral_app_side(client_id)
    if side and _call("admiralty_side_controls_cell", side, i, j):
        return "Yours"
    if side and _call("admiralty_cell_has_hostiles", side, i, j):
        return "Contested"
    _, owner = _system_of(i, j)
    if owner:
        sides = get_shared_variable("UNIVERSE_SIDES", None)
        return _call("sides_name", sides, owner) or str(owner)
    return "Unclaimed"


def admiral_app_identity(client_id, surface=SURFACE_SYSTEM):
    """The panel bar's three slots: what this place is called, what it is, how things are.

    THE SECOND SLOT IS THE COORDINATES LINE AND NOTHING ELSE. It first carried the
    system's subtitle too - a landmark's description, which is prose - and a farming
    colony with two sentences to its name wrapped to three lines, left the bar and drew
    over the tile sheet below it. The engine does not clip. The prose has a home in the
    Info app, which can scroll; a bar row has to be one line by construction.
    """
    name, _sub = admiral_app_system_title(client_id, surface)
    cell = admiral_app_cell(client_id, surface)
    if cell is None:
        return (name, "", admiral_app_status(client_id))
    i, j = cell
    # COORDS AND WHOSE IT IS. Two short lines is all a bar row can hold at this width,
    # and the third slot is deliberately blank - see admiral_app_status. A SPACE rather
    # than "": empty text has been seen to render as a lone backtick.
    return (name, "(%d, %d)  %s" % (i, j, _control_word(client_id, i, j)), " ")


def admiral_app_status(client_id=None):
    """The live status line - a build's countdown, the last order, a rejection.

    IT DOES NOT GO ON THE BAR. It is a sentence a mission writes ("No extractors yet -
    build an Extractor on a worldlet to produce ore and gas."), so its length is not ours
    to control, and a bar row is one line by construction: on a 28% column it wrapped to
    six lines and drew straight down over the tiles. Measured in the engine twice, and
    the second attempt - shortening what sat beside it - was treating a design mistake as
    a spacing one.

    So it is the tile sheet's PROSE BAND (`home_text`), which is a text area: it has the
    panel's full width, it scrolls itself, and it is capped so it can never push the tiles
    off the bottom. It is also still in the Log app in full, and still filed as an info
    card by the routes that set it - three surfaces, each with room for it.

    THIS SIDE'S. The queue and the message live on the side's Admiralty, so a rival
    admiral's construction no longer reports itself on your panel."""
    side = admiral_app_side(client_id)
    line = _call("admiralty_status_line", _builds(side), _call("admiralty_msg", side) or "")
    return line or ""


def _builds(side):
    """This side's build queue - the list itself, which the build tasks mutate."""
    return _call("admiralty_builds", side) or []


def admiral_app_revision(client_id, surface=SURFACE_SYSTEM):
    """What the APP AREA rebuilds for - never a timer.

    The build countdown lives on the bar, which is compared separately. Put a clock in
    here and every tile sheet is torn down and rebuilt once a second, which on the Build
    app means the queue row under the cursor is replaced as it is clicked.
    """
    side = admiral_app_side(client_id)
    key = _call("admiralty_build_count_key", _builds(side), _call("admiralty_msg", side) or "")
    extra = None
    if surface == SURFACE_GALAXY:
        extra = _call("galaxy_theater_roster_sig", admiral_app_side(client_id))
    return (key, admiral_app_cell(client_id, surface), extra)


# --- the apps ------------------------------------------------------------------------

def _economy():
    return bool(get_shared_variable("ADMIRALTY_ECONOMY", False))


def _economy_available(client_id):
    return _economy()


def admiral_app_info_draw(client_id):
    """INFO - where you are, what is here, and what you have.

    This is the title band's content, which used to be a full-width strip above the map
    carrying the resource ticker and nothing else. As an app it can answer the question
    the strip could not: which system this is.
    """
    surface = _drawing_surface(client_id)
    gui_xess_head(client_id, "Info", surface=surface)
    cell = admiral_app_cell(client_id, surface)
    side = admiral_app_side(client_id)
    name, sub = admiral_app_system_title(client_id, surface)

    gui_row("row-height: 1.6em; padding: 4px, 8px, 0, 10px;")
    gui_text("$text:%s;font:gui-3;overflow:shrink;" % name)
    if sub:
        # `content`, not a fixed 1.2em: a system's description is a sentence, and at
        # gui-1 (the smallest font, so `shrink` has nowhere to go) it wraps. In a fixed
        # row the second line was drawn over the facts below it (engine-seen).
        gui_row("row-height: content; padding: 0, 8px, 4px, 10px;")
        gui_text("$text:%s;font:gui-1;color:%s;" % (sub, _DIM))

    if cell is None:
        gui_row("row-height: 1.4em; padding: 4px, 8px, 4px, 10px;")
        gui_text("$text:No camera - reopen the console.;font:gui-1;color:%s;" % _DIM)
        gui_row("row-height: 1fr;")
        gui_blank()
        return
    i, j = cell
    kind, owner = _system_of(i, j)
    sides = get_shared_variable("UNIVERSE_SIDES", None)
    # ONE text area holding a header-less GRID, rather than a pair of gui_text widgets
    # per fact at a hand-set 7em label column. The grid sizes its label column to the
    # longest label, and the yes/no answers are icons a glance can read.
    facts = [
        ("Coords", "(%d, %d)" % (i, j)),
        ("Type", _KIND_WORD.get(kind, "System")),
        ("Owner", (_call("sides_name", sides, owner) or str(owner)) if owner else "Unclaimed"),
        ("Control", _control_word(client_id, i, j)),
        ("Worldlets", str(len(_call("worldlets_in_cell", i, j) or []))),
    ]
    if side:
        plats = [p for p in (to_object_list(role("admiral_platform") & role(side)) or [])
                 if _cell_of(p.id) == cell]
        facts.append(("Platforms", str(len(plats))))
        facts.append(("Fleet here", _yes_no(_call("admiralty_side_fleet_in_cell", side, i, j))))
        facts.append(("Hostiles", _yes_no(_call("admiralty_cell_has_hostiles", side, i, j),
                                          yes_icon="skull", yes_color="Crimson")))
    lines = ["| | |", "|:--|:--|"] + ["| %s | %s |" % (_cell(k), v) for k, v in facts]

    if _economy() and side:
        ticker = _call("admiralty_ticker_text", side) or ""
        parts = [p.strip() for p in ticker.split("  ") if p.strip()]
        if parts:
            # A BLANK line after the heading: a heading's style carries onto the lines
            # under it until one, so the stock came out heading-sized (engine-seen).
            lines += ["", "### Admiralty", ""] + [_ticker_line(p) for p in parts]
    gui_row("row-height: 1fr; padding: 4px, 8px, 0, 10px;")
    gui_text_area(chr(10).join(lines))


def _ticker_line(part):
    """One ticker entry. `ORE 2400/4800` - a stock against its capacity - is a GAUGE,
    so how full the store is reads at a glance; anything else stays text."""
    import re
    m = re.match(r"^([A-Za-z][\w ]*?)\s+(-?\d+)\s*/\s*(\d+)$", part)
    if m is None:
        return _cell(part)
    label, have, cap = m.group(1).strip(), int(m.group(2)), int(m.group(3))
    return "[%s](gauge://%d?max=%d&show=frac)" % (label.replace("]", ""), have, max(cap, 1))


def _cell(text):
    """A value going into a grid cell: a `|` would split the row."""
    return str(text if text is not None else "").replace("|", "/").replace(chr(10), " ").strip()


def _yes_no(flag, yes_icon="check.on", yes_color="springgreen"):
    """A yes/no fact as an icon and the word, so it reads at a glance."""
    if flag:
        return "![](icon://%s?color=%s) yes" % (yes_icon, yes_color)
    return "![](icon://check.off?color=%s) no" % _DIM


def _cell_of(obj_id):
    cell = _call("object_cell", obj_id)
    return (int(cell[0]), int(cell[1])) if cell else None


def admiral_app_build_draw(client_id):
    """BUILD - the queue, and the way to stop one.

    The list and its templates are the ones the console has always drawn; what changed is
    that a countdown on the bar no longer rebuilds them underneath a click.
    """
    surface = _drawing_surface(client_id)
    gui_xess_head(client_id, "Build", surface=surface)
    builds = _builds(admiral_app_side(client_id))
    if not builds:
        gui_row("row-height: 1.6em; padding: 6px, 8px, 6px, 10px;")
        gui_text("$text:Nothing under construction.;font:gui-1;color:%s;" % _DIM)
        gui_row("row-height: 1.4em; padding: 0, 8px, 6px, 10px;")
        gui_text("$text:Click a worldlet on the map to build.;font:gui-1;color:%s;" % _DIM)
        gui_row("row-height: 1fr;")
        gui_blank()
        return
    gui_row("row-height: 1fr;")
    lb = gui_list_box(builds, "row-height: 1.8em;",
                      item_template=_sibling("admiralty_build_row"),
                      title_template=_sibling("admiralty_build_title"), select=True)
    gui_message_callback(lb, lambda event, sender, _cid=client_id, _lb=lb, _s=surface:
                         xess_set_focus(_cid, _lb.get_value(), _s))
    gui_row("row-height: 2.2em; padding: 6px, 8px, 6px, 8px;")
    gui_button("Cancel selected",
               on_press=lambda _cid=client_id, _s=surface:
               admiral_app_cancel(xess_focus(_cid, _s), admiral_app_side(_cid)))


def admiral_app_cancel(rec, side=None):
    """Stop a queued build. True when there was one to stop.

    A bare string is a legacy row (research runs file one), so it is refused rather than
    crashed on - `admiralty_build_row` already tolerates them in the list. The build task
    itself notices `cancel`, refunds and frees the worldlet; this only asks.
    """
    if rec is None or isinstance(rec, str):
        return False
    try:
        rec.cancel = True
        name = rec.get("name", "build")
    except Exception:                                    # noqa: BLE001
        return False
    if side is not None:
        _call("admiralty_say", side, "Cancelling " + str(name) + "...")
    return True


def admiral_app_forces_draw(client_id):
    """FORCES - who is where, and a way to go and look.

    Window-INDEPENDENT, like the roster it replaces: a ship three systems past the edge of
    the board is still listed. On the system view this is new - "who is where" used to be
    the theater's alone.
    """
    surface = _drawing_surface(client_id)
    gui_xess_head(client_id, "Forces", surface=surface)
    side = admiral_app_side(client_id)
    rows = _call("galaxy_theater_roster_items", side) or []
    if not rows:
        gui_row("row-height: 1.6em; padding: 6px, 8px, 6px, 10px;")
        gui_text("$text:No ships or fleets.;font:gui-1;color:%s;" % _DIM)
        gui_row("row-height: 1fr;")
        gui_blank()
        return
    gui_row("row-height: 1fr;")
    lb = gui_list_box(rows, "row-height: 1.7em;",
                      item_template=_sibling("galaxy_theater_roster_item_template"),
                      title_template=_sibling("galaxy_theater_roster_title"), select=True)
    gui_message_callback(lb, lambda event, sender, _cid=client_id, _lb=lb:
                         admiral_app_focus(_cid, _lb.get_value()))


def admiral_app_focus(client_id, row):
    """Take the overseer to a roster row's system - the same jump the map's menu uses."""
    if row is None:
        return False
    try:
        i, j = int(row.i), int(row.j)
    except Exception:                                    # noqa: BLE001
        return False
    task_schedule("theater_jump_here", {"JMP_I": i, "JMP_J": j, "JH_CLIENT": client_id})
    return True


def admiral_app_log_draw(client_id):
    """LOG - the queue in full, one build per line, and the last thing that happened."""
    surface = _drawing_surface(client_id)
    gui_xess_head(client_id, "Log", surface=surface)
    side = admiral_app_side(client_id)
    text = _call("admiralty_build_queue_area", _builds(side), _call("admiralty_msg", side) or "")
    # NEVER an empty text area: empty text renders as a lone backtick.
    gui_row("row-height: 1fr; padding: 4px, 8px, 4px, 10px;")
    gui_text_area(text if (text or "").strip() else "Nothing to report.")


def admiral_padd_research_badge():
    """The Research tile's badge: how many milestones this side could start now.

    An ePADD status provider takes NO arguments, so it reads the console off the page the
    same way the panel's badges do - and answers "" rather than a wrong number when there
    is no console to ask about.
    """
    page = FrameContext.page
    cid = getattr(page, "client_id", None) if page is not None else None
    if cid is None:
        return ""
    side = admiral_app_side(cid)
    if side is None:
        return ""
    items = _call("research_list") or []
    n = 0
    for item in items:
        try:
            if (_call("research_state", side, item.get("key")) or "").lower() == "available":
                n += 1
        except Exception:                                # noqa: BLE001
            continue
    return str(n) if n else ""


def _build_badge():
    """How many builds are running - for the tile.

    A badge provider is called with NO arguments, so it reads the console off the page
    the way the handheld's own badges do. No console, no number rather than a wrong one.
    """
    page = FrameContext.page
    cid = getattr(page, "client_id", None) if page is not None else None
    if cid is None:
        return ""
    builds = _builds(admiral_app_side(cid))
    return str(len(builds)) if builds else ""


# --- registration ----------------------------------------------------------------------
#
# WHICH SURFACE IS DRAWING. An app's `draw` is handed only a client id, and both panels
# register the same drawing functions, so the surface is remembered as the panel is built.
# It decides where Back goes - a Back that names the wrong surface closes nothing.

_DRAWING = {}


def admiral_app_drawing(client_id, surface):
    """Remember which panel this console is building, for the apps' Back buttons."""
    _DRAWING[client_id] = surface
    return surface


def _drawing_surface(client_id):
    return _DRAWING.get(client_id, SURFACE_SYSTEM)


def admiral_apps_clear():
    """Forget which panel each console was drawing (mission reset / tests)."""
    _DRAWING.clear()


def admiral_apps_register():
    """Put the Admiralty's surfaces and apps on the device. Idempotent.

    Called from the console page rather than at load, because `xess_clear()` on a mission
    reset drops every mission surface and re-registers only the handheld's built-ins.
    """
    for surface in (SURFACE_SYSTEM, SURFACE_GALAXY):
        # PIXELS, NOT PERCENTAGES - in both directions, and for the same reason.
        #
        # The console's tab strip (and the ePADD button on it) owns the first 45px
        # whatever the screen is, so a percentage TOP put the panel under it at one
        # resolution and clear of it at another. 45 + 30 (NAME_PX) + 26 (SUB_PX) = 101,
        # so the bar ends at 105px with a little air.
        #
        # The WIDTH is the one that actually bit. At 28% the column was ~360px on a 1280
        # screen and ~287px at 1024x768 - and text does not shrink with the screen, so a
        # layout that fitted at one resolution wrapped and overlapped at the other. A
        # panel holds words, and words want a width in PIXELS: `100-PANEL_PX` is the same
        # column on every display, and the map takes whatever is left. This is the
        # arrangement LM's helm console already uses for the engine widgets it owns.
        xess_surface(surface, title="Admiralty",
                     identity=lambda cid, _s=surface: admiral_app_identity(cid, _s),
                     revision=lambda cid, _s=surface: admiral_app_revision(cid, _s),
                     # The status line lives HERE, above the tiles, where a sentence has
                     # the width to be one - not in the bar (see admiral_app_status).
                     home_text=lambda cid: admiral_app_status(cid),
                     identity_area="area: 100-%dpx, 45px, 100, 105px;" % ADMIRAL_PANEL_PX,
                     app_area="area: 100-%dpx, 105px, 100, 100;" % ADMIRAL_PANEL_PX)
        xess_register("info", title="Info", icon="sitemap", sort=10,
                      blurb="Where you are, and what you have",
                      draw=admiral_app_info_draw, surface=surface)
        xess_register("forces", title="Forces", icon="squad", sort=30,
                      blurb="Who is where - click to go there",
                      draw=admiral_app_forces_draw, surface=surface)
        xess_register("log", title="Log", icon="folder", sort=90,
                      blurb="The queue, in full",
                      draw=admiral_app_log_draw, surface=surface)
    xess_register("build", title="Build", icon="factory", sort=20,
                  blurb="What is under construction",
                  draw=admiral_app_build_draw, badge=_build_badge,
                  available=_economy_available, surface=SURFACE_SYSTEM)
    return True
