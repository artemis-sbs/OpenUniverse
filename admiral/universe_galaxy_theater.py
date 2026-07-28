"""Galaxy theater - the admiral's strategic map as a 2D-view board of real marker
objects in the dead space far from the play slots (ADMIRAL_CONSOLE.md section 19).
Markers never move and the galaxy cambot parks among them, so far-coordinate float
precision (a movement problem) doesn't matter. Still HQ-button-triggered while it grows
into the Galaxy tab.

The client is TEMPORARILY re-assigned to the galaxy cambot to view the board (returns
to its command cambot via the per-client ADMIRAL_CAM) - the engine-solid way to move a
console's view (assign_client_to_alt_ship did not move the detached comms 2D view).

Shared-namespace notes (like the other universe_*.py files): no relative sibling
imports; sbs_utils absolute imports only. universe_system_kind / universe_system_side /
universe_cell_known come from sibling modules via the merged MAST namespace.
"""
from sbs_utils.procedural.spawn import terrain_spawn, player_spawn
from sbs_utils.procedural.roles import role, remove_role
from sbs_utils.procedural.query import to_object_list, to_object
from sbs_utils.procedural.inventory import set_inventory_value, get_inventory_value
from sbs_utils.procedural.science import science_set_scan_data
from sbs_utils.procedural.gui import gui_row, gui_text
from sbs_utils.helpers import FrameContext
from sbs_utils.mast.mast_node import MastDataObject
from sbs_utils.vec import Vec3


# Far from the play slots (within +-1M); markers are static so the distance is safe.
GALAXY_THEATER = Vec3(50_000_000.0, 0.0, 0.0)
THEATER_SPACING = 4_000.0
# A COPY PER ADMIRAL: each overseer's galaxy cam gets its own board REGION, offset in z
# by (slot * GALAXY_REGION_GAP) so boards never overlap. The gap is well beyond a cam's
# radar range (40k) + the board span (~24k), so each cam sees only its own board.
GALAXY_REGION_GAP = 200_000.0
# The static system-marker GRID is drawn in a small dense window around the overseer's
# cell (GALAXY_GRID_WIN), but friendly UNIT/FLEET icons render out to the radar's full
# visible edge (GALAXY_UNIT_WIN ~= scan range 40k / THEATER_SPACING) so a ship or fleet
# sent SYSTEMS away still shows on the board - not just those in the dense grid. Beyond the
# radar edge an icon can't be drawn at all; the "who is where" roster covers those.
GALAXY_GRID_WIN = 3
GALAXY_UNIT_WIN = 10

# Icon vocabulary: system KIND -> (art, color, scale, icon_index). behav_selection is
# SPECIAL - it draws a flat RADAR ICON from the game atlas (icon_index), sized by icon_scale
# and tinted by radar_color_override; it does NOT render the ship mesh. So the `art` arg is
# effectively ignored for these markers (kept only as a spawn placeholder); the glyph is
# entirely the icon_index. icon_scale is what makes a unit token read smaller than a system.
# The icon_index values are the authored atlas glyphs (a later `## Galaxy Icons` AMD chapter
# can own this mapping).
_KIND_ICON = {
    "home":    ("starbase_command",  "#33ff66", 1.4, 159),
    "station": ("starbase_civil",    "#00ccff", 1.2, 114),
    "enemy":   ("tsn_light_cruiser", "#ff4444", 1.2, 78),
    "nebula":  ("unknown",           "#cc66ff", 1.1, 8),
    "anomaly": ("unknown",           "#aa33ff", 1.1, 0),
    "empty":   ("unknown",           "#888888", 0.8, 129),
    "fog":     ("unknown",           "#555555", 0.8, 121),
}

# Friendly-unit icons: kept deliberately SMALLER than the system markers (and offset to a
# cell corner) so a ship/fleet reads as a token ON its system, not a second system.
# Format: (icon_index, icon_scale).
GALAXY_SHIP_ICON = (140, 0.5)     # player ship
GALAXY_FLEET_ICON = (37, 0.7)    # fleet
# How far a unit icon sits from its system marker (fraction of a cell) - a corner offset so
# the marker + its unit token are clearly separated, not stacked.
GALAXY_UNIT_OFFSET = 0.36
# Fan-out (fractions of a cell) so MULTIPLE unit icons in the SAME system don't stack on one
# point. Slot 0 = the base corner; further slots step out around it. Kept small so the whole
# cluster stays inside the cell (base 0.36 + max ~0.11 < the 0.5 cell half-width).
_UNIT_FAN = [(0.0, 0.0), (0.09, 0.05), (-0.05, 0.09), (0.07, -0.08), (-0.08, -0.05),
             (0.11, -0.01), (-0.01, 0.11), (-0.11, 0.02), (0.02, -0.11)]


def _fan_xz(slot):
    """A small, STABLE per-slot (dx, dz) so co-located unit icons fan out instead of
    stacking. Slot is the unit's index among same-cell units (assigned in a stable id/key
    order), so an icon keeps its spot across reconciles."""
    f = _UNIT_FAN[slot % len(_UNIT_FAN)]
    return (THEATER_SPACING * f[0], THEATER_SPACING * f[1])

# A cell KIND -> friendly label word, so a marker's on-radar name reads as a place (not a
# bare code). Paired with the coordinates by galaxy_theater_marker_label.
_KIND_LABEL = {
    "home":    "Home",
    "station": "Base",
    "enemy":   "Threat",
    "nebula":  "Nebula",
    "anomaly": "Anomaly",
    "empty":   "System",
    "fog":     "Unknown",
}


def galaxy_theater_marker_label(kind, i, j):
    """A system marker's on-radar label: the cell KIND as a friendly word plus its (i, j)
    coordinates, so the overseer can always read a system's position at a glance - e.g.
    'Threat (2,1)', 'Home (0,0)', 'Unknown (5,4)' under fog. Derived from the SAME kind the
    marker's icon uses, so the label and the shape/colour always agree."""
    return _KIND_LABEL.get(kind, "System") + " (" + str(i) + "," + str(j) + ")"


# Relation colours for a system marker (diplomacy overrides kind): your controlled territory
# vs a hostile owner vs a neutral side's own colour.
_REL_FRIENDLY = "#33ff66"
_REL_HOSTILE = "#ff4444"


def galaxy_theater_marker_color(sides, i, j, side, owner, kind_color):
    """A system marker's radar colour by DIPLOMACY, not just kind. A system YOUR side
    controls (has built a structure in) reads friendly green; one owned by a side HOSTILE to
    your side (ceasefire-aware, _side_is_foe) reads red; one owned by a NEUTRAL side takes
    that side's own house colour (sides_color); an unowned + uncontrolled system keeps its
    kind colour. So enemy territory - including a foe side's HOME, whose kind is 'station' -
    stops reading as a neutral cyan base. admiralty_side_controls_cell / _side_is_foe /
    sides_color are sibling free globals."""
    if admiralty_side_controls_cell(side, i, j):
        return _REL_FRIENDLY
    if owner is None:
        return kind_color
    if _side_is_foe(sides, owner, side):
        return _REL_HOSTILE
    return sides_color(sides, owner)


def galaxy_theater_marker_pos(di, dj, rz):
    """World position of the marker at window offset (di, dj) from a board centred in the
    cam's region (region-z = rz)."""
    return Vec3(GALAXY_THEATER.x + di * THEATER_SPACING,
                GALAXY_THEATER.y,
                rz + dj * THEATER_SPACING)


def _unit_health_color(s):
    """A unit icon's at-a-glance HEALTH tint from its shield fraction (front + rear):
    green healthy -> amber -> red. Shields are the readable live health proxy (a true
    hull % isn't one field); shield_val/shield_max_val index 0=front, 1=rear."""
    cur = (s.data_set.get("shield_val", 0) or 0) + (s.data_set.get("shield_val", 1) or 0)
    mx = (s.data_set.get("shield_max_val", 0) or 0) + (s.data_set.get("shield_max_val", 1) or 0)
    frac = 1.0 if mx <= 0 else cur / mx
    if frac >= 0.66:
        return "#33ff66"
    if frac >= 0.33:
        return "#ffcc33"
    return "#ff4444"


def _unit_label(s, cell):
    """A unit icon's label: ship name + its CURRENT system coords (so an icon out past the
    dense grid still reads which system it's in), plus '->(i,j)' when it has an active
    objective in a DIFFERENT system (so the board shows who's headed where). active_objective
    is set by the Missions Engage and the Admiral 'Send <ship> here'."""
    base = s.name + " (" + str(cell[0]) + "," + str(cell[1]) + ")"
    dest = get_inventory_value(s.id, "active_objective", None)
    if dest and len(dest) == 2 and (int(dest[0]) != cell[0] or int(dest[1]) != cell[1]):
        return base + " ->(" + str(int(dest[0])) + "," + str(int(dest[1])) + ")"
    return base


def _fleet_label(fkey):
    """A fleet icon's label: commanding officer + standing order, e.g. 'Harkin (patrol)'
    (falls back to the fleet key when no officer name resolves). fleet_officer_name /
    fleet_current_order are sibling free globals (universe_fleets.py)."""
    name = fleet_officer_name(fkey) or ("Fleet " + str(fkey).upper())
    return name + " (" + fleet_current_order(fkey) + ")"


def galaxy_theater_cam_for(client_id):
    """THIS admiral client's OWN galaxy cam (a copy per admiral). Stored per client as
    GALAXY_CAM; each cam is spawned into its own board REGION (a distinct z slot + backdrop
    navarea) so two overseers never share/clear one board, and remembers its region-z
    (board_rz) + board centre (board_ci/cj). Returns the cam id (0 on spawn failure)."""
    cam_id = get_inventory_value(client_id, "GALAXY_CAM", 0)
    if cam_id and to_object(cam_id) is not None:
        return cam_id
    slot = len(to_object_list(role("galaxy_theater_cam")))
    rz = GALAXY_THEATER.z + slot * GALAXY_REGION_GAP
    sim = FrameContext.sim
    r = THEATER_SPACING * 8
    ox = GALAXY_THEATER.x
    sim.add_navarea(ox - r, rz + r, ox + r, rz + r,
                    ox - r, rz - r, ox + r, rz - r,
                    "Galaxy", "#08f4")
    cam = player_spawn(GALAXY_THEATER.x, GALAXY_THEATER.y + 1000.0, rz,
                       "", "#,galaxy_theater_cam,has_science_scan", "invisible")
    if cam is None:
        return 0
    remove_role(cam, "__player__")
    set_inventory_value(cam.id, "board_rz", rz)
    set_inventory_value(cam.id, "board_ci", 999999)
    set_inventory_value(cam.id, "board_cj", 999999)
    set_inventory_value(client_id, "GALAXY_CAM", cam.id)
    return cam.id


def _board_markers(cam_id, role_name):
    """Objects of `role_name` (galaxy_marker / galaxy_unit) belonging to ONE cam's board
    (tagged board_cam) - so each admiral's board clears / scans / reconciles independently."""
    return [m for m in to_object_list(role(role_name))
            if get_inventory_value(m.id, "board_cam", 0) == cam_id]


def galaxy_theater_clear(cam_id):
    """Despawn ONE cam's whole board (its system markers + unit icons + ship->icon links).
    A full teardown; normal operation REUSES the board and reconciles in place."""
    for m in _board_markers(cam_id, "galaxy_marker"):
        m.delete_object()
    for u in _board_markers(cam_id, "galaxy_unit"):
        _forget_unit_icon(u)
        u.delete_object()
    for u in _board_markers(cam_id, "galaxy_fleet"):
        u.delete_object()


def galaxy_theater_clear_system(cam_id):
    """Despawn only ONE cam's static SYSTEM markers (leaves its unit icons). Used when the
    board re-centers: the system grid rebuilds, but the unit icons just move (sync_units)."""
    for m in _board_markers(cam_id, "galaxy_marker"):
        m.delete_object()


def _forget_unit_icon(icon):
    """Clear the ship->icon back-link (per-cam key) for a unit icon about to be deleted."""
    sid = get_inventory_value(icon.id, "unit_ship", 0)
    cam = get_inventory_value(icon.id, "board_cam", 0)
    if sid and cam:
        set_inventory_value(sid, "galaxy_icon:" + str(cam), 0)


def galaxy_theater_sync_units(cam_id, ci, cj, side, win=GALAXY_UNIT_WIN):
    """Reconcile ONE cam's friendly-unit icons IN PLACE (by change, not rebuild). Each
    player ship of `side` keeps ONE persistent icon per board (role galaxy_unit, tagged
    board_cam): it is MOVED to its current cell offset in this cam's region and re-tinted
    (shield health) / re-labelled (name + destination); an icon whose ship left the window
    or is gone is removed. Called on activation and by the ~1s unit watcher, so a SENT ship
    updates live without a board rebuild. The ship->icon link is per-cam (galaxy_icon:<cam>)
    so the same ship can appear on several admirals' boards (co-op)."""
    rz = get_inventory_value(cam_id, "board_rz", GALAXY_THEATER.z)
    origin = to_object(cam_id)   # scan new icons for the cam so its 2D view can SELECT them
    link_key = "galaxy_icon:" + str(cam_id)
    keep = set()
    cell_slot = {}   # (sdi, sdj) -> how many unit icons already placed there (fan-out slot)
    if side is not None:
        # Stable id order so a unit keeps its fan slot across reconciles (no jitter).
        for s in sorted(to_object_list(role("__player__") & role(side)), key=lambda o: o.id):
            sc = object_cell(s.id)
            sdi = sc[0] - ci
            sdj = sc[1] - cj
            icon_id = get_inventory_value(s.id, link_key, 0)
            icon = to_object(icon_id) if icon_id else None
            if not (-win <= sdi <= win and -win <= sdj <= win):
                if icon is not None:
                    icon.delete_object()
                set_inventory_value(s.id, link_key, 0)
                continue
            slot = cell_slot.get((sdi, sdj), 0)
            cell_slot[(sdi, sdj)] = slot + 1
            fdx, fdz = _fan_xz(slot)
            up = galaxy_theater_marker_pos(sdi, sdj, rz)
            px = up.x + THEATER_SPACING * GALAXY_UNIT_OFFSET + fdx
            pz = up.z + THEATER_SPACING * GALAXY_UNIT_OFFSET + fdz
            if icon is None:
                icon = terrain_spawn(px, up.y, pz, s.name, "galaxy_unit",
                                     "tsn_fighter", "behav_selection")
                if icon is None:
                    continue
                set_inventory_value(s.id, link_key, icon.id)
                set_inventory_value(icon.id, "unit_ship", s.id)
                set_inventory_value(icon.id, "board_cam", cam_id)
                # Scan so the galaxy cam can SELECT the token (comms is gated on scan data).
                if origin is not None:
                    science_set_scan_data(origin, icon.id, "Galaxy ship")
            else:
                icon.pos = Vec3(px, up.y, pz)   # MOVE in place, not respawn
            icon.data_set.set("radar_color_override", _unit_health_color(s), 0)
            icon.data_set.set("icon_index", GALAXY_SHIP_ICON[0], 0)
            icon.data_set.set("icon_scale", GALAXY_SHIP_ICON[1], 0)
            icon.data_set.set("name_tag", _unit_label(s, sc), 0)
            keep.add(icon.id)
    # Remove orphans on THIS board only: icons whose ship is gone / left the window.
    for u in _board_markers(cam_id, "galaxy_unit"):
        if u.id not in keep:
            _forget_unit_icon(u)
            u.delete_object()


def galaxy_theater_sync_fleets(cam_id, ci, cj, side, win=GALAXY_UNIT_WIN):
    """Reconcile ONE cam's friendly-FLEET icons IN PLACE (mirrors sync_units for player
    ships, so the overseer sees WHICH SYSTEM each of the side's fleets is holding). Each
    live fleet of `side` keeps ONE persistent icon per board (role galaxy_fleet, tagged
    board_cam): placed on its recorded post cell's window offset, labelled with the officer
    + standing order, in navy gold with the heavier battle-cruiser shape so a fleet reads
    distinctly from a lone player fighter icon. A fleet icon whose fleet stood down or left
    the window is removed. Keyed by the STABLE fleet key stored on the icon (not an object
    id) so hulls respawning under the fleet never orphan its marker. fleets_of_side /
    fleet_cell are sibling free globals (universe_fleets.py)."""
    rz = get_inventory_value(cam_id, "board_rz", GALAXY_THEATER.z)
    origin = to_object(cam_id)   # scan new icons for the cam so its 2D view can SELECT them
    existing = {}
    for u in _board_markers(cam_id, "galaxy_fleet"):
        existing[get_inventory_value(u.id, "fleet_key", "")] = u
    keep = set()
    cell_slot = {}   # (fdi, fdj) -> how many fleet icons already placed there (fan-out slot)
    if side is not None:
        # Stable key order so a fleet keeps its fan slot across reconciles (no jitter).
        for f in sorted(fleets_of_side(side), key=lambda x: str(x.get("key"))):
            fkey = f.get("key")
            fc = fleet_cell(fkey)
            fdi = fc[0] - ci
            fdj = fc[1] - cj
            icon = existing.get(fkey)
            if not (-win <= fdi <= win and -win <= fdj <= win):
                continue          # out of the board window -> not kept -> removed below
            # Officer + order, plus the fleet's CURRENT system coords (so an icon out past
            # the dense grid still reads which system it's holding).
            flabel = _fleet_label(fkey) + " (" + str(fc[0]) + "," + str(fc[1]) + ")"
            slot = cell_slot.get((fdi, fdj), 0)
            cell_slot[(fdi, fdj)] = slot + 1
            fdx, fdz = _fan_xz(slot)
            up = galaxy_theater_marker_pos(fdi, fdj, rz)
            # Offset OPPOSITE the player-ship icon so a fleet and a ship sharing a cell don't
            # stack on top of each other.
            px = up.x - THEATER_SPACING * GALAXY_UNIT_OFFSET + fdx
            pz = up.z - THEATER_SPACING * GALAXY_UNIT_OFFSET + fdz
            if icon is None:
                icon = terrain_spawn(px, up.y, pz, flabel, "galaxy_fleet",
                                     "tsn_battle_cruiser", "behav_selection")
                if icon is None:
                    continue
                set_inventory_value(icon.id, "fleet_key", fkey)
                set_inventory_value(icon.id, "board_cam", cam_id)
                # Scan so the galaxy cam can SELECT the token (comms is gated on scan data).
                if origin is not None:
                    science_set_scan_data(origin, icon.id, "Galaxy fleet")
            else:
                icon.pos = Vec3(px, up.y, pz)   # MOVE in place, not respawn
            icon.data_set.set("radar_color_override", "#ffd24a", 0)
            icon.data_set.set("icon_index", GALAXY_FLEET_ICON[0], 0)
            icon.data_set.set("icon_scale", GALAXY_FLEET_ICON[1], 0)
            icon.data_set.set("name_tag", flabel, 0)
            keep.add(icon.id)
    # Remove orphans on THIS board only: icons whose fleet stood down / left the window.
    for u in _board_markers(cam_id, "galaxy_fleet"):
        if u.id not in keep:
            u.delete_object()


def galaxy_theater_build(cam_id, seed, danger, sides, systems, reveal, ci, cj, side, win=GALAXY_GRID_WIN):
    """Rebuild ONE cam's STATIC system-marker grid: a (2*win+1) window of real system
    markers around cell (ci, cj) in this cam's region, meshed by actual kind (fog ->
    unknown), each tagged board_cam. Only called when the board re-centers (the caller
    gates on a CHANGED cell), NOT on every activation - the unit icons are reconciled
    separately (galaxy_theater_sync_units) so a sent ship updates by change."""
    rz = get_inventory_value(cam_id, "board_rz", GALAXY_THEATER.z)
    galaxy_theater_clear_system(cam_id)
    for di in range(-win, win + 1):
        for dj in range(-win, win + 1):
            i = ci + di
            j = cj + dj
            owner = None
            if not universe_cell_known(systems, i, j, reveal):
                kind = "fog"
            else:
                base_kind = universe_system_kind(seed, i, j, danger)
                owner, kind = universe_system_side(sides, seed, i, j, base_kind)
            icon = _KIND_ICON.get(kind, _KIND_ICON["fog"])
            # Colour by DIPLOMACY (owner relation / your control), falling back to the kind
            # colour for unowned space; a fogged cell keeps its (unknown) kind colour.
            color = icon[1] if kind == "fog" else galaxy_theater_marker_color(sides, i, j, side, owner, icon[1])
            p = galaxy_theater_marker_pos(di, dj, rz)
            label = galaxy_theater_marker_label(kind, i, j)
            # Passive map marker: behav_selection draws a flat radar ICON (icon_index) sized
            # by icon_scale and coloured by radar_color_override; name_tag is its text.
            m = terrain_spawn(p.x, p.y, p.z, label,
                              "galaxy_marker", icon[0], "behav_selection")
            if m is not None:
                m.data_set.set("radar_color_override", color, 0)
                m.data_set.set("icon_scale", icon[2], 0)
                m.data_set.set("icon_index", icon[3], 0)
                # name_tag is what the 2D radar draws as text: the kind word + coords.
                m.data_set.set("name_tag", label, 0)
                set_inventory_value(m.id, "marker_i", i)
                set_inventory_value(m.id, "marker_j", j)
                set_inventory_value(m.id, "marker_kind", kind)
                set_inventory_value(m.id, "board_cam", cam_id)
    # Reconcile the unit + fleet icons to the (possibly new) centre - in place, not a
    # respawn - so player ships AND fleets show which system they're in. These use the WIDER
    # unit window (out to the radar edge), NOT the dense grid `win`, so a unit systems away
    # from the overseer still shows.
    galaxy_theater_sync_units(cam_id, ci, cj, side, GALAXY_UNIT_WIN)
    galaxy_theater_sync_fleets(cam_id, ci, cj, side, GALAXY_UNIT_WIN)


def galaxy_theater_scan_for(cam_id):
    """Mark ONE cam's board markers scanned for it (the galaxy cambot), so its 2D view can
    select them (comms/selection is gated by the science-data rule)."""
    origin = to_object(cam_id)
    if origin is None:
        return
    for m in _board_markers(cam_id, "galaxy_marker"):
        science_set_scan_data(origin, m.id, "Galaxy marker")


def galaxy_theater_roster_items(side):
    """Selectable 'who is where' rows for the side's forces - one MastDataObject per player
    ship and per fleet, each carrying its system (i, j) so selecting a row can FOCUS the
    overseer there (theater_jump_here). This is window-INDEPENDENT: it lists forces even
    when they sit OFF the board window (the icon layer only reaches the radar edge). Sorted
    by system then kind then name. object_cell / fleets_of_side / fleet_cell are sibling
    free globals (universe_helpers / universe_fleets)."""
    rows = []
    for s in to_object_list(role("__player__") & role(side)):
        c = object_cell(s.id)
        rows.append(MastDataObject({
            "kind": "ship", "i": int(c[0]), "j": int(c[1]), "name": s.name,
            "label": s.name + "  -  (" + str(int(c[0])) + "," + str(int(c[1])) + ")",
            "color": "#dfe"}))
    for f in fleets_of_side(side):
        c = fleet_cell(f.get("key"))
        n = int(f.get("alive", 0))
        rows.append(MastDataObject({
            "kind": "fleet", "i": int(c[0]), "j": int(c[1]),
            "name": _fleet_label(f.get("key")),
            "label": _fleet_label(f.get("key")) + "  x" + str(n) + "  -  ("
                     + str(int(c[0])) + "," + str(int(c[1])) + ")",
            "color": "#ffd24a"}))
    rows.sort(key=lambda r: (r.get("i"), r.get("j"), r.get("kind"), r.get("name")))
    return rows


def galaxy_theater_roster_title():
    """Title row for the roster listbox (labels the list per the listbox best practice -
    not a separate text row above it)."""
    gui_row("row-height: 1.3em;padding:6px;background:#1578;")
    gui_text("$text:Forces - click to focus;font:gui-1;color:#cde")


def galaxy_theater_roster_item_template(item):
    """One roster row: the unit label + its system, tinted by kind (ships near-white,
    fleets navy gold)."""
    gui_row("row-height: 1.7em;")
    gui_text("$text:" + item.get("label") + ";font:gui-1;color:" + item.get("color"))


def galaxy_theater_roster_sig(side):
    """A cheap change-signature for the roster, so an `on change` can rebuild the listbox
    only when it actually changes - a unit moves system, a fleet forms / stands down, or a
    fleet's order or hull count changes. fleet_current_order is a sibling free global."""
    parts = []
    for s in to_object_list(role("__player__") & role(side)):
        c = object_cell(s.id)
        parts.append(s.name + ":" + str(c[0]) + "," + str(c[1]))
    for f in fleets_of_side(side):
        c = fleet_cell(f.get("key"))
        parts.append(str(f.get("key")) + ":" + str(c[0]) + "," + str(c[1]) + ":"
                     + fleet_current_order(f.get("key")) + ":" + str(int(f.get("alive", 0))))
    return "|".join(sorted(parts))
