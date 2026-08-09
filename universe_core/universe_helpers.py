"""Helpers for the Open Universe map (maps/universe.mast).

A sector's contents are a pure function of (universe_seed, i, j): only the
current sector is instantiated, always around the origin, and a jump clears it
and regenerates the neighbour. So the whole universe is "stored" in its seed
plus the current coordinates (persistence of player-made changes comes later).
"""
import math
import os

from sbs_utils import scatter
from sbs_utils.vec import Vec3
from sbs_utils.fs import get_mission_dir
from sbs_utils.procedural.terrain import (terrain_spawn_field_keyed,
                                          terrain_sow_begin, terrain_sow_end,
                                          terrain_sow_reset)
from sbs_utils.procedural.space_objects import delete_objects_box
from sbs_utils.procedural.roles import role
from sbs_utils.procedural.query import to_object_list, to_object
from sbs_utils.procedural.execution import labels_get_type
from sbs_utils.procedural.inventory import get_inventory_value, set_inventory_value
from sbs_utils.procedural.sides import to_side_id
from sbs_utils.procedural.upgrades import upgrade_add
from sbs_utils.procedural.persistence import PersistentStore
from sbs_utils.procedural.quest import (quest_agent_quests, quest_add, quest_set_key,
                                        quest_get_state, quest_get, QuestState)
from sbs_utils.agent import Agent
import random as _random

# Half-extent of a sector's playable area (world units).
UNIVERSE_SYSTEM_R = 50_000

# --- Save format version + migration ----------------------------------------
# The universe is mostly procedural (regenerated from the seed); the save stores
# only deltas, so most changes need NO migration. Bump this only for a breaking
# restructure of a stored field, and add a matching _MIGRATIONS step. Additive
# fields are read with .get(default) and don't need a bump. See QUESTS_PLAN 8a.
UNIVERSE_SAVE_VERSION = 1

# Ordered single-step migrations: _MIGRATIONS[v] upgrades a v save to v+1.
# e.g. _MIGRATIONS = {1: _migrate_1_to_2}
_MIGRATIONS = {}


def universe_read_optional_file(file):
    """media_read_relative_file, but None when the file doesn't exist instead of
    raising. Used for the legacy split-file fallbacks (side_quests.amd) so a
    modern universe with no ## Jobs section simply offers no side work."""
    from sbs_utils.helpers import FrameContext
    from sbs_utils.procedural.media import media_read_from_zip, media_read_file
    task = FrameContext.task
    source_map = task.get_active_node_source_map() if task is not None else None
    if source_map is None:
        return None
    try:
        if source_map.is_lib:
            return media_read_from_zip(source_map.basedir, file)
        if not os.path.isfile(os.path.join(source_map.basedir, file)):
            return None
        return media_read_file(source_map.basedir, file)
    except (OSError, KeyError):
        return None


def universe_system_key(universe_seed, i, j):
    """Stable per-sector seed derived from the universe seed and logical coords.

    Uses the same position-keyed mix as the scatter lattice, so a sector's
    terrain is reproducible and independent of any other sector.
    """
    return scatter._mix(int(universe_seed), int(i), int(j))


# --- Multi-cell coordinate slots (Model A) -----------------------------------
# The galaxy is endless: a cell's identity (i, j) is unbounded and used for seed
# / save / map. But the sim's usable space is bounded (~+-1M before float
# precision + radar bleed bite), so cells CANNOT sit at (i*spacing, j*spacing) -
# a cell at i=100 would be 25M units out. Identity is therefore decoupled from
# position: a live cell is assigned a transient SLOT (a world origin inside the
# budget) when it spawns and frees it when it despawns. Only ~30-50 cells are
# ever live at once, so a bounded pool of slots covers it. Slot 0 is the origin,
# so a single live cell reproduces today's at-origin layout exactly.
UNIVERSE_CELL_SPACING = 250_000        # center-to-center; 50k-radius cells -> ~150k gap
_UNIVERSE_MAX_LIVE_CELLS = 64          # pool size within +-1M

_cell_slot_offsets = None              # slot index -> Vec3 (nearest-first, [0] = origin)
_cell_slot_of = {}                     # (i, j) -> slot index
_cell_slot_used = set()                # allocated slot indices


def _universe_slot_offsets():
    global _cell_slot_offsets
    if _cell_slot_offsets is not None:
        return _cell_slot_offsets
    coords = [(0, 0)]
    ring = 1
    while len(coords) < _UNIVERSE_MAX_LIVE_CELLS:
        for di in range(-ring, ring + 1):
            for dj in range(-ring, ring + 1):
                if max(abs(di), abs(dj)) == ring:
                    coords.append((di, dj))
        ring += 1
    _cell_slot_offsets = [Vec3(di * UNIVERSE_CELL_SPACING, 0, dj * UNIVERSE_CELL_SPACING)
                          for (di, dj) in coords[:_UNIVERSE_MAX_LIVE_CELLS]]
    return _cell_slot_offsets


def universe_cell_origin(i, j):
    """World-space origin (Vec3) of live cell (i, j), allocating a slot on first
    use. Slot 0 is (0,0,0), so one live cell reproduces today's origin layout
    (Phase-0 behaviour-preserving). Endless (i,j) identity is decoupled from
    bounded world position - see the module note above."""
    slot = _cell_slot_of.get((int(i), int(j)))
    if slot is None:
        offsets = _universe_slot_offsets()
        slot = next((k for k in range(len(offsets)) if k not in _cell_slot_used), None)
        if slot is None:
            slot = 0   # pool exhausted (shouldn't happen at ~30-50 live); fall back to origin
        _cell_slot_used.add(slot)
        _cell_slot_of[(int(i), int(j))] = slot
    return _universe_slot_offsets()[slot]


def universe_cell_release(i, j):
    """Free cell (i, j)'s world slot when it despawns, so it can be reused."""
    slot = _cell_slot_of.pop((int(i), int(j)), None)
    if slot is not None:
        _cell_slot_used.discard(slot)


# --- Cell occupancy + lifecycle (Model A, Phase 2) ---------------------------
# Which occupants (player ships / admiral cams) are in each live cell. A cell
# spawns on its first occupant and despawns (clear + slot release) when the last
# one leaves, so a cell with a viewer stays resident and empty ones stop costing
# the engine. This replaces the old wipe-on-jump.
_cell_occupants = {}   # (i, j) -> set(occupant_id)

# A cell's clear-box half-extent: covers all cell content (fleets out to ~49k,
# POIs/landmarks within ~50k) with margin, while staying well inside the 250k
# slot spacing so it never reaches a neighbouring live cell.
UNIVERSE_CELL_CLEAR_R = 100_000


def universe_cell_enter(i, j, occ_id):
    """Register occ_id as present in cell (i, j) (allocating its slot). Returns
    True if the cell was empty before - the caller must then generate it."""
    key = (int(i), int(j))
    occ = _cell_occupants.get(key)
    was_empty = not occ
    if occ is None:
        occ = set()
        _cell_occupants[key] = occ
    occ.add(occ_id)
    universe_cell_origin(i, j)   # ensure a world slot is allocated
    return was_empty


def universe_cell_leave(i, j, occ_id):
    """Remove occ_id from cell (i, j). Returns True if the cell is now empty
    (the caller should clear + release it)."""
    key = (int(i), int(j))
    occ = _cell_occupants.get(key)
    if not occ:
        return True
    occ.discard(occ_id)
    if occ:
        return False
    _cell_occupants.pop(key, None)
    return True


def universe_clear_cell(i, j):
    """Despawn a cell's content (terrain + NPCs; players excluded via broad_type)
    and free its world slot. Scoped to the cell's box, so other live cells are
    untouched - unlike the legacy universe_clear_system 1M box."""
    co = universe_cell_origin(i, j)
    r = UNIVERSE_CELL_CLEAR_R
    delete_objects_box(co.x, co.y, co.z, r, r, r, broad_type=0x1F)
    universe_cell_release(i, j)


def ship_cell(ship_id):
    """The (i, j) cell a ship is currently in (defaults to (0, 0))."""
    return (get_inventory_value(ship_id, "universe_cell_i", 0),
            get_inventory_value(ship_id, "universe_cell_j", 0))


def ship_set_cell(ship_id, i, j):
    """Record which cell a ship is in (used by the per-ship jump + nav console)."""
    set_inventory_value(ship_id, "universe_cell_i", int(i))
    set_inventory_value(ship_id, "universe_cell_j", int(j))


def universe_cell_live(i, j):
    """True if cell (i, j) is currently instantiated (has at least one occupant).
    A cell despawns when its last occupant leaves, so this is the per-cell answer
    to 'are we still here?' that replaces the old `== universe_i` global check."""
    return (int(i), int(j)) in _cell_occupants


def universe_live_cells():
    """The (i, j) of every currently instantiated cell. The economy tick snapshots
    each live cell's worldlets/platforms to its OWN sector delta, instead of dumping
    whatever role("worldlet") returns (all cells at once) into the global (i, j)."""
    return list(_cell_occupants.keys())


def universe_cell_at_pos(x, z):
    """Which live cell's box a world position falls in, as (i, j). Slots are 250k
    apart and each cell's box is +/-100k, so the boxes never overlap - the answer
    is unambiguous. Defaults to (0, 0) (slot 0 = origin) if no live cell matches,
    which keeps the single-cell case behaviour-preserving. Lets a route/watch that
    holds an OBJECT (a station, a wreck) derive that object's cell from where it
    sits, without every spawn having to be tagged."""
    r = UNIVERSE_CELL_CLEAR_R
    for (i, j) in _cell_slot_of.keys():
        o = universe_cell_origin(i, j)
        if abs(x - o.x) <= r and abs(z - o.z) <= r:
            return (i, j)
    return (0, 0)


def object_cell(obj_id):
    """The (i, j) cell an object is in, derived from its world position (see
    universe_cell_at_pos). Use for objects without a ship cell tag - stations,
    wrecks, worldlets. Returns (0, 0) if the object is gone."""
    obj = to_object(obj_id)
    if obj is None:
        return (0, 0)
    p = obj.pos
    return universe_cell_at_pos(p.x, p.z)


def objects_in_cell(objs, i, j):
    """Filter an object list to those physically inside cell (i, j)'s box. This is
    how an UNBOUNDED role query (role("raider"), role("__player__")) is confined to
    one cell now that several are live at once - a radius-bounded closest() is
    already cell-safe (cells are 250k apart), but a bare role enumeration spans
    them all. Pass to_object_list(role(...))."""
    o = universe_cell_origin(i, j)
    r = UNIVERSE_CELL_CLEAR_R
    out = []
    for obj in objs:
        if obj is None:
            continue
        p = obj.pos
        if abs(p.x - o.x) <= r and abs(p.z - o.z) <= r:
            out.append(obj)
    return out


def universe_generate_system(universe_seed, i, j, terrain_value=2):
    """Spawn a sector's keyed asteroid/nebula field at the cell's live slot.

    Pure function of (universe_seed, i, j): the same sector always regenerates
    the same field. Features (stations, enemies, anomalies) come in a later step.
    """
    key = universe_system_key(universe_seed, i, j)
    r = UNIVERSE_SYSTEM_R
    co = universe_cell_origin(i, j)
    # Nebula clouds are the heaviest terrain for the engine to transmit, so the
    # per-cell chance is kept low (dialled down from 0.0012). Ramp back up if the
    # universe wants thicker nebulae and the client can carry them.
    nebula_chance = terrain_value * 0.0004
    asteroid_chance = terrain_value * 0.0010
    # marker=False: no per-nebula map markers in the universe (they clutter /
    # misbehave on the galaxy-scale map; the field itself is enough).
    # Position-keyed field: offsetting the box to the cell's slot shifts which
    # window of the (key-seeded) field shows, so a cell's asteroid pattern can
    # differ by slot across visits - acceptable (flavor). Slot 0 = origin, so
    # single-cell is unchanged; identity content is key-seeded + co-translated.
    # SOWED. This is the worst burst in the game: unlike a map, it happens
    # MID-FLIGHT, every time the players jump, so the hitch lands while they are
    # actually flying. Sowing spreads it over ~5 seconds, ordered outward from the
    # cell origin where the players arrive - so their immediate surroundings are
    # right at once and the rest fills in beyond radar range. The keyed spawner
    # re-seeds per cell and restores the RNG, so the field is identical either way.
    terrain_sow_begin(over=5, focus=co)
    terrain_spawn_field_keyed(key, 1000, co.x - r, co.z - r, co.x + r, co.z + r, terrain_value,
                              nebula_chance, asteroid_chance, marker=False)
    terrain_sow_end()


def universe_clear_system():
    """Remove the current sector's terrain and NPCs, keeping player ships.

    broad_type 0x1F = terrain (0x0f) + NPC (0x10); PLAYER (0x20) is excluded, so
    the player ships survive the jump while everything else is despawned.
    """
    # Drop terrain still queued for the system we are LEAVING. Without this, a jump
    # taken before the sow finished would keep creating the old sector's asteroids
    # into the new one, after the delete below has already run.
    terrain_sow_reset()
    delete_objects_box(0, 0, 0, 1_000_000, 1_000_000, 1_000_000, broad_type=0x1F)


def universe_reposition_players():
    """Place player ships back near the origin after arriving in a new sector."""
    players = to_object_list(role("__player__"))
    n = max(1, len(players))
    for idx, p in enumerate(players):
        ang = (idx / n) * 2.0 * math.pi
        p.pos = Vec3(2000.0 * math.cos(ang), 0.0, 2000.0 * math.sin(ang))


# --- Persistence (procedural + delta) ---------------------------------------
# The base universe regenerates from the seed; only player-made changes are stored,
# under data/missions/common_data. The active save is keyed by the loaded UNIVERSE + a
# SLOT (universe_set_active_save), so different universes - and different missions that
# load this engine - never share a save, and one universe can hold several campaigns.
_ACTIVE_SAVE = "default_1"


def _universe_save_slug(text):
    """A filename-safe slug: lowercased, each run of non-alphanumerics collapsed to one _."""
    out = []
    prev_us = False
    for ch in str(text).lower():
        if ch.isalnum():
            out.append(ch)
            prev_us = False
        elif not prev_us:
            out.append("_")
            prev_us = True
    return "".join(out).strip("_") or "x"


def universe_set_active_save(universe, slot=1):
    """Select which save file the universe store reads/writes, keyed by the loaded UNIVERSE
    and a SLOT. Call once at load, BEFORE universe_load()."""
    global _ACTIVE_SAVE
    try:
        slot = int(float(slot))
    except (TypeError, ValueError):
        pass
    _ACTIVE_SAVE = _universe_save_slug(universe) + "_" + _universe_save_slug(slot)


def universe_save_path():
    """Path to the ACTIVE universe save file (per-universe + per-slot), creating
    common_data if needed. See universe_set_active_save."""
    common = os.path.join(os.path.dirname(get_mission_dir()), "common_data")
    os.makedirs(common, exist_ok=True)
    return os.path.join(common, "universe_save_" + _ACTIVE_SAVE + ".yaml")


def _universe_store():
    """The versioned save store (schema/migrate/merge/backup live in the library
    sbs_utils.procedural.persistence; this file owns only the path + schema)."""
    return PersistentStore(universe_save_path(), version=UNIVERSE_SAVE_VERSION,
                           migrations=_MIGRATIONS, fmt="yaml")


def universe_save_state(data):
    """Write the full save dict (low-level), stamped with the current version."""
    _universe_store().save(data)


def universe_save_diplomacy(diplomacy):
    """Persist the per-pair diplomacy deltas (merges into the save)."""
    _universe_store().update(diplomacy=diplomacy)


def universe_migrate(data):
    """Bring a loaded save up to UNIVERSE_SAVE_VERSION via the migration ladder.
    Delegates to the store; only stored deltas are migrated (procedural content
    regenerates from the seed). Newer-than-build -> unchanged; failure -> None
    (callers treat as New Game)."""
    return _universe_store().migrate(data)


def universe_save(seed, i, j, systems):
    """Persist the universe seed, current sector, and delta map.

    Merges into the existing save so the players/side_credits sections (written
    by universe_save_players) are preserved.
    """
    _universe_store().update(universe_seed=seed, current_system=[i, j], systems=systems)


# --- Player / economy persistence -------------------------------------------
# Items are per-ship (counts); credits are a shared per-side pool (the future
# admiral / RTS console will own more of this economy). Keyed by ship name /
# side key, which are stable across reloads (runtime ids are not).
UNIVERSE_START_CREDITS = 500


def _item_keys():
    return [l.get_inventory_value("key") for l in labels_get_type("item/")]


def _item_label(key):
    for l in labels_get_type("item/"):
        if l.get_inventory_value("key") == key:
            return l
    return None


# Quests persist alongside items: per-ship quests by ship name, plus the
# shared/game quest tree. NESTED arcs are serialized in full (a `children` dict
# per record) - a narrative arc like `beacon_arc/ep1_go` (Storm's Beacon) is a
# quest TREE, not a flat list, so a flat serialize dropped every arc step and a
# flat restore re-added the childless PARENT over the freshly-granted tree,
# wiping the steps (the arc reverted to nothing on Continue). Serialized fields
# are YAML-safe (state/progress are ints, data is the AMD yaml dict). Old flat
# saves (no `children` key) restore unchanged.
def _serialize_quest_children(children):
    out = {}
    for qid, q in (children or {}).items():
        out[qid] = {
            "display_text": q.get("display_text", ""),
            "description": q.get("description", ""),
            "state": int(q.get("state", 0) or 0),
            "data": q.get("data"),
            "progress": q.get("progress", 0),
            "children": _serialize_quest_children(q.get("children")),
        }
    return out


def _serialize_quests(agent_id):
    tree = quest_agent_quests(agent_id)
    if tree is None:
        return {}
    return _serialize_quest_children(tree.get("children"))


def _restore_quests(agent_id, quests, _prefix=""):
    # Restore runs AFTER quest_grant_amd has (re)built the authored tree, so it
    # MERGES saved progress onto that tree rather than replacing nodes: a saved
    # node updates the granted node's state/progress in place; only a saved node
    # the grant didn't produce is created fresh. This is what recovers an OLD
    # flat save (parent only, no `children`) - quest_add would re-add a childless
    # parent over the granted arc and wipe its steps; a merge leaves the granted
    # steps intact. Recurses top-down so parents exist before their children.
    if not isinstance(quests, dict):
        return
    for qid, rec in quests.items():
        full = _prefix + qid
        if quest_get(agent_id, full) is None:
            quest_add(agent_id, full, rec.get("display_text", ""),
                      rec.get("description", ""), state=rec.get("state", 0),
                      data=rec.get("data"))
        else:
            quest_set_key(agent_id, full, "state", rec.get("state", 0))
        prog = rec.get("progress", 0)
        if prog:
            quest_set_key(agent_id, full, "progress", prog)
        kids = rec.get("children")
        if kids:
            _restore_quests(agent_id, kids, _prefix=full + "/")


def universe_save_players():
    """Persist per-ship items/installs/quests, shared credits, and game quests."""
    data = universe_load() or {}
    players = {}
    side_credits = {}
    for ship in to_object_list(role("__player__")):
        items = {}
        for k in _item_keys():
            c = get_inventory_value(ship.id, k, 0)
            if c:
                items[k] = c
        installs = get_inventory_value(ship.id, "installs", [])
        players[ship.name] = {"items": items, "installs": list(installs),
                              "quests": _serialize_quests(ship.id),
                              "reputation": get_inventory_value(ship.id, "reputation", {})}
        side = ship.side
        if side:
            side_credits[side] = get_inventory_value(to_side_id(side), "credits", 0)
    data["players"] = players
    data["side_credits"] = side_credits
    # Admiralty economy (worldlets/research - additive, no migration needed):
    # per-side stockpiles + completed research, straight off the side agent's
    # inventory so this stays self-contained (see universe_worldlets.py).
    side_adm = {}
    for side in side_credits:
        sid = to_side_id(side)
        if get_inventory_value(sid, "adm_seeded", False):
            side_adm[side] = {
                "pools": {r: get_inventory_value(sid, "adm_" + r, 0)
                          for r in ("ore", "gas", "crew")},
                "research": list(get_inventory_value(sid, "adm_research", []) or []),
                "fleets": list(get_inventory_value(sid, "adm_fleets", []) or []),
                "officers": dict(get_inventory_value(sid, "adm_officers", {}) or {}),
                "subsidy": float(get_inventory_value(sid, "market_subsidy", 0.0) or 0.0),
            }
    data["side_admiralty"] = side_adm
    data["shared_quests"] = _serialize_quests(Agent.SHARED_ID)
    universe_save_state(data)


def universe_load_players(restore=True):
    """Restore per-ship items/installs + per-side credits; re-apply installs.

    New universes (no save) start each player side at UNIVERSE_START_CREDITS.
    restore=False (a New Game with an old save on disk) initializes the same
    way but ignores the saved campaign - without it, the previous campaign's
    credits/items/admiralty would leak into the fresh one. The caller's
    baseline universe_save_players then overwrites the stale sections."""
    data = (universe_load() or {}) if restore else {}
    players = data.get("players", {})
    side_credits = data.get("side_credits", {})
    seen_sides = set()
    _restore_quests(Agent.SHARED_ID, data.get("shared_quests"))
    side_adm = data.get("side_admiralty", {})
    for ship in to_object_list(role("__player__")):
        side = ship.side
        if side and side not in seen_sides:
            set_inventory_value(to_side_id(side), "credits",
                                side_credits.get(side, UNIVERSE_START_CREDITS))
            # Admiralty stockpiles + research (marks the side seeded so
            # admiralty_seed_pools won't re-seed a restored campaign).
            adm = side_adm.get(side)
            if adm:
                sid = to_side_id(side)
                set_inventory_value(sid, "adm_seeded", True)
                for r, v in (adm.get("pools") or {}).items():
                    set_inventory_value(sid, "adm_" + r, int(v))
                set_inventory_value(sid, "adm_research", list(adm.get("research") or []))
                # Fleets rebuild from this on the first enter_system
                # (universe_fleets.admiralty_fleets_respawn); officer fates ride along.
                set_inventory_value(sid, "adm_fleets", list(adm.get("fleets") or []))
                set_inventory_value(sid, "adm_officers", dict(adm.get("officers") or {}))
                set_inventory_value(sid, "market_subsidy", float(adm.get("subsidy") or 0.0))
            seen_sides.add(side)
        pdata = players.get(ship.name)
        if not pdata:
            continue
        for k, c in pdata.get("items", {}).items():
            set_inventory_value(ship.id, k, c)
        installs = pdata.get("installs", [])
        set_inventory_value(ship.id, "installs", installs)
        for k in installs:
            lbl = _item_label(k)
            if lbl is not None:
                upgrade_add(ship.id, lbl, data={"key": k}, activate=True)
        _restore_quests(ship.id, pdata.get("quests"))
        set_inventory_value(ship.id, "reputation", pdata.get("reputation", {}))


def universe_load():
    """Load the saved universe (migrated to the current version), or None.
    Backs up once before an upgrading migration (universe_save.yaml.bak)."""
    return _universe_store().load()


def universe_system_flag(systems, i, j, flag):
    """True if a per-sector delta flag (e.g. station_destroyed) is set."""
    if not isinstance(systems, dict):
        return False
    s = systems.get(f"{i},{j}")
    return bool(s.get(flag)) if isinstance(s, dict) else False


def universe_set_system_flag(systems, i, j, flag, value=True):
    """Set a per-sector delta flag; returns the (possibly new) systems dict."""
    return universe_set_system_value(systems, i, j, flag, value)


def universe_system_value(systems, i, j, field, default=None):
    """Read an arbitrary per-sector delta field (e.g. market stock)."""
    if not isinstance(systems, dict):
        return default
    s = systems.get(f"{i},{j}")
    return s.get(field, default) if isinstance(s, dict) else default


def universe_set_system_value(systems, i, j, field, value):
    """Set an arbitrary per-sector delta field; returns the systems dict."""
    if not isinstance(systems, dict):
        systems = {}
    k = f"{i},{j}"
    s = systems.get(k)
    if not isinstance(s, dict):
        s = {}
    s[field] = value
    systems[k] = s
    return systems


# --- Sector quests (deterministic givers) ------------------------------------
# Station systems offer a deterministic cargo run whose destination is keyed to
# the giving sector, so the same station always offers the same run. The quest
# is granted to the player ship and persists (see _serialize_quests); reaching
# the destination completes it via the on_reach trigger in the quest driver.
def universe_delivery_target(seed, i, j):
    """Deterministic delivery destination sector for a station at (i,j)."""
    rng = _random.Random(universe_system_key(seed, i, j) + 99)
    di = rng.choice([-3, -2, 2, 3])
    dj = rng.choice([-3, -2, 2, 3])
    return int(i) + di, int(j) + dj


def universe_delivery_quest_id(i, j):
    return f"cargo_{int(i)}_{int(j)}"


def universe_delivery_available(ship_id, i, j):
    """True if this station's cargo run hasn't been taken/finished by the ship."""
    return quest_get_state(ship_id, universe_delivery_quest_id(i, j)) == QuestState.IDLE


def universe_grant_delivery(ship_id, seed, i, j):
    """Grant (activate) this station's deterministic cargo run to the ship.

    Returns (quest_id, target_i, target_j). Reaching the target sector completes
    it via the on_reach trigger (quest driver), paying credits.
    """
    ti, tj = universe_delivery_target(seed, i, j)
    qid = universe_delivery_quest_id(i, j)
    quest_add(ship_id, qid, f"Cargo Run to ({ti}, {tj})",
              f"Haul cargo from sector ({int(i)}, {int(j)}) to sector ({ti}, {tj}). "
              f"Engage the jump drive on Navigation to make the run.",
              state=QuestState.ACTIVE,
              data={"on_reach": {"sector": [ti, tj]}, "reward": {"credits": 400}})
    return qid, ti, tj


def universe_mystery_quest_id(i, j):
    return f"mystery_{int(i)}_{int(j)}"


def universe_mystery_available(ship_id, i, j):
    """True if this anomaly's mystery hasn't been offered to the ship yet."""
    return quest_get_state(ship_id, universe_mystery_quest_id(i, j)) == QuestState.IDLE


def universe_mystery_target(seed, i, j):
    """Deterministic sector the anomaly's signal points to."""
    rng = _random.Random(universe_system_key(seed, i, j) + 555)
    di = rng.choice([-4, -3, 3, 4])
    dj = rng.choice([-4, -3, 3, 4])
    return int(i) + di, int(j) + dj


def universe_grant_mystery(ship_id, seed, i, j):
    """Offer (activate) the anomaly's 'follow the signal' mystery to the ship.

    Reaching the target sector completes it (on_reach) for a larger payout than a
    cargo run. Returns (quest_id, target_i, target_j).
    """
    ti, tj = universe_mystery_target(seed, i, j)
    qid = universe_mystery_quest_id(i, j)
    quest_add(ship_id, qid, f"Anomaly Signal to ({ti}, {tj})",
              f"The anomaly in sector ({int(i)}, {int(j)}) is beaming a coded signal "
              f"toward sector ({ti}, {tj}). Follow it to uncover what waits there.",
              state=QuestState.ACTIVE,
              data={"on_reach": {"sector": [ti, tj]}, "reward": {"credits": 600}})
    return qid, ti, tj


def universe_quest_target_sectors():
    """(i,j) target systems of all players' ACTIVE on_reach quests (map markers)."""
    out = set()
    for ship in to_object_list(role("__player__")):
        tree = quest_agent_quests(ship.id)
        children = tree.get("children") if tree is not None else None
        for qid, q in (children or {}).items():
            if quest_get_state(ship.id, qid) != QuestState.ACTIVE:
                continue
            reach = (q.get("data") or {}).get("on_reach")
            if isinstance(reach, dict):
                sec = reach.get("sector")
                if sec and len(sec) == 2:
                    out.add((int(sec[0]), int(sec[1])))
    return out


def universe_quest_reach_sector(agent_id, qid):
    """The [ti, tj] on_reach target sector of quest `qid` on `agent_id`, or None. The LM
    Quests tab's "Engage" button emits quest_engage(agent, key); //signal/quest_engage
    resolves the target here and jumps the ship (quest-driven movement, no Nav map)."""
    # Path-aware (quest_get navigates a nested `arc/step` key via quest_folder), so a
    # jump leg authored as a child of a mission arc still resolves its on_reach target.
    q = quest_get(agent_id, qid)
    if q is None:
        return None
    data = q.get("data") or {}
    reach = data.get("on_reach")
    if isinstance(reach, dict):
        sec = reach.get("sector")
        if sec and len(sec) == 2:
            return [int(sec[0]), int(sec[1])]
    # Charted-location waypoints (universe_add_waypoint) carry a plain `waypoint`
    # sector instead of `on_reach`: Engage can travel there, but the quest driver
    # never sees it as a reach objective, so the waypoint never "completes" and
    # stays a clean, permanent nav entry (no checkmark).
    wp = data.get("waypoint")
    if wp and len(wp) == 2:
        return [int(wp[0]), int(wp[1])]
    return None


def universe_add_waypoint(agent_id, i, j, name):
    """Chart system (i, j) as a re-visitable "Charted Locations" waypoint on `agent_id`,
    so the player can jump back to it later from the Quests tab (Engage). Idempotent - a
    cell already charted is left alone. Returns True only when a NEW waypoint was added
    (so the caller can announce it once). Waypoints are children of a `waypoints` parent
    quest and carry a `waypoint` sector (not `on_reach`), so they are Engageable but never
    complete. For quest-driven-nav missions with no galaxy map (WAYPOINTS_ENABLED)."""
    i = int(i)
    j = int(j)
    # Parent container quest (created lazily on first charting; a plain active grouping
    # that folds its waypoint children in the Quests tab).
    if quest_get(agent_id, "waypoints") is None:
        quest_add(agent_id, "waypoints", "Charted Locations",
                  "Places you have been. Select one and Engage to jump back.",
                  state=QuestState.ACTIVE)
    key = "waypoints/wp_%d_%d" % (i, j)
    if quest_get(agent_id, key) is not None:
        return False
    quest_add(agent_id, key, name, "Jump back to " + name + ".",
              state=QuestState.ACTIVE, data={"waypoint": [i, j]})
    return True


# --- Sector kind + galaxy map ------------------------------------------------
# Named landmarks now come from sides (sides.amd home systems), layered onto the
# galaxy map by universe.mast. The procedural kind below is side-agnostic; side
# ownership/naming is applied on top (see universe_sides.universe_system_side).
_KIND_ABBR = {"home": "Home", "station": "Base", "enemy": "Threat",
              "nebula": "Neb", "anomaly": "!!", "empty": "."}


def universe_system_name(i, j):
    """Deprecated: procedural names removed - sides name their home systems.
    Kept (returns '') so existing callers don't break."""
    return ""


# --- Generation knobs (author-exposed; see the universe.amd `generation:` block) --
# The galaxy's shape: system-kind mix + POI-deck weights. Defaults reproduce the
# built-in generator; a universe overrides any subset via generation_configure.
# (The deck reads these via universe_generation(); the system-kind mix reads _GEN
# directly here, the hot map-render path.)
_GEN_DEFAULTS = {
    # system-kind base chances (Quiet profile); the rest of the cell is "empty".
    "station": 0.15, "enemy": 0.15, "nebula": 0.12, "anomaly": 0.08,
    # POI-deck weights (universe_systems.universe_system_deck).
    "loot_max": 2, "derelict": 0.4, "derelict_nebula": 0.7, "outpost": 0.4, "mines": 0.5,
    # Worldlets (Admiral console economy) are off unless a universe authors an
    # Admiralty chapter (its Worldlet chance dial arrives via generation_set).
    "worldlet": 0.0,
}
_GEN = dict(_GEN_DEFAULTS)
# Regions with local generation overrides (set at load by regions_configure), so a
# region can be its own warzone/haven. universe_system_kind merges a cell's region
# config over the global, keeping the map and the spawn agreeing.
_REGIONS = []
# Danger scales enemy density relative to the authored base (Quiet = base). Default
# base enemy 0.15 -> Balanced 0.25, Dangerous 0.40 (the old per-Danger enemy rates).
_DANGER_ENEMY = {"Quiet": 1.0, "Balanced": 1.67, "Dangerous": 2.67}


def generation_configure(cfg):
    """Apply a universe's `generation:` block (system mix + deck weights). Resets to
    the built-in defaults first; cfg None or missing keys -> the defaults stand."""
    global _GEN
    _GEN = dict(_GEN_DEFAULTS)
    if isinstance(cfg, dict):
        for k, v in cfg.items():
            if k in _GEN_DEFAULTS:
                _GEN[k] = v


def generation_set(name, value):
    """Set one generation knob after configure - the Admiralty chapter's
    Worldlet chance arrives this way (admiralty_configure in
    universe_worldlets.py), since it is authored outside the root fence."""
    if name in _GEN_DEFAULTS:
        _GEN[name] = value


def regions_configure(regions):
    """Register the regions whose local `generation:` overrides reshape the system
    mix within their bounds (universe_system_kind reads them)."""
    global _REGIONS
    _REGIONS = regions or []


def _gen_for_cell(i, j):
    """The generation config in effect at (i, j): a region's overrides merged over
    the global, or just the global. region_for_system is from universe_regions.py."""
    if _REGIONS:
        rgn = region_for_system(_REGIONS, i, j)
        if rgn is not None and rgn.get("generation"):
            merged = dict(_GEN)
            merged.update(rgn.get("generation"))
            return merged
    return _GEN


def universe_generation(name, i=None, j=None):
    """A generation knob's current value. With (i, j), returns the value in effect at
    that cell (a region's override merged over the global) so the deck is region-
    aware too; without, the global value."""
    g = _gen_for_cell(i, j) if i is not None else _GEN
    return g.get(name, _GEN_DEFAULTS.get(name))


def universe_generation_cfg(doc):
    """The universe root's `generation:` config block, or None (-> defaults). Fed to
    generation_configure. universe_root_node comes from universe_sides.py."""
    root = universe_root_node(doc)
    data = (root.get("data") if root is not None else None) or {}
    return data.get("generation")


def universe_system_kind(seed, i, j, danger="Quiet"):
    """The deterministic kind of any sector (pure - does not spawn anything).

    (0,0) is always home; otherwise a keyed roll against the authored system mix,
    with Danger scaling enemy density. Both the generator and the galaxy map call
    this, so what you see on the map is exactly what spawns. Side ownership/naming
    is layered on top in universe.mast.
    """
    i = int(i)
    j = int(j)
    if i == 0 and j == 0:
        return "home"
    roll = scatter.cell_roll(seed, 1, i, j, 7)
    g = _gen_for_cell(i, j)
    t_station = g["station"]
    t_enemy = g["enemy"] * _DANGER_ENEMY.get(danger, 1.0)
    t_nebula = g["nebula"]
    t_anomaly = g["anomaly"]
    if roll < t_station:
        return "station"
    if roll < t_station + t_enemy:
        return "enemy"
    if roll < t_station + t_enemy + t_nebula:
        return "nebula"
    if roll < t_station + t_enemy + t_nebula + t_anomaly:
        return "anomaly"
    return "empty"


def universe_cell_known(systems, i, j, reveal):
    """A galaxy-map cell's contents are known if the chart is full, the crew has
    visited it, or a Sensor Relay has sensed it (universe_reveal_neighbors)."""
    return (reveal == "Full Chart"
            or universe_system_flag(systems, i, j, "visited")
            or universe_system_flag(systems, i, j, "sensed"))


def universe_reveal_neighbors(systems, i, j):
    """Mark a system and its 8 neighbours 'sensed' in the systems delta - the
    intel a Sensor Relay built here provides (galaxy-map contents shown without a
    visit). Returns the (possibly new) systems dict."""
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            systems = universe_set_system_flag(systems, i + di, j + dj, "sensed")
    return systems


def universe_map_cell_text(seed, i, j, danger, systems, reveal):
    """Short label for a galaxy-map cell.

    Named POIs always show; otherwise cells that aren't known (visited, sensed,
    or Full Chart) read '?' under fog of war.
    """
    name = universe_system_name(i, j)
    if name:
        return name
    if not universe_cell_known(systems, i, j, reveal):
        return "?"
    return _KIND_ABBR.get(universe_system_kind(seed, i, j, danger), ".")
