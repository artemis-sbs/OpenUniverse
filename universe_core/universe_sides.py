"""Sides in the Open Universe: which exist and what they are like, and which
of them a player COMMANDS.

The authored half was called "sides" - a private word for something universe_sides.py
itself described as "spawned as sides". It lives here now: what a side is called, its
color, its character, the systems it calls home, the ships it flies. The document
plumbing that used to sit beside it is in universe_doc.py.

Player-side roster

Which sides are player-COMMANDED (Admiral economy + consoles), so the game is
multi-side instead of assuming "tsn". The roster is the set of sides marked at
spawn; consoles/loops iterate or derive from it rather than hardcoding a literal.

Relations between player sides come purely from diplomacy config - co-op vs rival
is just how the universe sets `side_set_relations`, so this layer never assumes
ally or enemy (the "configurable" model).
"""
import os
import random
from sbs_utils import scatter
from sbs_utils.procedural.amd_doc import amd_section, amd_root_data
from sbs_utils.procedural.roles import all_roles
from sbs_utils.procedural.gui import gui_row, gui_text
from sbs_utils.procedural.comms import comms_info_card
from sbs_utils.mast.mast_node import MastDataObject
from sbs_utils.helpers import FrameContext
from sbs_utils.procedural.query import to_object
from sbs_utils.procedural.roles import role
from sbs_utils.procedural.sides import side_are_enemies, side_enemy_members_set

# Ordered player-side keys (Admiral economy + consoles), in spawn order.
_PLAYER_SIDES = []


def universe_clear_player_sides():
    """Forget the roster (call when (re)building the universe's sides)."""
    _PLAYER_SIDES.clear()


def universe_register_player_side(side):
    """Mark a side key as player-commanded (idempotent). Returns the key."""
    if side not in _PLAYER_SIDES:
        _PLAYER_SIDES.append(side)
    return side


def universe_player_sides():
    """The player-commanded side keys (Admiral economy + consoles)."""
    return list(_PLAYER_SIDES)


def universe_is_player_side(side):
    return side in _PLAYER_SIDES


def universe_primary_side():
    """The first player side - a sane default where exactly one side is needed
    (e.g. an unowned landmark's home). None before any side is registered."""
    return _PLAYER_SIDES[0] if _PLAYER_SIDES else None


def universe_console_side(client_id):
    """The player side a console commands: the client's ship side, falling back
    to the primary player side. Use instead of a literal in the Admiral GUIs."""
    ctx = FrameContext.context
    if ctx is not None and ctx.sbs is not None:
        ship = ctx.sbs.get_ship_of_client(client_id)
        if ship:
            obj = to_object(ship)
            if obj is not None and getattr(obj, "side", None):
                return obj.side
    return universe_primary_side()


def universe_hostile_to_players(side):
    """True if `side` is hostile to ANY player side (universe threat logic - 'is
    this a foe of the player faction(s)'). Diplomacy-driven, so it respects
    whatever relations the universe configured (co-op or rival)."""
    return any(side_are_enemies(side, ps) for ps in _PLAYER_SIDES)


def universe_player_enemy_members():
    """Agent ids of every ship on a side HOSTILE to any player side (diplomacy
    driven). A ceasefired side (now NEUTRAL, though its ships keep the raider tag)
    drops out. Empty before player sides are registered."""
    out = set()
    for ps in _PLAYER_SIDES:
        out |= side_enemy_members_set(ps)
    return out


def universe_player_hostiles_scoped():
    """Raider-tagged combat ships that are still HOSTILE to a player side (the fleet
    -group marker excluded). The ceasefire-aware replacement for a bare
    role("raider") in presence / cleared / count checks: role scopes to combat
    ships, the enemy set is the allegiance test."""
    return (role("raider") - role("raider_fleet")) & universe_player_enemy_members()


def universe_mode_is_pvp():
    """True when the active mission Mode makes the PLAYER sides mutually hostile -
    skirmish and war (the PvP archetypes). sandbox/campaign/story keep whatever
    co-op/ally relations the universe authored. mission_mode is a sibling free
    global (universe_worldlets.py); the caller applies the relation in MAST where
    sbs.DIPLOMACY lives. See FOUNDATION_PLAN.md (Phase 3)."""
    return mission_mode() in ("skirmish", "war")



# Fallback race pool when a side declares no makeup.
_DEFAULT_RACES = ["Kralien", "Torgoth", "Arvonian", "Ximni"]




# --- Nav "known locations" list ----------------------------------------------
def universe_known_locations(sides, quest_targets):
    """Notable systems for the nav list: home base, side homes, and active quest
    targets - each a MastDataObject with name + i/j."""
    locs = [MastDataObject({"name": "Home Base", "i": 0, "j": 0})]
    for c in sides:
        for h in (c.get("homes") or []):
            if len(h) == 2:
                locs.append(MastDataObject({"name": c.name, "i": int(h[0]), "j": int(h[1])}))
    for t in quest_targets:
        locs.append(MastDataObject({"name": "Quest Target", "i": int(t[0]), "j": int(t[1])}))
    return locs




def universe_location_template(item):
    gui_row("row-height: 1.2em;")
    gui_text(f"$text:{item.name}  ({item.i}, {item.j});justify:left;font:gui-1")




def universe_location_title():
    gui_row("row-height: 1.2em;padding:6px;background:#1578;")
    gui_text("$text:Known Locations;justify:left;")




def universe_sides_from_doc(doc):
    """Side records from a parsed universe doc: the `sides` section's children if
    present, else the doc's top-level children (a legacy flat sides.amd).

    A modern universe file is one root heading (identity fence + section
    children); if it simply has no ## Sides section that means NO sides - don't
    mistake the root itself for a legacy flat-file side entry."""
    section = universe_section(doc, "sides")
    if section is not None:
        return _sides_from_nodes(section.get("children", []))
    kids = doc.get("children", []) if doc else []
    if len(kids) == 1 and (kids[0].get("children") or (kids[0].get("data") or {}).get("display")):
        return []
    return _sides_from_nodes(kids)




def universe_parse_sides(content):
    """Parse universe.amd / sides.amd content into a list of side records
    (MastDataObject). Section-aware with a legacy flat-file fallback.

    Each record: key, name, desc, color, archetype, diplomacy (foe/neutral),
    homes [[i,j],...], leans {axis:val}, quest_pool [..]. A foe side's hostile
    relations are set at spawn against the live player-side roster (universe.mast),
    not baked here - so "foe" means foe of whatever sides are playing.
    """
    return universe_sides_from_doc(universe_doc(content))




def _sides_from_nodes(nodes):
    sides = []
    for n in nodes:
        data = n.get("data") or {}
        diplomacy = data.get("diplomacy", "neutral")
        sides.append(MastDataObject({
            "key": n.get("key"),
            "name": n.get("display_text"),
            "desc": (n.get("description") or "").strip(),
            "color": data.get("color", "#888888"),
            "archetype": data.get("archetype", "neutral"),
            "diplomacy": diplomacy,
            "homes": data.get("homes") or [],
            "leans": data.get("leans") or {},
            "quest_pool": data.get("quest_pool") or [],
            "chatter": data.get("chatter") or [],
            # makeup: race composition of this side's ships - a single race, an
            # even list, or a {race: weight} dict (see sides_pick_race).
            "makeup": data.get("makeup"),
            # Optional comms-card identity (info panel): a face string + an icon.
            "face": data.get("face"),
            "icon": data.get("icon"),
            # How this side's drives LOOK winding up for a jump - an ## Effects
            # record, or a built-in charge look. None falls back through the
            # archetype to `coil` (universe_charge_look), so a side that says
            # nothing still charges up in its own Color:.
            "jump_charge": data.get("jump_charge"),
        }))
    return sides


# Ambient comms chatter by archetype (sides.amd may override with a `chatter:`
# list). {name} is substituted with the side name. Flavor only - never reveals
# the map (round-5 decision).
_ARCHETYPE_CHATTER = {
    "military":  ["This is {name} space - mind your conduct, captain.",
                  "{name} patrols have you on scope."],
    "trader":    ["{name} welcomes honest custom - credits talk.",
                  "Safe lanes, captain. {name} has cargo if you have coin."],
    "settler":   ["{name} holds the drift out here. Keep it civil.",
                  "Not much law this far out - {name} looks after its own."],
    "mercenary": ["{name} works for the highest bidder. Got a contract?",
                  "Coin first, questions later - the {name} way."],
    "pirate":    ["{name} smells weakness, captain...",
                  "Best run along - this is {name} territory."],
    "cult":      ["The {name} sees more than you know.",
                  "{name} whispers in the dark between stars."],
}




def universe_chatter_line(side):
    """A random ambient line for a side (its authored chatter, else archetype
    defaults), with {name} substituted. '' if none."""
    if side is None:
        return ""
    lines = side.get("chatter") or _ARCHETYPE_CHATTER.get(side.get("archetype"), [])
    if not lines:
        return ""
    return random.choice(lines).replace("{name}", side.get("name", "the locals"))




# --- Chatter / narrative comms delivery (info panel, NOT the text waterfall) ---
# Chatter reads as a hail from a side, not a log blip: an info-panel card carrying
# the side's name + color (+ optional face/icon), kept in history, auto-dismissed.
# These are thin wrappers over the reusable sbs_utils helper comms_info_card
# (promoted from the HereThereBeMonsters here_*_info_message pattern).
def _chatter_consoles():
    """The comms consoles that should receive universe chatter/comms cards."""
    return all_roles("console, comms")




def universe_chatter_card(side, line, time=10):
    """Deliver a side's ambient line as an info-panel card (face/name/color)."""
    if not line:
        return
    color = side.get("color", "#0cf") if side is not None else "#0cf"
    name = side.get("name") if side is not None else None
    comms_info_card(
        _chatter_consoles(), line, title=name, color=color,
        face=(side.get("face") if side is not None else None),
        icon_index=(side.get("icon") if side is not None else None), time=time,
        notify=True)




def sides_pick_race(side):
    """Pick a race for one of a side's ships from its authored makeup.

    makeup may be a single race string, an even list ([Torgoth, Kralien]), or a
    weighted dict ({Torgoth: 70, Kralien: 30}). No makeup (or no side) -> a random
    pick from the default pool, preserving the old mixed behavior.
    """
    makeup = side.get("makeup") if side is not None else None
    if not makeup:
        return random.choice(_DEFAULT_RACES)
    if isinstance(makeup, dict):
        races = list(makeup.keys())
        weights = list(makeup.values())
        return random.choices(races, weights=weights)[0]
    if isinstance(makeup, list):
        return random.choice(makeup) if makeup else random.choice(_DEFAULT_RACES)
    return str(makeup)




def sides_get(sides, key):
    """The side record with this key, or None."""
    for c in sides:
        if c.key == key:
            return c
    return None




def sides_home_owner(sides, i, j):
    """The side key whose home is system (i,j), or None (named homes win)."""
    for c in sides:
        for h in c.get("homes", []):
            if len(h) == 2 and int(h[0]) == int(i) and int(h[1]) == int(j):
                return c.key
    return None




def sides_name(sides, key):
    """Display name for a side key (or the key if unknown)."""
    c = sides_get(sides, key)
    return c.name if c is not None else key




def sides_color(sides, key):
    """Map/side color for a side key (or a default)."""
    c = sides_get(sides, key)
    return c.color if c is not None else "#888888"




def sides_character(sides, key):
    """Archetype for a side key (military/trader/...), or None. Used to flavor the
    system POI deck (universe_systems.py)."""
    c = sides_get(sides, key)
    return c.archetype if c is not None else None




def universe_system_side(sides, seed, i, j, base_kind):
    """Owning side key + effective kind for a system, given its base kind.

    A side home -> that side + 'station' (a side presence); a keyed 'enemy'
    system -> a foe side (still 'enemy'); otherwise no side. Both the map and the
    generator call this so naming/ownership match what spawns. base_kind comes
    from universe_system_kind (side-agnostic) - passed in to avoid a cross-import.
    """
    home = sides_home_owner(sides, i, j)
    if home is not None:
        return home, "station"
    if base_kind == "enemy":
        return sides_for_system(sides, seed, i, j), "enemy"
    return None, base_kind




def sides_for_system(sides, seed, i, j):
    """Owning side key for a side/foe system: home wins, else a keyed pick among
    foe sides (deterministic). Returns None if there are no foe sides.

    The caller decides whether a given system IS a side system (by kind); this
    just names the owner reproducibly so the map and spawn agree.
    """
    owner = sides_home_owner(sides, i, j)
    if owner is not None:
        return owner
    foes = [c.key for c in sides if c.diplomacy == "foe"]
    if not foes:
        return None
    roll = scatter.cell_roll(seed, 13, int(i), int(j), 7)
    return foes[int(roll * len(foes)) % len(foes)]


# --- how a side's drives LOOK winding up for a jump --------------------------
#
# The engine's hyper-warp screen is per-client: only the jumping ship's own crew
# sees the tunnel. A charge-up on the HULL is the other half - it happens in shared
# space, so everyone in the system watches a ship spool up before it goes. That is
# the point of doing it this way rather than as another client-side screen.

# Which built-in look a side's Character: implies, when it names none of its own.
# Every side has a Character:, so this alone gives an unauthored universe a
# different wind-up per faction.
_CHARACTER_CHARGE = {
    "military": "coil",
    "trader": "preburn",
    "pirate": "arc",
    "scientist": "implode",
    "mercenary": "arc",
    "settler": "preburn",
}

DEFAULT_CHARGE_LOOK = "coil"


def universe_charge_look(sides, ship_id):
    """Which charge look this ship's drives use. NEVER returns empty.

    In order:
      1. the ship's own ``charge`` inventory value - a prefab or a quest pinned one;
      2. its side's ``Jump Charge:``;
      3. a default for its side's ``Character:``;
      4. ``coil``.

    A silent nothing is indistinguishable from a bug, so an NPC with no side record
    at all still winds up - it just does it in the default look.
    """
    from sbs_utils.procedural.inventory import get_inventory_value
    obj = to_object(ship_id)
    if obj is None:
        return DEFAULT_CHARGE_LOOK

    own = get_inventory_value(ship_id, "charge", None)
    if own:
        return str(own)

    side = getattr(obj, "side", None)
    rec = sides_get(sides, side) if side else None
    if rec is not None:
        declared = rec.get("jump_charge", None)
        if declared:
            return str(declared)
        arch = rec.get("archetype", None)
        if arch and arch in _CHARACTER_CHARGE:
            return _CHARACTER_CHARGE[arch]
    return DEFAULT_CHARGE_LOOK


def universe_charge_color(sides, ship_id):
    """The tint for a ship's charge-up: its side's own color, or None.

    This is the free half - every side already has a color, so factions look
    different from each other on day one with nothing authored.

    Two registries, because a side can come from either. The universe's `## Sides`
    section holds the NPC FACTIONS; the PLAYER sides are created at server start
    (create_sides) and live in the engine-side registry instead. Asking only the
    first handed every player ship - the most-watched wind-up in the game - the
    "#888888" not-found gray.

    Returns None rather than a gray when neither knows, so the charge driver falls
    back to its own blue-white. A dead color is worse than no color.
    """
    obj = to_object(ship_id)
    side = getattr(obj, "side", None) if obj is not None else None
    if not side:
        return None
    rec = sides_get(sides, side)
    if rec is not None and rec.get("color", None):
        return rec.color
    from sbs_utils.procedural.sides import side_get_side_color
    return side_get_side_color(side, None)
