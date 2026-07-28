"""Side quest pools for the Open Universe (Epic E/F tie-in).

Sides offer generic jobs (side_quests.amd) drawn from each side's quest_pool
(sides.amd), gated and reward-scaled by the captain's standing with that side
(universe_reputation.sides_standing). Completing a job earns standing with the
offering side along the poles it values, so doing a side's work makes it like you.

Generic by design now (one job per pool type, any side can offer it); authoring
stays open - a side can later carry bespoke quests and these remain the baseline.
See UNIVERSE_CHANGES.md.
"""
from sbs_utils.procedural.quest import (
    document_get_amd_file, quest_add, quest_get_state, QuestState,
    quest_kill_count_for_difficulty)
from sbs_utils.procedural.execution import get_shared_variable
from sbs_utils.mast.mast_node import MastDataObject
# NOTE: no relative sibling imports. Mission .py files are loaded by __init__.mast
# (`import universe_sides.py`, `import universe_reputation.py`) into one shared engine
# namespace - they are not a package, so `from .universe_sides import ...` fails to
# compile in-engine. sides_get / sides_standing / side_offer_tier / side_reward_mult are
# already available because __init__.mast imports those files before this one. Only
# absolute `sbs_utils...` imports are valid here.


def universe_parse_side_quests(content):
    """Parse a standalone side_quests.amd into a doc (each heading key is a pool job
    type). Legacy split-file path; the merged format uses universe_jobs_from_doc."""
    return document_get_amd_file(None, "SideQuests", content=content)


def universe_jobs_from_doc(doc):
    """The `jobs` section node of a merged universe doc, whose children are the job
    types (the shape side_work_offers / _side_job_node expect). None when the doc
    has no jobs section (a legacy split file) so the caller falls back to a
    standalone side_quests.amd. universe_section is defined in universe_sides.py -
    this cross-file bare call works because all of a mission's .py files now share
    one namespace (the engine shared-namespace fix)."""
    return universe_section(doc, "jobs")


def _side_job_node(doc, job_type):
    if doc is None:
        return None
    for n in doc.get("children", []):
        if n.get("key") == job_type:
            return n
    return None


def side_work_offers(agent_id, sides, side_key, doc):
    """Jobs a side extends to this captain: its quest_pool entries whose tier the
    captain's standing unlocks, with standing-scaled rewards. Returns a list of
    MastDataObject (type/key/side/title/objective/credits/tier).

    Empty if the station isn't a known side, the doc is missing, or the captain
    hasn't earned the right to do business (foe sides need positive standing
    first - "only the dangerous bargain with them").
    """
    side = sides_get(sides, side_key)
    if side is None or doc is None:
        return []
    standing = sides_standing(agent_id, side)
    if side.get("diplomacy") == "foe" and standing < side_foe_deal_standing():
        return []
    tier = side_offer_tier(standing)
    mult = side_reward_mult(standing)
    offers = []
    for job_type in (side.get("quest_pool") or []):
        node = _side_job_node(doc, job_type)
        if node is None:
            continue
        data = node.get("data") or {}
        if int(data.get("tier", 1)) > tier:
            continue
        base = (data.get("reward") or {}).get("credits", 0)
        offers.append(MastDataObject({
            "type": job_type,
            "key": "side_" + str(side_key) + "_" + str(job_type),
            "side": side_key,
            "title": node.get("display_text", job_type),
            "objective": data.get("objective", ""),
            "credits": int(base * mult),
            "tier": int(data.get("tier", 1)),
        }))
    return offers


def universe_grant_side_job(agent_id, sides, side_key, job_type, doc):
    """Add + activate a side job on the captain. Reward credits are scaled by
    current standing; a rep block is attached so completing it earns standing with
    the offering side (along the poles it values). Idempotent while active/secret;
    re-acceptable once completed or failed. Returns the quest id, or None."""
    side = sides_get(sides, side_key)
    node = _side_job_node(doc, job_type)
    if side is None or node is None:
        return None
    qid = "side_" + str(side_key) + "_" + str(job_type)
    st = quest_get_state(agent_id, qid)
    if st == QuestState.ACTIVE or st == QuestState.SECRET:
        return qid
    src = node.get("data") or {}
    standing = sides_standing(agent_id, side)
    mult = side_reward_mult(standing)
    tier = int(src.get("tier", 1))
    data = dict(src)
    data["reward"] = dict(src.get("reward") or {})
    base = data["reward"].get("credits", 0)
    data["reward"]["credits"] = int(base * mult)
    data["side"] = side_key
    # Scale a grind kill target (e.g. "destroy N enemies") to difficulty - the
    # authored count is the DIFFICULTY 5 baseline; single/boss kills (<3) are left
    # as authored. Any grind kill goal (role / roles / hostile) scales; copy the
    # on_kill dict first so the shared AMD doc isn't mutated.
    kill = data.get("on_kill")
    if isinstance(kill, dict) and kill.get("count") and (kill.get("role") or kill.get("roles") or kill.get("hostile")):
        kill = dict(kill)
        kill["count"] = quest_kill_count_for_difficulty(kill.get("count", 1), get_shared_variable("DIFFICULTY", 5))
        data["on_kill"] = kill
    # Completing side work earns standing with that side along its valued poles.
    data["rep"] = {side_key: {pole: 5 * tier for pole in (side.get("leans") or {})}}
    title = str(side.get("name")) + ": " + str(node.get("display_text"))
    desc = (node.get("description") or "").strip()
    quest_add(agent_id, qid, title, desc, state=QuestState.ACTIVE, data=data)
    return qid
