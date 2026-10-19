"""Universe chatter goes to the COMMS WATERFALL, and the big beats are incoming hails.

The rule (2026-10-19): what matters or wants an answer is an incoming hail; what the
comms officer reads is the waterfall. OU sent all of it as info-panel cards, which Comms
does not read - in the engine a dialogue line sent that way never reached Comms at all.

    python -m unittest tests.test_chatter_reaches_comms
"""
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
OU_CORE = os.path.abspath(os.path.join(_HERE, "..", "universe_core"))
SBS = os.path.abspath(os.path.join(_HERE, "..", "..", "sbs_utils"))
if os.path.isdir(SBS):
    sys.path.insert(0, SBS)
sys.path.insert(0, OU_CORE)

from sbs_utils.fs import test_set_exe_dir
test_set_exe_dir()

import sbs_utils.mast_sbs.story_nodes  # noqa: F401  import first (circular import)
import cosmos_dev.mock.sbs as mock_sbs
sys.modules.setdefault("sbs", mock_sbs)
from sbs_utils.helpers import FrameContext, Context, FakeEvent
from sbs_utils.spaceobject import SpaceObject
from sbs_utils.procedural.a2x.spawn import create_enemy
from sbs_utils.procedural.query import to_id
from sbs_utils.procedural.roles import add_role
from sbs_utils.procedural import hail as H
from sbs_utils.mast.mast_node import MastDataObject

import universe_sides as US  # noqa: E402


class Chatter(unittest.TestCase):
    def setUp(self):
        mock_sbs.create_new_sim()
        FrameContext.context = Context(mock_sbs.sim, mock_sbs, FakeEvent())
        SpaceObject.clear()
        self.ship = to_id(create_enemy(0, 0, 0, "tsn_light_cruiser", name="Artemis"))
        add_role(self.ship, "__player__")
        self.station = to_id(create_enemy(800, 0, 0, "starbase_command", name="Kestrel Relay"))
        add_role(self.station, "station")
        add_role(self.station, "hollin")
        self.side = MastDataObject({"key": "hollin", "name": "Hollin Compact", "color": "#8f8"})
        self.sent = []
        self._orig = mock_sbs.send_comms_message_to_player_ship

        def tap(contactID, playerID, otherID, faceDesc, titleText, titleColor,
                bodyText, bodyColor, tagset, name="unset"):
            self.sent.append({"contact": contactID, "player": playerID,
                              "text": bodyText, "tag": tagset, "name": name})
        mock_sbs.send_comms_message_to_player_ship = tap

    def tearDown(self):
        mock_sbs.send_comms_message_to_player_ship = self._orig

    def test_a_sides_line_comes_from_its_station(self):
        US.universe_chatter_card(self.side, "Hollin looks after its own.")
        self.assertEqual(len(self.sent), 1)
        m = self.sent[0]
        self.assertEqual((m["player"], m["contact"], m["tag"]), (self.ship, self.station, "recv"))
        self.assertEqual(m["text"], "Hollin looks after its own.")

    def test_no_station_out_there_is_the_sides_name_on_the_ships_channel(self):
        side = MastDataObject({"key": "deepwell", "name": "Deepwell Assembly"})
        US.universe_chatter_card(side, "Deepwell sends its regards.")
        self.assertEqual(len(self.sent), 1)
        self.assertEqual(self.sent[0]["player"], self.ship)
        self.assertEqual(self.sent[0]["name"], "Deepwell Assembly")

    def test_a_line_with_no_side_is_the_ships_channel_under_its_title(self):
        US.universe_comms("Sensors flag a derelict nearby.", title="Sensors")
        self.assertEqual(len(self.sent), 1)
        self.assertEqual((self.sent[0]["player"], self.sent[0]["name"]), (self.ship, "Sensors"))

    def test_nothing_for_an_empty_line(self):
        US.universe_chatter_card(self.side, "")
        US.universe_comms("")
        self.assertEqual(self.sent, [])

    def test_a_big_beat_is_an_incoming_hail(self):
        US.universe_hail("The frontier is yours.", title="VICTORY")
        q = H.hail_pending(self.ship)
        self.assertEqual(len(q), 1)
        self.assertEqual(q[0].get("name"), "VICTORY")


if __name__ == "__main__":
    unittest.main()
