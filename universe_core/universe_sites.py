"""Away sites in a universe - a landmark that is a place you BEAM DOWN to.

A landmark carrying `Site:` is neither a prop nor an interior you fly into. It is
somewhere the crew leaves the ship for: a colony dome, a silent outpost, a station whose
crew stopped answering. The scene it plays is authored as a self-contained `.amd` - a
cast under `## Away Team`, beats under `## Scenes`, optionally an arrival call under
`## Hails` - and the away module (`sbs_utils.procedural.away`) drives it, giving every
console its own character with its own menu.

This is the same shape `universe_relics.py` has, for the same three reasons:

* **A cell's world origin is transient**, so a site cannot author a position. It is bound
  on arrival to whatever object the landmark spawned.
* **A cell is destroyed on departure and rebuilt on return**, while the NEXT cell is
  already being built, so teardown is per-site and never global.
* **Two sites can be live at once** - two ships in two systems, Model A. Nothing here may
  assume there is only one.

**The content is portable, and that is the point.** The `## Away Team` / `## Scenes`
vocabulary is exactly what a standalone mission uses (`LandingParty`), so a site file
written for one plays in the other unchanged. `Site:` is the seam, not a second dialect.

Every function is prefixed `universe_` because an addon's module-level functions land in
one flat, mission-wide MAST namespace - a leading underscore does not make one private.
"""

from sbs_utils.procedural.amd_dialogue import dialogue_scenes
from sbs_utils.procedural.amd_doc import amd_document, amd_section
from sbs_utils.procedural.amd_lifeforms import lifeforms_spawn
from sbs_utils.procedural.amd_mission import amd_mission_data
from sbs_utils.procedural.execution import log
from sbs_utils.procedural.inventory import set_inventory_value
from sbs_utils.procedural.query import to_id
from sbs_utils.procedural.roles import add_role


# Live sites, so teardown and "what site is this object" can both answer per cell.
# {(i, j): {site_key: {"object": id, "name": str}}}
_UNIVERSE_SITES = {}

# Parsed site files, by key. The record is what a hail, a quest or a comms line asks
# about, and it must answer whether or not anyone is currently standing in the place -
# so registering is separate from placing, exactly as it is for relics.
# {key: {"key", "file", "scenes", "cast", "hails", "name"}}
_UNIVERSE_SITE_RECORDS = {}

# Files already read, so a second landmark naming a key that is not in the file gets
# told rather than silently falling back to being a prop.
_UNIVERSE_SITE_FILES = set()

# The role a site's object carries. A mission's own routes gate on this - it is how
# "the crew is in orbit of something they can beam down to" is asked.
UNIVERSE_SITE_ROLE = "away_site"


def universe_site_record(key):
    """The parsed record for a site key, or None if nothing has registered it."""
    return _UNIVERSE_SITE_RECORDS.get(str(key).strip()) if key else None


def universe_site_load(key, fname, content=None):
    """Read and register a site file, once. Returns the record or None.

    ``content`` is for tests and for a caller that has the text already; production
    reads it the universe's own way (consumer mission dir first, then code-relative and
    packaged-mastlib aware), because an addon inside a `.mastlib` cannot open its own
    files by path.
    """
    key = str(key).strip()
    if not key:
        return None
    rec = _UNIVERSE_SITE_RECORDS.get(key)
    if rec is not None:
        return rec
    if content is None:
        if fname in _UNIVERSE_SITE_FILES:
            # The file was read and this key was not in it. Worth naming: the landmark
            # will otherwise be a place the crew can reach and find nothing in.
            log(f"site '{key}' is not in '{fname}'", "universe", "warning")
            return None
        try:
            # BARE, with no import, exactly as `universe_relics.py` calls it. Every OU
            # module is exec'd into ONE shared namespace - the MAST merge - so a
            # cross-module name resolves at CALL time. A relative import here would be
            # the thing that breaks: there is no package to be relative to.
            content = universe_read_content(fname)
        except Exception as e:
            content = None
            log(f"site file '{fname}' would not read: {e}", "universe", "warning")
        if not content:
            log(f"site file '{fname}' not found for '{key}'", "universe", "warning")
            return None
        _UNIVERSE_SITE_FILES.add(fname)

    try:
        doc = amd_document(content, data_parser=amd_mission_data)
    except Exception as e:
        log(f"site file '{fname}' failed to parse: {e}", "universe", "warning")
        return None

    scenes = dialogue_scenes(amd_section(doc, "away")) or {}
    if not scenes:
        # A site with no beats is an authoring mistake, not an empty place: the crew
        # would beam down into a conversation that closes on the frame it opens.
        log(f"site '{key}' has no '## Scenes' beats", "universe", "warning")
        return None

    rec = {
        "key": key,
        "file": fname,
        "scenes": scenes,
        # The CAST IS NOT SPAWNED HERE. Spawning is an arrival-time act - a lifeform is a
        # body in the world, and a cell that has not been visited has no world to put one
        # in. Held as the section so `universe_site_arrive` can spawn on arrival and the
        # bodies go with the cell.
        "cast_section": amd_section(doc, "team"),
        "hails": dialogue_scenes(amd_section(doc, "hails")) or {},
        "name": None,
    }
    _UNIVERSE_SITE_RECORDS[key] = rec
    return rec


def universe_site_place(key, obj, ei, ej, name=None):
    """Bind a site to the object a landmark spawned, in cell (ei, ej).

    Idempotent per cell: arriving twice, or a second ship arriving, binds nothing new.
    Returns the record, or None when the site never registered.
    """
    rec = _UNIVERSE_SITE_RECORDS.get(str(key).strip()) if key else None
    if rec is None:
        return None
    obj_id = to_id(obj)
    if not obj_id:
        return None
    live = _UNIVERSE_SITES.setdefault((int(ei), int(ej)), {})
    if rec["key"] in live:
        return rec
    live[rec["key"]] = {"object": obj_id, "name": name or rec["key"]}
    if name:
        rec["name"] = name
    # The ROLE is the question a mission asks ("is this something we can beam down to");
    # the inventory value is the answer to "which site". Both, because a role cannot
    # carry a key and an inventory value cannot be queried as a set.
    add_role(obj_id, UNIVERSE_SITE_ROLE)
    set_inventory_value(obj_id, "SITE_KEY", rec["key"])
    return rec


def universe_site_for(obj):
    """The site key bound to this object, or None. The inverse of `universe_site_place`."""
    obj_id = to_id(obj)
    if not obj_id:
        return None
    for live in _UNIVERSE_SITES.values():
        for key, entry in live.items():
            if entry.get("object") == obj_id:
                return key
    return None


def universe_site_object(key, ei=None, ej=None):
    """The object a site is bound to, or None.

    With a cell, only that cell's binding answers - which matters with two ships in two
    systems, where the same site key could be live in both.
    """
    key = str(key).strip() if key else None
    if not key:
        return None
    if ei is not None and ej is not None:
        return (_UNIVERSE_SITES.get((int(ei), int(ej))) or {}).get(key, {}).get("object")
    for live in _UNIVERSE_SITES.values():
        if key in live:
            return live[key].get("object")
    return None


def universe_site_scenes(key):
    """The beats a site plays, ready for `away_scene_begin`."""
    rec = universe_site_record(key)
    return (rec or {}).get("scenes") or {}


def universe_site_hails(key):
    """The arrival call a site authors, ready for `hail_ask(scenes=...)`. May be empty."""
    rec = universe_site_record(key)
    return (rec or {}).get("hails") or {}


def universe_site_cast_section(key):
    """The site's `## Away Team` section, for spawning its bodies on arrival."""
    rec = universe_site_record(key)
    return (rec or {}).get("cast_section")


def universe_site_spawn_cast(key):
    """Spawn the site's cast. Returns `{member_key: lifeform}`, or `{}`.

    Deliberately NOT done at load: a lifeform is a body in the world, and a site that has
    been read but never visited has no world to put one in. Called on arrival.
    """
    section = universe_site_cast_section(key)
    if section is None:
        return {}
    try:
        return lifeforms_spawn(section) or {}
    except Exception as e:
        log(f"site '{key}' cast would not spawn: {e}", "universe", "warning")
        return {}


def universe_site_release_cell(ei, ej):
    """Release every site in a cell. Called as the cell is torn down.

    Per-site, never global: the next cell is already being built by the time a departure
    is processed, so clearing everything would take the site the OTHER ship is standing
    in. The OBJECTS are not deleted here - `universe_clear_cell` deletes everything in
    the cell's box, which is what the landmark and its cast are.

    The RECORD survives, because it is the parsed file rather than the placement: coming
    back to the same system must not re-read it, and a quest asking about a site the crew
    has left still deserves an answer.
    """
    live = _UNIVERSE_SITES.pop((int(ei), int(ej)), None)
    if not live:
        return 0
    return len(live)


def universe_sites_in_cell(ei, ej):
    """The site keys currently bound in a cell."""
    return list((_UNIVERSE_SITES.get((int(ei), int(ej))) or {}).keys())


def universe_sites_clear():
    """Drop every site, placed and parsed. For a mission restart and for tests.

    Registered with the reset ledger by the consumer, like every other module-level
    per-mission container - an unregistered one is invisible to the restart soak.
    """
    _UNIVERSE_SITES.clear()
    _UNIVERSE_SITE_RECORDS.clear()
    _UNIVERSE_SITE_FILES.clear()
