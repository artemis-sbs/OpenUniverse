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
                # Optional map tint (a #RGB / #RRGGBB color) - washes the region's
                # cells on the galaxy map so its geography reads at a glance.
                "color": data.get("color"),
                # Local generation overrides (same friendly knobs as the root
                # `generation:` block) - the system-kind mix inside this region.
                "generation": data.get("generation"),
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


def _region_faint(col):
    """An authored region color forced to a low alpha, so it reads as a subtle map
    wash that clan/quest colors still override. #RGB -> #RGBA, #RRGGBB -> #RRGGBBAA."""
    s = str(col).strip()
    if s.startswith("#"):
        hexd = s[1:]
        if len(hexd) == 3:
            return "#" + hexd + "3"
        if len(hexd) == 6:
            return "#" + hexd + "33"
    return s


def region_map_color(regions, i, j):
    """The faint map tint for cell (i, j) from its region's Color, or None (no
    region, or the region set no Color). Geography, not intel - shown even unexplored."""
    rgn = region_for_system(regions, i, j)
    if rgn is None:
        return None
    col = rgn.get("color")
    if not col:
        return None
    return _region_faint(col)
