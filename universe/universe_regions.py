"""Regions for the Open Universe - named areas of the galaxy map with their own
identity. A `## Regions` section authors them: a Center + Radius (a Chebyshev
square in i,j space) plus a Skybox and Music. On arrival the system's region sets
the sky + music (universe.mast); cells no region claims keep the default. This
gives the galaxy *geography* - the Ashen Reach vs. the Verdant Belt - as content.

Driver only (parse + point-in-region lookup); the visual effect is the
skybox_schedule / music_schedule calls in universe.mast. universe_section comes
from universe_clans.py (shared namespace).
"""
from sbs_utils.mast.mast_node import MastDataObject


def universe_parse_regions(doc):
    """Region records from the `## Regions` section (empty if none)."""
    section = universe_section(doc, "regions")
    out = []
    if section is not None:
        for n in section.get("children", []):
            data = n.get("data") or {}
            c = data.get("center")
            out.append(MastDataObject({
                "key": n.get("key"),
                "name": n.get("display_text"),
                "desc": (n.get("description") or "").strip(),
                "center": c if (c and len(c) == 2) else None,
                "radius": int(data.get("radius") or 0),
                "skybox": data.get("skybox"),
                "music": data.get("music"),
            }))
    return out


def region_for_system(regions, i, j):
    """The first region whose Center/Radius (a Chebyshev square) contains (i, j), or
    None. Author smaller/inner regions first so they win over larger ones."""
    for rgn in regions:
        c = rgn.get("center")
        r = rgn.get("radius") or 0
        if c and abs(int(i) - int(c[0])) <= r and abs(int(j) - int(c[1])) <= r:
            return rgn
    return None
