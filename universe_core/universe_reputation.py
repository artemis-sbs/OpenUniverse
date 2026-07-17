"""Per-captain reputation with clans (Open Universe, Epic F).

Now a thin binder over the shared sbs_utils.procedural.reputation service (the whole
multi-axis reputation engine, axes/tuning config, standing, tiers, reward, and the
diplomacy-economy pricing were promoted from here). OU keeps the `clan_*` names its mast
routes + helpers already call; the generic engine lives in the library and pairs with
amd_dialogue (guards read reputation).

Distinct from diplomacy (side-wide "are we at war?"): reputation is how a clan sees a
*captain*, stored on the captain's ship agent (inventory key "reputation").
"""
from sbs_utils.procedural.reputation import (   # noqa: F401  (re-exported into the OU namespace)
    reputation_configure, reputation_get, reputation_adjust, reputation_apply,
    reputation_standing, reputation_offer_tier, reputation_foe_deal_standing,
    reputation_reward_mult, reputation_ceasefire_cost, reputation_alliance_standing,
    reputation_ransom_cost)

# OU-facing names: its mast routes + helpers (universe_dialogue, universe_captains,
# universe_clan_quests, ...) call these clan_* aliases. A "clan record" is the faction
# record the shared engine takes (a dict with key + optional leans).
clan_standing = reputation_standing
clan_offer_tier = reputation_offer_tier
clan_foe_deal_standing = reputation_foe_deal_standing
clan_reward_mult = reputation_reward_mult
clan_ceasefire_cost = reputation_ceasefire_cost
clan_alliance_standing = reputation_alliance_standing
clan_ransom_cost = reputation_ransom_cost
