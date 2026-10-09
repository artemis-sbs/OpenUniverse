"""Dialogue scenes for the Open Universe (the movie-script flavor of AMD).

Now a thin binder over the shared sbs_utils.procedural.amd_dialogue driver (promoted from
here). The generic engine - scene parsing, `%` random lines, guarded choices, outcome
dispatch - lives in the library; OU injects the two domain seams:
  * metric resolver: guard left-sides `credits` and `carrying <item>`. `standing` and the
    reputation poles are the library's own guard words now (reputation_metric); OU hands
    them on, and keeps its habit of reading any other name as a pole.
  * outcome handler: `costs <n> credits` (spend). `earns <side> <pole> <±n>` is the
    library's (reputation_earns_outcome) and `signal` is built into the shared driver.
Speaker resolution (key -> face/color/name card) stays OU-specific in universe_captains.py
(dialogue_speaker); the shared driver treats the speaker record opaquely.

See UNIVERSE_CHANGES.md (Epic F). The `## Dialogue` section of universe.amd authors the scenes.
"""
# The away module, imported HERE and not where it is used. `load_mission_vocabulary`
# imports `*_amd.py` and `*_dialogue.py` only, so this is the file that decides what
# `sbs lint` knows - the same reason `costs` and `earns` are registered here. Importing
# `away` registers the `learn` outcome verb that Site: scenes use; without it the linter
# calls every `; learn cold` an unknown verb on a file that works perfectly.
from sbs_utils.procedural import boarding as _boarding_vocab  # noqa: F401

from sbs_utils.procedural.amd_dialogue import (  # noqa: F401  (re-exported into the OU namespace)
    dialogue_parse, dialogue_get, dialogue_guard_ok, dialogue_pick_line,
    dialogue_choices, dialogue_apply, dialogue_entry_for, _dlg_norm,
    dialogue_register_scenes,
    dialogue_set_metric_resolver, dialogue_register_outcome)
from sbs_utils.procedural.reputation import reputation_metric
from sbs_utils.procedural.inventory import get_inventory_value, set_inventory_value
from sbs_utils.procedural.sides import to_side_id
from sbs_utils.procedural.query import get_side


def universe_dialogue_scenes(doc):
    """key -> scene node for the universe's `## Dialogue` section (empty if none).

    Also REGISTERS them, so a scene can be found by key alone - which is what lets
    `hail_offer(scene=...)` and a declarative `Action: <who> hails <scene>` work with
    no dict to hand them. The dict is still returned, so every caller is unchanged.
    """
    return dialogue_register_scenes(universe_section(doc, "dialogue"))


def dialogue_side_entry(scenes, side_key):
    """The entry scene key for a side's hail (Speaker == side, When == comms), or None."""
    return dialogue_entry_for(scenes, side_key, "comms")


# --- OU seams: reputation-aware guards + credit/reputation outcomes ----------
def _ou_metric(name, agent_id, side):
    """Resolve a guard's left side: `credits` (side inventory) and `carrying <item>` are
    the universe's own; `standing` and the reputation poles are handed to the library,
    read against the speaker side/captain record."""
    name = str(name).strip().lower()
    if name == "credits":
        return get_inventory_value(to_side_id(get_side(agent_id)), "credits", 0)
    # `if carrying clue_manifest >= 1` - what is in the hold. The items addon stores a
    # collected item on the SHIP under its own key, so this is a direct read.
    #
    # It earns its own word because the fallthrough below is a REPUTATION read, and an
    # unknown name there answers 0 rather than failing: without this, a guard asking about
    # cargo would quietly be a guard asking about a reputation pole nobody has, and it
    # would simply never open. A wrong answer that looks like a considered one.
    if name.startswith("carrying ") or name.startswith("have "):
        return get_inventory_value(agent_id, name.split(" ", 1)[1].strip(), 0)
    # `standing`, a pole - and ANY other name, read as a pole. The library answers 0 for
    # a name that is not a pole; the universe has always read it as one (an axis a
    # scene's own `earns` invented), so that is asked for here.
    return reputation_metric(name, agent_id, side, any_pole=True)


dialogue_set_metric_resolver(_ou_metric)


def _ou_costs(agent_id, side, toks):
    """`costs <n> [credits]` - spend credits from the agent's side; refuse if unaffordable."""
    if not toks or not str(toks[0]).lstrip("-").isdigit():
        return
    n = int(toks[0])
    sid = to_side_id(get_side(agent_id))
    have = get_inventory_value(sid, "credits", 0)
    if have < n:
        return False
    set_inventory_value(sid, "credits", have - n)


# `earns <side> <pole...> <±n>` is the library's outcome verb (registered as
# sbs_utils.procedural.reputation imports), so it is no longer declared here.
dialogue_register_outcome("costs", _ou_costs)
