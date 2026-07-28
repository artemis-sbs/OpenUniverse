"""Friendly AMD fact-sheet reader for the Open Universe (Option A).

A universe AMD fence is authored as `Label: value` fact lines instead of YAML
(keep the `---` fence, drop the YAML). This module turns one fence block into the
internal data dict the rest of the universe code already reads.

Generic parsing + value coercion lives in `sbs_utils.procedural.amd`, and the
generic QUEST vocabulary (Goal/When/Then/Pays/Scope/State/Win/Lose/Tier/Display and
the trigger verbs) now lives in `sbs_utils.procedural.amd_quest` - shared with any
mission (e.g. the LM siege map), so universe AMD is a strict SUPERSET of that
subset. This file keeps only the Open Universe's OWN vocabulary (sides, generation,
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
    Each comma item is 'side pole delta'."""
    out = {}
    for item in amd_list(s):
        toks = item.split()
        if len(toks) >= 3 and toks[-1].lstrip("+-").isdigit():
            out.setdefault(toks[0], {})[amd_norm(" ".join(toks[1:-1]))] = int(toks[-1])
    return out


def _ou_facts(data, label, value):
    """The Open Universe's label->key interpretation, as an amd_parse_facts handler.
    The shared quest vocabulary is tried first; this adds the universe's own labels
    (sides, generation, worldlets, admiralty, reputation). Returns True when a label
    is consumed; None for unknown labels so amd_parse_facts applies its default."""
    if _quest_facts(data, label, value):
        return True
    if label == "color":
        data["color"] = value
    elif label in ("character", "archetype"):
        # `Character:` is what a side IS - military, trader, pirate. It used to be
        # called `Archetype:`, which is our word for a record's TYPE; a reader met the
        # implementation's noun on the page. Old files still parse.
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
    elif label in ("standing", "earns"):
        # `Standing:` - what finishing this does to how a side sees you. It was `Earns:`,
        # which sat next to `Reward:` looking like a second payment; this is reputation,
        # a different currency entirely. And a record speaks in the JOB's voice, so it
        # says what it GIVES, not what the crew "earns".
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
        text, integer, pct, csv, enum, ref, color, coord2, weighted, makeup, field)

    # `Earns:` is a REPUTATION nudge, not a reward - it belongs to the Open Universe,
    # which is the only place it is authored and the only thing that reads it. It used
    # to be declared in the shared quest table typed as a `reward`, where every tool
    # offered it to authors who had nothing to read it.
    amd_register_fields("quest", {
        "standing": field(text(hint="iron honest 20, iron fearsome 10"),
                          key="rep", aka=("earns",)),
    }, domain="OpenUniverse")

    # A side IS A SIDE - universe_sides.py has said so since the beginning ("spawned
    # as sides"). It was a private archetype because there was nowhere to put the half
    # that is not a side: its standing, its home patch, its fleet mix. Those hang off
    # `side` now, so an author writes Side and the extra words come with it.
    amd_register_fields("side", {
        "character": field(enum("military", "trader", "scientist", "pirate", open=True),
                           key="archetype", aka=("archetype",)),
        "disposition": enum("friendly", "neutral", "hostile", open=True),
        "home": coord2(),
        "values": weighted(hint="by-the-book 40, fearsome 30"),
        "offers": csv(hint="patrol, escort, strike"),
        "flies": makeup(hint="60% Kralien, 40% Arvonian"),
    }, domain="universe")

    # A captain is a CHARACTER - a named person who flies for a side and is hailable.
    # It was a private archetype whose `title` and `values` were already declared on
    # lifeform right below it: the same two fields, twice, which is what a redundant
    # archetype looks like from the inside.
    amd_register_fields("lifeform", {
        "title": text(hint="rank or role, e.g. Chief Engineer"),
        "values": weighted(hint="what this character cares about"),
        "side": ref("node", hint="the side this person flies for"),
        "flies": makeup(hint="60% Kralien, 40% Arvonian"),
        "roams": csv(hint="the systems they are found in"),
        "rival when": text(hint="what turns them against you"),
        "file": text(hint="a sibling .amd holding this character's dialogue"),
    }, domain="universe")

    # A worldlet is a LANDMARK that yields - not a kind of thing of its own. `Yields:`
    # and `Reserve:` come from the shared `economy` trait (anything that produces can
    # claim it); `Palette:` is how this landmark LOOKS, so it belongs to landmark.
    amd_register_fields("landmark", {
        "palette": text(hint="the look of the surface"),
    }, domain="universe")

    amd_register_fields("map", {
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
    # `## Sides` still parses; `## Sides` is the word.
    amd_register_section_names(("sides",), "side", domain="universe")
    amd_register_section_names(("captains",), "lifeform", domain="universe")
    amd_register_section_names(("worldlets",), "landmark", domain="universe")
    amd_register_section_names(("admiralty",), "map", domain="universe")
    # A trade good IS an item - a thing with a weight that scatters as loot. A research
    # milestone is an item you unlock, and what it costs and how long it takes come
    # from the shared `economy` trait.
    amd_register_section_names(("goods",), "item", domain="universe")
    amd_register_section_names(("research",), "item", domain="universe")
    amd_register_fields("item", {
        "branch": text(hint="which ladder this milestone sits on"),
        "unlocks": text(hint="storage N | extraction N% | requisition <item>"),
        "requires": ref("node", hint="the milestone before this one"),
    }, domain="universe")
    amd_register_section_names(("officers", "cast", "crew"), "lifeform", domain="universe")


try:
    _declare_universe_vocabulary()
except Exception as _e:      # never let a vocabulary clash stop the mission loading
    print(f"universe_amd: vocabulary not declared - {_e}")
