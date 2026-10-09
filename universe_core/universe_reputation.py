"""Per-captain reputation with sides (Open Universe, Epic F).

Now a thin binder over the shared sbs_utils.procedural.reputation service (the whole
multi-axis reputation engine, axes/tuning config, standing, tiers, reward, and the
diplomacy-economy pricing were promoted from here). OU keeps the `side_*` names its mast
routes + helpers already call; the generic engine lives in the library and pairs with
amd_dialogue (guards read reputation).

Distinct from diplomacy (side-wide "are we at war?"): reputation is how a side sees a
*captain*, stored on the captain's ship agent (inventory key "reputation").
"""
from sbs_utils.procedural.reputation import (   # noqa: F401  (re-exported into the OU namespace)
    reputation_configure, reputation_get, reputation_adjust, reputation_apply,
    reputation_standing, reputation_offer_tier, reputation_foe_deal_standing,
    reputation_reward_mult, reputation_ceasefire_cost, reputation_alliance_standing,
    reputation_ransom_cost)

# OU-facing names: its mast routes + helpers (universe_dialogue, universe_captains,
# universe_side_quests, ...) call these side_* aliases. A "side record" is the faction
# record the shared engine takes (a dict with key + optional leans).
#
# REAL FUNCTIONS, NOT ALIASES. `sides_standing = reputation_standing` made a second name
# for the LIBRARY's function, and only a function this file DEFINES becomes a MAST global
# (a re-export keeps the library's `__module__`). So Python callers found the name and
# the mast routes did not: the first time Comms selected a station belonging to an
# authored side, the diplomacy menu raised `NameError: name 'sides_standing' is not
# defined` and every task on the server page ended. Seen by the Class 5 lessons on a
# mission made by `sbs create -t ou`, and in Open Universe itself.
def sides_standing(*args, **kwargs):  # lint: allow ns-generic-name
    """A captain's standing with a side (`reputation_standing`)."""
    return reputation_standing(*args, **kwargs)


def side_offer_tier(*args, **kwargs):  # lint: allow ns-generic-name
    """The highest job tier a side offers at this standing (`reputation_offer_tier`)."""
    return reputation_offer_tier(*args, **kwargs)


def side_foe_deal_standing(*args, **kwargs):  # lint: allow ns-generic-name
    """The standing at which a foe will deal (`reputation_foe_deal_standing`)."""
    return reputation_foe_deal_standing(*args, **kwargs)


def side_reward_mult(*args, **kwargs):  # lint: allow ns-generic-name
    """How standing scales a reward (`reputation_reward_mult`)."""
    return reputation_reward_mult(*args, **kwargs)


def side_ceasefire_cost(*args, **kwargs):  # lint: allow ns-generic-name
    """The tribute a ceasefire costs at this standing (`reputation_ceasefire_cost`)."""
    return reputation_ceasefire_cost(*args, **kwargs)


def side_alliance_standing(*args, **kwargs):  # lint: allow ns-generic-name
    """The standing an alliance needs (`reputation_alliance_standing`)."""
    return reputation_alliance_standing(*args, **kwargs)


def side_ransom_cost(*args, **kwargs):  # lint: allow ns-generic-name
    """What buying back a prisoner costs at this standing (`reputation_ransom_cost`)."""
    return reputation_ransom_cost(*args, **kwargs)


def universe_officers_held_by(side_key):
    """The Admiralty officers `side_key` holds - or none, when the Admiral addon is not
    part of this mission.

    `officers_captured_by` belongs to the `admiral` addon. universe_core's own routes
    called it directly, so a universe with no Admiral (every mission made by
    `sbs create -t ou`) raised a NameError the moment a station was selected, captured or
    destroyed.

    Looked up among the MAST globals - the table a bare call in a route resolves
    against - and not in this file's own namespace, which two addons only share when
    both run from source folders (as packaged mastlibs each has its own)."""
    from sbs_utils.mast.mast_globals import MastGlobals
    held = MastGlobals.globals.get("officers_captured_by")
    if held is None:
        return []
    return held(side_key) or []
