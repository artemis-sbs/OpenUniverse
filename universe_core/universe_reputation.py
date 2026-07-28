"""Per-captain reputation with sides (Open Universe, Epic F).

Now a thin binder over the shared sbs_utils.procedural.reputation service (the whole
multi-axis reputation engine, axes/tuning config, standing, tiers, reward, and the
diplomacy-economy pricing were promoted from here). OU keeps the `side_*` names its mast
routes + helpers already call; the generic engine lives in the library and pairs with
amd_dialogue (guards read reputation).

Distinct from diplomacy (side-wide "are we at war?"): reputation is how a side sees a
*captain*, stored on the captain's ship agent (inventory key "reputation").
"""
from sbs_utils.procedural.reputation import (   # noqa: F401  (re-exported into the OU namespace)
    reputation_configure, reputation_get, reputation_adjust, reputation_apply,
    reputation_standing, reputation_offer_tier, reputation_foe_deal_standing,
    reputation_reward_mult, reputation_ceasefire_cost, reputation_alliance_standing,
    reputation_ransom_cost)

# OU-facing names: its mast routes + helpers (universe_dialogue, universe_captains,
# universe_side_quests, ...) call these side_* aliases. A "side record" is the faction
# record the shared engine takes (a dict with key + optional leans).
sides_standing = reputation_standing
side_offer_tier = reputation_offer_tier
side_foe_deal_standing = reputation_foe_deal_standing
side_reward_mult = reputation_reward_mult
side_ceasefire_cost = reputation_ceasefire_cost
side_alliance_standing = reputation_alliance_standing
side_ransom_cost = reputation_ransom_cost
