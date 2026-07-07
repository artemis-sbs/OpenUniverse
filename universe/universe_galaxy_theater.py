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


def galaxy_theater_marker_pos(di, dj):
    """World position of the marker at window offset (di, dj) from the board center."""
    return Vec3(GALAXY_THEATER.x + di * THEATER_SPACING,
                GALAXY_THEATER.y,
                GALAXY_THEATER.z + dj * THEATER_SPACING)


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


def galaxy_theater_ensure_cam():
    """Spawn the galaxy cambot (invisible, scan-capable) + one backdrop navarea, once.
    The cambot is the ship the viewing client is temporarily assigned to; a distinct
    role (galaxy_theater_cam) gates its //popup routes."""
    if galaxy_theater_cam_id() != 0:
        return
    sim = FrameContext.sim
    r = THEATER_SPACING * 8
    ox = GALAXY_THEATER.x
    oz = GALAXY_THEATER.z
    sim.add_navarea(ox - r, oz + r, ox + r, oz + r,
                    ox - r, oz - r, ox + r, oz - r,
                    "Galaxy", "#08f4")
    cam = player_spawn(GALAXY_THEATER.x, GALAXY_THEATER.y + 1000.0, GALAXY_THEATER.z,
                       "", "#,galaxy_theater_cam,has_science_scan", "invisible")
    if cam is not None:
        remove_role(cam, "__player__")


def galaxy_theater_cam_id():
    """The galaxy cambot id the viewing client is assigned to (0 if not spawned)."""
    cams = to_object_list(role("galaxy_theater_cam"))
    return cams[0].id if cams else 0


def galaxy_theater_clear():
    """Despawn the current board (system markers + friendly-unit icons)."""
    for m in to_object_list(role("galaxy_marker")):
        m.delete_object()
    for u in to_object_list(role("galaxy_unit")):
        u.delete_object()


def galaxy_theater_build(seed, danger, clans, sectors, reveal, ci, cj, side, win=3):
    """Refresh the board: a (2*win+1) square window of REAL system markers around cell
    (ci, cj), meshed by actual system kind (fog -> unknown). Clears the old markers
    first. seed/danger/clans/sectors/reveal are the universe's shared config, passed in
    from MAST (they aren't module globals)."""
    galaxy_theater_clear()
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
            p = galaxy_theater_marker_pos(di, dj)
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
    # Friendly UNITS: a small bright icon at each cell holding a player ship of `side`,
    # so the overseer sees where its crews are (the theater is the single strategic map
    # now). Display-only (not scanned -> not selectable); role galaxy_unit so the next
    # build clears them. object_cell resolves via the merged universe_* namespace.
    if side is not None:
        for s in to_object_list(role("__player__") & role(side)):
            sc = object_cell(s.id)
            sdi = sc[0] - ci
            sdj = sc[1] - cj
            if -win <= sdi <= win and -win <= sdj <= win:
                up = galaxy_theater_marker_pos(sdi, sdj)
                u = terrain_spawn(up.x + THEATER_SPACING * 0.28, up.y, up.z + THEATER_SPACING * 0.28,
                                  s.name, "galaxy_unit", "tsn_fighter", "behav_marker")
                if u is not None:
                    u.data_set.set("radar_color_override", "#ffee44", 0)
                    u.data_set.set("icon_scale", 0.8, 0)
                    u.data_set.set("name_tag", s.name, 0)


def galaxy_theater_scan_for(origin_id):
    """Mark the markers scanned for `origin_id` (the galaxy cambot), so its 2D view can
    select them (comms/selection is gated by the science-data rule)."""
    origin = to_object(origin_id)
    if origin is None:
        return
    for m in to_object_list(role("galaxy_marker")):
        science_set_scan_data(origin, m.id, "Galaxy marker")
