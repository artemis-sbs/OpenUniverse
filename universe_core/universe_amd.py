"""Friendly AMD fact-sheet reader for the Open Universe (Option A).

A universe AMD fence is authored as `Label: value` fact lines instead of YAML
(keep the `---` fence, drop the YAML). This module turns one fence block into the
internal data dict the rest of the universe code already reads.

Generic parsing + value coercion lives in `sbs_utils.procedural.amd`, and the
generic QUEST vocabulary (Goal/When/Then/Pays/Scope/State/Win/Lose/Tier/Display and
the trigger verbs) now lives in `sbs_utils.procedural.amd_quest` - shared with any
mission (e.g. the LM siege map), so universe AMD is a strict SUPERSET of that
subset. This file keeps only the Open Universe's OWN vocabulary (clans, generation,
worldlets, admiralty, reputation) and composes the shared quest handler underneath
it. `universe_amd_data` is still the public entry (`data_parser=universe_amd_data`).
"""
from sbs_utils.procedural.amd import (
    amd_parse_facts, amd_norm, amd_num, amd_pct, amd_list,
    amd_weighted, amd_makeup, amd_coords)
from sbs_utils.procedural.amd_quest import amd_quest_facts, amd_reward

_ROLE_ALIASES = {"derelict": "universe_derelict", "derelicts": "universe_derelict"}

# Generation knobs (the `generation:` block): friendly label -> internal key.
_GEN_PCT = {
    "station mix": "station", "enemy mix": "enemy", "nebula mix": "nebula",
    "anomaly mix": "anomaly", "derelict chance": "derelict",
    "outpost chance": "outpost", "mine chance": "mines",
}

# The shared quest vocabulary (Goal/When/Then/Pays/Scope/State/Win/Lose/Tier/Display),
# bound with the universe's role aliases. Tried first in _ou_facts.
_quest_facts = amd_quest_facts(_ROLE_ALIASES)


def _f_rep(s):
    """'iron honest 20, iron fearsome 10' -> {iron: {honest: 20, fearsome: 10}}.
    Each comma item is 'clan pole delta'."""
    out = {}
    for item in amd_list(s):
        toks = item.split()
        if len(toks) >= 3 and toks[-1].lstrip("+-").isdigit():
            out.setdefault(toks[0], {})[amd_norm(" ".join(toks[1:-1]))] = int(toks[-1])
    return out


def _ou_facts(data, label, value):
    """The Open Universe's label->key interpretation, as an amd_parse_facts handler.
    The shared quest vocabulary is tried first; this adds the universe's own labels
    (clans, generation, worldlets, admiralty, reputation). Returns True when a label
    is consumed; None for unknown labels so amd_parse_facts applies its default."""
    if _quest_facts(data, label, value):
        return True
    if label == "color":
        data["color"] = value
    elif label == "archetype":
        data["archetype"] = value
    elif label == "disposition":
        data["diplomacy"] = value
    elif label in ("home", "homes", "roams"):
        data["homes"] = [c for c in (amd_coords(p) for p in value.split(";")) if len(c) == 2]
    elif label in ("deliver to", "deliver_to", "destination"):
        data["deliver_to"] = amd_coords(value)
    elif label == "pickup":
        data["pickup"] = amd_coords(value)
    elif label == "center":
        data["center"] = amd_coords(value)
    elif label == "at":
        data["at"] = amd_coords(value)
    elif label == "sabotage":
        data["sabotage"] = amd_list(value)
    elif label in _GEN_PCT:
        data.setdefault("generation", {})[_GEN_PCT[label]] = amd_pct(value)
    elif label == "loot max":
        data.setdefault("generation", {})["loot_max"] = amd_num(value)
    elif label == "worldlet chance":
        data.setdefault("generation", {})["worldlet"] = amd_pct(value)
    elif label == "yields":
        data["yields"] = amd_weighted(value)
    elif label == "reserve":
        data["reserve"] = None if value.strip().lower() == "unlimited" else amd_num(value)
    elif label == "palette":
        pal = {}
        for item in amd_list(value):
            toks = item.split()
            if len(toks) >= 2:
                pal[amd_norm(toks[0])] = amd_num(" ".join(toks[1:]))
        data["palette"] = pal
    elif label in ("start ore", "start gas", "start crew"):
        data.setdefault("admiralty", {})[amd_norm(label)] = amd_num(value)
    elif label == "storage":
        data.setdefault("admiralty", {})["storage"] = amd_num(value)
    elif label == "costs":
        data["costs"] = amd_weighted(value)
    elif label == "unlocks":
        data["unlocks"] = amd_list(value)
    elif label == "command points":
        data.setdefault("admiralty", {})["command_points"] = amd_num(value)
    elif label == "fleet gas burn":
        data.setdefault("admiralty", {})["fleet_gas_burn"] = amd_num(value)
    elif label == "requisition budget":
        data.setdefault("admiralty", {})["requisition_budget"] = amd_reward(value)["credits"]
    elif label == "skirmish pressure":
        data.setdefault("admiralty", {})["skirmish_pressure"] = value
    elif label in ("skirmish interval", "mia timer"):
        data.setdefault("admiralty", {})[amd_norm(label)] = amd_num(value)
    elif label == "relay rate":
        data.setdefault("admiralty", {})["relay_rate"] = amd_pct(value)
    elif label == "build model":
        data.setdefault("admiralty", {})["build_model"] = str(value).strip().lower()
    elif label == "mode":
        data.setdefault("admiralty", {})["mode"] = str(value).strip().lower()
    elif label == "economy pace":
        data.setdefault("admiralty", {})["economy_pace"] = str(value).strip().lower()
    elif label == "research pace":
        data.setdefault("admiralty", {})["research_pace"] = value
    elif label == "values":
        data["leans"] = amd_weighted(value)
    elif label == "offers":
        data["quest_pool"] = amd_list(value)
    elif label == "flies":
        data["makeup"] = amd_makeup(value)
    elif label in ("file", "files"):
        data.setdefault("file", []).extend(amd_list(value))
    elif label == "earns":
        data["rep"] = _f_rep(value)
    elif label == "axis":
        parts = [p.strip() for p in value.split("/")]
        ax = {"axis": amd_norm(parts[0]), "pos": amd_norm(parts[0])}
        if len(parts) > 1 and parts[1]:
            ax["neg"] = amd_norm(parts[1])
        data.setdefault("reputation", {}).setdefault("axes", []).append(ax)
    elif label in ("job tiers", "tiers"):
        nums = [int(x) for x in value.replace(",", " ").split() if x.isdigit()]
        if len(nums) >= 2:
            data.setdefault("reputation", {})["tiers"] = {"t2": nums[0], "t3": nums[1]}
    elif label in ("foe deals at", "foe deal"):
        data.setdefault("reputation", {})["foe_deal"] = amd_num(value)
    elif label in ("alliance at", "alliance"):
        data.setdefault("reputation", {})["alliance_standing"] = amd_num(value)
    elif label in ("max reward", "reward at 100"):
        data.setdefault("reputation", {})["reward_mult_max"] = amd_num(value)
    elif label == "ceasefire free at":
        data.setdefault("reputation", {})["ceasefire_free_at"] = amd_num(value)
    elif label == "ceasefire per point":
        data.setdefault("reputation", {})["ceasefire_per_point"] = amd_num(value)
    else:
        return None      # unknown label -> amd_parse_facts applies amd_num default
    return True


def universe_amd_data(text):
    """Parse one friendly fact-sheet fence block into the internal data dict the
    universe code reads. Generic parsing/coercion lives in sbs_utils.procedural.amd;
    the shared quest vocabulary in sbs_utils.procedural.amd_quest; this supplies the
    Open Universe's own labels."""
    return amd_parse_facts(text, _ou_facts)


# --- declare the universe's own vocabulary to the shared registry -------------
# `_ou_facts` above is the RUNTIME handler - it turns these labels into the internal
# dict. Declaring them here is the other half: it tells the linter what a value should
# look like and gives the VS Code Inspector a real widget per field. Without it the
# universe's ~30 labels are invisible to every tool, which is why a typo in
# `Disposition:` or `Flies:` used to fail silently.
#
# Registration RAISES on a collision with a core field, so a future sbs_utils field
# named `Offers` or `Home` fails at startup instead of quietly shadowing ours.
def _declare_universe_vocabulary():
    from sbs_utils.procedural.amd_schema import (
        amd_register_fields, amd_register_section_names,
        text, integer, pct, csv, enum, ref, color, coord2, weighted, makeup)

    amd_register_fields("clan", {
        "archetype": enum("military", "trader", "scientist", "pirate", open=True),
        "disposition": enum("friendly", "neutral", "hostile", open=True),
        "home": coord2(),
        "values": weighted(hint="by-the-book 40, fearsome 30"),
        "offers": csv(hint="patrol, escort, strike"),
        "flies": makeup(hint="60% Kralien, 40% Arvonian"),
    }, domain="universe")

    amd_register_fields("captain", {
        "clan": ref("node"), "title": text(), "values": weighted(),
        "flies": makeup(), "roams": csv(), "rival when": text(),
        "file": text(hint="a sibling .amd holding this captain's dialogue"),
    }, domain="universe")

    # The universe gives its officers a rank and a personality on top of the
    # shared LIFEFORM fields.
    amd_register_fields("lifeform", {
        "title": text(hint="rank or role, e.g. Chief Engineer"),
        "values": weighted(hint="what this character cares about"),
    }, domain="universe")

    amd_register_fields("worldlet", {
        "yields": csv(hint="what can be mined here"),
        "reserve": integer(hint="how much is left"),
        "palette": text(hint="the look of the surface"),
    }, domain="universe")

    amd_register_fields("admiralty", {
        "economy pace": pct(), "research pace": pct(), "relay rate": pct(),
        "worldlet chance": pct(), "skirmish pressure": pct(),
        "skirmish interval": integer(hint="seconds"),
        "mia timer": integer(hint="seconds"),
        "start ore": integer(), "start gas": integer(), "start crew": integer(),
        "storage": integer(), "command points": integer(),
        "fleet gas burn": integer(), "requisition budget": integer(),
        "sabotage": text(),
    }, domain="universe")

    # Region generation knobs the universe adds on top of the shared REGION fields.
    amd_register_fields("region", {
        "skybox": text(), "music": text(),
        "enemy mix": makeup(), "station mix": makeup(), "nebula mix": makeup(),
        "anomaly mix": makeup(), "mine chance": pct(),
        "derelict chance": pct(), "outpost chance": pct(),
    }, domain="universe")

    amd_register_fields("landmark", {
        "terrain": csv(), "guards": csv(hint="what defends it"),
    }, domain="universe")

    # Sections the universe names its own way.
    amd_register_section_names(("clans",), "clan", domain="universe")
    amd_register_section_names(("captains",), "captain", domain="universe")
    amd_register_section_names(("worldlets",), "worldlet", domain="universe")
    amd_register_section_names(("admiralty",), "admiralty", domain="universe")
    amd_register_section_names(("officers", "cast", "crew"), "lifeform", domain="universe")


try:
    _declare_universe_vocabulary()
except Exception as _e:      # never let a vocabulary clash stop the mission loading
    print(f"universe_amd: vocabulary not declared - {_e}")
