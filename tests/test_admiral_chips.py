"""The Admiral's map filter chips (admiral/admiral_chips.py), on the galaxy board.

The board is made of proxy tokens, so its chips are a lens on those: the ship and fleet
proxies, and the system markers split into Known and Unknown (fog). What matters is that
a lens reaches the cam's `comms_map_filter` and SURVIVES a board sync, which re-writes
that filter from the whole board.

Run from the OpenUniverse folder with sbs_utils on the path:
    PYTHONPATH=../sbs_utils python -m unittest tests.test_admiral_chips
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sbs_utils.fs import test_set_exe_dir
test_set_exe_dir()

import sbs_utils.mast_sbs.story_nodes  # noqa: F401  (import first to break a circular import)
from cosmos_dev.mock import sbs as mock_sbs
from sbs_utils.agent import clear_shared
from sbs_utils.gui import GuiClient
from sbs_utils.helpers import FrameContext, Context, FakeEvent
from sbs_utils.spaceobject import SpaceObject
from sbs_utils.procedural.inventory import set_inventory_value
from sbs_utils.procedural.query import to_id
from sbs_utils.procedural.spawn import player_spawn, terrain_spawn

from admiral import admiral_chips as AC

ADMIRAL = 0x8080000000000001


class _FakeListBox:
    """Just the two things the chips use: what is picked, and being told to redraw."""
    def __init__(self, picked):
        self.selected = list(picked)
        self.items = []
        self.dirty = 0

    def get_selected(self):
        return list(self.selected)

    def mark_visual_dirty(self):
        self.dirty += 1


class AdmiralGalaxyChipsTests(unittest.TestCase):
    def setUp(self):
        mock_sbs.create_new_sim()
        clear_shared()
        SpaceObject.clear()
        AC.admiral_chips_clear()
        FrameContext.context = Context(mock_sbs.sim, mock_sbs, FakeEvent())
        GuiClient(ADMIRAL)
        self.cam = to_id(player_spawn(0, 0, 0, "Galaxy Cam", "#,galaxy_theater_cam", "invisible"))
        set_inventory_value(ADMIRAL, "GALAXY_CAM", self.cam)
        self.ship = self._token("galaxy_unit", "Artemis")
        self.fleet = self._token("galaxy_fleet", "Harkin")
        self.home = self._token("galaxy_marker", "Home (0,0)", kind="home", cell=(0, 0))
        self.foe = self._token("galaxy_marker", "Threat (1,1)", kind="enemy", cell=(1, 1))
        self.mine = self._token("galaxy_marker", "System (2,0)", kind="empty", cell=(2, 0),
                                worldlets=1)
        self.fog = self._token("galaxy_marker", "Unknown (5,4)", kind="fog", cell=(5, 4))

    def tearDown(self):
        FrameContext.context = None

    def _token(self, role_name, name, kind=None, cell=None, worldlets=0):
        obj = terrain_spawn(0, 0, 0, name, role_name, "unknown", "behav_selection")
        set_inventory_value(obj.id, "board_cam", self.cam)
        if kind is not None:
            set_inventory_value(obj.id, "marker_kind", kind)
        if cell is not None:
            set_inventory_value(obj.id, "marker_i", cell[0])
            set_inventory_value(obj.id, "marker_j", cell[1])
        if worldlets:
            set_inventory_value(obj.id, "marker_worldlets", worldlets)
        return obj.id

    def _filter_written(self):
        ds = mock_sbs.sim.get_space_object(self.cam).data_set
        return [ds.get("comms_map_filter", i) for i in range(ds.num_elements("comms_map_filter"))]

    def _pick(self, *keys):
        lb = _FakeListBox(["galaxy:" + k for k in keys])
        AC.admiral_chips_normalize(ADMIRAL, self.cam, "galaxy", lb, "tsn")
        return lb

    def test_the_board_sorts_into_its_own_lenses(self):
        sets = AC.admiral_chips_sets(self.cam, "galaxy")
        self.assertEqual(sets["ships"], {self.ship})
        self.assertEqual(sets["fleets"], {self.fleet})
        self.assertEqual(sets["bases"], {self.home})
        self.assertEqual(sets["threats"], {self.foe})
        self.assertEqual(sets["worldlets"], {self.mine})
        self.assertEqual(sets["unknown"], {self.fog})

    def test_fog_is_in_no_lens_but_unknown(self):
        """A fogged cell's kind, owner and worldlets are what the overseer has NOT
        charted - so no other chip may count it, or the count gives the fog away."""
        sets = AC.admiral_chips_sets(self.cam, "galaxy")
        for key, ids in sets.items():
            if key not in ("all", "unknown"):
                self.assertNotIn(self.fog, ids, key)

    def test_orders_marks_where_ships_were_sent(self):
        artemis = to_id(player_spawn(0, 0, 0, "Artemis", "tsn", "tsn_light_cruiser"))
        set_inventory_value(artemis, "active_objective", [1, 1])
        AC.admiral_chips_clear()
        sets = AC.admiral_chips_sets(self.cam, "galaxy", "tsn")
        self.assertEqual(sets["orders"], {self.foe})       # the system it is headed for

    def test_a_lens_filters_the_cams_map(self):
        self._pick("ships")
        # The cam itself is always kept, so the overseer never loses their own view.
        self.assertEqual(set(self._filter_written()), {self.cam, self.ship})

    def test_all_clears_the_filter(self):
        self._pick("ships")
        lb = _FakeListBox(["galaxy:ships", "galaxy:all"])
        AC.admiral_chips_normalize(ADMIRAL, self.cam, "galaxy", lb, "tsn")
        self.assertEqual(lb.get_selected(), ["galaxy:all"])
        self.assertEqual(self._filter_written(), [])

    def _every_token(self):
        return [self.ship, self.fleet, self.home, self.foe, self.mine, self.fog]

    def test_a_board_sync_keeps_the_lens(self):
        """galaxy_theater_map_filter re-writes the filter from the WHOLE board after every
        sync; without the lens it would restore everything a moment after a tap."""
        self._pick("unknown")
        self.assertEqual(AC.admiral_chips_lens_for_cam(self.cam, "galaxy", self._every_token()),
                         [self.fog])

    def test_no_lens_leaves_the_board_alone(self):
        self.assertEqual(AC.admiral_chips_lens_for_cam(self.cam, "galaxy", self._every_token()),
                         self._every_token())


if __name__ == "__main__":
    unittest.main()
