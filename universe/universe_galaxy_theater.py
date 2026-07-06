"""SPIKE (throwaway proof - ADMIRAL_CONSOLE.md section 19, "Deploy UX"): prove that
far-coordinate TERRAIN markers render + SELECT on a 2D view, and that a //popup route
fires on them, BEFORE building the real galaxy theater. Guarded and trivially removable.

Spawns a 3x3 patch of mesh-varied TERRAIN markers + one region navarea in the dead space
far from the play slots, plus an invisible ALT cambot at the center. The admiral keeps
its real command cambot; the 2D radar is pointed at the alt cambot via
sbs.assign_client_to_alt_ship (a VIEW focus, not a reassignment), so viewing the map
never displaces the command camera.

Shared-namespace notes (like the other universe_*.py files): no relative sibling
imports; sbs_utils absolute imports only.
"""
from sbs_utils.procedural.spawn import terrain_spawn, player_spawn
from sbs_utils.procedural.roles import role, remove_role
from sbs_utils.procedural.query import to_object_list, to_object
from sbs_utils.procedural.inventory import set_inventory_value
from sbs_utils.procedural.science import science_set_scan_data
from sbs_utils.helpers import FrameContext
from sbs_utils.vec import Vec3


# The theater lives in the DEAD SPACE far from the play slots (which sit within +-1M):
# the markers never move and the alt cambot parks among them, so the far-coordinate
# float precision that hurts MOVEMENT doesn't matter here. See section 19.
GALAXY_THEATER = Vec3(50_000_000.0, 0.0, 0.0)
THEATER_SPACING = 4_000.0

# Spike icon vocabulary: distinct MESHES so the silhouette carries meaning. Fog/unknown
# uses the `unknown` shipData art (same as the empty-system marker). The real mapping is
# a table later (a `## Galaxy Icons` AMD chapter).
_SPIKE_ICONS = {
    "home":   "starbase_command",
    "base":   "starbase_civil",
    "threat": "tsn_light_cruiser",
    "nebula": "unknown",
    "empty":  "unknown",
}
# The 3x3 patch (row-major over i in -1..1, then j in -1..1). Center (index 4, right
# under the cam) is a starbase so the mesh variety is obvious the moment it opens.
_SPIKE_LAYOUT = ["threat", "base", "nebula",
                 "empty", "home", "base",
                 "threat", "nebula", "base"]


def galaxy_theater_marker_pos(i, j):
    """World position of the marker for galaxy cell (i, j) on the theater board."""
    return Vec3(GALAXY_THEATER.x + i * THEATER_SPACING,
                GALAXY_THEATER.y,
                GALAXY_THEATER.z + j * THEATER_SPACING)


def galaxy_theater_spike_spawn():
    """Spawn the 3x3 TERRAIN marker patch + one region navarea + the alt cambot, once.
    Terrain (passive) keeps the board out of the active sim. Idempotent."""
    if len(to_object_list(role("galaxy_marker"))) > 0:
        return
    n = 0
    for i in (-1, 0, 1):
        for j in (-1, 0, 1):
            kind = _SPIKE_LAYOUT[n]
            n += 1
            art = _SPIKE_ICONS.get(kind, "unknown")
            p = galaxy_theater_marker_pos(i, j)
            m = terrain_spawn(p.x, p.y, p.z, "System " + str(i) + "," + str(j),
                              "galaxy_marker", art, "behav_asteroid")
            if m is not None:
                set_inventory_value(m.id, "marker_i", i)
                set_inventory_value(m.id, "marker_j", j)
                set_inventory_value(m.id, "marker_kind", kind)
    # A region navarea under the patch - the shaded-zone backdrop test. Corners in
    # TL,TR,BL,BR order as (x, z) pairs, covering the 3x3 with a margin.
    sim = FrameContext.sim
    r = THEATER_SPACING * 1.6
    ox = GALAXY_THEATER.x
    oz = GALAXY_THEATER.z
    sim.add_navarea(ox - r, oz + r, ox + r, oz + r,
                    ox - r, oz - r, ox + r, oz - r,
                    "Test Region", "#08fc")
    # The galaxy cambot at the theater center: the client is TEMPORARILY re-assigned to
    # THIS ship (assign_client_to_ship) to view the theater, then back to its command
    # cambot - the standard, engine-solid way to move a console's view. Invisible,
    # __player__ stripped; `has_science_scan` + a side (set at open) so its 2D view can
    # select the (scanned) markers; `galaxy_theater_cam` role gates its popups.
    cam = player_spawn(GALAXY_THEATER.x, GALAXY_THEATER.y + 1000.0, GALAXY_THEATER.z,
                       "", "#,galaxy_theater_cam,has_science_scan", "invisible")
    if cam is not None:
        remove_role(cam, "__player__")


def galaxy_theater_cam_id():
    """The alt cambot id to focus the 2D radar on (0 if not spawned)."""
    cams = to_object_list(role("galaxy_theater_cam"))
    return cams[0].id if cams else 0


def galaxy_theater_scan_for(origin_id):
    """Mark the markers scanned for `origin_id` (the admiral's command cambot), so
    comms/selection on them isn't gated by the science-data rule."""
    origin = to_object(origin_id)
    if origin is None:
        return
    for m in to_object_list(role("galaxy_marker")):
        science_set_scan_data(origin, m.id, "Galaxy marker")
