"""Trade goods for the Open Universe - the authorable economy's loot pool. A
`## Goods` section lists the goods (a key + a Weight = how common it is as loot);
the POI deck scatters loot drawn from this weighted pool. Defaults reproduce the
built-in five. A universe can drop goods or reweight them (a spice-route galaxy vs.
a tech-salvage one); good keys must be registered items (the LM items mastlib) -
adding brand-new items is a follow-up. universe_section comes from
universe_sides.py (shared namespace).
"""
import random
from sbs_utils.mast.mast_node import MastDataObject

# (key, weight) - the built-in goods; all are registered trade items.
_DEFAULT_GOODS = [("ore", 1), ("gas", 1), ("provisions", 1), ("tech", 1), ("contraband", 1)]
_GOODS = list(_DEFAULT_GOODS)


def universe_parse_goods(doc):
    """Good records from the `## Goods` section (empty if none)."""
    section = universe_section(doc, "goods")
    out = []
    if section is not None:
        for n in section.get("children", []):
            data = n.get("data") or {}
            out.append(MastDataObject({
                "key": n.get("key"),
                "name": n.get("display_text"),
                "desc": (n.get("description") or "").strip(),
                "weight": int(data.get("weight") or 1),
            }))
    return out


def goods_configure(goods):
    """Set the universe's loot pool (weighted good keys). Resets to the built-in five
    first (process-global; a re-selected universe must not inherit the last pool)."""
    global _GOODS
    _GOODS = list(_DEFAULT_GOODS)
    if goods:
        pool = [(g.get("key"), max(1, int(g.get("weight") or 1))) for g in goods if g.get("key")]
        if pool:
            _GOODS = pool


def universe_loot_pick(r):
    """A weighted-random good key for a loot cache (r is the deck's seeded Random)."""
    keys = [k for k, _ in _GOODS]
    weights = [w for _, w in _GOODS]
    return r.choices(keys, weights=weights)[0]
