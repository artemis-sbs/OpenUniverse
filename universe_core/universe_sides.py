"""Player-side roster for the Open Universe.

Which sides are player-COMMANDED (Admiral economy + consoles), so the game is
multi-side instead of assuming "tsn". The roster is the set of sides marked at
spawn; consoles/loops iterate or derive from it rather than hardcoding a literal.

Relations between player sides come purely from diplomacy config - co-op vs rival
is just how the universe sets `side_set_relations`, so this layer never assumes
ally or enemy (the "configurable" model).
"""
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
    driven). A ceasefired clan (now NEUTRAL, though its ships keep the raider tag)
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
