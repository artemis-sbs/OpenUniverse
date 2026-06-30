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
from sbs_utils.faces import random_terran, random_terran_male, random_terran_female
from sbs_utils.procedural.lifeform import lifeform_spawn
from sbs_utils.procedural.inventory import set_inventory_value
from sbs_utils.mast.mast_node import MastDataObject

_FACE_GEN = {"terran": random_terran, "male": random_terran_male,
             "terran_male": random_terran_male, "female": random_terran_female,
             "terran_female": random_terran_female}


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
                "clan": data.get("clan"),
            }))
    return out


def lifeform_get(lifeforms, key):
    for c in lifeforms:
        if c.key == key:
            return c
    return None


def lifeform_face(record):
    """Resolve a record's face: a keyword (terran/male/female) -> a random face of
    that kind; a literal face string -> itself; nothing -> a random terran."""
    f = record.get("face") if record is not None else None
    if f is None:
        return random_terran()
    gen = _FACE_GEN.get(str(f).strip().lower())
    return gen() if gen is not None else f


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
