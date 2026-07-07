"""Galaxy theater - the admiral's strategic map as a 2D-view board of real marker
objects in the dead space far from the play slots (ADMIRAL_CONSOLE.md section 19).
Markers never move and the galaxy cambot parks among them, so far-coordinate float
precision (a movement problem) doesn't matter. Still HQ-button-triggered while it grows
into the Galaxy tab.

The client is TEMPORARILY re-assigned to the galaxy cambot to view the board (returns
to its command cambot via the per-client ADMIRAL_CAM) - the engine-solid way to move a
console's view (assign_client_to_alt_ship did not move the detached comms 2D view).

Shared-namespace notes (like the other universe_*.py files): no relative sibling
imports; sbs_utils absolute imports only. universe_system_kind / universe_system_clan /
universe_cell_known come from sibling modules via the merged MAST namespace.
"""
from sbs_utils.procedural.spawn import terrain_spawn, player_spawn
from sbs_utils.procedural.roles import role, remove_role
from sbs_utils.procedural.query import to_object_list, to_object
from sbs_utils.procedural.inventory import set_inventory_value, get_inventory_value
from sbs_utils.procedural.science import science_set_scan_data
from sbs_utils.helpers import FrameContext
from sbs_utils.vec import Vec3


# Far from the play slots (within +-1M); markers are static so the distance is safe.
GALAXY_THEATER = Vec3(50_000_000.0, 0.0, 0.0)
THEATER_SPACING = 4_000.0
# A COPY PER ADMIRAL: each overseer's galaxy cam gets its own board REGION, offset in z
# by (slot * GALAXY_REGION_GAP) so boards never overlap. The gap is well beyond a cam's
# radar range (40k) + the board span (~24k), so each cam sees only its own board.
GALAXY_REGION_GAP = 200_000.0

# Icon vocabulary: system KIND -> (art, color, scale). behav_marker renders the ART
# (shape channel); the COLOR is applied via a per-kind colored SIDE (radar color comes
# from the side's icon color, not a per-object property); scale via icon_scale. Each
# marker's side is "gm_<kind>" (colored once in _galaxy_theater_define_sides). A later
# `## Galaxy Icons` AMD chapter can own this mapping.
_KIND_ICON = {
    "home":    ("starbase_command",  "#33ff66", 1.6),
    "station": ("starbase_civil",    "#00ccff", 1.2),
    "enemy":   ("tsn_light_cruiser", "#ff4444", 1.2),
    "nebula":  ("unknown",           "#cc66ff", 1.0),
    "anomaly": ("unknown",           "#aa33ff", 1.0),
    "empty":   ("unknown",           "#888888", 0.7),
    "fog":     ("unknown",           "#555555", 0.7),
}


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
    """A unit icon's label: ship name, plus '->(i,j)' when it has an active objective in
    a DIFFERENT system (so the board shows who's headed where). active_objective is set by
    the Missions Engage and the Admiral 'Send <ship> here'."""
    dest = get_inventory_value(s.id, "active_objective", None)
    if dest and len(dest) == 2 and (int(dest[0]) != cell[0] or int(dest[1]) != cell[1]):
        return s.name + " ->(" + str(int(dest[0])) + "," + str(int(dest[1])) + ")"
    return s.name


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


def galaxy_theater_sync_units(cam_id, ci, cj, side, win=3):
    """Reconcile ONE cam's friendly-unit icons IN PLACE (by change, not rebuild). Each
    player ship of `side` keeps ONE persistent icon per board (role galaxy_unit, tagged
    board_cam): it is MOVED to its current cell offset in this cam's region and re-tinted
    (shield health) / re-labelled (name + destination); an icon whose ship left the window
    or is gone is removed. Called on activation and by the ~1s unit watcher, so a SENT ship
    updates live without a board rebuild. The ship->icon link is per-cam (galaxy_icon:<cam>)
    so the same ship can appear on several admirals' boards (co-op)."""
    rz = get_inventory_value(cam_id, "board_rz", GALAXY_THEATER.z)
    link_key = "galaxy_icon:" + str(cam_id)
    keep = set()
    if side is not None:
        for s in to_object_list(role("__player__") & role(side)):
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
            up = galaxy_theater_marker_pos(sdi, sdj, rz)
            px = up.x + THEATER_SPACING * 0.28
            pz = up.z + THEATER_SPACING * 0.28
            if icon is None:
                icon = terrain_spawn(px, up.y, pz, s.name, "galaxy_unit",
                                     "tsn_fighter", "behav_marker")
                if icon is None:
                    continue
                set_inventory_value(s.id, link_key, icon.id)
                set_inventory_value(icon.id, "unit_ship", s.id)
                set_inventory_value(icon.id, "board_cam", cam_id)
            else:
                icon.pos = Vec3(px, up.y, pz)   # MOVE in place, not respawn
            icon.data_set.set("radar_color_override", _unit_health_color(s), 0)
            icon.data_set.set("icon_scale", 0.8, 0)
            icon.data_set.set("name_tag", _unit_label(s, sc), 0)
            keep.add(icon.id)
    # Remove orphans on THIS board only: icons whose ship is gone / left the window.
    for u in _board_markers(cam_id, "galaxy_unit"):
        if u.id not in keep:
            _forget_unit_icon(u)
            u.delete_object()


def galaxy_theater_build(cam_id, seed, danger, clans, sectors, reveal, ci, cj, side, win=3):
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
            if not universe_cell_known(sectors, i, j, reveal):
                kind = "fog"
            else:
                base_kind = universe_system_kind(seed, i, j, danger)
                kind = universe_system_clan(clans, seed, i, j, base_kind)[1]
            icon = _KIND_ICON.get(kind, _KIND_ICON["fog"])
            p = galaxy_theater_marker_pos(di, dj, rz)
            # Passive map marker: behav_marker renders the ART; radar_color_override
            # forces the 2D-radar colour per object; icon_scale sizes it.
            m = terrain_spawn(p.x, p.y, p.z, "System " + str(i) + "," + str(j),
                              "galaxy_marker", icon[0], "behav_marker")
            if m is not None:
                m.data_set.set("radar_color_override", icon[1], 0)
                m.data_set.set("icon_scale", icon[2], 0)
                # Label the marker on the map with its coords (enrich with owner/name
                # later). name_tag is what the 2D radar draws as text.
                m.data_set.set("name_tag", str(i) + "," + str(j), 0)
                set_inventory_value(m.id, "marker_i", i)
                set_inventory_value(m.id, "marker_j", j)
                set_inventory_value(m.id, "marker_kind", kind)
                set_inventory_value(m.id, "board_cam", cam_id)
    # Reconcile the unit icons to the (possibly new) centre - in place, not a respawn.
    galaxy_theater_sync_units(cam_id, ci, cj, side, win)


def galaxy_theater_scan_for(cam_id):
    """Mark ONE cam's board markers scanned for it (the galaxy cambot), so its 2D view can
    select them (comms/selection is gated by the science-data rule)."""
    origin = to_object(cam_id)
    if origin is None:
        return
    for m in _board_markers(cam_id, "galaxy_marker"):
        science_set_scan_data(origin, m.id, "Galaxy marker")
