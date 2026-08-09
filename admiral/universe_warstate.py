"""War-state watcher for the Open Universe (Foundation Phase 3, FOUNDATION_PLAN.md).

Emits the milestones a PvP / war game turns on - a player side ELIMINATED (it held
an HQ and now holds none = conquest), and the LAST SIDE STANDING - as events the MAST
loop turns into signals. Victory POLICY lives elsewhere: quests (Win:/Lose:) or the
Mode default that ends skirmish/war on last-standing. This layer only reports facts,
so it never assumes what "winning" means.

The decapitation quick-win (capture/destroy a side's fixed capital) is NOT here - it's
an authored quest against the <side>_capital role (tagged in universe_platform_spawn),
so it needs no code beyond the tag.

Shared-namespace: universe_player_sides (universe_sides.py); role/to_object_list.
"""
from sbs_utils.mast.mast_node import MastDataObject
from sbs_utils.procedural.roles import role
from sbs_utils.procedural.query import to_object_list

# Runtime state (reset on universe load). established: sides that have HELD an HQ
# (so an unbuilt HQ at start isn't an instant loss); eliminated: sides now HQ-less;
# done: the last-standing verdict has fired (the watcher then idles).
_WARSTATE = {"established": set(), "eliminated": set(), "done": False}


def warstate_reset():
    global _WARSTATE
    _WARSTATE = {"established": set(), "eliminated": set(), "done": False}


def _admiralty_side_has_hq(side):
    return len(to_object_list(role("admiral_hq") & role(side))) > 0


def warstate_tick():
    """One check. Returns MastDataObject events for the loop to signal:
      {type: eliminated, side}      - that side lost its last HQ (conquest)
      {type: last_standing, side}   - one (or zero = draw) player side remains
    Each fires once; after last_standing the watcher is done."""
    out = []
    st = _WARSTATE
    if st["done"]:
        return out
    sides = universe_player_sides()
    for s in sides:
        if s in st["eliminated"]:
            continue
        if _admiralty_side_has_hq(s):
            st["established"].add(s)
        elif s in st["established"]:
            st["eliminated"].add(s)
            out.append(MastDataObject({"type": "eliminated", "side": s}))
    # Last side standing: only meaningful with >=2 player sides, once someone's out.
    if len(sides) >= 2 and st["eliminated"]:
        alive = [s for s in sides if s not in st["eliminated"]]
        if len(alive) <= 1:
            st["done"] = True
            out.append(MastDataObject({"type": "last_standing",
                                       "side": alive[0] if alive else None}))
    return out


def warstate_done():
    """True once the last-standing verdict has fired (the loop can stop)."""
    return bool(_WARSTATE.get("done"))
