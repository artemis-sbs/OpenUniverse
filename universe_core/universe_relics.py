"""Relic interiors in a universe - a landmark that is a place you fly INTO.

A landmark is normally one prop: `terrain_spawn` of a wreck, and a scan objective. A
landmark carrying `Relic:` is instead a whole interior - chambers, passages, boxes,
subtracted masses, named places, authored contents - built from a `## Relics` section in
the mission's own `.amd`. The library owns the geometry (`sbs_utils.procedural.volume` and
`amd_relics`); this file owns everything that makes one work IN A GALAXY.

Three things make the galaxy case different from a relic in a fixed map:

* **A cell's world origin is transient.** The same system lands on a different slot on a
  different visit, so a relic's `Loc:` cannot be authored - it is placed on arrival
  (`relic_place`) at the landmark's own deterministic position.
* **A cell is destroyed on departure and rebuilt on return**, while the NEXT cell is
  already being built. So teardown is per-relic (`relic_release`), never `volume_clear()`,
  and every object this file makes carries a role scoped to its relic key.
* **Two relics can be live at once** - two ships in two systems, Model A. Nothing here may
  assume there is only one.

The look is deliberately driven by the FILE: `Art:` picks the prop meshes, `Seed:` makes
the scatter repeatable, `Atmosphere:` decides the nebula. A universe mission changes how
its ruins look by editing the `.amd`, not this module.

Every function is prefixed `universe_` because an addon's module-level functions land in
one flat, mission-wide MAST namespace - a leading underscore does not make one private.
"""
import math
import random

from sbs_utils.procedural.amd_relics import (
    relics_load, relic_record, relic_place, relic_volume, relic_contain,
    relic_release, relic_contents_arm, relic_points, relic_pos,
)
from sbs_utils.procedural.volume import (
    volume_get, volume_engaged, volume_surface_points, volume_solid_points,
    volume_contains,
)
from sbs_utils.procedural.spawn import terrain_spawn
from sbs_utils.procedural.roles import role
from sbs_utils.procedural.query import to_object_list
from sbs_utils.procedural.markers import marker_object, marker_point
from sbs_utils.procedural.terrain import (
    terrain_spawn_nebula_sphere, terrain_set_nebula_object_size,
)
from sbs_utils.procedural.execution import log
from sbs_utils.mast.mast import DEBUG


# Live relics, so teardown and "am I inside one" can both answer per cell.
# {(i, j): {relic_key: {"volume": name, "mouth": (x,y,z) | None}}}
_UNIVERSE_RELICS = {}

# Relic files already read. Records are registered mission-wide by key, so re-reading a
# file on every arrival would be wasted work and would also drop any runtime placement.
_UNIVERSE_RELIC_FILES = set()

# A nebula thin enough to see the wall you are trying not to hit. The point is mechanical
# rather than cosmetic: the ENGINE caps warp for a ship inside a nebula, so an interior
# needs no script throttle governor - nothing per-tick, nothing for the helm to fight.
UNIVERSE_RELIC_NEBULA_DENSITY = 0.6
UNIVERSE_RELIC_NEBULA_SCALE = 0.35

# How big ONE nebula object may be. `terrain_set_nebula_object_size` documents anything
# above ~3000 as needing the projection-depth shader fix, so a relic sized to the whole
# structure (the Voice would ask for 9947) is asking for a size nobody has tested. The
# relic still gets ONE cloud - `radius` covers the ruin - but it is BUILT from objects of
# a size the renderer is known to be happy with.
UNIVERSE_RELIC_NEBULA_OBJECT = 2500

# Bisect switches. A relic on a Continue builds several hundred objects into a cell that
# already has its own terrain, and when an engine falls over there is no way to tell which
# half did it by reading code. Turn one off, run, repeat.
UNIVERSE_RELIC_DRESS = True        # the wall props
UNIVERSE_RELIC_ATMOSPHERE = True   # the nebula (and the warp cap that comes with it)

# Props per relic. ~0.08 ms each in the engine, so this is ~50 ms of build - paid once per
# arrival, inside the jump tunnel where the crew is already waiting.
UNIVERSE_RELIC_PROPS = 600

# A NAVPOINT at the mouth, on top of the sensor contact.
#
# KEPT (user call, after flying it): the map names the WAY IN and nothing else. That is
# the right place to draw the line - a ruin 30,000u out that the crew cannot steer to is
# a chore rather than a discovery, while the inside stays unmapped, which is where the
# finding actually belongs.
#
# The interior carries no map furniture at all: the measuring posts behind
# `Starts when: reach <role>` are invisible and unselectable, so the radar does not draw
# a floor plan of the rooms, the caches and the triggers before the crew has flown any
# of it.
UNIVERSE_RELIC_NAVPOINT = True


def universe_relic_wall_role(key):
    """The role this relic's wall props carry.

    Scoped to the relic KEY, not a shared `relic_wall`, because two systems can be live at
    once: an unscoped role would let one cell's teardown delete another cell's ruin.
    """
    return "relic_wall:" + str(key)


def universe_relic_atmos_role(key):
    """The role this relic's nebula carries. Scoped for the same reason."""
    return "relic_atmos:" + str(key)


def universe_relic_mark_role(key):
    """The role this relic's sensor contact carries."""
    return "relic_contact:" + str(key)


def universe_relic_load(key, fname):
    """Read and register a relic file, once. Returns the record or None.

    Registering is separate from building on purpose (`relics_register` vs
    `relics_build`): the record is what a quest, a comms line or the Storm dispatcher asks
    about, and it must answer whether or not the crew is currently standing in the ruin.
    """
    rec = relic_record(key)
    if rec is not None:
        return rec
    if fname in _UNIVERSE_RELIC_FILES:
        # The file was read and this key was not in it - an authoring error, and one worth
        # naming, because the landmark will silently fall back to being a prop.
        log(f"relic '{key}' is not in '{fname}'", "universe", "warning")
        return None
    # Read it the universe's own way - consumer mission dir first, then code/lib
    # relative and packaged-mastlib-zip aware. An addon inside a .mastlib cannot open its
    # own files by path, which is why the text is handed to relics_load rather than a name.
    try:
        content = universe_read_content(fname)
    except Exception as e:
        content = None
        log(f"relic file '{fname}' would not read: {e}", "universe", "warning")
    if not content:
        log(f"relic file '{fname}' not found for '{key}'", "universe", "warning")
        return None
    try:
        relics_load(fname, content=content)
    except Exception as e:
        log(f"relic file '{fname}' failed to load: {e}", "universe", "warning")
        return None
    _UNIVERSE_RELIC_FILES.add(fname)
    universe_relic_declare_items(content)
    universe_relic_declare_scenes(content)
    rec = relic_record(key)
    if rec is None:
        log(f"relic '{key}' is not in '{fname}'", "universe", "warning")
    return rec


def universe_relic_declare_items(content):
    """Register any `## Items` section in a relic file. Returns the keys.

    A RELIC FILE IS SELF-CONTAINED: the ruin, what is in it, and what those things are,
    in one document the relic panel can open. `Item:` on a part is a reference, so
    without this the reference resolves to nothing and the pickup spawns the fallback
    art - a treasure that looks like a question mark.

    Items are their own section with their own reader, which is why this is a second
    pass rather than something `relics_load` does: a mission is free to keep its items
    anywhere, and this only says that a relic MAY carry its own.
    """
    try:
        from sbs_utils.procedural.amd_doc import amd_document, amd_section
        from sbs_utils.procedural.amd_items import items_declare_amd
        doc = amd_document(content)
        section = amd_section(doc, "items")
        if section is None:
            return []
        return items_declare_amd(section) or []
    except Exception as e:
        log(f"relic items would not register: {e}", "universe", "warning")
        return []


def universe_relic_declare_scenes(content):
    """Register a relic file's cutscenes and its dialogue scenes.

    The rest of "a relic file is self-contained": the ruin, what is in it, the shot list
    for arriving at it, and the hails its rooms fire. A landmark's `Cutscene:` and a
    quest's `Action: X hails Y` both look their target up in a REGISTRY, so a scene that
    is never registered is a set-piece that silently does not play.
    """
    n = 0
    try:
        from sbs_utils.procedural.amd_doc import amd_document, amd_root_node, amd_section
        from sbs_utils.procedural.amd_cutscene import amd_cutscenes
        from sbs_utils.procedural.amd_dialogue import dialogue_register_scenes
        doc = amd_document(content)
        got = amd_cutscenes(amd_root_node(doc))
        n = len((got or {}).get("cutscenes") or {})
        scenes = amd_section(doc, "dialogue")
        if scenes is not None:
            dialogue_register_scenes(scenes)
    except Exception as e:
        log(f"relic scenes would not register: {e}", "universe", "warning")
    return n


def universe_relic_build(key, fname, x, y, z, ei, ej, name=None):
    """Build a landmark's interior at (x, y, z) in cell (ei, ej). Returns the record.

    The whole arrival path in one call, in the order the pieces depend on each other:
    read, place, build the geometry, dress the walls, fill it with its atmosphere, apply
    the authored containment, arm the authored contents, and put a sensor contact at the
    mouth so science has something to call a bearing on.

    Idempotent per cell: arriving twice, or a second ship arriving, rebuilds nothing.
    """
    rec = universe_relic_load(key, fname)
    if rec is None:
        return None
    live = _UNIVERSE_RELICS.setdefault((int(ei), int(ej)), {})
    if key in live:
        return rec
    relic_place(rec, x, y, z)
    vol = relic_volume(rec)
    if vol is None:
        log(f"relic '{key}' built no volume", "universe", "warning")
        return None
    live[key] = {"volume": rec.get("volume") or key, "mouth": None}
    if UNIVERSE_RELIC_DRESS:
        universe_relic_dress(key)
    if UNIVERSE_RELIC_ATMOSPHERE:
        universe_relic_atmosphere(key)
    # Containment from the AUTHORED fields - a mission repeating the numbers here would
    # only create a second place for them to disagree.
    relic_contain(rec)
    relic_contents_arm(key)
    live[key]["mouth"] = universe_relic_contact(key, name or rec.get("name") or key)
    # SAY SO. A relic that fails to build looks exactly like a system with a wreck in it,
    # and a headless run reports PASS either way - so the one line that distinguishes
    # "the ruin is there" from "the ruin silently is not" has to be printed, not inferred
    # from an object count.
    (bc, br) = vol.bound()
    # DEBUG, not log(): a NAMED logger never reaches mast.runtime.log, and print() goes to
    # an uncaptured stdout under the engine. debug.log is the one channel that survives
    # both an engine run and the dev runner.
    DEBUG(f"relic '{key}' built in cell {int(ei)},{int(ej)}: "
          f"{len(role(universe_relic_wall_role(key)))} props, {br * 2:.0f}u across")
    return rec


def universe_relic_dress(key, props=None):
    """Scatter wall props over the relic's boundary. Returns how many were made.

    The MATHS is the library's (`volume_surface_points` samples evenly over spheres,
    around capsules at any orientation, across box faces, and clips to the outside of the
    union); this picks art, scale and roles.

    IDENTITY, not a once-flag: if the walls are already there this is a no-op, so a second
    ship arriving in the same system cannot double the prop count.
    """
    vol = volume_get(_universe_relic_volume_name(key))
    if vol is None:
        return 0
    wall = universe_relic_wall_role(key)
    existing = len(role(wall))
    if existing:
        return existing
    rec = relic_record(key)
    seed = int(rec.get("seed") or 7) if rec is not None else 7
    art = universe_relic_art(rec)
    count = int(props if props is not None else UNIVERSE_RELIC_PROPS)
    rng = random.Random(seed)
    made = 0
    for (x, y, z, nx, ny, nz) in volume_surface_points(vol, count, seed=seed):
        _universe_relic_prop(rng, art, x, y, z,
                             _universe_relic_near_size(vol, (x, y, z)) / 90.0, wall)
        made += 1
    # A subtracted mass MUST be dressed or it is an invisible obstacle - containment stops
    # the ship at something with nothing there to see.
    for (x, y, z, nx, ny, nz) in volume_solid_points(vol, max(8, count // 12), seed=seed):
        _universe_relic_prop(rng, art, x, y, z, 110.0 / 90.0, wall)
        made += 1
    return made


def universe_relic_art(rec):
    """The prop meshes: whatever the relic authored, else the plain asteroid set.

    VERIFY AN AUTHORED KEY AGAINST shipData. An unknown art key does not fail - it falls
    back to the `unknown` mesh, so a typo reads as a ruin built out of question marks.
    """
    authored = (rec.get("art") if rec is not None else None) or ""
    keys = [k.strip() for k in str(authored).split(",") if k.strip()]
    if keys:
        return tuple(keys)
    try:
        from sbs_utils.procedural.ship_data import plain_asteroid_keys
        got = tuple(plain_asteroid_keys() or ())
        if got:
            return got
    except Exception:
        pass
    return ("plain_asteroid_6", "plain_asteroid_7", "plain_asteroid_8")


def universe_relic_atmosphere(key):
    """Fill the relic with ONE nebula. Returns how many were made.

    THE POINT IS NOT THE LOOK: the engine caps warp for a ship inside a nebula by itself,
    so the interior needs no script governor. One object, not one per chamber - a single
    nebula covers ~12000u and the relic's bounding sphere is smaller than that.

    `Atmosphere: none` opts out, for a ruin that is meant to be enterable at speed.
    """
    vol = volume_get(_universe_relic_volume_name(key))
    if vol is None:
        return 0
    rec = relic_record(key)
    color = str((rec.get("atmosphere") if rec is not None else None) or "purple").strip()
    if color.lower() in ("none", "no", "off"):
        return 0
    atmos = universe_relic_atmos_role(key)
    if len(role(atmos)):
        return len(role(atmos))
    (cx, cy, cz), radius = vol.bound()
    # The CLOUD covers the ruin: the relic's own bounding radius, which is what makes the
    # engine cap warp everywhere inside the structure. That is a different number from how
    # big each nebula OBJECT is, and conflating the two is what asked the renderer for a
    # single 9947-unit object.
    span = radius
    # A GLOBAL, and it is RESTORED. It changes the size of every nebula object spawned
    # after it, so leaving it set meant this ruin quietly resized the clouds of every
    # system the crew visited afterwards - a relic reaching out of its own cell and into
    # the rest of the galaxy. Set it, spawn, put it back.
    import sbs_utils.procedural.terrain as _terrain
    _was = getattr(_terrain, "NEB_SIZE_LARGE", 1500)
    terrain_set_nebula_object_size(UNIVERSE_RELIC_NEBULA_OBJECT)
    made = 0
    try:
        neb = terrain_spawn_nebula_sphere(
            cx, cy, cz, radius=int(span),
            density_scale=UNIVERSE_RELIC_NEBULA_SCALE,
            density=UNIVERSE_RELIC_NEBULA_DENSITY, height=int(span),
            cluster_color=color, marker=False)
    finally:
        terrain_set_nebula_object_size(_was)
    for n in (neb or []):
        # terrain_* hands back SpawnData; the agent is .py_object.
        agent = getattr(n, "py_object", None)
        if agent is not None:
            agent.add_role(atmos)
            made += 1
    return made


def universe_relic_contact(key, name):
    """A selectable contact at the relic's mouth, so science can call a bearing.

    THE CREW HAS TO FIND THE RUIN, and a landmark sits 8,000-30,000u from where a jump
    puts you. Without something on the radar the search is not archaeology, it is a
    featureless sweep of empty space. So the mouth reads as a contact from arrival - a
    direction and a distance - and everything past that is flying.

    The point carrying `Roles: entrance` decides where; failing that, the relic's own
    centre. Returns the world position, or None.
    """
    pos = None
    ways = relic_points(key, "entrance")
    if ways:
        pos = list(ways.values())[0]
    else:
        rec = relic_record(key)
        if rec is not None:
            pos = tuple(relic_pos(rec))
    if pos is None:
        return None
    try:
        marker_object(pos[0], pos[1], pos[2], str(name),
                      roles=universe_relic_mark_role(key) + ", relic_contact, landmark")
        if UNIVERSE_RELIC_NAVPOINT:
            marker_point(pos[0], pos[1], pos[2], str(name))
    except Exception as e:
        log(f"relic '{key}': no sensor contact: {e}", "universe", "warning")
        return pos
    return pos


def universe_relic_release_cell(ei, ej):
    """Release every relic in a cell. Called as the cell is torn down.

    Per-relic, never `volume_clear()`: the next cell is already being built by the time a
    departure is processed, so clearing everything would take the ruin the crew just flew
    into. The OBJECTS are not deleted here - `universe_clear_cell` deletes everything in
    the cell's box, which is what the props and the nebula are.
    """
    live = _UNIVERSE_RELICS.pop((int(ei), int(ej)), None)
    if not live:
        return 0
    for key in list(live.keys()):
        try:
            relic_release(key)
        except Exception as e:
            log(f"relic '{key}' would not release: {e}", "universe", "warning")
    return len(live)


def universe_relics_in_cell(ei, ej):
    """The relic keys currently built in a cell."""
    return list((_UNIVERSE_RELICS.get((int(ei), int(ej))) or {}).keys())


def universe_in_relic(ship_id=None):
    """Is this ship inside a relic right now? Returns the relic key, or None.

    The answer to "leave them alone, they are in the ruin". Reads the containment
    watcher's own latch (`volume_engaged`) rather than recomputing depth, so it agrees
    with whatever containment is actually doing to that ship.

    With no ship, True if ANY ship is inside any relic.
    """
    for cell, live in _UNIVERSE_RELICS.items():
        for key, info in live.items():
            inside = volume_engaged(info.get("volume") or key)
            if not inside:
                continue
            if ship_id is None:
                return key
            if int(ship_id) in inside:
                return key
    return None


def universe_relic_holds(key, pos):
    """Is this position inside relic `key`? The extraction test.

    Hauling a thing OUT of a ruin is the one question the containment latch cannot answer,
    because the latch is about ships and the thing on the tether is cargo.
    """
    vol = volume_get(_universe_relic_volume_name(key))
    if vol is None:
        return False
    return volume_contains(vol, pos)


def universe_arrival_consoles(ei, ej):
    """Every console of every player ship in a cell - the audience for an arrival.

    A cutscene or an overlay resolves its audience through `consoles_of`, which takes a
    ship and finds its consoles; a set of SHIPS is the honest way to say "whoever is
    here". Returns a set, empty when nobody has landed yet.
    """
    out = set()
    for so in objects_in_cell(to_object_list(role("__player__")), ei, ej):
        out.add(so.id)
    return out


def universe_relics_clear():
    """Forget every live relic (mission reset). The records and volumes are dropped by the
    library's own reset; this is only the cell bookkeeping."""
    _UNIVERSE_RELICS.clear()
    _UNIVERSE_RELIC_FILES.clear()


def universe_relic_count():
    """How many relics are built right now, across every live cell."""
    return sum(len(v) for v in _UNIVERSE_RELICS.values())


# --- internals ---------------------------------------------------------------

def _universe_relic_volume_name(key):
    rec = relic_record(key)
    return (rec.get("volume") if rec is not None else None) or key


def _universe_relic_prop(rng, art_keys, x, y, z, scale, wall_role):
    """One piece of wall: terrain, non-solid, never an AI behavior.

    `exclusion_radius = 0` matters - an AI `behav_*` object with radius 0 NaNs the engine,
    and terrain with a radius pushes the ship away from the wall it is meant to be.
    """
    art = art_keys[rng.randrange(len(art_keys))]
    p = terrain_spawn(x, y, z, "", "#," + wall_role, art, "behav_asteroid")
    s = scale * rng.uniform(0.75, 1.35)
    p.blob.set("local_scale_x_coeff", s, 0)
    p.blob.set("local_scale_y_coeff", s * rng.uniform(0.8, 1.2), 0)
    p.blob.set("local_scale_z_coeff", s * rng.uniform(0.8, 1.2), 0)
    p.engine_object.exclusion_radius = 0
    return p


def _universe_relic_near_size(vol, p):
    """The size of the feature a point belongs to, so a prop scales to its room.

    Nearest-primitive rather than exact ownership: a prop at a junction could belong to
    either shape, and the closer one is both cheap and what the eye expects.
    """
    best, bestd = 600.0, float("inf")
    for prim in vol.primitives():
        if prim[0] == "sphere":
            d, size = abs(_universe_relic_dist(p, prim[1]) - prim[2]), prim[2]
        elif prim[0] == "capsule":
            d, size = abs(_universe_relic_dist(p, prim[1]) - prim[3]), prim[3]
        else:
            d, size = _universe_relic_dist(p, prim[1]), min(prim[2])
        if d < bestd:
            bestd, best = d, size
    return best


def _universe_relic_dist(a, b):
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(3)))
