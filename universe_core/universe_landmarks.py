"""Landmarks for the Open Universe - named, hand-placed stations / wrecks / beacons
pinned to a system (like clan homes), as discovery anchors and quest hooks. A
`## Landmarks` section authors them; on entering their system universe.mast spawns
each by kind at a deterministic position. universe_section comes from
universe_clans.py (shared namespace).
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


def universe_landmark_art(lm):
    """The art for a landmark: the authored Art, else a kind default (grid-backed
    station / a wreck)."""
    a = lm.get("art")
    if a:
        return a
    return "wreck" if lm.get("kind") == "derelict" else "starbase_science"
