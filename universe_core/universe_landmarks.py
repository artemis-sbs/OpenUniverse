"""Landmarks for the Open Universe - named, hand-placed stations / wrecks / beacons
pinned to a system (like side homes), as discovery anchors and quest hooks. A
`## Landmarks` section authors them; on entering their system universe.mast creates
each through its `Prefab:` at a deterministic position. universe_section comes from
universe_sides.py (shared namespace).

`Prefab:` replaced `Kind:` (2026-10-14). Open Universe's own `derelict`, `station` and
`worldlet` prefabs live in universe_prefabs.mast and override the library defaults of
the same name; any other prefab a mission or LM provides works too. `Guards:` and
`Terrain:` take a prefab as well - a one-line name, or a nested Prefab / Count / Data
block - and the older `<race> [difficulty]` / `<kind> [color]` phrases still read.
"""
import math
import random
from sbs_utils.mast.mast_node import MastDataObject


def universe_parse_landmarks(doc):
    """Landmark records from the `## Landmarks` section (empty if none)."""
    section = universe_section(doc, "landmarks")
    out = []
    if section is not None:
        for n in section.get("children", []):
            data = n.get("data") or {}
            at = data.get("at")
            out.append(MastDataObject({
                "key": n.get("key"),
                "name": n.get("display_text"),
                "desc": (n.get("description") or "").strip(),
                "at": at if (at and len(at) == 2) else None,
                # WHAT it is: a prefab type or label name. No default - a landmark that
                # names none creates nothing, and lint says so (landmark-no-prefab).
                "prefab": (str(data.get("prefab")).strip().lower()
                           if data.get("prefab") else None),
                "side": data.get("side") or universe_primary_side(),
                # The side as WRITTEN. Only an authored side is handed to the prefab, so a
                # wreck or a nebula is not quietly put on the primary side.
                "side_written": data.get("side"),
                # Data: the prefab's own arguments, one nested line each.
                "args": data.get("data") if hasattr(data.get("data"), "items") else {},
                "art": data.get("art"),
                "roles": data.get("roles"),
                # Prefab: worldlet landmarks name their worldlet type (Type: cinder).
                "wtype": data.get("type"),
                # Guards: an optional complication fleet contesting this landmark -
                # `Guards: <race> [difficulty]` (e.g. "skaraan" or "torgoth 3").
                # Spawned on arrival, one-shot (persisted), by universe.mast.
                "guards": data.get("guards"),
                # Terrain: an optional terrain envelope wrapping this landmark -
                # `Terrain: <kind> [color]` (nebula / asteroids; color is nebula-only).
                # Guarantees the ruin sits in cover regardless of the cell's rolled
                # kind; spawned on arrival by universe.mast.
                "terrain": data.get("terrain"),
                # Relic: this landmark is not a prop but an INTERIOR - a flyable ruin
                # authored as an `## Relics` section. The key names the relic; the file
                # is read mission-relative (universe_read_content), so a consumer keeps
                # its relics in its own repo. Built on arrival, released with the cell.
                "relic": data.get("relic"),
                # UNDERSCORED: the fence parser turns `Relic file:` into `relic_file`,
                # the same way `Scrape band:` becomes `scrape_band`. Reading the spaced
                # form gets None and the loader falls back to `<key>.amd`, which is a
                # missing-file error against a name the author never wrote.
                "relic_file": data.get("relic_file"),
                # Site: this landmark is a place the crew BEAMS DOWN to - a colony, an
                # outpost, a station that stopped answering. The key names the site; the
                # file is read mission-relative, same as a relic. A site and a relic are
                # different verbs on the same landmark (fly INTO vs leave the ship FOR),
                # so nothing stops one carrying both.
                "site": data.get("site"),
                # UNDERSCORED, for the reason spelled out above: the fence parser turns
                # `Site file:` into `site_file`.
                "site_file": data.get("site_file"),
                # Cutscene: played ONCE per system, the first time anyone arrives here
                # (the flag is persisted, like guards_cleared). The name is a cutscene
                # bed the mission has loaded with amd_cutscenes.
                "cutscene": data.get("cutscene"),
            }))
    return out


def universe_landmark_prefab_data(lm, pos, ei=None, ej=None):
    """The variables a landmark hands its prefab: position (exact - a landmark is
    authored to a point), name, the side and roles as written, art, the worldlet type,
    the record and the cell it is in, then its `Data:` block, which wins."""
    from sbs_utils.procedural.prefab import prefab_data
    data = {"START_X": pos[0], "START_Y": pos[1], "START_Z": pos[2], "START_EXACT": True,
            "AMD_RECORD": lm, "AMD_KEY": lm.get("key"),
            "UNIVERSE_EI": ei, "UNIVERSE_EJ": ej}
    name = lm.get("name")
    if name:
        data["NAME"] = name
        data["name"] = name
        data["display_text"] = name
    if lm.get("side_written"):
        data["side_value"] = lm.get("side_written")
    if lm.get("roles"):
        data["roles_value"] = lm.get("roles")
    if lm.get("art"):
        data["art"] = lm.get("art")
    if lm.get("wtype"):
        data["worldlet_type"] = lm.get("wtype")
    data.update(prefab_data(lm.get("args"), where=f"landmark {lm.get('key')}"))
    return data


def universe_landmark_create(lm, pos, ei=None, ej=None):
    """Create a landmark through its `Prefab:`; returns what was created, or None (a
    `point`, a landmark naming no prefab, or one that does not resolve - logged)."""
    from sbs_utils.procedural.prefab import prefab_create
    spec = lm.get("prefab")
    if not spec:
        from sbs_utils.procedural.execution import log
        log(f"landmark '{lm.get('key')}' names no Prefab: - nothing created",
            "universe", "warning")
        return None
    return prefab_create(spec, universe_landmark_prefab_data(lm, pos, ei, ej),
                         where=f"landmark {lm.get('key')}")


def _universe_spec(value, legacy, legacy_words=()):
    """A Guards:/Terrain: value as a prefab spec, its `Data:` already normalized. A value
    whose first word is no prefab - or is one of ``legacy_words``, which the older phrase
    owns even where a prefab of that name exists - is read by ``legacy(spec) -> spec``."""
    from sbs_utils.procedural.prefab import amd_prefab_spec, prefab_resolve, prefab_data
    spec = amd_prefab_spec(value)
    if spec is None:
        return None
    if not hasattr(value, "items") and (
            spec["prefab"] in legacy_words
            or prefab_resolve(spec["prefab"], warn=False) is None):
        spec = legacy(spec)
        if spec is None:
            return None
    spec["args"] = prefab_data(spec.get("args"))
    return spec


def universe_landmark_guards_spec(lm, default_difficulty=5):
    """A landmark's `Guards:` as a prefab spec ``{"prefab", "count", "args"}``, or None.

    `Guards: fleet/raider` (a prefab), the nested Prefab / Count / Data block, or the
    older `Guards: <race> [difficulty]`, which is `fleet/raider` with that race."""
    def legacy(spec):
        g = universe_landmark_guards(lm, default_difficulty)
        return {"prefab": "fleet/raider", "count": 1,
                "args": {"race": g["race"], "fleet_difficulty": g["difficulty"]}}
    if not lm.get("guards"):
        return None
    spec = _universe_spec(lm.get("guards"), legacy)
    if spec is not None and spec["prefab"] == "fleet/raider":
        spec["args"].setdefault("fleet_difficulty", default_difficulty)
    return spec


def universe_landmark_guards_create(lm, pos, default_difficulty=5):
    """Spawn a landmark's guards at ``pos``; True if any prefab started.

    Every guard carries `raider, landmark_guards` (the watch scopes the clear to those)
    unless the `Data:` block names its own `ship_roles`."""
    from sbs_utils.procedural.prefab import prefab_create
    spec = universe_landmark_guards_spec(lm, default_difficulty)
    if spec is None:
        return False
    started = False
    for n in range(max(1, int(spec["count"] or 1))):
        data = {"ship_roles": "raider, landmark_guards",
                "START_X": pos[0] + n * 1500, "START_Y": pos[1], "START_Z": pos[2]}
        data.update(spec["args"])
        if prefab_create(spec["prefab"], data, where=f"guards of {lm.get('key')}") is not None:
            started = True
    return started


def universe_landmark_terrain_spec(lm):
    """A landmark's `Terrain:` as a prefab spec, or None.

    `Terrain: terrain/nebula/sphere`, the nested block, or the older `<kind> [color]`:
    `nebula [color]` and `asteroids` are LM's sphere prefabs with the cover-sized
    settings this envelope has always used."""
    def legacy(spec):
        t = universe_landmark_terrain(lm)
        if t is None:
            return None
        if t["kind"] == "nebula":
            return {"prefab": "terrain/nebula/sphere", "count": 1,
                    "args": {"SIZE_X": 9000, "density_scale": 2.5, "density": 2,
                             "height": 8000, "cluster_color": t["color"] or "blue",
                             "selectable": False}}
        if t["kind"] == "asteroid":
            # The LM prefab takes a DIAMETER (SIZE_X // 2 is the radius).
            return {"prefab": "terrain/asteroid/sphere", "count": 1,
                    "args": {"SIZE_X": 16000, "density_scale": 2.0, "density": 2,
                             "height": 2000, "selectable": True}}
        return None
    if not lm.get("terrain"):
        return None
    # `nebula` and `asteroids` are the OLD phrase here, never the library's one-object
    # `nebula` landmark prefab - that one needs an Art: and is not cover.
    return _universe_spec(lm.get("terrain"), legacy,
                          legacy_words=("nebula", "nebulas", "nebulae", "asteroid", "asteroids"))


def universe_landmark_terrain_create(lm, pos):
    """Wrap a landmark in its `Terrain:` envelope at ``pos``; True if it started."""
    from sbs_utils.procedural.prefab import prefab_create
    spec = universe_landmark_terrain_spec(lm)
    if spec is None:
        return False
    data = {"START_X": pos[0], "START_Y": pos[1], "START_Z": pos[2]}
    # Normalized args are lower case; SIZE_X is the prefab's own spelling.
    args = dict(spec["args"] or {})
    if "size_x" in args:
        args["SIZE_X"] = args.pop("size_x")
    data.update(args)
    return prefab_create(spec["prefab"], data, where=f"terrain of {lm.get('key')}") is not None


def universe_landmark_guards(lm, default_difficulty=5):
    """A landmark's optional complication fleet, parsed from its `Guards:` field.

    `Guards: <race> [difficulty]` -> {"race": <str>, "difficulty": <int>}. The race
    is passed straight to prefab_fleet_raider (author picks a valid one, e.g.
    skaraan / torgoth / kralien); an omitted difficulty falls back to the mission's.
    Returns None when the landmark authors no guards.
    """
    g = lm.get("guards")
    if not g:
        return None
    toks = str(g).split()
    if not toks:
        return None
    diff = default_difficulty
    if len(toks) >= 2:
        try:
            diff = int(toks[1])
        except ValueError:
            diff = default_difficulty
    return {"race": toks[0], "difficulty": diff}


def universe_landmark_terrain(lm):
    """A landmark's optional terrain envelope, from its `Terrain:` field.

    `Terrain: <kind> [color]` -> {"kind": <str>, "color": <str|None>}. kind is
    normalized to singular ("asteroids"->"asteroid"); the color applies to nebula
    only (a color name the engine knows, e.g. blue/violet/red). Returns None when
    the landmark authors no terrain.
    """
    t = lm.get("terrain")
    if not t:
        return None
    toks = str(t).split()
    if not toks:
        return None
    kind = toks[0].strip().lower()
    if kind.endswith("s"):
        kind = kind[:-1]
    color = toks[1].strip() if len(toks) >= 2 else None
    return {"kind": kind, "color": color}


def universe_landmarks_in_system(landmarks, i, j):
    """Landmarks pinned to system (i, j)."""
    out = []
    for lm in landmarks:
        a = lm.get("at")
        if a and len(a) == 2 and int(a[0]) == int(i) and int(a[1]) == int(j):
            out.append(lm)
    return out


def universe_landmark_pos(syskey, lm):
    """A deterministic [x, y, z] for a landmark in its system (per-landmark seed, so
    several in one system don't overlap)."""
    r = random.Random()
    r.seed(int(syskey) + sum(ord(c) for c in str(lm.get("key"))))
    ang = r.uniform(0, 2 * math.pi)
    dist = r.uniform(8000, 30000)
    return [math.cos(ang) * dist, r.uniform(-300.0, 300.0), math.sin(ang) * dist]


def universe_landmark_relic(lm):
    """A landmark's interior, as `(key, file)`, or None when it is just a prop.

    The file defaults to `<key>.amd` beside the mission's other content, because an
    author who names one relic per file should not have to say so twice.
    """
    key = lm.get("relic")
    if not key:
        return None
    key = str(key).strip()
    if not key:
        return None
    fname = lm.get("relic_file")
    return (key, str(fname).strip() if fname else key + ".amd")


def universe_landmark_site(lm):
    """A landmark's boarding site, as `(key, file)`, or None when nobody beams down here.

    The file defaults to `<key>.amd`, because an author who names one site per file
    should not have to say so twice. Exactly `universe_landmark_relic`'s contract - the
    two are different verbs on a landmark, not competing ones.
    """
    key = lm.get("site")
    if not key:
        return None
    key = str(key).strip()
    if not key:
        return None
    fname = lm.get("site_file")
    return (key, str(fname).strip() if fname else key + ".amd")

def universe_landmark_cutscene_for(landmarks, i, j):
    """The cutscene a system plays on its FIRST visit, or None.

    First landmark that authors one wins. A cell with two set-pieces is an authoring
    mistake rather than a feature - they would fight over the same console.
    """
    for lm in universe_landmarks_in_system(landmarks or [], i, j):
        cut = lm.get("cutscene")
        if cut and str(cut).strip():
            return str(cut).strip()
    return None


def universe_landmark_art(lm):
    """The art for a landmark: the authored Art, else its prefab's usual one (a wreck
    for a derelict, a grid-backed station otherwise). The OU prefabs default the same
    way; this is for callers that need the art without creating anything."""
    a = lm.get("art")
    if a:
        return a
    return "wreck" if lm.get("prefab") == "derelict" else "starbase_science"
