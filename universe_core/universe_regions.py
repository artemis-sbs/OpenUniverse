"""Regions for the Open Universe - named areas of the galaxy map with their own
identity. A `## Regions` section authors them: a Center + Radius (a Chebyshev
square in i,j space) plus a Skybox and Music. On arrival the system's region sets
the sky + music (universe.mast); cells no region claims keep the default. This
gives the galaxy *geography* - the Ashen Reach vs. the Verdant Belt - as content.

A region with `Kind: antimatter` is an **antimatter veil** (ADMIRAL_CONSOLE.md
section 8): its systems are survivable only briefly - every player ship inside
takes continuous heat + system damage (region_veil_tick, driven from
universe.mast's veil loop). The veil is a story fence: crossing it is possible,
lingering is not. Optional `Heat:` / `Damage:` lines tune the per-second rates.

Mostly a driver (parse + point-in-region lookup); the visual effect is the
skybox_schedule / music_schedule calls in universe.mast. universe_section comes
from universe_sides.py (shared namespace).
"""
from sbs_utils.mast.mast_node import MastDataObject
from sbs_utils.procedural.roles import role
from sbs_utils.procedural.query import to_object_list, get_data_set_value, set_data_set_value


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
                # Kind: antimatter -> a veil region (unsurvivable to linger).
                "kind": str(data.get("kind") or "").strip().lower() or None,
                # Optional veil tuning (per-second rates; defaults below).
                "heat": data.get("heat"),
                "damage": data.get("damage"),
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
    wash that side/quest colors still override. #RGB -> #RGBA, #RRGGBB -> #RRGGBBAA."""
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
    region, or the region set no Color). Geography, not intel - shown even
    unexplored. A veil region always washes (default amber, harder alpha) -
    the information IS the wall, so the band must read on the chart."""
    rgn = region_for_system(regions, i, j)
    if rgn is None:
        return None
    col = rgn.get("color")
    if rgn.get("kind") == "antimatter":
        s = str(col or "#f80").strip()
        if s.startswith("#") and len(s) == 4:
            return s + "6"
        if s.startswith("#") and len(s) == 7:
            return s + "66"
        return s
    if not col:
        return None
    return _region_faint(col)


# --- The antimatter veil ------------------------------------------------------
VEIL_HEAT_PER_S = 0.02      # system_cur_heat added per second (0-1 scale)
VEIL_DAMAGE_PER_S = 0.004   # system_damage added per second
VEIL_SYSTEM_COUNT = 8       # engineering system indices swept


def region_is_veiled(regions, i, j):
    """True when (i, j) lies inside an antimatter veil region."""
    rgn = region_for_system(regions, i, j)
    return rgn is not None and rgn.get("kind") == "antimatter"


def _veil_rate(value, default):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def region_veil_tick(regions, i, j, dt):
    """One veil damage step: every player ship in a veiled system heats up
    across all engineering systems (the heat damage channel - the engine's
    heat/damage routes fire from there). Returns False when (i, j) is not
    veiled, so the caller's loop ends after a jump out."""
    rgn = region_for_system(regions, i, j)
    if rgn is None or rgn.get("kind") != "antimatter":
        return False
    heat = _veil_rate(rgn.get("heat"), VEIL_HEAT_PER_S) * float(dt)
    dmg = _veil_rate(rgn.get("damage"), VEIL_DAMAGE_PER_S) * float(dt)
    # Only players actually IN cell (i, j) heat - not everyone in the galaxy.
    # objects_in_cell is a sibling helper resolved through the shared MAST namespace
    # (like region_for_system used in universe_helpers.py).
    for p in objects_in_cell(to_object_list(role("__player__")), i, j):
        for idx in range(VEIL_SYSTEM_COUNT):
            cur = get_data_set_value(p.id, "system_cur_heat", idx)
            if cur is None:
                continue
            set_data_set_value(p.id, "system_cur_heat", min(1.0, float(cur) + heat), idx)
            curd = get_data_set_value(p.id, "system_damage", idx) or 0.0
            set_data_set_value(p.id, "system_damage", float(curd) + dmg, idx)
    return True
