"""Lifeforms (the cast) for the Open Universe - built on the library lifeform.

A lifeform is the engine's hosted-character substrate (sbs_utils.procedural.
lifeform): a named Agent with a face, roles, a host space object it is aboard, and
a comms `path` (its voice). A `## Lifeforms` section authors the cast - comms NPCs
(frontier command, news), and in time captains/passengers/saboteurs - each as a
fact-sheet. The driver spawns them via lifeform_spawn and points their `path` at
one universe bridge route (//comms/universe_cast) so a lifeform's `Scene` plays
through the dialogue driver we already have - the dialogue layer IS a lifeform's
voice.

This slice: hosted comms characters. A lifeform with no host is a galaxy-wide comms
NPC (hailable with no target, like TSNN); a host is resolved to a station/ship by
the mast. universe_section / dialogue_* come from sibling files (shared namespace).
"""
from sbs_utils.faces import random_terran, face_resolve
from sbs_utils.procedural.lifeform import lifeform_spawn, lifeform_transfer
from sbs_utils.procedural.inventory import set_inventory_value, get_inventory_value
from sbs_utils.procedural.roles import role
from sbs_utils.procedural.query import to_object, to_object_list
from sbs_utils.procedural.quest import quest_add, QuestState
from sbs_utils.mast.mast_node import MastDataObject

def universe_parse_lifeforms(doc):
    """Cast records from the `## Lifeforms` section (empty if none)."""
    section = universe_section(doc, "lifeforms")
    out = []
    if section is not None:
        for n in section.get("children", []):
            data = n.get("data") or {}
            out.append(MastDataObject({
                "key": n.get("key"),
                "name": n.get("display_text"),
                "desc": (n.get("description") or "").strip(),
                "face": data.get("face"),
                "host": data.get("host"),
                "roles": data.get("roles") or "",
                "scene": data.get("scene"),
                "color": data.get("color") or "green",
                # `Side:` is the authored word now; `Clan:` still parses.
                "clan": data.get("side") or data.get("clan"),
                # Passenger fields (a lifeform you transport): pickup + destination
                # systems and the fare. A lifeform with a deliver_to is a passenger.
                "pickup": data.get("pickup"),
                "deliver_to": data.get("deliver_to"),
                "pays": (data.get("reward") or {}).get("credits"),
                # Saboteur: ship systems this lifeform sabotages once aboard (slice 3).
                "sabotage": data.get("sabotage"),
            }))
    return out


def lifeform_get(lifeforms, key):
    for c in lifeforms:
        if c.key == key:
            return c
    return None


def lifeform_face(record):
    """Resolve a record's face spec via the shared face_resolve (keyword -> random face of
    that kind; literal -> itself; nothing -> a random terran)."""
    return face_resolve(record.get("face") if record is not None else None)


def universe_spawn_lifeform(record, host_id):
    """Spawn an authored lifeform on host_id (None = a galaxy comms NPC). Its `path`
    bridges to the dialogue driver; its scene/key are stored for that route."""
    agent = lifeform_spawn(record.get("name"), lifeform_face(record),
                           record.get("roles") or "", host_id,
                           path="//comms/universe_cast", title_color=record.get("color") or "green")
    set_inventory_value(agent, "scene", record.get("scene"))
    set_inventory_value(agent, "lf_key", record.get("key"))
    return agent


def lifeform_speaker(lifeforms, key):
    """A dialogue voice record (key/name/color/leans) for a cast lifeform, so a
    scene's `Speaker: <lifeform key>` resolves to that character's card. None if the
    key is not a lifeform. Cast NPCs carry no reputation, so leans is empty."""
    lf = lifeform_get(lifeforms, key)
    if lf is None:
        return None
    return MastDataObject({"key": lf.key, "name": lf.name, "color": lf.get("color") or "#0cf", "leans": {}})


# --- Passenger delivery (slice 2) --------------------------------------------
# A passenger is a lifeform you transport: pick up at a station, it boards your
# ship (lifeform_transfer to host=ship), and disembarks on reaching its destination
# system (the on_reach quest pays the fare). B = authored named passengers (a cast
# lifeform with Pickup + Deliver to + Pays + a voice); A = a generic traveler the
# clan station offers to the deterministic cargo destination. Reuses the cargo-run
# quest pattern (universe_helpers.universe_delivery_target).
def universe_passenger_quest_id(key):
    return "passenger_" + str(key)


def universe_passengers_at(lifeforms, i, j):
    """Authored passengers awaiting pickup at system (i, j) (have a pickup here and
    a destination)."""
    out = []
    for lf in lifeforms:
        p = lf.get("pickup")
        if lf.get("deliver_to") and p and len(p) == 2 and int(p[0]) == int(i) and int(p[1]) == int(j):
            out.append(lf)
    return out


def universe_generic_passenger(i, j, ti, tj):
    """A generic traveler (case A) bound for the deterministic cargo destination."""
    return MastDataObject({
        "key": "traveler_" + str(int(i)) + "_" + str(int(j)),
        "name": "a stranded traveler", "deliver_to": [int(ti), int(tj)],
        "pays": 400, "roles": "", "color": "#9cf", "scene": None, "face": None})


def universe_grant_passenger(ship_id, passenger):
    """Accept a transport: grant the on_reach delivery quest (the fare) + board the
    passenger lifeform on the ship. Returns the quest id (None if no destination)."""
    dest = passenger.get("deliver_to")
    if not dest or len(dest) != 2:
        return None
    qid = universe_passenger_quest_id(passenger.get("key"))
    pays = passenger.get("pays") or 300
    dn = "(" + str(int(dest[0])) + ", " + str(int(dest[1])) + ")"
    quest_add(ship_id, qid, "Transport " + str(passenger.get("name")) + " to " + dn,
              "Carry " + str(passenger.get("name")) + " to system " + dn + ". Jump there to complete the run.",
              state=QuestState.ACTIVE,
              data={"on_reach": {"sector": [int(dest[0]), int(dest[1])]}, "reward": {"credits": int(pays)}})
    roles = passenger.get("roles") or ""
    roles = (roles + ", passenger") if roles else "passenger"
    # A passenger with a Sabotage list is a hidden saboteur (slice 3): tag the role
    # so the sabotage task runs while one is aboard and a Detain can end it.
    if passenger.get("sabotage"):
        roles = roles + ", saboteur"
    agent = lifeform_spawn(passenger.get("name"), lifeform_face(passenger), roles, ship_id,
                           path="//comms/universe_cast", title_color=passenger.get("color") or "green")
    set_inventory_value(agent, "scene", passenger.get("scene"))
    set_inventory_value(agent, "deliver_quest", qid)
    set_inventory_value(agent, "deliver_to", [int(dest[0]), int(dest[1])])
    return qid


def universe_passengers_destined(i, j):
    """Aboard passenger lifeform ids whose destination is system (i, j)."""
    out = []
    for lf_id in role("passenger"):
        d = get_inventory_value(lf_id, "deliver_to", None)
        if d and len(d) == 2 and int(d[0]) == int(i) and int(d[1]) == int(j):
            out.append(lf_id)
    return out


def universe_deliver_passenger(lf_id):
    """Disembark a passenger (off the ship); returns their name for the message."""
    obj = to_object(lf_id)
    name = obj.name if obj is not None else ""
    lifeform_transfer(lf_id, None)
    return name
