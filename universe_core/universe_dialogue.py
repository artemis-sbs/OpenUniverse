"""Dialogue scenes for the Open Universe (the movie-script flavor of AMD).

Now a thin binder over the shared sbs_utils.procedural.amd_dialogue driver (promoted from
here). The generic engine - scene parsing, `%` random lines, guarded choices, outcome
dispatch - lives in the library; OU injects the two domain seams:
  * metric resolver: guard left-sides `credits` / `standing` / a reputation pole.
  * outcome handlers: `costs <n> credits` (spend), `earns <clan> <pole> <±n>` (reputation);
    `signal` is built into the shared driver.
Speaker resolution (key -> face/color/name card) stays OU-specific in universe_captains.py
(dialogue_speaker); the shared driver treats the speaker record opaquely.

See UNIVERSE_CHANGES.md (Epic F). The `## Dialogue` section of universe.amd authors the scenes.
"""
from sbs_utils.procedural.amd_dialogue import (  # noqa: F401  (re-exported into the OU namespace)
    dialogue_parse, dialogue_get, dialogue_guard_ok, dialogue_pick_line,
    dialogue_choices, dialogue_apply, dialogue_entry_for, _dlg_norm,
    dialogue_scenes as _dlg_scenes,
    dialogue_set_metric_resolver, dialogue_register_outcome)
from sbs_utils.procedural.reputation import reputation_get, reputation_adjust, reputation_standing
from sbs_utils.procedural.inventory import get_inventory_value, set_inventory_value
from sbs_utils.procedural.sides import to_side_id
from sbs_utils.procedural.query import get_side


def dialogue_scenes(doc):
    """key -> scene node for the universe's `## Dialogue` section (empty if none)."""
    return _dlg_scenes(universe_section(doc, "dialogue"))


def dialogue_clan_entry(scenes, clan_key):
    """The entry scene key for a clan's hail (Speaker == clan, When == comms), or None."""
    return dialogue_entry_for(scenes, clan_key, "comms")


# --- OU seams: reputation-aware guards + credit/reputation outcomes ----------
def _ou_metric(name, agent_id, clan):
    """Resolve a guard's left side: `credits` (side inventory), `standing`, or a reputation
    pole read against the speaker clan/captain record."""
    name = str(name).strip().lower()
    if name == "credits":
        return get_inventory_value(to_side_id(get_side(agent_id)), "credits", 0)
    if name in ("standing", "rep", "reputation"):
        return reputation_standing(agent_id, clan)
    return reputation_get(agent_id, (clan.get("key") if clan else None), _dlg_norm(name))


dialogue_set_metric_resolver(_ou_metric)


def _ou_costs(agent_id, clan, toks):
    """`costs <n> [credits]` - spend credits from the agent's side; refuse if unaffordable."""
    if not toks or not str(toks[0]).lstrip("-").isdigit():
        return
    n = int(toks[0])
    sid = to_side_id(get_side(agent_id))
    have = get_inventory_value(sid, "credits", 0)
    if have < n:
        return False
    set_inventory_value(sid, "credits", have - n)


def _ou_earns(agent_id, clan, toks):
    """`earns <clan> <pole...> <±n>` - shift reputation with a clan along a pole."""
    if len(toks) >= 3 and str(toks[-1]).lstrip("+-").isdigit():
        reputation_adjust(agent_id, toks[0], _dlg_norm(" ".join(toks[1:-1])), int(toks[-1]))


dialogue_register_outcome("costs", _ou_costs)
dialogue_register_outcome("earns", _ou_earns)
