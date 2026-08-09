"""The Fabricator - Admiral build model B (ADMIRAL_CONSOLE.md section 5), an A/B
alternative to instant menu building. One slow, unarmed Fabricator ship per side
physically flies to each queued worldlet and constructs the platform there:
serial (one at a time), travel takes time, and the ship is a target -
"build-by-vulnerable-ship feels like a navy". Selected by `Build model:
fabricator` in the Admiralty AMD; the default menu model is untouched.

Auto-queue, so it is not a micro chore: the Admiral queues builds and the
Fabricator works through them on its own. The death penalty is TIME, not
resources - the queue lives on the side inventory (adm_fab_queue) and survives
the ship, so a lost Fabricator relaunches from the yards after a delay and
resumes (you lose the travel + build time, not the materials). A jump that
clears the system drops jobs whose worldlet is gone, exactly like a menu build.

Shared-namespace notes: admiralty_platform_def / admiralty_build_done from
universe_worldlets.py.
"""
from sbs_utils.procedural.spawn import npc_spawn
from sbs_utils.procedural.inventory import get_inventory_value, set_inventory_value
from sbs_utils.procedural.sides import to_side_id
from sbs_utils.procedural.roles import role
from sbs_utils.procedural.query import to_object_list, to_object
from sbs_utils.procedural.space_objects import target_pos

FAB_THROTTLE = 0.6           # slow builder
FAB_ARRIVE_DIST = 2200.0     # within this of the worldlet -> construct
FAB_RESPAWN_DELAY = 25.0     # seconds to launch a replacement after a loss
FAB_ART = "tsn_light_cruiser"    # placeholder hull (see ART_WANTED.md)

_FAB = {}   # side -> {"build_left": float|None, "respawn_left": float}


def fabricator_reset():
    """Clear per-load Fabricator state (mirrors skirmish_reset at map load)."""
    global _FAB
    _FAB = {}


def _queue(side):
    return list(get_inventory_value(to_side_id(side), "adm_fab_queue", []) or [])


def _admiralty_set_queue(side, q):
    set_inventory_value(to_side_id(side), "adm_fab_queue", q)


def fabricator_queue(side):
    """The pending build jobs (list of {kind, worldlet_id}) - console display."""
    return _queue(side)


def fabricator_enqueue(side, kind, worldlet_id):
    """Queue a build for the Fabricator (the caller has already paid). Flags the
    worldlet under construction so the build menu won't offer it again."""
    q = _queue(side)
    q.append({"kind": kind, "worldlet_id": worldlet_id})
    _admiralty_set_queue(side, q)
    wobj = to_object(worldlet_id)
    if wobj is not None:
        wobj.set_inventory_value("building_" + kind, True)


def _fab_get(side):
    fabs = to_object_list(role("adm_fabricator") & role(side))
    return fabs[0] if fabs else None


def _fab_home(side):
    """Where the Fabricator launches from / idles: the HQ, else the origin."""
    hqs = to_object_list(role("admiral_hq") & role(side))
    return hqs[0].pos if hqs else None


def _fab_spawn(side):
    home = _fab_home(side)
    x, y, z = (home.x, home.y, home.z) if home is not None else (0.0, 0.0, 0.0)
    npc_spawn(x, y, z, "Fabricator", side + ", adm_fabricator", FAB_ART, "behav_npcship")


def fabricator_tick(side, dt):
    """One driver step for a side's Fabricator. Returns a short Admiralty ops
    line on a notable event (relaunch / build complete), else None."""
    st = _FAB.setdefault(side, {"build_left": None, "respawn_left": FAB_RESPAWN_DELAY})
    q = _queue(side)
    fab = _fab_get(side)

    if fab is None:
        # No Fabricator yet (game start) or it was destroyed. Launch one when
        # there is work; the interrupted job restarts (death costs time).
        if not q:
            st["respawn_left"] = FAB_RESPAWN_DELAY
            return None
        st["respawn_left"] -= float(dt)
        if st["respawn_left"] <= 0:
            _fab_spawn(side)
            st["respawn_left"] = FAB_RESPAWN_DELAY
            st["build_left"] = None
            return "Fabricator launched from the yards."
        return None

    if not q:
        # Idle: hold near home.
        home = _fab_home(side)
        if home is not None:
            target_pos(set([fab.id]), home.x, home.y, home.z, FAB_THROTTLE, stop_dist=1500)
        st["build_left"] = None
        return None

    job = q[0]
    wobj = to_object(job.get("worldlet_id"))
    if wobj is None:
        # Build site gone (a jump cleared the system) - drop it, like a menu build.
        q.pop(0)
        _admiralty_set_queue(side, q)
        st["build_left"] = None
        return None

    fp, wp = fab.pos, wobj.pos
    if (fp.x - wp.x) ** 2 + (fp.z - wp.z) ** 2 > FAB_ARRIVE_DIST ** 2:
        target_pos(set([fab.id]), wp.x, wp.y, wp.z, FAB_THROTTLE, stop_dist=FAB_ARRIVE_DIST * 0.8)
        st["build_left"] = None
        return None

    # Arrived: construct over the platform's build time.
    pdef = admiralty_platform_def(job.get("kind"))
    if pdef is None:
        q.pop(0)
        _admiralty_set_queue(side, q)
        return None
    if st["build_left"] is None:
        st["build_left"] = float(pdef.get("build_time", 20))
    st["build_left"] -= float(dt)
    if st["build_left"] <= 0:
        admiralty_build_done(job.get("kind"), side, job.get("worldlet_id"))
        q.pop(0)
        _admiralty_set_queue(side, q)
        st["build_left"] = None
        return str(pdef.get("name")) + " construction complete."
    return None
