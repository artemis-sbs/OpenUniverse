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
            }))
    return out


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
