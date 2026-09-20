"""THE ADMIRALTY - one per side, and the bug that proves it was needed.

The Admiral's build queue and status line used to be two story-wide `shared` variables,
so two admirals on opposing sides shared one queue and one line: a rival's build showed in
your list, your confirmation appeared on their bar. The fix is the hangar's Flight Wing
shape - an Agent per side, remembered on the side agent - so this file's central claim is
simply that TWO SIDES DO NOT SHARE.

The second claim is the quest holder: an Admiral flies an invisible camera, so without
`admiralty_use_command` the quest screens' "You" is a thing with no name.

Run from the OpenUniverse folder with sbs_utils on the path:
    PYTHONPATH=../sbs_utils python -m unittest tests.test_admiralty
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sbs_utils.fs import test_set_exe_dir

test_set_exe_dir()

import sbs_utils.mast_sbs.story_nodes  # noqa: F401  (import first to break a circular import)
from cosmos_dev.mock import sbs as mock_sbs
from sbs_utils.agent import Agent, clear_shared
from sbs_utils.gui import GuiClient
from sbs_utils.helpers import Context, FakeEvent, FrameContext
from sbs_utils.procedural.quest import quest_add
from sbs_utils.procedural.quest_driver import quest_holder_for_client
from sbs_utils.procedural.sides import side_ensure
from sbs_utils.spaceobject import SpaceObject

from admiral import universe_admiralty as AD

CID = 0x8080000000000001


class AdmiraltyTests(unittest.TestCase):
    def setUp(self):
        mock_sbs.create_new_sim()
        clear_shared()
        SpaceObject.clear()
        FrameContext.context = Context(mock_sbs.sim, mock_sbs, FakeEvent())
        GuiClient(CID)
        side_ensure("tsn")
        side_ensure("kralien")

    def tearDown(self):
        FrameContext.context = None

    def test_one_admiralty_per_side_and_it_stays_the_same_one(self):
        a = AD.admiralty_of("tsn")
        self.assertIsNotNone(a)
        self.assertEqual(a, AD.admiralty_of("tsn"))
        self.assertTrue(AD.admiralty_is(a))

    def test_two_sides_do_not_share(self):
        """The bug. A rival's construction must not appear in your queue, and your
        confirmation must not appear on their status line."""
        AD.admiralty_builds("tsn").append({"name": "Extractor"})
        AD.admiralty_say("tsn", "Construction started: Extractor.")
        self.assertEqual(len(AD.admiralty_builds("kralien")), 0)
        self.assertEqual(AD.admiralty_msg("kralien"), "")
        self.assertEqual(AD.admiralty_msg("tsn"), "Construction started: Extractor.")

    def test_the_queue_is_the_same_list_object(self):
        """A build task holds this list across an await and then removes its own record.
        Hand back a copy and a cancelled build is removed from nothing."""
        rec = {"name": "Refinery"}
        AD.admiralty_builds("tsn").append(rec)
        AD.admiralty_builds("tsn").remove(rec)
        self.assertEqual(AD.admiralty_builds("tsn"), [])

    def test_saying_it_hands_the_line_back(self):
        """Several call sites file the same text as an info card in the next breath;
        reading it back out of the store to do that is how the two drift apart."""
        self.assertEqual(AD.admiralty_say("tsn", "Research started."), "Research started.")

    def test_no_side_is_not_a_crash(self):
        self.assertIsNone(AD.admiralty_of(None))
        self.assertEqual(AD.admiralty_builds(None), [])
        self.assertEqual(AD.admiralty_msg(None), "")

    def test_an_admiral_consoles_quests_belong_to_the_admiralty(self):
        adm = AD.admiralty_use_command(CID, "tsn")
        self.assertEqual(adm, AD.admiralty_of("tsn"))
        label, holder = quest_holder_for_client(CID, 12345)
        self.assertEqual(holder, adm, "the console's quests still belong to its camera")
        self.assertEqual(label, AD.ADMIRALTY_LABEL)

    def test_a_quest_granted_to_the_admiralty_is_held_there(self):
        adm = AD.admiralty_of("tsn")
        quest_add(adm, "hold_the_line", "Hold the line", "")
        self.assertTrue(Agent.get(adm) is not None)

    def test_leaving_the_console_gives_the_ship_back(self):
        AD.admiralty_use_command(CID, "tsn")
        AD.admiralty_release_command(CID)
        label, holder = quest_holder_for_client(CID, 12345)
        self.assertEqual(holder, 12345)


if __name__ == "__main__":
    unittest.main()
