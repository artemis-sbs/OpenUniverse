"""Away sites in a universe - a landmark that is a place you BEAM DOWN to.

A landmark carrying `Site:` is neither a prop nor an interior you fly into. It is
somewhere the crew leaves the ship for: a colony dome, a silent outpost, a station whose
crew stopped answering. The scene it plays is authored as a self-contained `.amd` -
beats under `## Scenes`, optionally an arrival call under `## Hails` - and the boarding
module (`sbs_utils.procedural.boarding`) drives it, giving every console its own menu.

**The crew go as themselves.** A site file has no cast of its own: the party is the
people already at the consoles, with the name, face and `Roles:` the ship's crew roster
gave them, and a job nobody aboard holds is forwarded to one console. One cast per
ship, for the whole story - the person on the bridge is the person who boards.

This is the same shape `universe_relics.py` has, for the same three reasons:

* **A cell's world origin is transient**, so a site cannot author a position. It is bound
  on arrival to whatever object the landmark spawned.
* **A cell is destroyed on departure and rebuilt on return**, while the NEXT cell is
  already being built, so teardown is per-site and never global.
* **Two sites can be live at once** - two ships in two systems, Model A. Nothing here may
  assume there is only one.

**The content is portable, and that is the point.** The `## Scenes` vocabulary is exactly
what a standalone mission uses, so a site file written for one plays in the other
unchanged. `Site:` is the seam, not a second dialect.

**A site the party WALKS is the same word.** When the universe's folder holds a tile
area file whose header says `area: <the site's key>`, the party beams down onto that
map instead of into a first room, and the site file's `## Props`, `## People` and
`## Hostiles` are what stands on it - the vocabulary of a standalone tile-map mission
(`boarding_ground_load`), unchanged. A site with no area of its own key is the text site
it always was. The tile files and the art load ONCE, as the universe starts
(`universe_site_ground_begin`); a site's own things are declared when its file is read.
Both are keyed, so a system rebuilt on return finds its doors as the crew left them.

Every function is prefixed `universe_` because an addon's module-level functions land in
one flat, mission-wide MAST namespace - a leading underscore does not make one private.
"""

from sbs_utils.procedural.amd_dialogue import dialogue_scenes
from sbs_utils.procedural.amd_doc import amd_document, amd_section
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
# {key: {"key", "file", "scenes", "hails", "name", "doc", "stories"}}
_UNIVERSE_SITE_RECORDS = {}

# Files already read, so a second landmark naming a key that is not in the file gets
# told rather than silently falling back to being a prop.
_UNIVERSE_SITE_FILES = set()

# What has already been said about a site that cannot be made, so a system rebuilt on
# every return says it once a game and not once a visit.
_UNIVERSE_SITE_SAID = set()

# Site keys whose file was read and REFUSED (no rooms, no map of its key). Asked for
# again - the system is rebuilt on every return - the answer is the same, and nothing
# more is said: without this the second asking read as "that file is another site's".
_UNIVERSE_SITE_REFUSED = set()

# One watcher per ship with a visit open: {ship id: tick task}. It ends a visit nobody
# went down to when the ship lets go of the place (`universe_site_visit_watch`).
_UNIVERSE_SITE_WATCH = {}

# The role a site's object carries. A mission's own routes gate on this - it is how
# "the crew is in orbit of something they can beam down to" is asked.
UNIVERSE_SITE_ROLE = "boarding_site"


def universe_site_say(message, once=None):
    """Tell the WRITER about a site that cannot be made or cannot be entered.

    In `mast.runtime.log`, which is the log a writer reads and the one a headless test
    fails on. `log(..., "universe", "warning")` alone goes nowhere - a named category has
    no handler unless a mission attaches one - and that is how a site that was refused
    came to have an empty log beside it. Said ONCE a game for the same thing (``once``):
    a system is rebuilt on every return, and its site is read again each time.
    """
    if once is not None:
        if once in _UNIVERSE_SITE_SAID:
            return False
        _UNIVERSE_SITE_SAID.add(once)
    try:
        log(message, "universe", "warning")
    except Exception:
        pass
    import logging
    logging.getLogger("mast.runtime").warning("universe site: " + str(message))
    return True


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
    if key in _UNIVERSE_SITE_REFUSED:
        return None                     # read once, refused, and said so then
    if content is None:
        if fname in _UNIVERSE_SITE_FILES:
            # The file was read and this key was not in it. Worth naming: the landmark
            # will otherwise be a place the crew can reach and find nothing in.
            universe_site_say(
                f"the landmark's `Site: {key}` was looked for in '{fname}', and that file "
                f"is another site's. This landmark has no site, so docking there does "
                f"nothing. Give it a file of its own (`{key}.amd`), or name one with "
                f"`Site file:`.", once=f"other:{key}")
            return None
        try:
            # BARE, with no import, exactly as `universe_relics.py` calls it. Every OU
            # module is exec'd into ONE shared namespace - the MAST merge - so a
            # cross-module name resolves at CALL time. A relative import here would be
            # the thing that breaks: there is no package to be relative to.
            content = universe_read_content(fname)
        except Exception as e:
            content = None
            universe_site_say(f"the site file '{fname}' (for `Site: {key}`) would not "
                              f"read: {e}", once=f"read:{key}")
        if not content:
            universe_site_say(
                f"the landmark's `Site: {key}` names the file '{fname}', and it was not "
                f"found beside the universe file. This landmark has no site, so docking "
                f"there does nothing. The file is `<key>.amd` unless the landmark says "
                f"`Site file:`.", once=f"missing:{key}")
            return None
        _UNIVERSE_SITE_FILES.add(fname)

    try:
        doc = amd_document(content, data_parser=amd_mission_data)
    except Exception as e:
        universe_site_say(f"the site file '{fname}' (for `Site: {key}`) could not be "
                          f"read as a document: {e}", once=f"parse:{key}")
        return None

    scenes = dialogue_scenes(amd_section(doc, "boarding")) or {}
    # A SITE THE PARTY WALKS: the universe's folder holds a tile area with this site's
    # key. Nothing else says so - no field, no second word.
    area = universe_site_area(key)
    if area is not None:
        # On a map a scene belongs to the thing or the person that opens it, and a
        # tile-map file heads them `## [Scenes](scenes)`. The text key still counts.
        for name in ("scenes", "scene"):
            for scene_key, node in (dialogue_scenes(amd_section(doc, name)) or {}).items():
                scenes.setdefault(scene_key, node)
    if not scenes and area is None:
        # A site with no beats is an authoring mistake, not an empty place: the crew
        # would beam down into a conversation that closes on the frame it opens.
        # (With an area there is a place to stand, so it is a place.)
        walked = {}
        for name in ("scenes", "scene"):
            walked.update(dialogue_scenes(amd_section(doc, name)) or {})
        if walked or _universe_site_ground_sections(doc):
            # Written as a site the party WALKS, and there is no map with its key. It is
            # NOT played as text: a walked site's scenes belong to its things and its
            # people, and none of them is a first room to arrive in.
            universe_site_say(
                f"the site '{key}' ('{fname}') is written as a place the party walks - "
                f"its scenes are under `## [Scenes](scenes)` and it stands things on a "
                f"map - and no .tiles file in this universe's folder says `area: {key}`. "
                f"So this site does not exist: no call when the ship docks, and nothing "
                f"to board. Make the area's key the site's key (`area: {key}` on the "
                f"first lines of the .tiles file). For a site of rooms and choices with "
                f"no map, key its rooms `boarding` instead: `## [Scenes](boarding)`.",
                once=f"norooms:{key}")
            _UNIVERSE_SITE_REFUSED.add(key)
        else:
            universe_site_say(
                f"the site '{key}' ('{fname}') has no rooms, so this site does not "
                f"exist: no call when the ship docks, and nothing to board. A site's "
                f"rooms go in a chapter keyed `boarding` - `## [Scenes](boarding)` - and "
                f"the first one is where the party arrives.", once=f"norooms:{key}")
            _UNIVERSE_SITE_REFUSED.add(key)
        return None

    rec = {
        "key": key,
        "file": fname,
        "scenes": scenes,
        "hails": dialogue_scenes(amd_section(doc, "hails")) or {},
        "name": None,
        # KEPT, because a walked site is more than its scenes: its props, its people and
        # the quests that belong to one of the party are sections of the same document.
        "doc": doc,
        "stories": amd_section(doc, "side_stories"),
    }
    _UNIVERSE_SITE_RECORDS[key] = rec
    if area is not None:
        _universe_site_ground(rec)
    elif _universe_site_ground_sections(doc):
        # Things to stand on a map, and no map. Said, because the other reading - a
        # text site whose props simply never appear - has nothing in any log.
        universe_site_say(
            f"the site '{key}' ('{fname}') has Props or People, and no .tiles file in "
            f"this universe's folder says `area: {key}`. It has rooms under "
            f"`## [Scenes](boarding)`, so it is played as a site of rooms and choices, "
            f"and its Props and People are not used. For a site the party walks, make "
            f"the area's key the site's key.", once=f"noarea:{key}")
    if rec["hails"] and not _universe_site_hail_sends(rec["hails"]):
        # The crew can take the call, and no answer to it ever sends anybody down.
        universe_site_say(
            f"the site '{key}' ('{fname}') has a call in `## Hails`, and none of its "
            f"answers sends a party: no answer ends with `; signal boarding_down`. The "
            f"crew can take the call and can never go down. Add it to the answer that "
            f"accepts - `- [Assemble a boarding party]() ; signal boarding_down` - or "
            f"take the `## Hails` chapter out, and the party is offered on arrival.",
            once=f"nodown:{key}")
    return rec


def _universe_site_hail_sends(hails):
    """Whether any answer in a site's `## Hails` carries `; signal boarding_down`."""
    from sbs_utils.procedural.amd import amd_choice
    for node in (hails or {}).values():
        text = node.get("description") if isinstance(node, dict) else getattr(node, "description", "")
        for raw in str(text or "").splitlines():
            line = raw.strip()
            if not (line.startswith("-") and "](" in line):
                continue
            try:
                outcomes = (amd_choice(line) or {}).get("outcomes") or []
            except Exception:
                outcomes = []
            for outcome in outcomes:
                if len(outcome) >= 2 and str(outcome[0]).lower() == "signal" \
                        and str(outcome[1]).strip().lower() == "boarding_down":
                    return True
    return False


# The sections of a site file that stand things on a tile map (the frozen keys
# `boarding_ground_load` reads).
_UNIVERSE_SITE_GROUND_KEYS = ("props", "prop", "objects", "people", "hostiles", "hostile")


def _universe_site_ground_sections(doc):
    return [k for k in _UNIVERSE_SITE_GROUND_KEYS if amd_section(doc, k) is not None]


def _universe_site_ground(rec):
    """Declare and place what a walked site's file stands on its map.

    `boarding_ground_load` is keyed: a prop or a person already declared is left exactly
    as it is, so this runs once per site per game however often its system is rebuilt,
    and an opened door stays open. (That is also why prop and people keys must be unique
    across a universe's site files: the second file's `door` would be the first file's.
    `sbs lint` says so - `site-key-collision`.)
    """
    from sbs_utils.procedural.boarding_ground import boarding_ground_load
    try:
        rec["ground"] = boarding_ground_load(rec["doc"])
    except Exception as e:
        rec["ground"] = None
        universe_site_say(f"the site '{rec['key']}': what stands on its map would not "
                          f"load: {e}", once=f"ground:{rec['key']}")
        return None
    # The loader hands every scene it has seen to the props, first key wins. A party
    # that is on the ground somewhere ELSE - another ship, another system - must keep
    # hearing its own site's scenes while this one's file is read.
    try:
        from sbs_utils.procedural.boarding import boarding_visiting
        from sbs_utils.procedural.boarding_props import boarding_props_scenes
        visit = boarding_visiting()
        if visit and visit.get("tile"):
            here = _UNIVERSE_SITE_RECORDS.get(str(visit.get("place") or ""))
            if here is not None and here.get("scenes"):
                boarding_props_scenes(here["scenes"])
    except Exception:
        pass
    return rec["ground"]


def universe_site_ground_begin(folder=None):
    """Load the universe's tile world, once, as the universe starts: every `*.tileset`
    and `*.tiles` in the mission's folder, and the art the `TILE_ART` setting names.

    At the START rather than on first arrival, so the hitch of reading the art is paid
    while the crew is still looking at a loading screen, not as they dock.

    A universe with no `.tiles` file makes no call into the tile world at all and logs
    nothing: this returns None. Otherwise it returns what `boarding_ground_load` reports.
    Nothing is put ON the ground here - that is each site's own file, read on arrival.
    """
    from sbs_utils.procedural.boarding_ground import boarding_ground_files, boarding_ground_load
    try:
        _tilesets, areas = boarding_ground_files(folder)
    except Exception:
        return None
    if not areas:
        return None
    try:
        return boarding_ground_load(None, folder)
    except Exception as e:
        universe_site_say(f"the universe's tile files would not load: {e}", once="tiles")
        return None


def universe_site_area(key):
    """The tile area a site's party walks - the site's own key - or None for a text site.

    It is a walked site when an area with the SAME KEY is loaded: a `.tiles` file in the
    universe's folder whose header says `area: <key>`. No field on the landmark and no
    word in the site file says it; the map being there is what says it.
    """
    key = str(key).strip() if key else ""
    if not key:
        return None
    from sbs_utils.procedural.tilemap import tilemap_area
    return key if tilemap_area(key) is not None else None


def universe_site_stories(key):
    """A site's `## Side Stories` section - quests that each belong to ONE of the party -
    ready for `boarding_visit(stories=...)`. None when the file has none."""
    rec = universe_site_record(key)
    return (rec or {}).get("stories")


def universe_site_visit_leave():
    """Somebody came back aboard. If that was the last of a walked site's party, the
    visit is over: END it, and say whether it was.

    A text visit ends itself when its scene closes. A walked one has no scene to close,
    so "everybody is home" is what ends it - and docking again offers the place again.

    Only for a visit one of THIS file's sites opened (the ship carries `SITE_VISITING`):
    a boarded ship's deck, or a mission's own landing party, is not this file's to end.
    """
    from sbs_utils.procedural.boarding import (boarding_visiting, boarding_visit_end,
                                               boarding_team)
    from sbs_utils.procedural.inventory import get_inventory_value
    from sbs_utils.procedural.tilemap import tilemap_where
    visit = boarding_visiting()
    if not visit or not visit.get("tile"):
        return False
    if get_inventory_value(visit.get("ship"), "SITE_VISITING", None) is None:
        return False
    if any(tilemap_where(lf) is not None for lf in boarding_team()):
        return False                    # somebody is still down there
    return bool(boarding_visit_end())


def _universe_site_end_visit_in(live):
    """End a visit whose site is one of these (a cell's sites, being released).

    A WALKED visit ends whoever is on the ground: the place is about to have no object in
    space, and they come home. A TEXT visit ends only when nobody is in it - a call that
    was taken and a party that never formed - because a conversation somebody is in the
    middle of ends itself, as it always has."""
    from sbs_utils.procedural.boarding import boarding_visiting, boarding_visit_end
    from sbs_utils.procedural.inventory import get_inventory_value
    visit = boarding_visiting()
    if not visit:
        return False
    at = get_inventory_value(visit.get("ship"), "SITE_VISITING", None)
    if at is None or at not in {entry.get("object") for entry in live.values()}:
        return False
    if not visit.get("tile") and universe_site_party_down():
        return False
    return bool(boarding_visit_end())


def universe_site_party_down():
    """Whether anybody is DOWN at the visit in progress: standing on its map (a walked
    site), or in its rooms (a text site). False with no visit open."""
    from sbs_utils.procedural.boarding import (boarding_visiting, boarding_team,
                                               boarding_clients)
    visit = boarding_visiting()
    if not visit:
        return False
    if visit.get("tile"):
        from sbs_utils.procedural.tilemap import tilemap_where
        return any(tilemap_where(lf) is not None for lf in boarding_team())
    return bool(boarding_clients())


def universe_site_call_waiting(site_obj):
    """Is this site's call still OUT: being placed, waiting to be answered, or open?

    What `universe_site_arrive` asks before it calls. It used to ask "was this site ever
    asked" - and a crew that answered "Stay aboard" was never called again, at that
    site, until its system was rebuilt. A call that was declined, or closed, or timed
    out is not out: docking again offers it again.
    """
    from sbs_utils.procedural.hail import hail_active, hail_pending
    from sbs_utils.procedural.inventory import get_inventory_value
    from sbs_utils.procedural.roles import role
    site_id = to_id(site_obj)
    if not site_id or not get_inventory_value(site_id, "SITE_ASKED", False):
        return False
    if get_inventory_value(site_id, "SITE_CALLING", False):
        return True                     # the few seconds before the call is placed
    hails = universe_site_hails(get_inventory_value(site_id, "SITE_KEY", None))
    for ship in list(role("__player__")):
        if get_inventory_value(ship, "SITE_PENDING", None) != site_id:
            continue
        open_now = hail_active(ship)
        calls = ([open_now] if open_now else []) + list(hail_pending(ship) or [])
        if any(str(getattr(c, "scene", None) or "") in hails for c in calls):
            return True
    # Nobody is holding this site's call any more. Re-armed.
    set_inventory_value(site_id, "SITE_ASKED", False)
    return False


def universe_site_visit_watch(ship):
    """Watch the visit this ship opened, and END it if nobody went down and the ship has
    let go of the place - undocked, or left orbit. Started as the visit opens.

    A site with no `## Hails` opens its party the moment the ship arrives. A crew that
    never goes down and flies off used to leave that visit open for good, and every other
    site then offered nothing ("somebody is already down there"). Leaving the SYSTEM ends
    it too (`universe_site_release_cell`).

    It ends nothing while anybody is down, and nothing until it has itself SEEN the ship
    docked: a ship that is not docked when the visit opens never was let go of.
    """
    from sbs_utils.tickdispatcher import TickDispatcher
    ship_id = to_id(ship)
    if not ship_id:
        return False
    old = _UNIVERSE_SITE_WATCH.pop(ship_id, None)
    if old is not None:
        try:
            old.stop()
        except Exception:
            pass
    state = {"docked": False}
    _UNIVERSE_SITE_WATCH[ship_id] = TickDispatcher.do_interval(
        lambda t, _ship=ship_id, _state=state: _universe_site_watch_tick(t, _ship, _state),
        2.0)
    return True


def _universe_site_watch_tick(t, ship_id, state):
    """One look. NEVER RAISES: a raising interval pauses the sim."""
    try:
        from sbs_utils.procedural.boarding import boarding_visiting, boarding_visit_end
        from sbs_utils.procedural.inventory import get_inventory_value
        from sbs_utils.procedural.query import to_object
        visit = boarding_visiting()
        ship = to_object(ship_id)
        if (not visit or visit.get("ship") != ship_id or ship is None
                or get_inventory_value(ship_id, "SITE_VISITING", None) is None):
            _universe_site_watch_stop(t, ship_id)       # over some other way
            return
        docked = str(ship.data_set.get("dock_state", 0) or "undocked") != "undocked"
        if docked:
            state["docked"] = True
            return
        if not state["docked"] or universe_site_party_down():
            return
        _universe_site_watch_stop(t, ship_id)
        boarding_visit_end()
    except Exception as e:
        _universe_site_watch_stop(t, ship_id)
        try:
            log(f"a site's visit watcher stopped: {e}", "universe", "warning")
        except Exception:
            pass


def _universe_site_watch_stop(t, ship_id):
    _UNIVERSE_SITE_WATCH.pop(ship_id, None)
    try:
        t.stop()
    except Exception:
        pass


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
    """The beats a site plays, ready for `boarding_scene_begin` - or, at a walked site,
    the scenes its props and people name."""
    rec = universe_site_record(key)
    return (rec or {}).get("scenes") or {}


def universe_site_hails(key):
    """The arrival call a site authors, ready for `hail_ask(scenes=...)`. May be empty."""
    rec = universe_site_record(key)
    return (rec or {}).get("hails") or {}


def universe_site_title(key):
    """What the shared view calls this place - the landmark's name, else the key.

    The landmark's name, because that is what the crew saw on the map and heard on the
    comms; a site key is an author's filename and reads like one on a main screen.
    """
    rec = universe_site_record(key)
    if rec is None:
        return str(key or "").upper()
    return str(rec.get("name") or rec.get("key") or key).upper()

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
    # A PARTY STILL ON THE GROUND HERE comes home: the place they are standing in is
    # about to have no object in space, and a walked visit ends no other way. What they
    # opened and took stays as it is (the ground is keyed, not rebuilt).
    try:
        _universe_site_end_visit_in(live)
    except Exception as e:
        universe_site_say(f"a site's visit would not end with its system: {e}")
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
    _UNIVERSE_SITE_SAID.clear()
    _UNIVERSE_SITE_REFUSED.clear()
    for task in list(_UNIVERSE_SITE_WATCH.values()):
        try:
            task.stop()
        except Exception:
            pass            # already dropped by the reset
    _UNIVERSE_SITE_WATCH.clear()
