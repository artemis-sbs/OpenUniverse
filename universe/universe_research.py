"""Milestone research + the Requisition catalog for the Admiral console
(slice 2 - see ADMIRAL_CONSOLE.md sections 7 and 10).

Research is a ladder of authored milestones (`## Research` in the universe
AMD): each has a branch, resource Costs, a Time, an optional Requires
prerequisite, and plain-English Unlocks phrases. One research runs at a time
per side (at a Shipyard); completed milestone keys persist in the universe
save. Effects are computed lazily from the completed set, so restoring a
save restores the effects for free:

  storage N          -> +N on every stockpile cap
  extraction N%      -> all extractors run N% faster
  requisition <key>  -> the item joins the Requisition catalog

Requisition converts Admiralty resources into a real item (the LM item
registry) delivered beside the player ships - research reaching the bridge
crews, per the section-1 rule.

Shared-namespace notes: universe_section comes from universe_clans.py;
admiralty_* pool/tuning calls come from universe_worldlets.py.
"""
from sbs_utils.mast.mast_node import MastDataObject
from sbs_utils.procedural.inventory import get_inventory_value, set_inventory_value
from sbs_utils.procedural.sides import to_side_id
from sbs_utils.procedural.roles import role
from sbs_utils.procedural.query import to_object_list
from sbs_utils.procedural.gui import gui_row, gui_text

_RESEARCH = {}        # key -> record, insertion-ordered (the authored ladder)


def universe_parse_research(doc):
    """Milestone records from the `## Research` chapter (empty if none)."""
    section = universe_section(doc, "research")
    out = []
    if section is not None:
        for n in section.get("children", []):
            data = n.get("data") or {}
            out.append(MastDataObject({
                "key": n.get("key"),
                "name": n.get("display_text"),
                "desc": (n.get("description") or "").strip(),
                "branch": data.get("branch") or "general",
                "costs": data.get("costs") or {},
                "time": data.get("time") or 30,
                "requires": data.get("requires"),
                "unlocks": data.get("unlocks") or [],
            }))
    return out


def research_configure(items):
    """Register the authored ladder for this universe load."""
    global _RESEARCH
    _RESEARCH = {r.get("key"): r for r in (items or [])}


def research_def(key):
    return _RESEARCH.get(key)


def research_list():
    return list(_RESEARCH.values())


# --- Per-side state (side-agent inventory; persisted in the universe save) ----
def research_done(side):
    return list(get_inventory_value(to_side_id(side), "adm_research", []) or [])


def research_has(side, key):
    return key in research_done(side)


def research_current(side):
    return get_inventory_value(to_side_id(side), "adm_researching", None)


def research_state(side, key):
    """'done' / 'researching' / 'available' / 'locked' for the Research tab."""
    r = _RESEARCH.get(key)
    if r is None:
        return "locked"
    if research_has(side, key):
        return "done"
    if research_current(side) == key:
        return "researching"
    req = r.get("requires")
    if req and not research_has(side, req):
        return "locked"
    return "available"


def research_try_start(side, key):
    """Validate + pay for a milestone. Returns None on success (the caller
    schedules the research task) or a short reason string."""
    r = _RESEARCH.get(key)
    if r is None:
        return "Unknown research."
    if research_has(side, key):
        return "Already researched."
    cur = research_current(side)
    if cur:
        cdef = _RESEARCH.get(cur)
        return "Already researching " + (cdef.get("name") if cdef else cur) + "."
    req = r.get("requires")
    if req and not research_has(side, req):
        rdef = _RESEARCH.get(req)
        return "Requires " + (rdef.get("name") if rdef else req) + "."
    if len(to_object_list(role("admiral_shipyard") & role(side))) == 0:
        return "Requires a Shipyard."
    if not admiralty_spend(side, r.get("costs")):
        return "Not enough resources (" + research_costs_text(key) + ")."
    set_inventory_value(to_side_id(side), "adm_researching", key)
    return None


def research_complete(side, key):
    """Finish a milestone: record it (effects apply lazily from the set)."""
    sid = to_side_id(side)
    if get_inventory_value(sid, "adm_researching", None) == key:
        set_inventory_value(sid, "adm_researching", None)
    done = research_done(side)
    if key not in done:
        done.append(key)
        set_inventory_value(sid, "adm_research", done)


def research_costs_text(key):
    r = _RESEARCH.get(key) or {}
    costs = r.get("costs") if hasattr(r, "get") else {}
    return ", ".join(str(v) + " " + k for k, v in (costs or {}).items())


# --- Effects (computed from the completed set) ---------------------------------
def _done_unlocks(side):
    for key in research_done(side):
        r = _RESEARCH.get(key)
        if r is None:
            continue
        for phrase in (r.get("unlocks") or []):
            yield str(phrase).strip().lower()


def research_storage_bonus(side):
    """Sum of 'storage N' unlocks."""
    total = 0
    for phrase in _done_unlocks(side):
        toks = phrase.split()
        if toks and toks[0] == "storage" and len(toks) > 1 and toks[1].isdigit():
            total += int(toks[1])
    return total


def research_extraction_mult(side):
    """1.0 plus every 'extraction N%' unlock."""
    mult = 1.0
    for phrase in _done_unlocks(side):
        toks = phrase.replace("%", " ").split()
        if toks and toks[0] == "extraction" and len(toks) > 1:
            try:
                mult += float(toks[1]) / 100.0
            except ValueError:
                pass
    return mult


def research_requisition_unlocks(side):
    """Item keys added to the catalog by 'requisition <key>' unlocks."""
    out = []
    for phrase in _done_unlocks(side):
        toks = phrase.split()
        if len(toks) >= 2 and toks[0] == "requisition":
            out.append(toks[1])
    return out


# --- Requisition catalog ---------------------------------------------------------
# Base catalog = the original LM upgrade items ("include the originals").
# Research 'requisition <key>' unlocks append to it. Costs are Admiralty
# resources; delivery is a real item beside the player ships.
_REQ_BASE = [
    ("carapaction_coil", "Carapaction Coil", {"ore": 80, "gas": 30}),
    ("infusion_pcoils", "Infusion P-Coils", {"ore": 60, "gas": 50}),
    ("hidens_powercell", "HiDens Powercell", {"ore": 40, "gas": 60}),
]
_REQ_UNLOCKABLE = {
    "tauron_focuser": ("Tauron Focuser", {"ore": 150, "gas": 80, "crew": 5}),
    "haplix_overcharger": ("Haplix Overcharger", {"ore": 150, "gas": 100, "crew": 5}),
}


def requisition_catalog(side):
    """[(key, name, costs)] available to this side right now."""
    out = list(_REQ_BASE)
    for key in research_requisition_unlocks(side):
        entry = _REQ_UNLOCKABLE.get(key)
        if entry is not None and all(k != key for k, _, _ in out):
            out.append((key, entry[0], entry[1]))
    return out


def requisition_entry(side, key):
    for k, name, costs in requisition_catalog(side):
        if k == key:
            return (k, name, costs)
    return None


def requisition_costs_text(side, key):
    entry = requisition_entry(side, key)
    if entry is None:
        return ""
    return ", ".join(str(v) + " " + k for k, v in entry[2].items())


# --- Console listbox templates (admiral.mast) ------------------------------------
def research_list_title():
    gui_row("row-height: 1.2em;padding:6px;background:#1578;")
    gui_text("$text:Research milestones")


def research_list_template(item):
    state = research_state("tsn", item.get("key"))
    line = str(item.get("name")) + "  [" + str(item.get("branch")) + "]  -  " + state
    gui_row("row-height: 2.2em;")
    gui_text("$text:" + line + ";font:gui-1")


def requisition_catalog_items(side):
    """The catalog as listbox items (key/name/costs_text)."""
    out = []
    for key, name, costs in requisition_catalog(side):
        out.append(MastDataObject({
            "key": key, "name": name,
            "costs_text": ", ".join(str(v) + " " + k for k, v in costs.items())}))
    return out


def requisition_list_title():
    gui_row("row-height: 1.2em;padding:6px;background:#1578;")
    gui_text("$text:Requisition catalog")


def requisition_list_template(item):
    gui_row("row-height: 2.2em;")
    gui_text("$text:" + str(item.get("name")) + "   (" + str(item.get("costs_text")) + ");font:gui-1")


def requisition_try_deliver(side, key):
    """Validate + pay for a requisition. Returns None on success (the caller
    spawns the item and tells the crews) or a short reason string."""
    entry = requisition_entry(side, key)
    if entry is None:
        return "Not in the catalog."
    if len(to_object_list(role("admiral_hq") & role(side))) == 0:
        return "Requires a Headquarters."
    if not admiralty_spend(side, entry[2]):
        return "Not enough resources (" + requisition_costs_text(side, key) + ")."
    return None
