"""A story beat's `Standing:` reaches the ships - and the dialogue words read as before.

THE DEFECT. A narrative step is `Scope: shared`, so it is held by the SHARED story agent,
and `//shared/signal/quest_succeeded` applied its `Standing:` block to that holder. Every
guard reads the acting SHIP (`if standing >= 30` asks COMMS_ORIGIN_ID), so the standing
"The Long Truce: The Accord" pays moved a number no line and no choice could ever see.
The route now uses the library's `reputation_grant`: a shared beat reaches every player
ship flying, a ship's own job still pays that ship.

THE REST IS A GUARD. `standing` and the reputation poles are the library's guard words
now and `earns` is the library's outcome verb; universe_dialogue.py keeps `credits`,
`carrying <item>` and `costs`. For a ship, every one of them answers what it answered
before - including the universe's habit of reading ANY unknown name as a pole.

The route body is sliced out of universe.mast, and the beat is read out of default.amd
with the universe's own parser, so neither can drift from what ships.

Run (from a folder that is NOT a mission repo - a test run writes debug.log where it
stands):
    PYTHONPATH=<sbs_utils> python -m unittest discover -s tests -p "test_reputation_reaches_ships.py"
"""
import glob
import os
import re
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
OU = os.path.abspath(os.path.join(_HERE, ".."))
OU_CORE = os.path.join(OU, "universe_core")
SBS = os.path.abspath(os.path.join(OU, "..", "sbs_utils"))
if os.path.isdir(SBS):
    sys.path.insert(0, SBS)

from sbs_utils.fs import test_set_exe_dir
test_set_exe_dir()

import cosmos_dev.mock.sbs as mock_sbs

sys.modules.setdefault("sbs", mock_sbs)

from sbs_utils.agent import Agent, clear_shared
from sbs_utils.gui import Gui
from sbs_utils.helpers import Context, FakeEvent, FrameContext
from sbs_utils.mast.mast_globals import MastGlobals
from sbs_utils.mast.mast_node import MastDataObject
from sbs_utils.mast.mastscheduler import MastScheduler
from sbs_utils.mast.maststory import MastStory
from sbs_utils.mast_sbs import mast_sbs_procedural  # noqa: F401  (MAST globals)
from sbs_utils.mast_sbs import story_nodes  # noqa: F401  (registers the route nodes)
from sbs_utils.mast_sbs.maststorypage import StoryPage
from sbs_utils.procedural import amd_dialogue as D
from sbs_utils.procedural import boarding as B
from sbs_utils.procedural import reputation as R
from sbs_utils.procedural.inventory import get_inventory_value, set_inventory_value
from sbs_utils.procedural.quest import QuestState, document_get_amd_file, quest_get_state
from sbs_utils.procedural.quest_driver import quest_grant_amd, quest_mark_complete
from sbs_utils.procedural.query import to_id
from sbs_utils.procedural.sides import side_create, to_side_id
from sbs_utils.procedural.signal import signal_register
from sbs_utils.procedural.spawn import player_spawn
from sbs_utils.spaceobject import SpaceObject

SIGNAL = "quest_succeeded"

# The universe's own Python, exec'd into ONE namespace the way test_foundation does it
# (MAST's `import file.py` merge). universe_dialogue.py installs the universe's guard
# resolver and its `costs` verb as it loads - the real registration.
NS = {"__name__": "ou_reputation_test", "__builtins__": __builtins__}
for _path in sorted(glob.glob(os.path.join(OU_CORE, "*.py"))):
    with open(_path, "r", encoding="utf-8") as _f:
        exec(compile(_f.read(), os.path.basename(_path), "exec"), NS)
OU_METRIC = NS["_ou_metric"]

# A route fires on the SERVER task, so main has to still be alive when the signal lands.
_MAIN = """shared UNIVERSE_ACTIVE = True
shared UNIVERSE_GAME_OVER = False
---ou_rep_idle
    await delay_sim(60)
    jump ou_rep_idle

"""

_CALLS = []


def universe_info_card(*args, **kwargs):
    _CALLS.append(("card", args))


def universe_save_request(*args, **kwargs):
    _CALLS.append(("save",))


def universe_save_flush(*args, **kwargs):
    _CALLS.append(("flush",))


def _route(name):
    """The named shared-signal route, verbatim from universe.mast."""
    with open(os.path.join(OU_CORE, "universe.mast"), encoding="utf-8") as handle:
        source = handle.read()
    match = re.search(r"^//shared/signal/" + name + r"\b.*?(?=^(?://|=|@))",
                      source, re.S | re.M)
    assert match is not None, f"route //shared/signal/{name} not found in universe.mast"
    return match.group(0)


def _narrative():
    """`## Narrative` of the default universe, parsed with the universe's own words."""
    doc = document_get_amd_file(os.path.join(OU, "default.amd"),
                                data_parser=NS["universe_amd_data"])
    return NS["universe_section"](doc, "narrative")


def _iron():
    """The Iron Concord's side record, as the default universe authors it."""
    doc = document_get_amd_file(os.path.join(OU, "default.amd"),
                                data_parser=NS["universe_amd_data"])
    for name in ("sides", "clans"):
        section = NS["universe_section"](doc, name)
        for n in (section or {}).get("children", []):
            if n.get("key") == "iron":
                return MastDataObject({"key": "iron",
                                       "leans": (n.get("data") or {}).get("leans") or {}})
    raise AssertionError("default.amd no longer declares a side called iron")


class Base(unittest.TestCase):
    def setUp(self):
        from sbs_utils.handlerhooks import reset_mission_state
        reset_mission_state()
        mock_sbs.create_new_sim()
        mock_sbs.resume_sim()
        SpaceObject.clear()
        clear_shared()
        FrameContext.context = Context(mock_sbs.sim, mock_sbs, FakeEvent(0, "test"))
        Agent.SHARED.set_inventory_value("sim", mock_sbs.sim)
        del _CALLS[:]
        # The universe's resolver, exactly as importing universe_dialogue.py leaves it.
        B.boarding_metric_uninstall()
        self._prev_resolver = D._METRIC_RESOLVER
        D.dialogue_set_metric_resolver(OU_METRIC)
        R.reputation_configure(None)
        side_create("tsn", "TSN")          # credits are a SIDE's, so it has to exist
        self.a = to_id(player_spawn(0, 0, 0, "Artemis", "tsn", "tsn_light_cruiser"))
        self.b = to_id(player_spawn(0, 0, 900, "Hera", "tsn", "tsn_light_cruiser"))

    def tearDown(self):
        B.boarding_metric_uninstall()
        D.dialogue_set_metric_resolver(self._prev_resolver)
        FrameContext.context = None


class AStoryBeatsStandingReachesTheShips(Base):
    def setUp(self):
        super().setUp()
        self.saved_globals = dict(MastGlobals.globals)
        for fn in (universe_info_card, universe_save_request, universe_save_flush):
            MastGlobals.import_python_function(fn)
        self.story = MastStory()
        errors = self.story.compile(_MAIN + _route(SIGNAL), "ou_rep", self.story)
        self.assertEqual(errors, [], f"compile errors: {errors}")
        FrameContext.mast = self.story
        self.errors = []
        self._orig_rte = MastScheduler.on_runtime_error
        MastScheduler.on_runtime_error = self.errors.append
        Gui.clients = {}
        Gui.widget_list_sent = {}
        StoryPage.story = self.story
        self.page = StoryPage()
        Gui.push(0, self.page)
        self._present()
        label = next(name for name in self.story.labels
                     if name.startswith("__route__shared/signal/" + SIGNAL))
        FrameContext.task = self.page.story_scheduler.tasks[0]
        signal_register(SIGNAL, label, True)
        FrameContext.task = None

    def tearDown(self):
        MastScheduler.on_runtime_error = self._orig_rte
        MastGlobals.globals.clear()
        MastGlobals.globals.update(self.saved_globals)
        Gui.clients = {}
        Gui.widget_list_sent = {}
        StoryPage.story = None
        FrameContext.page = None
        FrameContext.mast = None
        FrameContext.task = None
        SpaceObject.clear()
        super().tearDown()

    def _present(self):
        for _ in range(2):
            mock_sbs.sim._time_tick_counter += 30
            FrameContext.context = Context(mock_sbs.sim, mock_sbs, FakeEvent(0, "gui_present"))
            self.page.gui_state = "repaint"
            self.page.present(FakeEvent(0, "gui_present"))

    def test_the_accord_moves_every_ship_flying(self):
        quest_grant_amd(Agent.SHARED_ID, _narrative())
        self.assertEqual(quest_get_state(Agent.SHARED_ID, "truce_3"), QuestState.SECRET)
        quest_mark_complete(Agent.SHARED_ID, "truce_3")
        self._present()
        self.assertEqual(self.errors, [], f"runtime errors: {self.errors}")
        self.assertIn(("card", ("Word of your deeds spreads among the sides.",)), _CALLS)
        for ship in (self.a, self.b):
            # Standing: iron honest 20, iron fearsome 10
            self.assertEqual(R.reputation_get(ship, "iron", "honest"), 20)
            self.assertEqual(R.reputation_get(ship, "iron", "fearsome"), 10)
        # ...which is what a line and a choice read.
        iron = _iron()
        self.assertTrue(iron.get("leans"), "the Iron Concord values nothing?")
        self.assertGreater(OU_METRIC("standing", self.a, iron), 0)
        self.assertTrue(D.dialogue_guard_ok("honest >= 20", self.b, iron))
        # A ship that joins afterwards starts at nothing.
        late = to_id(player_spawn(0, 0, 1800, "Aegis", "tsn", "tsn_light_cruiser"))
        self.assertEqual(OU_METRIC("standing", late, iron), 0)

    def test_a_ships_own_job_still_pays_only_that_ship(self):
        from sbs_utils.procedural.signal import signal_emit
        signal_emit(SIGNAL, {"AGENT_ID": self.a, "QUEST_ID": "job",
                             "DATA": {"rep": {"iron": {"honest": 5}}}})
        self._present()
        self.assertEqual(self.errors, [], f"runtime errors: {self.errors}")
        self.assertEqual(R.reputation_get(self.a, "iron", "honest"), 5)
        self.assertEqual(R.reputation_get(self.b, "iron", "honest"), 0)


class TheDialogueWordsReadAsBefore(Base):
    """For a ship, against the records the universe hands the driver."""

    CLAN = MastDataObject({"key": "ashfang", "name": "Ashfang Raiders", "color": "#f44",
                           "leans": {"cruel": 40, "fearsome": 30, "violent": 20}})
    # A captain with no Values of their own: regarded under their own key.
    PLAIN = MastDataObject({"key": "kade", "name": "Kade", "color": "#ccc", "leans": {}})

    def test_the_universes_resolver_is_the_one_installed(self):
        self.assertIs(D._METRIC_RESOLVER, OU_METRIC)

    def test_earns_moves_the_ship_that_answered(self):
        self.assertTrue(D.dialogue_apply(self.a, self.CLAN,
                                         [("earns", "ashfang", "fearsome", "10")]))
        self.assertEqual(R.reputation_get(self.a, "ashfang", "fearsome"), 10)
        self.assertEqual(R.reputation_get(self.b, "ashfang", "fearsome"), 0)
        self.assertEqual(get_inventory_value(Agent.SHARED_ID, "reputation", None), None)
        # `cowardly` is the other pole of the same axis.
        D.dialogue_apply(self.a, self.CLAN, [("earns", "ashfang", "cowardly", "5")])
        self.assertEqual(R.reputation_get(self.a, "ashfang", "fearsome"), 5)

    def test_a_pole_guard(self):
        self.assertFalse(D.dialogue_guard_ok("fearsome > 20", self.a, self.CLAN))
        R.reputation_adjust(self.a, "ashfang", "fearsome", 25)
        self.assertTrue(D.dialogue_guard_ok("fearsome > 20", self.a, self.CLAN))
        self.assertFalse(D.dialogue_guard_ok("fearsome > 20", self.b, self.CLAN))

    def test_standing_is_the_weighted_standing_with_the_speaker(self):
        R.reputation_adjust(self.a, "ashfang", "fearsome", 60)
        R.reputation_adjust(self.a, "ashfang", "cruel", -20)
        want = R.reputation_standing(self.a, self.CLAN)
        self.assertEqual(want, int((40 * -20 + 30 * 60 + 20 * 0) / 90))
        for word in ("standing", "rep", "reputation"):
            self.assertEqual(OU_METRIC(word, self.a, self.CLAN), want)
        self.assertTrue(D.dialogue_guard_ok(f"standing >= {want}", self.a, self.CLAN))
        self.assertFalse(D.dialogue_guard_ok(f"standing > {want}", self.a, self.CLAN))

    def test_a_speaker_with_no_values_is_regarded_under_their_own_key(self):
        D.dialogue_apply(self.a, self.PLAIN, [("earns", "kade", "kind", "5")])
        self.assertEqual(OU_METRIC("standing", self.a, self.PLAIN), 5)
        self.assertEqual(OU_METRIC("kind", self.a, self.PLAIN), 5)
        self.assertEqual(OU_METRIC("cruel", self.a, self.PLAIN), -5)

    def test_any_unknown_name_is_still_read_as_a_pole(self):
        # An axis a scene's own `earns` invented. The library alone answers 0 for a
        # name that is not a pole; the universe has always read it.
        D.dialogue_apply(self.a, self.CLAN, [("earns", "ashfang", "swagger", "7")])
        self.assertEqual(OU_METRIC("swagger", self.a, self.CLAN), 7)
        self.assertTrue(D.dialogue_guard_ok("swagger >= 7", self.a, self.CLAN))
        self.assertEqual(R.reputation_metric("swagger", self.a, self.CLAN), 0)
        self.assertEqual(OU_METRIC("nothing_at_all", self.a, self.CLAN), 0)

    def test_credits_and_costs(self):
        side = to_side_id("tsn")
        set_inventory_value(side, "credits", 250)
        self.assertTrue(D.dialogue_guard_ok("credits >= 200", self.a, self.CLAN))
        self.assertTrue(D.dialogue_apply(self.a, self.CLAN, [("costs", "200", "credits")]))
        self.assertEqual(get_inventory_value(side, "credits", 0), 50)
        self.assertFalse(D.dialogue_guard_ok("credits >= 200", self.a, self.CLAN))
        # Unaffordable: the pick is refused and nothing after it is applied.
        self.assertFalse(D.dialogue_apply(self.a, self.CLAN,
                                          [("costs", "200", "credits"),
                                           ("earns", "ashfang", "selfish", "5")]))
        self.assertEqual(get_inventory_value(side, "credits", 0), 50)
        self.assertEqual(R.reputation_get(self.a, "ashfang", "selfish"), 0)

    def test_carrying(self):
        self.assertFalse(D.dialogue_guard_ok("carrying clue_manifest >= 1", self.a, self.CLAN))
        set_inventory_value(self.a, "clue_manifest", 1)
        self.assertTrue(D.dialogue_guard_ok("carrying clue_manifest >= 1", self.a, self.CLAN))
        self.assertTrue(D.dialogue_guard_ok("have clue_manifest", self.a, self.CLAN))
        self.assertFalse(D.dialogue_guard_ok("carrying clue_manifest >= 1", self.b, self.CLAN))

    def test_the_universe_no_longer_declares_earns_itself(self):
        self.assertFalse("_ou_earns" in NS, "universe_dialogue.py still defines _ou_earns")
        self.assertIs(D._OUTCOME_HANDLERS.get("earns"), R.reputation_earns_outcome)
        # By name: every test file here execs the universe's Python into a namespace of
        # its own, and the last one to load is the one registered.
        self.assertEqual(getattr(D._OUTCOME_HANDLERS.get("costs"), "__name__", None),
                         "_ou_costs")

    # --- a universe's sides are the library's sides too -------------------------------
    def sides(self):
        doc = document_get_amd_file(os.path.join(OU, "default.amd"),
                                    data_parser=NS["universe_amd_data"])
        return NS["universe_sides_from_doc"](doc)

    def test_a_universes_sides_are_registered_with_the_library(self):
        """`build_report_reputation.md`, open question 1."""
        self.assertIsNone(R.reputation_side("iron"), "registered by somebody else")
        count = NS["universe_sides_register_reputation"](self.sides())
        self.assertGreaterEqual(count, 6)
        iron = R.reputation_side("iron")
        self.assertIsNotNone(iron)
        self.assertEqual(iron["leans"], {"by_the_book": 40, "fearsome": 30, "honest": 20})

    def test_a_cast_character_with_a_side_and_no_values_is_read_against_the_sides(self):
        """A dockmaster who says `Side: iron` and has no `Values:` of their own."""
        NS["universe_sides_register_reputation"](self.sides())
        quill = MastDataObject({"key": "quill", "name": "Quill", "side": "iron"})
        R.reputation_adjust(self.a, "iron", "by_the_book", 50)
        R.reputation_adjust(self.a, "iron", "kind", 80)       # the Concord does not care
        want = R.reputation_standing(self.a, R.reputation_side("iron"))
        self.assertEqual(OU_METRIC("standing", self.a, quill), want)
        # Weighted by what the Concord values - not the plain average of what was earned.
        plain = R.reputation_standing(self.a, {"key": "iron", "leans": {}})
        self.assertNotEqual(want, plain)
        self.assertTrue(D.dialogue_guard_ok("standing >= %d" % want, self.a, quill))
        self.assertFalse(D.dialogue_guard_ok("standing >= %d" % (want + 1), self.a, quill))

    def test_without_the_registration_it_was_the_plain_average(self):
        quill = MastDataObject({"key": "quill", "name": "Quill", "side": "iron"})
        R.reputation_adjust(self.a, "iron", "by_the_book", 50)
        R.reputation_adjust(self.a, "iron", "kind", 80)
        self.assertEqual(OU_METRIC("standing", self.a, quill),
                         R.reputation_standing(self.a, {"key": "iron", "leans": {}}))

    def test_a_clan_or_captain_with_values_of_their_own_is_read_as_before(self):
        NS["universe_sides_register_reputation"](self.sides())
        R.reputation_adjust(self.a, "ashfang", "fearsome", 60)
        self.assertEqual(OU_METRIC("standing", self.a, self.CLAN),
                         R.reputation_standing(self.a, self.CLAN))

    def test_the_universe_registers_them_as_it_starts(self):
        with open(os.path.join(OU_CORE, "universe.mast"), encoding="utf-8") as handle:
            source = handle.read()
        at = source.index("shared UNIVERSE_SIDES = universe_sides_from_doc(UNIVERSE_DOC)")
        self.assertIn("universe_sides_register_reputation(UNIVERSE_SIDES)",
                      source[at:at + 700])


if __name__ == "__main__":
    unittest.main()
