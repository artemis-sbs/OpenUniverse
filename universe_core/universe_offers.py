"""Open Universe offers: the work in this system that nobody has taken.

This is the gap the Offers board exists to close. An OU station job is not a quest until
you ACCEPT it - ``universe_grant_side_job`` calls ``quest_add(..., state=ACTIVE)`` at the
moment of acceptance - so an untaken job existed nowhere a crew could look. The only way
to learn it was there was to hail that particular station and read its button list.

Nothing is stored here. Every row is recomputed from the same functions the comms route
calls, so the board can never disagree with the buttons: a job whose tier your standing
has not unlocked is absent from both, and a reward that moves with standing moves in both.
That is the whole reason offers are computed rather than granted - see
``sbs_utils.procedural.offer``.

Prefixed `universe_` like the rest of universe_core: every top-level def in an addon
becomes a MAST global in one flat, mission-wide namespace.
"""
from sbs_utils.procedural.execution import get_shared_variable
from sbs_utils.procedural.offer import offer_record
from sbs_utils.procedural.query import to_id, to_object, to_object_list, get_side
from sbs_utils.procedural.roles import role, has_role
from sbs_utils.procedural.quest import quest_get_state

# NOTE: no sibling imports. Mission .py files are loaded by __init__.mast into ONE
# shared engine namespace - they are not a package, so `from universe_helpers import
# ship_cell` both fails to compile in-engine AND, off-engine, would build a SECOND
# module whose own free globals (sides_standing, side_reward_mult, ...) are undefined,
# so universe_side_work_offers would raise NameError at call time. ship_cell,
# universe_side_work_offers, universe_delivery_available, universe_delivery_target,
# universe_passengers_at and universe_waiting_gone are already in the namespace because
# __init__.mast imports those files before this one. Only absolute `sbs_utils...`
# imports are valid here.


#: What a station's comms path is called, so a row can say where to go without the board
#: needing to know anything about Open Universe.
_WHERE = "Comms - hail {name}"


def _station_name(obj):
    return getattr(obj, "name", None) or "a station"


def _stations_here():
    """The stations that currently exist.

    The ENGINE clears NPCs on a jump, so what is spawned IS this system - there is no
    per-cell filter to apply and applying one would be inventing a second source of
    truth. A station that somehow outlived its cell would show up, and that is a spawn
    bug worth seeing rather than hiding.
    """
    return to_object_list(role("station"))


def universe_station_offers(ship_id, station):
    """Everything this one station is offering this captain, as offer records."""
    if station is None or ship_id in (None, 0):
        return []
    sides = get_shared_variable("UNIVERSE_SIDES", None)
    side_quests = get_shared_variable("UNIVERSE_SIDE_QUESTS", None)
    lifeforms = get_shared_variable("UNIVERSE_LIFEFORMS", None)
    seed = get_shared_variable("universe_seed", 0)
    if sides is None:
        return []

    sid = to_id(station)
    name = _station_name(station)
    where = _WHERE.format(name=name)
    cell = ship_cell(ship_id)
    h_i, h_j = cell[0], cell[1]
    out = []

    # --- side work ------------------------------------------------------------
    # The same call the comms route makes, so tier gating and standing-scaled rewards
    # are identical rather than merely similar.
    station_side = get_side(sid)
    if station_side is not None and side_quests is not None:
        for o in universe_side_work_offers(ship_id, sides, station_side, side_quests):
            # Already taken (or already running) is not an offer.
            if quest_get_state(ship_id, o.get("key")) != 0:
                continue
            out.append(offer_record(
                key=f"ou:{sid}:{o.get('key')}",
                title=str(o.get("title") or o.get("type")),
                detail=f"{o.get('credits')} cr",
                kind="job", source=name, agent_id=sid, where=where,
                route="//comms", sort=20,
                data={"job_side": o.get("side"), "job_type": o.get("type")},
            ))

    # NO try/except AROUND THE REST. offer._run_provider already catches, names the
    # exception type and reports it once - swallowing here would turn a real fault into
    # a board that is quietly missing rows, which is the failure this whole feature
    # exists to stop.

    # --- cargo ----------------------------------------------------------------
    if universe_delivery_available(ship_id, h_i, h_j):
        t = universe_delivery_target(seed, h_i, h_j)
        out.append(offer_record(
            key=f"ou:{sid}:cargo:{h_i}:{h_j}",
            title="Cargo Run",
            detail=f"to ({t[0]}, {t[1]})",
            kind="trade", source=name, agent_id=sid, where=where,
            route="//comms", sort=30,
        ))

    # --- passengers -----------------------------------------------------------
    for pax in (universe_passengers_at(lifeforms, h_i, h_j) or []):
        key = "passenger_" + str(pax.get("key"))
        if quest_get_state(ship_id, key) != 0:
            continue
        if universe_waiting_gone(ship_id, pax.get("key")):
            continue               # their patience ran out; the berth is not on offer
        to_ij = pax.get("deliver_to")
        out.append(offer_record(
            key=f"ou:{sid}:{key}",
            title=f"Transport {pax.get('name')}",
            detail=f"{pax.get('pays')} cr to ({to_ij[0]}, {to_ij[1]})",
            kind="contact", source=name, agent_id=sid, where=where,
            route="//comms", sort=40,
        ))

    return out


def universe_offer_provider(ctx):
    """The `universe` offer provider. Registered from universe.mast.

    Answers BOTH questions the registry can ask: with an `object_id` it reports what that
    one station has (which is what a comms selection title or a science scan reads), and
    without one it reports the whole system.
    """
    ship_id = ctx.get("ship_id")
    if not ship_id:
        return []
    if not get_shared_variable("UNIVERSE_ACTIVE", False):
        return []
    object_id = ctx.get("object_id")
    if object_id is not None:
        obj = to_object(object_id)
        if obj is None or not has_role(object_id, "station"):
            return []
        return universe_station_offers(ship_id, obj)
    out = []
    for station in _stations_here():
        out.extend(universe_station_offers(ship_id, station))
    return out


def universe_offers_register():
    """Install the provider. Called once from universe.mast's top level."""
    from sbs_utils.procedural.offer import offer_register
    offer_register("universe", universe_offer_provider, domain="universe")
    return True
