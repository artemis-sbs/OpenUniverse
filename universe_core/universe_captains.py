"""NPC captains for the Open Universe - named people, not just sides.

A `## Captains` section authors individuals. A captain belongs to a side, flies a
ship, has a personality (`Values` = the reputation poles he embodies) and a home/
roam system. He is a dialogue Speaker (scenes use `Speaker: <his key>`), and the
player holds a *personal* reputation with him: the very same per-(agent, subject)
reputation store, keyed by the captain's key instead of a side's - so sides_standing
and the dialogue guards/outcomes work on a captain record unchanged.

A captain turns **rival** when his authored `Rival when: <guard>` holds against
that personal standing - emergent from conduct, self-undoing, no script. This is a
driver (parse + lookup + guard eval + identity resolution); authoring stays a
fact-sheet. sides_get / sides_standing / reputation_get come from universe_sides.py /
universe_reputation.py; dialogue_guard_ok from universe_dialogue.py (one shared
mission namespace).
"""
from sbs_utils.mast.mast_node import MastDataObject


def universe_parse_captains(doc):
    """Captain records from the `## Captains` section (empty list if none)."""
    section = universe_section(doc, "captains")
    out = []
    if section is not None:
        for n in section.get("children", []):
            data = n.get("data") or {}
            out.append(MastDataObject({
                "key": n.get("key"),
                "name": n.get("display_text"),
                "desc": (n.get("description") or "").strip(),
                # `Side:` is the authored word now; `Side:` still parses.
                "side": data.get("side") or data.get("side"),
                "title": data.get("title"),
                "leans": data.get("leans") or {},
                "makeup": data.get("makeup"),
                "homes": data.get("homes") or [],
                "face": data.get("face"),
                "rival_when": data.get("rival_when"),
            }))
    return out


def captain_get(captains, key):
    for c in captains:
        if c.key == key:
            return c
    return None


def captains_in_system(captains, i, j):
    """Captains who roam system (i, j) - they can be hailed at its station."""
    out = []
    for c in captains:
        for h in (c.get("homes") or []):
            if len(h) == 2 and int(h[0]) == int(i) and int(h[1]) == int(j):
                out.append(c)
    return out


def captain_full_name(captain):
    """'Vex Karr, the Ash-Captain' (name + optional title)."""
    if captain is None:
        return ""
    t = captain.get("title")
    return (str(captain.get("name")) + ", " + str(t)) if t else captain.get("name")


def captain_is_rival(agent_id, captain):
    """True while the captain's authored `Rival when:` guard holds against the
    player's *personal* standing with him (the captain record is the rep context,
    so `standing` / a pole read his personal reputation). No guard -> never rival."""
    guard = captain.get("rival_when") if captain is not None else None
    if not guard:
        return False
    return dialogue_guard_ok(guard, agent_id, captain)


def dialogue_speaker(sides, captains, lifeforms, key):
    """Resolve a scene's Speaker key to a voice record (key/name/color/leans) used by
    the dialogue driver for the card AND as the reputation context. Checks, in order:
    a captain (his personal-rep key, his side's color), a cast lifeform (a comms NPC,
    no rep), an Academy officer (the Admiral's navy - personal rep via their Values),
    then a side. None if unknown. lifeform_speaker is the library's (amd_lifeforms, imported by
    universe_lifeforms.py), officer_speaker from universe_fleets.py (shared namespace)."""
    if key is None:
        return None
    cap = captain_get(captains, key)
    if cap is not None:
        side = sides_get(sides, cap.get("side"))
        return MastDataObject({
            "key": cap.key,
            "name": captain_full_name(cap),
            "color": side.get("color") if side is not None else "#cccccc",
            "face": cap.get("face") or (side.get("face") if side is not None else None),
            "leans": cap.get("leans") or {},
        })
    lf = lifeform_speaker(lifeforms, key)
    if lf is not None:
        return lf
    try:
        off = officer_speaker(key)
    except NameError:
        off = None
    if off is not None:
        return off
    return sides_get(sides, key)
