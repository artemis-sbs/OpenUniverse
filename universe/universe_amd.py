"""Friendly AMD fact-sheet reader for the Open Universe (Option A).

A universe AMD fence is authored as `Label: value` fact lines instead of YAML
(keep the `---` fence, drop the YAML). This module turns one fence block into the
internal data dict the rest of the universe code already reads.

The generic parsing + value coercion now lives in the library
(`sbs_utils.procedural.amd`); this file keeps only the Open Universe's VOCABULARY:
the domain coercers (trigger verbs, rewards, reputation) and the label->key
interpretation chain, wired in as an `amd_parse_facts` handler. `universe_amd_data`
is still the public entry point (referenced as `data_parser=universe_amd_data`).
"""
from sbs_utils.procedural.amd import (
    amd_parse_facts, amd_norm, amd_num, amd_pct, amd_list,
    amd_weighted, amd_makeup, amd_coords)

_ROLE_ALIASES = {"derelict": "universe_derelict", "derelicts": "universe_derelict"}
# verb -> (trigger key, target field): a role (npc), a key (item), or a sector.
_TRIGGER_VERBS = {
    "destroy": ("on_kill", "role"),   "kill": ("on_kill", "role"),
    "recover": ("on_collect", "key"), "collect": ("on_collect", "key"),
    "gather": ("on_collect", "key"),
    "scan": ("on_scan", "role"),      "survey": ("on_scan", "role"),
    "dock": ("on_dock", "role"),
    "reach": ("on_reach", "sector"),  "travel": ("on_reach", "sector"),
}

# Generation knobs (the `generation:` block): friendly label -> internal key.
_GEN_PCT = {
    "station mix": "station", "enemy mix": "enemy", "nebula mix": "nebula",
    "anomaly mix": "anomaly", "derelict chance": "derelict",
    "outpost chance": "outpost", "mine chance": "mines",
}


def _f_trigger(s):
    """'destroy 4 raiders' -> ('on_kill', {role: raider, count: 4}); 'reach 6, 4' ->
    ('on_reach', {sector: [6,4]}); 'recover 3 provisions' -> ('on_collect', {key:
    provisions, count: 3}). None if the leading word isn't a known verb."""
    toks = str(s).split()
    if not toks:
        return None
    spec = _TRIGGER_VERBS.get(toks[0].lower())
    if spec is None:
        return None
    trig, kind = spec
    rest = toks[1:]
    count = None
    if rest and rest[0].isdigit():
        count = int(rest[0])
        rest = rest[1:]
    target = " ".join(rest).strip()
    data = {}
    if kind == "sector":
        data["sector"] = amd_coords(target)
    elif kind == "key":
        if target:
            data["key"] = amd_norm(target)
        if count is not None:
            data["count"] = count
    else:  # role
        role = _ROLE_ALIASES.get(target.lower())
        if role is None:
            role = target.lower()
            if role.endswith("s"):
                role = role[:-1]
        data["role"] = role
        data["count"] = count if count is not None else 1
    return trig, data


def _f_reward(s):
    """'300 credits' -> {credits: 300}."""
    for t in str(s).split():
        if t.isdigit():
            return {"credits": int(t)}
    return {"credits": 0}


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
    """The Open Universe's label->key interpretation, as an amd_parse_facts
    handler. Returns True when a label is consumed; returns None for unknown
    labels so amd_parse_facts applies its default (amd_num)."""
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
    elif label in ("win", "lose"):
        data[label] = str(value).strip().lower() in ("true", "yes", "1", "")
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
        data.setdefault("admiralty", {})["requisition_budget"] = _f_reward(value)["credits"]
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
    elif label == "display":
        data["display"] = value
    elif label in ("file", "files"):
        data.setdefault("file", []).extend(amd_list(value))
    elif label == "tier":
        data["tier"] = amd_num(value)
    elif label in ("scope", "state"):
        data[label] = value
    elif label in ("goal", "when"):
        trig = _f_trigger(value)
        if trig is not None:
            data[trig[0]] = trig[1]
        if label == "goal":
            data["objective"] = value[:1].upper() + value[1:]
        elif label == "when" and trig is None:
            data["when"] = value
    elif label == "then":
        toks = value.split()
        if len(toks) >= 2 and toks[0].lower() in ("reveal", "signal"):
            data[toks[0].lower()] = toks[1]
        else:
            data["reveal"] = value
    elif label == "pays":
        data["reward"] = _f_reward(value)
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
    universe code reads. (Generic parsing/coercion lives in sbs_utils.procedural.amd;
    this supplies the Open Universe vocabulary.)"""
    return amd_parse_facts(text, _ou_facts)
