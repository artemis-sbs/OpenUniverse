"""The Open Universe's DOCUMENT layer: finding a universe's files, reading them,
splicing their sections together, and the diplomacy overrides they declare.

Split out of the file that used to be called universe_clans.py - named for one of the
things it loaded rather than for what it does. What a SIDE is lives in
universe_sides.py now; this is the plumbing under all of it.

Shared-namespace notes: OU imports each module with `import x.py` into ONE engine
namespace, so these names are global to the mission - no relative sibling imports.
"""
import os
from sbs_utils.procedural.quest import document_get_amd_file
from sbs_utils.procedural.amd_doc import (
    amd_read_content, amd_document, amd_root_node, amd_root_data,
    amd_section, amd_includes, amd_splice)
from sbs_utils.procedural.execution import labels_get_type
from sbs_utils.procedural.sides import (
    side_diplomacy_key, side_diplomacy_set, side_diplomacy_apply)
from sbs_utils.procedural.comms import comms_info_card
from sbs_utils.procedural.media import media_read_relative_file
from sbs_utils.fs import get_mission_dir_filename
from sbs_utils.agent import Agent




# --- Diplomacy deltas (persisted per side/side pair) -------------------------
# Authored defaults come from sides.amd (foe/neutral); these deltas override them
# (e.g. a negotiated ceasefire) and persist in the save. Keyed by a sorted pair.
# Per-pair diplomacy overrides now delegate to the shared sbs_utils.procedural.sides
# helpers (promoted from here); the universe_*_dip names stay for OU's mast + save layer.
def universe_dip_key(a, b):
    return side_diplomacy_key(a, b)




def universe_set_dip(dip, a, b, relation):
    """Record a per-pair relation override; returns the (possibly new) dict."""
    return side_diplomacy_set(dip, a, b, relation)




def universe_apply_dip(dip):
    """Re-apply saved per-pair relation overrides (call after sides exist)."""
    side_diplomacy_apply(dip)




# --- Universe registry (start-screen dropdown) -------------------------------
# Each universe is a label (type: universe/<key>) in universes.mast naming its
# sides/narrative AMD files. The dropdown lists them; selecting one picks which
# sides.amd (+ narrative.amd) to load.
def universe_registry():
    return labels_get_type("universe/")




def universe_options_csv():
    """Comma list of universe display names for the dropdown's list: field."""
    names = []
    for l in universe_registry():
        names.append(l.get_inventory_value("display", l.get_inventory_value("key", "Default")))
    return ", ".join(names) if names else "Default"




def _universe_field(display, field, default):
    for l in universe_registry():
        if l.get_inventory_value("display") == display or l.get_inventory_value("key") == display:
            return l.get_inventory_value(field, default)
    return default




def universe_sides_file(display):
    """The sides.amd filename for the selected universe (fallback sides.amd)."""
    return _universe_field(display, "sides", "sides.amd")




def universe_narrative_file(display):
    """The narrative.amd filename for the selected universe (fallback)."""
    return _universe_field(display, "narrative", "narrative.amd")




def universe_file(display):
    """The single merged universe.amd filename for the selected universe.

    The primary authoring format is one file holding identity + sides + jobs +
    narrative (see UNIVERSE_CHANGES.md capstone). A registry label names it with
    `universe:`. Labels that predate the merge name a split `sides:` file instead;
    fall back to that so old universes keep loading.
    """
    return _universe_field(display, "universe", None) or universe_sides_file(display)




# --- Merged universe document (one file, nested sections) --------------------
# The generic doc/section/include/splice machinery lives in the shared library now
# (sbs_utils.procedural.amd_doc); these thin wrappers bind it to the universe's title +
# data_parser and keep the universe_* names OU's mast and helpers already call.
def universe_read_content(fname):
    """Read a universe .amd file (or an include) as text: consumer mission dir first, then
    code/lib-relative (packaged-mastlib-zip aware). See amd_doc.amd_read_content."""
    return amd_read_content(fname)




def universe_doc(content):
    """Parse universe.amd (or a legacy flat sides.amd) into a document tree with the
    universe fact-sheet parser. Headings are the link form `# [Display](key)`."""
    return amd_document(content, universe_amd_data, "Universe")




def universe_root_node(doc):
    """The single level-1 universe heading node (the file's root content), or None."""
    return amd_root_node(doc)




def universe_section(doc, key):
    """The named section node (`sides`/`jobs`/`narrative`) under the universe root,
    or None when absent (a legacy flat file -> caller iterates the root instead)."""
    return amd_section(doc, key)




def universe_includes(doc):
    """One (section key, file) per `File:` to splice in - the mast reads each and calls
    universe_splice. See amd_doc.amd_includes."""
    return amd_includes(doc)




def universe_splice(doc, section_key, included_doc):
    """Append an included file's top-level entries as children of the named section."""
    return amd_splice(doc, section_key, included_doc)




def universe_reputation_cfg(doc):
    """The universe root's `reputation:` config block (axes + standing tuning), or
    None when absent (-> the built-in defaults). Fed to reputation_configure."""
    return amd_root_data(doc).get("reputation")




def universe_shared_id():
    """The game-wide SHARED agent id - where shared narrative arcs are granted
    (quest_grant_amd routes scope: shared steps here). Lets the mast grant the
    `narrative` section without referencing Agent in MAST scope."""
    return Agent.SHARED_ID




def universe_info_card(line, title=None, color="#0cf", time=10):
    """Deliver a non-side ambient/narrative line (sensors, comms chatter, news) as
    an info-panel card - same surface as side chatter, no portrait."""
    if not line:
        return
    comms_info_card(_chatter_consoles(), line, title=title, color=color, time=time, notify=True)
