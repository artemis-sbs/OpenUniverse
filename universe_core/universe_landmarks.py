"""Landmarks for the Open Universe - named, hand-placed stations / wrecks / beacons
pinned to a system (like side homes), as discovery anchors and quest hooks. A
`## Landmarks` section authors them; on entering their system universe.mast spawns
each by kind at a deterministic position. universe_section comes from
universe_sides.py (shared namespace).
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
                "kind": (data.get("kind") or "station"),
                "side": data.get("side") or universe_primary_side(),
                "art": data.get("art"),
                "roles": data.get("roles"),
                # Kind: worldlet landmarks name their worldlet type (Type: cinder).
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
    """A landmark's away site, as `(key, file)`, or None when nobody beams down here.

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
    """The art for a landmark: the authored Art, else a kind default (grid-backed
    station / a wreck)."""
    a = lm.get("art")
    if a:
        return a
    return "wreck" if lm.get("kind") == "derelict" else "starbase_science"
