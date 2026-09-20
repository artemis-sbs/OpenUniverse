"""THE ADMIRALTY - one per side, the thing an Admiral actually commands.

The hangar needed a Flight Wing for the same reason (`LegendaryMissions/hangar/hangar.py`):
a pilot on the flight deck is assigned to the CARRIER, so everything about them read as the
carrier's. An Admiral is worse off - they fly an invisible camera - so the side's war had
nowhere to live but two story-wide `shared` variables:

    shared ADM_BUILDS = []
    default shared ADM_LAST_MSG = ""

ONE QUEUE AND ONE STATUS LINE FOR THE WHOLE GAME. Two admirals on opposing sides shared
them: a rival's build appeared in your queue, your confirmation appeared on their console,
and cancelling from either screen reached into the other's war. Per-side pools already
existed (`admiralty_pools`); the queue and the message never moved.

So the Admiralty is an Agent per side, remembered on the side agent, holding what belongs
to the side's command rather than to any ship, camera or console:

    * its BUILD QUEUE - the same list object every task appends to and removes from;
    * its STATUS LINE - what the panel's bar reads;
    * and the quests an Admiral is given, because `admiralty_use_command` names it as the
      console's quest holder (`quest_holder_set`) instead of the cambot.

Prefixed `admiralty_` like the rest of this addon: every public function here is a MAST
global in one flat, mission-wide namespace.
"""
from sbs_utils.agent import Agent, get_story_id
from sbs_utils.procedural.inventory import get_inventory_value, set_inventory_value
from sbs_utils.procedural.sides import to_side_id

#: On the SIDE agent, so the Admiralty goes with the mission rather than outliving it on a
#: module - the same place the Flight Wing keeps its id.
ADMIRALTY_KEY = "admiralty_id"

#: What the quest screens call it, where a ship's own quests say "Ship".
ADMIRALTY_LABEL = "Admiralty"

_ROLE = "__admiralty__"
_BUILDS = "admiralty_builds"
_MSG = "admiralty_msg"


def admiralty_of(side):
    """The Admiralty agent for `side` (a side key, side id, or an object on that side),
    created on first use. None without a side.

    Deliberately NOT a space object: it has no position and nothing should be able to
    shoot the war effort. An Agent with a story id is what the Flight Wing uses.
    """
    side_id = to_side_id(side)
    if side_id is None:
        return None
    adm_id = get_inventory_value(side_id, ADMIRALTY_KEY, None)
    if adm_id is not None and Agent.get(adm_id) is not None:
        return adm_id
    adm = Agent()
    adm.id = get_story_id()
    adm.add()
    adm.add_role(_ROLE)
    adm.set_inventory_value("side_key", get_inventory_value(side_id, "side_key", None))
    adm.set_inventory_value(_BUILDS, [])
    adm.set_inventory_value(_MSG, "")
    set_inventory_value(side_id, ADMIRALTY_KEY, adm.id)
    return adm.id


def admiralty_builds(side):
    """This side's build queue.

    THE SAME LIST OBJECT every time, because the build and research tasks hold it across
    an await and then `.remove()` their own record from it - hand back a copy and a
    cancelled build is removed from nothing and runs forever.
    """
    adm_id = admiralty_of(side)
    if adm_id is None:
        return []
    builds = get_inventory_value(adm_id, _BUILDS, None)
    if builds is None:
        builds = []
        set_inventory_value(adm_id, _BUILDS, builds)
    return builds


def admiralty_say(side, msg):
    """Put a line on this side's status - and RETURN it.

    Returning the message is what keeps the call sites one line: several of them file the
    same text as an info card in the next breath, and reading it back out of the store to
    do that is how a status line and its card drift apart.
    """
    adm_id = admiralty_of(side)
    text = "" if msg is None else str(msg)
    if adm_id is not None:
        set_inventory_value(adm_id, _MSG, text)
    return text


def admiralty_msg(side):
    """This side's current status line."""
    adm_id = admiralty_of(side)
    return (get_inventory_value(adm_id, _MSG, "") or "") if adm_id is not None else ""


def admiralty_use_command(client_id, side):
    """Make this console's quest screens list the side's ADMIRALTY as its holder.

    Without it an Admiral's "You" quests belong to the invisible camera they are assigned
    to, which is nobody - the same bug the flight deck had when a pilot's quests belonged
    to the carrier. Returns the Admiralty id, or None (and clears any override).
    """
    from sbs_utils.procedural.quest_driver import quest_holder_set, quest_holder_clear
    adm_id = admiralty_of(side)
    if adm_id is None:
        quest_holder_clear(client_id)
        return None
    quest_holder_set(client_id, adm_id, ADMIRALTY_LABEL)
    return adm_id


def admiralty_release_command(client_id):
    """Give the console its own ship back as its quest holder (leaving the Admiral)."""
    from sbs_utils.procedural.quest_driver import quest_holder_clear
    quest_holder_clear(client_id)


def admiralty_is(agent_id):
    """True if this agent is a side's Admiralty - for a quest screen deciding what to call
    a holder it has been handed."""
    agent = Agent.get(agent_id)
    return agent is not None and agent.has_role(_ROLE)
