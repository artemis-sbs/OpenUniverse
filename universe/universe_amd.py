"""Friendly AMD fact-sheet reader for the Open Universe (Option A).

A universe AMD fence is authored as `Label: value` fact lines instead of YAML
(keep the `---` fence, drop the YAML). This module turns one fence block into the
internal data dict the rest of the universe code already reads, with friendly
value parsing: comma lists, "name N" weights, "name N%" makeup, "a / b" pole
pairs, and English trigger verbs. A fence that uses YAML flow ({ or [) is parsed
as YAML instead, so legacy files (clans.amd) and any inline YAML keep working
through the same reader. Wired in via document_get_amd_file(..., data_parser=...).

Kept dependency-light (only load_yaml_string) so it imports cleanly on its own and
is unit-testable outside the engine. See UNIVERSE_CHANGES.md.
"""
from sbs_utils.fs import load_yaml_string

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


def _f_norm(name):
    """A pole/key token canonicalized: lowercase, hyphens/spaces -> underscores."""
    return str(name).strip().lower().replace("-", "_").replace(" ", "_")


def _f_num(s):
    s = str(s).strip()
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return s


def _f_pct(s):
    """'40%' -> 0.4; '0.4' -> 0.4; a bare number -> float. Used by generation knobs."""
    s = str(s).strip()
    if s.endswith("%"):
        s = s[:-1].strip()
        try:
            return float(s) / 100.0
        except ValueError:
            return s
    try:
        return float(s)
    except ValueError:
        return s


# Generation knobs (the `generation:` block): friendly label -> internal key. Values
# are percentages; grouped under data["generation"] for generation_configure.
_GEN_PCT = {
    "station mix": "station", "enemy mix": "enemy", "nebula mix": "nebula",
    "anomaly mix": "anomaly", "derelict chance": "derelict",
    "outpost chance": "outpost", "mine chance": "mines",
}


def _f_list(s):
    return [x.strip() for x in str(s).split(",") if x.strip()]


def _f_weighted(s):
    """'by-the-book 40, fearsome 30' -> {by_the_book: 40, fearsome: 30}."""
    out = {}
    for item in _f_list(s):
        toks = item.split()
        if len(toks) >= 2 and toks[-1].lstrip("+-").isdigit():
            out[_f_norm(" ".join(toks[:-1]))] = int(toks[-1])
        elif toks:
            out[_f_norm(item)] = 0
    return out


def _f_makeup(s):
    """'60% Kralien, 40% Arvonian' -> {Kralien:60,...}; 'Kralien, Torgoth' -> list;
    'Torgoth' -> str (matches clan_pick_race's three makeup shapes)."""
    items = _f_list(s)
    if any("%" in it for it in items):
        out = {}
        for it in items:
            toks = it.replace("%", " ").split()
            if toks and toks[0].isdigit():
                out[" ".join(toks[1:])] = int(toks[0])
            elif len(toks) >= 2 and toks[-1].isdigit():
                out[" ".join(toks[:-1])] = int(toks[-1])
        return out
    return items[0] if len(items) == 1 else items


def _f_coords(s):
    """'6, 4' -> [6, 4]."""
    return [int(x) for x in str(s).replace(",", " ").split() if x.lstrip("-").isdigit()][:2]


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
        data["sector"] = _f_coords(target)
    elif kind == "key":
        if target:
            data["key"] = _f_norm(target)
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
    for item in _f_list(s):
        toks = item.split()
        if len(toks) >= 3 and toks[-1].lstrip("+-").isdigit():
            out.setdefault(toks[0], {})[_f_norm(" ".join(toks[1:-1]))] = int(toks[-1])
    return out


def universe_amd_data(text):
    """Parse one friendly fact-sheet fence block into the internal data dict the
    universe code reads. Delegates to YAML when the block uses YAML flow ({ or [)."""
    if "{" in text or "[" in text:
        return load_yaml_string(text)
    data = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("//") or ":" not in line:
            continue
        label, value = line.split(":", 1)
        label = label.strip().lower()
        value = value.strip()
        if label == "color":
            data["color"] = value
        elif label == "archetype":
            data["archetype"] = value
        elif label == "disposition":
            data["diplomacy"] = value
        elif label in ("home", "homes", "roams"):
            data["homes"] = [c for c in (_f_coords(p) for p in value.split(";")) if len(c) == 2]
        elif label in ("deliver to", "deliver_to", "destination"):
            data["deliver_to"] = _f_coords(value)
        elif label == "pickup":
            data["pickup"] = _f_coords(value)
        elif label == "center":
            data["center"] = _f_coords(value)
        elif label == "at":
            data["at"] = _f_coords(value)
        elif label == "sabotage":
            data["sabotage"] = _f_list(value)
        elif label in ("win", "lose"):
            # A campaign goal's outcome: completing it wins/loses the campaign.
            data[label] = str(value).strip().lower() in ("true", "yes", "1", "")
        elif label in _GEN_PCT:
            data.setdefault("generation", {})[_GEN_PCT[label]] = _f_pct(value)
        elif label == "loot max":
            data.setdefault("generation", {})["loot_max"] = _f_num(value)
        elif label == "worldlet chance":
            data.setdefault("generation", {})["worldlet"] = _f_pct(value)
        elif label == "yields":
            # Worldlet extraction: 'ore 8, crew 2' -> {ore: 8, crew: 2} per minute.
            data["yields"] = _f_weighted(value)
        elif label == "reserve":
            # Depletion pool; 'unlimited' -> None (never runs dry).
            data["reserve"] = None if value.strip().lower() == "unlimited" else _f_num(value)
        elif label == "palette":
            # behav_planet surface look: 'base #8c2f1c, clouds #b8c4e0, bands 3.7'
            # -> {base: '#8c2f1c', clouds: '#b8c4e0', bands: 3.7}.
            pal = {}
            for item in _f_list(value):
                toks = item.split()
                if len(toks) >= 2:
                    pal[_f_norm(toks[0])] = _f_num(" ".join(toks[1:]))
            data["palette"] = pal
        elif label in ("start ore", "start gas", "start crew"):
            # Admiralty starting stockpiles.
            data.setdefault("admiralty", {})[_f_norm(label)] = _f_num(value)
        elif label == "storage":
            data.setdefault("admiralty", {})["storage"] = _f_num(value)
        elif label == "costs":
            # Research milestone cost: 'ore 120, gas 40' -> {ore: 120, gas: 40}.
            data["costs"] = _f_weighted(value)
        elif label == "unlocks":
            # Research effects, plain English phrases interpreted by
            # universe_research.py: 'storage 500', 'extraction 25%',
            # 'requisition tauron_focuser' (comma-separated).
            data["unlocks"] = _f_list(value)
        elif label == "command points":
            data.setdefault("admiralty", {})["command_points"] = _f_num(value)
        elif label == "fleet gas burn":
            data.setdefault("admiralty", {})["fleet_gas_burn"] = _f_num(value)
        elif label == "requisition budget":
            data.setdefault("admiralty", {})["requisition_budget"] = _f_reward(value)["credits"]
        elif label == "skirmish pressure":
            data.setdefault("admiralty", {})["skirmish_pressure"] = value
        elif label in ("skirmish interval", "mia timer"):
            # Slice 4 pacing: seconds between border raids / the MIA rescue window.
            data.setdefault("admiralty", {})[_f_norm(label)] = _f_num(value)
        elif label == "relay rate":
            # Relay Gate remote income, a fraction ('50%' or '0.5').
            data.setdefault("admiralty", {})["relay_rate"] = _f_pct(value)
        elif label == "build model":
            # 'menu' (instant/parallel) or 'fabricator' (a builder ship). A/B knob.
            data.setdefault("admiralty", {})["build_model"] = str(value).strip().lower()
        elif label == "research pace":
            data.setdefault("admiralty", {})["research_pace"] = value
        elif label == "values":
            data["leans"] = _f_weighted(value)
        elif label == "offers":
            data["quest_pool"] = _f_list(value)
        elif label == "flies":
            data["makeup"] = _f_makeup(value)
        elif label == "display":
            data["display"] = value
        elif label in ("file", "files"):
            # A section may pull its entries from one or more files: repeat `File:`
            # lines, or a comma list (`Files: a.amd, b.amd`). Accumulated into a list.
            data.setdefault("file", []).extend(_f_list(value))
        elif label == "tier":
            data["tier"] = _f_num(value)
        elif label in ("scope", "state"):
            data[label] = value
        elif label in ("goal", "when"):
            trig = _f_trigger(value)
            if trig is not None:
                data[trig[0]] = trig[1]
            if label == "goal":
                data["objective"] = value[:1].upper() + value[1:]
            elif label == "when" and trig is None:
                # Not a quest trigger verb (e.g. dialogue `When: comms`) -> keep raw.
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
            ax = {"axis": _f_norm(parts[0]), "pos": _f_norm(parts[0])}
            if len(parts) > 1 and parts[1]:
                ax["neg"] = _f_norm(parts[1])
            data.setdefault("reputation", {}).setdefault("axes", []).append(ax)
        elif label in ("job tiers", "tiers"):
            nums = [int(x) for x in value.replace(",", " ").split() if x.isdigit()]
            if len(nums) >= 2:
                data.setdefault("reputation", {})["tiers"] = {"t2": nums[0], "t3": nums[1]}
        elif label in ("foe deals at", "foe deal"):
            data.setdefault("reputation", {})["foe_deal"] = _f_num(value)
        elif label in ("alliance at", "alliance"):
            data.setdefault("reputation", {})["alliance_standing"] = _f_num(value)
        elif label in ("max reward", "reward at 100"):
            data.setdefault("reputation", {})["reward_mult_max"] = _f_num(value)
        elif label == "ceasefire free at":
            data.setdefault("reputation", {})["ceasefire_free_at"] = _f_num(value)
        elif label == "ceasefire per point":
            data.setdefault("reputation", {})["ceasefire_per_point"] = _f_num(value)
        else:
            data[_f_norm(label)] = _f_num(value)
    return data
