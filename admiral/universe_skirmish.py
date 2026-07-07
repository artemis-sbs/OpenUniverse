"""Border skirmishes for the Admiral game (slice 4 - ADMIRAL_CONSOLE.md
sections 13/14). Extraction does not summon raids globally; pressure comes
from *proximity to foe territory*: a system inside or bordering foe-clan
space draws periodic raids against the side's platforms, scaled by how much
hostile border touches it. Deep-core mining is safe; the frontier is where
the Admiral's game and the crews' game meet.

Pacing rules (decided): skirmishes stay off until the side's first fleet
exists (economy peace through slices 1-2 play), and `Skirmish pressure: off`
in the Admiralty fence disables them entirely. Raids prefer a Bastion when
one stands - the fight happens at the fort, not the extractors.

The tick only *decides* (pure-ish Python, unit-testable); the raid itself is
spawned by admiral.mast's skirmish loop via prefab_fleet_raider, and the
alert reaches the crews as an Admiralty info card.

Shared-namespace notes: universe_system_kind from universe_helpers.py;
universe_system_clan / clan_get from universe_clans.py; admiralty_* from
universe_worldlets.py; fleet_count from universe_fleets.py.
"""
import math
import random
from sbs_utils.mast.mast_node import MastDataObject
from sbs_utils.procedural.roles import role, has_role
from sbs_utils.procedural.query import to_object_list
from sbs_utils.procedural.sides import to_side_id, side_are_enemies

# Live per-load state (reset by skirmish_reset on universe load).
_SKIRMISH = {}   # (side, i, j) -> {"armed": bool, "countdown": float}


def skirmish_reset():
    global _SKIRMISH
    _SKIRMISH = {}


def _clan_is_foe(clans, key, side):
    """Authored a foe AND still hostile: a negotiated ceasefire (diplomacy
    economy) lifts the pressure. Falls back to the authored disposition when
    the side agents don't exist (early start, headless tests)."""
    c = clan_get(clans, key)
    if c is None or c.get("diplomacy") != "foe":
        return False
    if to_side_id(key) is not None and to_side_id(side) is not None:
        return bool(side_are_enemies(key, side))
    return True


def skirmish_pressure(clans, seed, i, j, danger="Quiet", side=None):
    """(pressure, foe_keys) for a system: one point per foe-owned cell in the
    Chebyshev ring around it, two for the system itself being foe-owned.
    Zero deep in friendly space - the map IS the threat model. `side` is the
    player side under threat (defaults to the primary player side)."""
    if side is None:
        side = universe_primary_side()
    pressure = 0
    foes = []
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            ci, cj = int(i) + di, int(j) + dj
            kind = universe_system_kind(seed, ci, cj, danger)
            owner = universe_system_clan(clans, seed, ci, cj, kind)[0]
            if owner is not None and _clan_is_foe(clans, owner, side):
                pressure += 2 if (di == 0 and dj == 0) else 1
                if owner not in foes:
                    foes.append(owner)
    return pressure, foes


def skirmish_tick(side, clans, seed, i, j, danger, dt_seconds):
    """One pacing step. Returns a raid descriptor (clan / difficulty / spawn
    point / target name) when a raid is due, else None. The countdown runs
    faster under heavier pressure; it only runs at all when the navy exists,
    the system has platforms to hit, and a foe border touches it."""
    if not admiralty_active():
        return None
    mode = str(admiralty_tuning("skirmish_pressure", "border") or "").strip().lower()
    if mode in ("", "off", "none"):
        return None
    # Per (side, cell) countdown: each live frontier the side holds paces its own
    # raids from its own border pressure - a side spread across two systems is
    # pressured in both, not just wherever the flag happens to be.
    st = _SKIRMISH.setdefault((side, int(i), int(j)), {
        "armed": False,
        "countdown": float(admiralty_tuning("skirmish_interval", 240))})
    if not st["armed"]:
        # Economy peace until the first fleet forms (decision: border defense
        # is `patrol` first - raids arrive once the answer to them exists). The
        # navy is counted side-wide - any fleet means this frontier can be raided.
        if fleet_count() <= 0:
            return None
        st["armed"] = True
    # Target platforms IN cell (i, j) - the same cell the pressure is computed for
    # (objects_in_cell is a sibling free global). Without this the raid could spawn
    # on a platform in another live system while reading THIS cell's foe border.
    plats = objects_in_cell(to_object_list(role("admiral_platform") & role(side)), i, j)
    if not plats:
        return None
    pressure, foes = skirmish_pressure(clans, seed, i, j, danger, side)
    if pressure <= 0 or not foes:
        return None
    st["countdown"] -= float(dt_seconds) * (1.0 + 0.15 * (pressure - 1))
    if st["countdown"] > 0:
        return None
    st["countdown"] = float(admiralty_tuning("skirmish_interval", 240))
    bastions = [p for p in plats if has_role(p.id, "admiral_bastion")]
    tgt = random.choice(bastions or plats)
    ang = random.uniform(0, 2 * math.pi)
    dist = random.uniform(9000, 14000)
    return MastDataObject({
        "clan": random.choice(foes),
        "difficulty": max(1, min(9, pressure)),
        "target": str(tgt.name or "the works"),
        "x": tgt.pos.x + math.cos(ang) * dist,
        "y": 0.0,
        "z": tgt.pos.z + math.sin(ang) * dist,
    })
