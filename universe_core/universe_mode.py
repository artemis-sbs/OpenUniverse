"""Mission-shape Mode gate (the keystone `Mode` dial - see FOUNDATION_PLAN.md).

Extracted from universe_worldlets.py in Phase 2b (the universe_core / admiral mastlib
split) so a CORE-ONLY mission (a `story`/`campaign` universe that does NOT load the
admiral economy addon) still has mission_mode() and admiralty_active().

Loading the addon is not enough to wake it. `story` never runs the Admiral; `campaign`
runs it only when the universe file has its own `## Admiralty` chapter (MODE_PRESETS);
and in every Mode it needs `## Worldlets` types as well.

The split's invariant: **admiralty_active() can only be True when the `admiral` addon
is loaded** (the addon calls universe_mode_mark_admiral_present() at load) AND the
active Mode's preset allows the RTS AND the universe authored admiral content (worldlet
types). Every admiral call-site left in core files sits behind admiralty_active() or
admiral_present(), so a core-only load never evaluates a missing admiral symbol.

Shared-namespace note (like the other universe_*.py files): universe_section comes
from universe_sides.py; no relative sibling imports.
"""

# Mission-shape presets (the `Mode` dial). Each preset provides DEFAULTS for a few
# dials; a dial the author sets explicitly always wins. `admiral` gates whether the RTS
# economy runs at all:
#   True        the Mode permits it (it still needs the admiral addon and worldlet types)
#   False       never - a `story` mission runs none even if the chapters are present
#   "optional"  only when the universe file has its OWN `## Admiralty` chapter. This is
#               `campaign`: a persistent single-ship epic by default, and the same epic
#               with an Admiral beside the bridge crew when the author writes the chapter.
#               A `## Scenario` chapter alone does not count, and neither does a
#               `## Worldlets` chapter alone.
# The economy_pace / skirmish_pressure defaults are consumed by the admiral addon
# (universe_worldlets.admiralty_configure) when it is loaded.
MODE_PRESETS = {
    "sandbox":  {"admiral": True,  "economy_pace": "standard", "skirmish_pressure": "border"},
    "skirmish": {"admiral": True,  "economy_pace": "brisk",    "skirmish_pressure": "border"},
    "war":      {"admiral": True,  "economy_pace": "epic",     "skirmish_pressure": "border"},
    "campaign": {"admiral": "optional", "economy_pace": "epic", "skirmish_pressure": "off"},
    "story":    {"admiral": False, "economy_pace": "standard", "skirmish_pressure": "off"},
}

# Live per-load state (reset by universe_mode_configure on universe load).
_MODE = "sandbox"
_MODE_ALLOWS_ADMIRAL = True   # does the active Mode's preset permit the RTS?
_MODE_ACTIVE = False          # is the RTS actually running this load? (admiral enables)


def universe_admiralty_cfg(doc):
    """The `## Admiralty` chapter's tuning dict merged with the mission-level
    `## Scenario` `Mode:`, or None when neither is authored. Pure universe_section
    data (core-safe). The admiral addon reads the whole dict; core reads only `mode`.
    Returns non-None whenever EITHER chapter has content, so `Mode: story` alone
    (a Scenario chapter, no Admiralty) still configures the Mode.

    `own_chapter` is True in the dict when the file has a `## Admiralty` chapter of its
    own, however empty its fence is. That is what a `campaign` needs before it runs an
    Admiral (MODE_PRESETS), and it is what makes an Admiralty chapter with an empty fence
    count as "authored" in every Mode - it used to read the same as no chapter."""
    section = universe_section(doc, "admiralty")
    cfg = {}
    if section is not None:
        data = section.get("data") or {}
        cfg = dict(data.get("admiralty") or {})
        cfg["own_chapter"] = True
        gen = data.get("generation") or {}
        if "worldlet" in gen:
            cfg["worldlet_chance"] = gen["worldlet"]
    # Prefer Mode from a mission-level ## Scenario chapter (the label routes it to the
    # "admiralty" sub-dict of whatever chapter holds it; see universe_amd.py).
    scen = universe_section(doc, "scenario")
    if scen is not None:
        smode = ((scen.get("data") or {}).get("admiralty") or {}).get("mode")
        if smode is not None:
            cfg["mode"] = smode
    return cfg or None


def universe_mode_configure(cfg):
    """Resolve the active Mode from a universe's cfg dict (universe_admiralty_cfg).
    Sets mission_mode() and whether the Mode permits the RTS; leaves admiralty_active()
    False until the admiral addon enables it (universe_mode_set_admiral_active). Core
    calls this ALWAYS - it is the one piece of the old admiralty_configure that a
    core-only mission needs."""
    global _MODE, _MODE_ALLOWS_ADMIRAL, _MODE_ACTIVE
    mode = "sandbox"
    if cfg and cfg.get("mode") is not None:
        mode = str(cfg.get("mode")).strip().lower()
    _MODE = mode if mode in MODE_PRESETS else "sandbox"
    allows = MODE_PRESETS[_MODE].get("admiral", True)
    if allows == "optional":
        # campaign: the Admiral is the author's choice, made by writing the chapter.
        allows = bool(cfg and cfg.get("own_chapter"))
    _MODE_ALLOWS_ADMIRAL = bool(allows)
    _MODE_ACTIVE = False


def universe_mode_set_admiral_active(has_content):
    """The admiral addon enables the RTS for this load: active iff the Mode allows it
    (in a campaign: the file has its own Admiralty chapter - universe_mode_configure),
    the addon is present, and the universe authored admiral content (worldlet types).
    Called from the admiral addon's admiralty_configure."""
    global _MODE_ACTIVE
    _MODE_ACTIVE = bool(has_content) and _MODE_ALLOWS_ADMIRAL and admiral_present()


def admiralty_active():
    """True only when the admiral RTS economy is actually running this load (see the
    module invariant). Core gates every admiral call-site on this."""
    return _MODE_ACTIVE


def admiral_present():
    """True when the admiral economy addon is loaded. Detected by the presence of an
    admiral-defined symbol (admiralty_configure) in the SHARED MAST namespace - so it is
    INDEPENDENT of addon compile ORDER. This matters because local sibling addon folders
    are discovered alphabetically (`admiral` before `universe_core`), which is the wrong
    order for a compile-time marker; and a consumer lists mastlibs in story.json order.
    Either way, admiral_present() is only *called* at map start (universe.mast load block,
    admiralty_configure), after every addon has compiled, so the symbol is present iff the
    admiral addon loaded. A core-only mission never defines admiralty_configure -> False ->
    core skips every admiral call-site. (globals() here is the shared MastGlobals namespace:
    every universe_*.py execs into it, which is why they call each other by bare name.)"""
    return "admiralty_configure" in globals()


def mission_mode():
    """The active mission-shape Mode (sandbox | skirmish | war | campaign | story).
    The keystone dial - see FOUNDATION_PLAN.md."""
    return _MODE
