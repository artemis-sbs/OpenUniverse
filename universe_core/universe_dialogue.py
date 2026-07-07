"""Dialogue scenes for the Open Universe (the movie-script flavor of AMD).

A `## Dialogue` section of universe.amd authors clan conversations as scenes. Each
scene is a `###` heading: the fact sheet sets the Speaker (a clan, for face/name/
color) and When (comms = a clan station's hail opens here); the prose body is the
NPC's lines (`%` = a random variant), followed by a markdown list of choices that
link to the next scene:

    ### Ashfang Hail (ashfang_hail)
    ---
    Speaker: ashfang
    When: comms
    ---
    % You're a long way from friends, captain.
    % Brave or stupid, flying in here.

    - [Apologize](ashfang_backoff)
    - [Threaten them](ashfang_standoff) if fearsome > 20
    - [Offer a cut](ashfang_deal) if credits >= 200 ; costs 200 credits, earns ashfang selfish +5

This is a *runtime driver* (like the quest driver), not a code generator: the
universe.mast comms route renders the current scene + choices and advances on a
pick. Declarative only - no loops/variables/expressions, just speakers, lines,
guarded choices, and light outcomes (jump to a scene, nudge reputation, emit a
signal, spend credits). See UNIVERSE_CHANGES.md.

Parsing is pure (unit-testable); guard eval and outcome apply call the reputation
helpers + signals at runtime (resolved through the shared mission namespace).
"""
import random
import re
from sbs_utils.procedural.signal import signal_emit
from sbs_utils.procedural.inventory import get_inventory_value, set_inventory_value
from sbs_utils.procedural.sides import to_side_id
from sbs_utils.procedural.query import get_side
from sbs_utils.mast.mast_node import MastDataObject

_CHOICE = re.compile(r"^-\s*\[(?P<label>.*?)\]\((?P<target>[\w.\-]+)\)\s*(?P<rest>.*?)\s*$")
_GATE = re.compile(r"^%?\{(?P<gate>[^}]*)\}\s*(?P<text>.*)$")
_GUARD = re.compile(r"^(?P<lhs>[\w ]+?)\s*(?P<op>>=|<=|==|!=|>|<)\s*(?P<num>-?\d+)$")


def _dlg_norm(s):
    return str(s).strip().lower().replace("-", "_").replace(" ", "_")


def dialogue_parse(node):
    """Parse one scene node into a plain dict: speaker, when, lines [(text, gate)],
    and choices [{label, target, guard, outcomes}]. Pure - no engine calls."""
    data = node.get("data") or {}
    lines = []
    choices = []
    for raw in (node.get("description") or "").splitlines():
        line = raw.strip()
        if not line or line.startswith("//"):
            continue
        if line.startswith("-") and "](" in line:
            ch = _dlg_parse_choice(line)
            if ch is not None:
                choices.append(ch)
            continue
        # An NPC speech variant. `%` is optional; `%{gate}` / `{gate}` gates the line.
        if line.startswith("%"):
            line = line[1:].strip()
        m = _GATE.match(line) if line.startswith("{") else None
        if m is not None:
            lines.append((m.group("text").strip(), m.group("gate").strip()))
        else:
            lines.append((line, None))
    return {
        "speaker": data.get("speaker"),
        "when": data.get("when"),
        "lines": lines,
        "choices": choices,
    }


def _dlg_parse_choice(line):
    m = _CHOICE.match(line)
    if m is None:
        return None
    rest = m.group("rest").strip()
    guard = None
    outcomes = []
    # `; outcomes` first (so a guard can't swallow them), then a leading `if guard`.
    if ";" in rest:
        rest, outpart = rest.split(";", 1)
        outcomes = _dlg_parse_outcomes(outpart)
        rest = rest.strip()
    if rest.lower().startswith("if "):
        guard = rest[3:].strip()
    return {"label": m.group("label").strip(), "target": m.group("target").strip(),
            "guard": guard, "outcomes": outcomes}


def _dlg_parse_outcomes(s):
    """'costs 200 credits, earns ashfang selfish +5, signal paid_off' -> list of
    ('costs', 200) / ('earns', clan, pole, delta) / ('signal', name)."""
    out = []
    for item in [x.strip() for x in str(s).split(",") if x.strip()]:
        toks = item.split()
        verb = toks[0].lower()
        if verb == "costs" and len(toks) >= 2 and toks[1].lstrip("-").isdigit():
            out.append(("costs", int(toks[1])))
        elif verb == "earns" and len(toks) >= 4 and toks[-1].lstrip("+-").isdigit():
            out.append(("earns", toks[1], _dlg_norm(" ".join(toks[2:-1])), int(toks[-1])))
        elif verb == "signal" and len(toks) >= 2:
            out.append(("signal", toks[1]))
    return out


# --- Scene lookup ------------------------------------------------------------
def dialogue_scenes(doc):
    """key -> scene node for every scene in the `## Dialogue` section (empty if the
    universe authors none). universe_section comes from universe_clans.py."""
    section = universe_section(doc, "dialogue")
    out = {}
    if section is not None:
        for n in section.get("children", []):
            out[n.get("key")] = n
    return out


def dialogue_get(scenes, key):
    return scenes.get(key)


def dialogue_clan_entry(scenes, clan_key):
    """The entry scene key for a clan's hail: Speaker == clan and When == comms.
    None if the clan has no dialogue."""
    for key, n in scenes.items():
        data = n.get("data") or {}
        if data.get("speaker") == clan_key and str(data.get("when", "")).lower() == "comms":
            return key
    return None


# --- Runtime: guards, line pick, outcomes ------------------------------------
def _dlg_metric(name, agent_id, clan):
    """Resolve a guard's left side to a number: a reputation pole, 'standing', or
    'credits'. clan is the speaker clan record."""
    name = name.strip().lower()
    if name == "credits":
        return get_inventory_value(to_side_id(get_side(agent_id)), "credits", 0)
    if name in ("standing", "rep", "reputation"):
        return clan_standing(agent_id, clan)
    return reputation_get(agent_id, (clan.get("key") if clan else None), _dlg_norm(name))


def dialogue_guard_ok(guard, agent_id, clan):
    """Evaluate a simple `lhs op number` guard (no guard -> True). Safe: only a
    metric, a comparison operator, and an integer - never arbitrary code."""
    if not guard:
        return True
    m = _GUARD.match(guard.strip())
    if m is None:
        return False
    lhs = _dlg_metric(m.group("lhs"), agent_id, clan)
    op = m.group("op")
    rhs = int(m.group("num"))
    if op == ">":
        return lhs > rhs
    if op == ">=":
        return lhs >= rhs
    if op == "<":
        return lhs < rhs
    if op == "<=":
        return lhs <= rhs
    if op == "==":
        return lhs == rhs
    if op == "!=":
        return lhs != rhs
    return False


def dialogue_pick_line(scene, agent_id, clan):
    """A random NPC line whose gate passes (gates reuse the reputation read). '' if
    the scene has no eligible line."""
    eligible = [t for (t, gate) in scene["lines"] if dialogue_guard_ok(gate, agent_id, clan)]
    return random.choice(eligible) if eligible else ""


def dialogue_choices(scene, agent_id, clan):
    """Choices whose guard passes, as MastDataObject (label/target/outcomes) so the
    mast comms route can render one button each."""
    out = []
    for ch in scene["choices"]:
        if dialogue_guard_ok(ch.get("guard"), agent_id, clan):
            out.append(MastDataObject({"label": ch["label"], "target": ch["target"],
                                       "outcomes": ch.get("outcomes") or []}))
    return out


def dialogue_apply(agent_id, clan, outcomes):
    """Apply a chosen line's outcomes: spend credits, earn reputation, emit signals.
    Returns False if a 'costs' outcome can't be afforded (the pick is refused)."""
    clan_key = clan.get("key") if clan else None
    for oc in (outcomes or []):
        if oc[0] == "costs":
            sid = to_side_id(get_side(agent_id))
            have = get_inventory_value(sid, "credits", 0)
            if have < oc[1]:
                return False
            set_inventory_value(sid, "credits", have - oc[1])
        elif oc[0] == "earns":
            reputation_adjust(agent_id, oc[1], oc[2], oc[3])
        elif oc[0] == "signal":
            signal_emit(oc[1])
    return True
