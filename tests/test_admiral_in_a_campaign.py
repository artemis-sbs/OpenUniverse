"""The Admiral as an OPTION in a campaign, the home worldlet, and the research fields.

Three things a universe WRITER does, each of which used to do nothing and say nothing:

  1. `Mode: campaign` and an `## Admiralty` chapter. The Admiral was off, whatever the
     file said. It now runs when the file has its OWN Admiralty chapter and Worldlets
     types and the admiral addon is loaded - and stays off in every other case.
  2. A side whose `Home:` is 0, 0. That turned the start cell into a "station" system,
     and the guaranteed home worldlet was only given to a "home" system: an Admiral
     with no world to build a Headquarters on, so no economy at all.
  3. A research milestone. `Costs:` and `Time:` were reported as fields an item does
     not have; adding `Also: economy` to quiet that turned `Time: 40` into 2,400
     seconds.

Every test drives the mission's real functions in the order universe.mast's load block
calls them (universe_doc -> generation -> sides -> universe_mode_configure ->
worldlets_configure -> admiralty_configure), on universe text written the way a writer
writes it. The mission's Python is exec'd into one namespace, the way MAST's
`import x.py` merges it (the same loader tests/test_foundation.py uses).

Run from the OpenUniverse folder:
    PYTHONPATH=../sbs_utils python -m unittest discover -s tests -p "test_admiral_in_a_campaign.py"
"""
import glob
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
OU = os.path.abspath(os.path.join(_HERE, ".."))
OU_CORE = os.path.join(OU, "universe_core")
ADMIRAL = os.path.join(OU, "admiral")
SBS = os.path.abspath(os.path.join(_HERE, "..", "..", "sbs_utils"))
sys.path.insert(0, SBS)

from sbs_utils.fs import test_set_exe_dir
test_set_exe_dir()

import cosmos_dev.mock.sbs as mock_sbs
sys.modules.setdefault("sbs", mock_sbs)

import sbs_utils.mast_sbs.story_nodes  # noqa: F401
from sbs_utils.helpers import Context, FakeEvent, FrameContext
from sbs_utils.procedural import amd_schema
from sbs_utils.spaceobject import SpaceObject

SHIPPED = ("default.amd", "silver_reach.amd", "skirmish_arena.amd", "quiet_shore.amd",
           "scout_signal.amd")
SEEDS = (7, 1, 99, 123456789)


def _load_mission_python(folders):
    """Exec every .py of the given addon folders into ONE namespace."""
    ns = {"__name__": "ou_admiral_campaign", "__builtins__": __builtins__}
    for folder in folders:
        for path in sorted(glob.glob(os.path.join(folder, "*.py"))):
            with open(path, "r", encoding="utf-8") as f:
                exec(compile(f.read(), os.path.basename(path), "exec"), ns)
    return ns


# ---- universe text, the way a writer writes it ---------------------------------------
HEAD = """# [The Test Verge](test_verge)
---
Universe
Display: The Test Verge
---
A universe for a test.

"""

SIDES_HOME_AT_ORIGIN = """## [Sides](sides)

### [Hollin Compact](hollin)
---
Color: #44aa66
Character: settler
Disposition: neutral
Home: 0, 0
---
The first colony.

### [Deepwell Assembly](deepwell)
---
Color: #6688ff
Character: trader
Disposition: neutral
Home: 3, 1
---
The second colony.

"""

SIDES_HOME_ELSEWHERE = SIDES_HOME_AT_ORIGIN.replace("Home: 0, 0", "Home: -2, 5")

# The first type is NOT the unlimited one, so "the home pick" and "the first type" differ.
WORLDLETS = """## [Worldlets](worldlets)

### [Cinder](cinder)
---
Landmark
Also: economy
Yields: ore 8
Reserve: 4000
---
A cracked ember of a world.

### [Hollin Prime](hollin_prime)
---
Landmark
Also: economy
Yields: crew 2, ore 2, gas 2
Reserve: unlimited
---
The world the Compact farms.

"""

ADMIRALTY = """## [Admiralty](admiralty)
---
Command points: 2
---
The Compact has never had a navy.

"""

ADMIRALTY_EMPTY = """## [Admiralty](admiralty)
---
---

"""

RESEARCH = """## [Research](research)

### [Deeper Silos](silos)
---
Branch: engineering
Costs: ore 120, gas 40
Time: 40
Unlocks: storage 500
---
Bigger tanks.

### [Hot Drills](hot_drills)
---
Also: economy
Branch: engineering
Costs: ore 180, gas 90
Time: 60
Requires: silos
Unlocks: extraction 25%
---
Every extractor works a quarter again as fast.

"""


def scenario(mode):
    return "## [Scenario](scenario)\n---\nMode: %s\n---\n\n" % mode


class MissionCase(unittest.TestCase):
    FOLDERS = (OU_CORE, ADMIRAL)

    @classmethod
    def setUpClass(cls):
        # The mission's vocabulary is process-global; leave it as it was found.
        cls.vocabulary = amd_schema.amd_vocabulary_snapshot()
        mock_sbs.create_new_sim()
        SpaceObject.clear()
        FrameContext.context = Context(mock_sbs.sim, mock_sbs, FakeEvent())
        cls.ns = _load_mission_python(cls.FOLDERS)

    @classmethod
    def tearDownClass(cls):
        FrameContext.context = None
        amd_schema.amd_vocabulary_restore(cls.vocabulary)

    def load(self, text):
        """universe.mast's load block, as far as the Admiral: returns (doc, sides)."""
        ns = self.ns
        doc = ns["universe_doc"](text)
        ns["generation_configure"](ns["universe_generation_cfg"](doc))
        sides = ns["universe_sides_from_doc"](doc)
        ns["regions_configure"](ns["universe_parse_regions"](doc))
        ns["universe_mode_configure"](ns["universe_admiralty_cfg"](doc))
        if ns["admiral_present"]():
            ns["worldlets_configure"](ns["universe_parse_worldlets"](doc))
            ns["admiralty_configure"](ns["universe_admiralty_cfg"](doc))
            ns["research_configure"](ns["universe_parse_research"](doc))
            ns["admiralty_cell_worldlets_clear"]()
        return doc, sides

    def load_file(self, name):
        with open(os.path.join(OU, name), encoding="utf-8") as f:
            return self.load(f.read())

    def deck(self, sides, seed, i, j, danger="Quiet"):
        """The deck for a cell, with the kind and owner universe_enter_system gives it."""
        ns = self.ns
        key = ns["universe_system_key"](seed, i, j)
        kind = ns["universe_system_kind"](seed, i, j, danger)
        owner, kind = ns["universe_system_side"](sides, seed, i, j, kind)
        return kind, ns["universe_system_deck"](key, kind, owner,
                                                ns["sides_character"](sides, owner), False, 5, i, j)

    def worldlets(self, sides, seed, i, j):
        return [p.get("worldlet_type") for p in self.deck(sides, seed, i, j)[1]
                if p.get("type") == "worldlet"]


class HomeWorldlet(MissionCase):
    """Step 2 of the plan: the start cell always has a world to build on."""

    def test_A_SIDE_HOME_AT_0_0_STILL_GETS_THE_HOME_WORLDLET(self):
        _, sides = self.load(HEAD + scenario("sandbox") + SIDES_HOME_AT_ORIGIN + WORLDLETS + ADMIRALTY)
        self.assertTrue(self.ns["admiralty_active"]())
        for seed in SEEDS:
            kind, _ = self.deck(sides, seed, 0, 0)
            self.assertEqual(kind, "station", "the fault's precondition: 0,0 is a side home")
            self.assertEqual(self.worldlets(sides, seed, 0, 0), ["hollin_prime"],
                             "seed %d: the start cell has exactly one worldlet, the settled "
                             "(unlimited) type" % seed)

    def test_the_galaxy_map_counts_the_same_worldlet(self):
        _, sides = self.load(HEAD + scenario("sandbox") + SIDES_HOME_AT_ORIGIN + WORLDLETS + ADMIRALTY)
        for seed in SEEDS:
            self.assertEqual(self.ns["admiralty_cell_worldlets"](seed, sides, 0, 0), 1)

    def test_only_cell_0_0_is_widened(self):
        """Another side's home is an ordinary station system: no guaranteed worldlet
        (Worldlet chance is not written, so it is 0 and nothing is drawn)."""
        _, sides = self.load(HEAD + scenario("sandbox") + SIDES_HOME_AT_ORIGIN + WORLDLETS + ADMIRALTY)
        for seed in SEEDS:
            self.assertEqual(self.deck(sides, seed, 3, 1)[0], "station")
            self.assertEqual(self.worldlets(sides, seed, 3, 1), [])

    def test_an_ordinary_home_is_as_it_was(self):
        _, sides = self.load(HEAD + scenario("sandbox") + SIDES_HOME_ELSEWHERE + WORLDLETS + ADMIRALTY)
        for seed in SEEDS:
            self.assertEqual(self.deck(sides, seed, 0, 0)[0], "home")
            self.assertEqual(self.worldlets(sides, seed, 0, 0), ["hollin_prime"])

    def test_no_worldlet_when_the_admiral_is_off(self):
        _, sides = self.load(HEAD + scenario("story") + SIDES_HOME_AT_ORIGIN + WORLDLETS + ADMIRALTY)
        for seed in SEEDS:
            self.assertEqual(self.worldlets(sides, seed, 0, 0), [])

    def test_a_caller_that_does_not_name_the_cell_is_unchanged(self):
        """i / j are optional on the deck; without them a station is just a station."""
        _, sides = self.load(HEAD + scenario("sandbox") + SIDES_HOME_AT_ORIGIN + WORLDLETS + ADMIRALTY)
        ns = self.ns
        deck = ns["universe_system_deck"](ns["universe_system_key"](7, 0, 0), "station", "hollin")
        self.assertEqual([p for p in deck if p.get("type") == "worldlet"], [])

    def test_NO_SHIPPED_UNIVERSE_HAS_A_SIDE_HOME_AT_0_0(self):
        """Why the change cannot move anything in a universe that ships with this
        mission: the widened case needs a side home on the start cell. A pin - if a
        shipped universe ever gains one, its start cell changes and this says so."""
        for name in SHIPPED:
            _, sides = self.load_file(name)
            self.assertIsNone(self.ns["sides_home_owner"](sides, 0, 0), name)
            for seed in SEEDS:
                self.assertEqual(self.deck(sides, seed, 0, 0)[0], "home", name)


class CampaignIsOptional(MissionCase):
    """Step 3 of the plan: in a campaign the Admiral is the writer's choice."""

    BODY = SIDES_HOME_AT_ORIGIN

    def active(self, text):
        self.load(text)
        return self.ns["admiralty_active"]()

    def test_CAMPAIGN_WITH_ADMIRALTY_AND_WORLDLETS_RUNS_THE_ADMIRAL(self):
        self.assertTrue(self.active(HEAD + scenario("campaign") + self.BODY + WORLDLETS + ADMIRALTY))
        self.assertEqual(self.ns["mission_mode"](), "campaign")
        # The campaign's own defaults still apply to the dials the file did not set.
        self.assertEqual(self.ns["admiralty_tuning"]("economy_pace"), "epic")
        self.assertEqual(self.ns["admiralty_tuning"]("skirmish_pressure"), "off")
        self.assertEqual(self.ns["admiralty_tuning"]("command_points"), 2)

    def test_an_empty_admiralty_fence_is_still_the_chapter(self):
        self.assertTrue(self.active(HEAD + scenario("campaign") + self.BODY + WORLDLETS + ADMIRALTY_EMPTY))

    def test_campaign_with_no_admiralty_chapter_is_off(self):
        self.assertFalse(self.active(HEAD + scenario("campaign") + self.BODY))

    def test_campaign_with_worldlets_but_no_admiralty_chapter_is_off(self):
        self.assertFalse(self.active(HEAD + scenario("campaign") + self.BODY + WORLDLETS))

    def test_campaign_with_an_admiralty_chapter_but_no_worldlets_is_off(self):
        self.assertFalse(self.active(HEAD + scenario("campaign") + self.BODY + ADMIRALTY))

    def test_campaign_mode_written_inside_the_admiralty_chapter(self):
        """The older place for `Mode:`. The file has the chapter, so the Admiral runs."""
        text = HEAD + self.BODY + WORLDLETS + ADMIRALTY.replace("Command points: 2", "Mode: campaign")
        self.assertTrue(self.active(text))
        self.assertEqual(self.ns["mission_mode"](), "campaign")

    def test_STORY_IS_OFF_WHATEVER_THE_FILE_HAS(self):
        self.assertFalse(self.active(HEAD + scenario("story") + self.BODY + WORLDLETS + ADMIRALTY))
        self.assertEqual(self.ns["admiralty_tuning"]("skirmish_pressure"), "off")

    def test_sandbox_and_skirmish_are_as_they_were(self):
        for mode in ("sandbox", "skirmish", "war"):
            self.assertTrue(self.active(HEAD + scenario(mode) + self.BODY + WORLDLETS + ADMIRALTY), mode)
            # A Scenario chapter alone was already enough beside Worldlets in these modes.
            self.assertTrue(self.active(HEAD + scenario(mode) + self.BODY + WORLDLETS), mode)
            self.assertFalse(self.active(HEAD + scenario(mode) + self.BODY + ADMIRALTY), mode)

    def test_an_empty_admiralty_fence_switches_a_sandbox_on_too(self):
        """The writer's guide, step 2: "You can leave its fence completely empty". With
        no Scenario chapter that used to read the same as no Admiralty chapter."""
        self.assertTrue(self.active(HEAD + self.BODY + WORLDLETS + ADMIRALTY_EMPTY))
        self.assertFalse(self.active(HEAD + self.BODY + WORLDLETS))

    def test_the_shipped_universes_are_as_they_were(self):
        want = {"default.amd": ("sandbox", True), "skirmish_arena.amd": ("skirmish", True),
                "silver_reach.amd": ("sandbox", False), "quiet_shore.amd": ("sandbox", False),
                "scout_signal.amd": ("story", False)}
        for name, pair in want.items():
            self.load_file(name)
            self.assertEqual((self.ns["mission_mode"](), self.ns["admiralty_active"]()), pair, name)


class CampaignWithoutTheAddon(MissionCase):
    """A mission that does not load the admiral addon: nothing the file says wakes it."""

    FOLDERS = (OU_CORE,)

    def test_the_chapters_alone_do_not_run_an_admiral(self):
        ns = self.ns
        self.assertFalse(ns["admiral_present"]())
        self.load(HEAD + scenario("campaign") + SIDES_HOME_AT_ORIGIN + WORLDLETS + ADMIRALTY)
        self.assertFalse(ns["admiralty_active"]())
        ns["universe_mode_set_admiral_active"](True)
        self.assertFalse(ns["admiralty_active"](), "the addon is the third condition")
        # ...and so the deck never reaches for the addon's worldlet functions.
        deck = ns["universe_system_deck"](ns["universe_system_key"](7, 0, 0), "station", "hollin",
                                          None, False, 5, 0, 0)
        self.assertEqual([p for p in deck if p.get("type") == "worldlet"], [])


class ResearchFields(MissionCase):
    """Step 4 of the plan: a milestone's Costs and Time, with and without the trait."""

    TEXT = HEAD + scenario("campaign") + SIDES_HOME_AT_ORIGIN + WORLDLETS + ADMIRALTY + RESEARCH

    def research(self, text=None):
        doc, _ = self.load(text or self.TEXT)
        return {r.key: r for r in self.ns["universe_parse_research"](doc)}

    def test_TIME_IS_SECONDS_WITH_OR_WITHOUT_ALSO_ECONOMY(self):
        got = self.research()
        self.assertEqual(got["silos"].time, 40)
        self.assertEqual(got["hot_drills"].time, 60, "`Also: economy` made this 3,600")

    def test_costs_read_the_same_either_way(self):
        got = self.research()
        self.assertEqual(got["silos"].costs, {"ore": 120, "gas": 40})
        self.assertEqual(got["hot_drills"].costs, {"ore": 180, "gas": 90})

    def test_the_default_universes_ladder_runs_at_the_times_written(self):
        doc, _ = self.load_file("default.amd")
        got = [(r.key, r.time) for r in self.ns["universe_parse_research"](doc)]
        self.assertEqual(got, [("eng_silos", 40), ("eng_refining", 60), ("eng_fittings", 80)])

    def test_COSTS_AND_TIME_ARE_FIELDS_A_MILESTONE_HAS(self):
        for label in ("costs", "time", "branch", "unlocks", "requires"):
            self.assertTrue(amd_schema.amd_is_declared(label, "item"), label)
        # The item's own declaration wins over the trait's duration.
        self.assertEqual(amd_schema.field_schema("time", "item", ("economy",))["type"], "int")
        self.assertEqual(amd_schema.field_schema("time", "item")["type"], "int")

    def test_lint_has_nothing_to_say_about_a_milestone(self):
        from sbs_utils.procedural import amd_core, amd_lint
        doc = amd_core.parse(self.TEXT)
        found = [f for f in amd_lint.amd_lint_unknown_fields(doc)]
        found += [f for f in amd_lint.amd_lint_field_values(doc)]
        self.assertEqual([str(f) for f in found], [])

    def test_the_three_word_dials_are_words(self):
        for label, good, bad in (("economy pace", "brisk", "fast"),
                                 ("skirmish pressure", "none", "40%")):
            schema = amd_schema.field_schema(label, "map")
            self.assertEqual(schema["type"], "enum", label)
            self.assertIn(good, schema["values"], label)
            self.assertNotIn(bad, schema["values"], label)
        self.assertEqual(amd_schema.field_schema("research pace", "map")["type"], "text")

    def test_lint_names_a_pace_that_is_not_one(self):
        from sbs_utils.procedural import amd_core, amd_lint
        text = self.TEXT.replace("Command points: 2", "Command points: 2\nEconomy pace: fast")
        found = [str(f) for f in amd_lint.amd_lint_field_values(amd_core.parse(text))]
        self.assertEqual(len(found), 1, found)
        self.assertIn("fast", found[0])
        good = self.TEXT.replace("Command points: 2",
                                 "Command points: 2\nEconomy pace: brisk\nSkirmish pressure: none"
                                 "\nResearch pace: campaign")
        self.assertEqual([str(f) for f in amd_lint.amd_lint_field_values(amd_core.parse(good))], [])


class PlatformsReachTheSave(MissionCase):
    """Found by playing, stopping and continuing a campaign with an Admiral: platforms
    built at home were only in memory until a ship jumped, so a session that ended
    without a jump lost them (and kept the bill). The economy tick now writes the save
    file when a cell's platforms are not what the save holds; this is the question it
    asks. The write itself is admiral.mast's, and is proved by the headless
    play / stop / Continue run in the build report."""

    def differ(self, now, stored):
        return self.ns["admiralty_platforms_differ"](now, stored)

    def test_a_new_platform_is_a_difference(self):
        hq = {"k": "hq", "w": 0}
        yard = {"k": "shipyard", "w": 0}
        self.assertTrue(self.differ({"tsn": [hq]}, None))
        self.assertTrue(self.differ({"tsn": [hq, yard]}, {"tsn": [hq]}))
        self.assertTrue(self.differ({}, {"tsn": [hq]}), "a platform lost is one too")
        self.assertTrue(self.differ({"tsn": [hq], "orion": [hq]}, {"tsn": [hq]}))

    def test_nothing_built_is_not_a_difference(self):
        for now in ({}, None):
            for stored in (None, {}, [], {"tsn": []}):
                self.assertFalse(self.differ(now, stored), (now, stored))

    def test_the_same_platforms_in_another_order_are_not_a_difference(self):
        a = [{"k": "hq", "w": 0}, {"k": "extractor", "w": 0}, {"k": "extractor", "w": 1}]
        self.assertFalse(self.differ({"tsn": list(a)}, {"tsn": list(reversed(a))}))

    def test_an_older_saves_flat_list_is_the_primary_sides(self):
        ns = self.ns
        ns["universe_register_player_side"]("tsn")
        self.assertEqual(ns["universe_primary_side"](), "tsn")
        hq = [{"k": "hq", "w": 0}]
        self.assertFalse(self.differ({"tsn": hq}, hq))
        self.assertTrue(self.differ({"tsn": hq + [{"k": "lab", "w": 0}]}, hq))


if __name__ == "__main__":
    unittest.main()
