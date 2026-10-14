"""A landmark's `Guards:` and `Terrain:` are prefabs (universe_landmarks.py).

Drives the real helpers against REAL compiled prefab labels standing in for LM's
`fleet/raider` and `terrain/nebula/sphere`: the older phrases (`Guards: torgoth 3`,
`Terrain: nebula red`) still mean what they always did, and the nested Prefab / Count /
Data block reaches the prefab with its arguments.

Run (from the OpenUniverse folder):
    python -m unittest discover -s tests -p "test_landmark_prefabs.py"
"""
import importlib.util
import os
import types
import unittest

from sbs_utils.fs import test_set_exe_dir
test_set_exe_dir()

import sbs_utils.mast_sbs.story_nodes  # noqa: F401  import first to break a circular import
from cosmos_dev.mock import sbs
from sbs_utils.helpers import FrameContext, Context, FakeEvent
from sbs_utils.handlerhooks import reset_mission_state
from sbs_utils.gui import GuiClient
from sbs_utils.mast.maststory import MastStory
from sbs_utils.mast.mast_globals import MastGlobals
from sbs_utils.mast.mast_node import MastDataObject
from sbs_utils.mast_sbs.maststoryscheduler import StoryScheduler
from sbs_utils.procedural.inventory import get_inventory_value
from sbs_utils.procedural.roles import role
from sbs_utils.procedural.query import to_id_list

for _m in ("spawn", "inventory", "query"):
    MastGlobals.import_python_module("sbs_utils.procedural." + _m)

_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "universe_landmarks", os.path.join(_HERE, "..", "universe_core", "universe_landmarks.py"))
UL = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(UL)

STORY = '''
->END

=== prefab_test_fleet
metadata: ``` yaml
type: prefab/fleet/raider
race: kralien
fleet_difficulty: 5
ship_roles: raider
```
    obj = npc_spawn(START_X, START_Y, START_Z, "Guard", "raider, test_guard", "tsn_light_cruiser", "behav_npcship")
    set_inventory_value(obj, "race", race)
    set_inventory_value(obj, "fleet_difficulty", fleet_difficulty)
    set_inventory_value(obj, "ship_roles", ship_roles)
    yield result to_id(obj)

=== prefab_test_nebula
metadata: ``` yaml
type: prefab/terrain/nebula/sphere
```
    default cluster_color = None
    default density = 1.0
    obj = terrain_spawn(START_X, START_Y, START_Z, "", "#, test_nebula", "nebula", "behav_nebula")
    set_inventory_value(obj, "size_x", SIZE_X)
    set_inventory_value(obj, "cluster_color", cluster_color)
    set_inventory_value(obj, "density", density)
    yield result to_id(obj)
'''


class LandmarkPrefabFields(unittest.TestCase):
    def setUp(self):
        reset_mission_state()
        sbs.create_new_sim()
        FrameContext.context = Context(sbs.sim, sbs, FakeEvent())
        self.story = MastStory()
        self.assertEqual(self.story.compile(STORY, "lm_prefabs", self.story), [])
        FrameContext.mast = self.story
        self.sched = StoryScheduler(self.story)
        self.page = types.SimpleNamespace(story=self.story, gui_task=None)
        self.page.gui_task = self.sched.run(0, self.page, "main", None, None, True)
        GuiClient(0).page_stack.append(self.page)
        FrameContext.page = self.page

    def tearDown(self):
        FrameContext.task = None
        FrameContext.page = None
        FrameContext.mast = None
        reset_mission_state()

    def _guards(self):
        return [i for i in to_id_list(role("test_guard"))]

    def test_the_old_guards_phrase_is_the_raider_fleet(self):
        lm = MastDataObject({"key": "ruin", "guards": "torgoth 3"})
        self.assertTrue(UL.universe_landmark_guards_create(lm, (0, 0, 0), 5))
        (g,) = self._guards()
        self.assertEqual(get_inventory_value(g, "race"), "torgoth")
        self.assertEqual(get_inventory_value(g, "fleet_difficulty"), 3)
        self.assertEqual(get_inventory_value(g, "ship_roles"), "raider, landmark_guards")

    def test_a_named_prefab_with_a_count(self):
        lm = MastDataObject({"key": "ruin", "guards": "fleet/raider x2"})
        self.assertTrue(UL.universe_landmark_guards_create(lm, (0, 0, 0), 4))
        guards = self._guards()
        self.assertEqual(len(guards), 2)
        # Unwritten difficulty is the mission's, as it always was.
        self.assertEqual(get_inventory_value(guards[0], "fleet_difficulty"), 4)

    def test_the_nested_block_carries_its_arguments(self):
        lm = MastDataObject({"key": "ruin", "guards": {
            "Prefab": "fleet/raider", "Count": 1,
            "Data": {"Race": "skaraan", "Fleet difficulty": 7}}})
        self.assertTrue(UL.universe_landmark_guards_create(lm, (0, 0, 0), 4))
        (g,) = self._guards()
        self.assertEqual(get_inventory_value(g, "race"), "skaraan")
        self.assertEqual(get_inventory_value(g, "fleet_difficulty"), 7)

    def test_the_old_terrain_phrase_is_the_cover_nebula(self):
        lm = MastDataObject({"key": "ruin", "terrain": "nebula red"})
        self.assertTrue(UL.universe_landmark_terrain_create(lm, (0, 0, 0)))
        (n,) = to_id_list(role("test_nebula"))
        self.assertEqual(get_inventory_value(n, "size_x"), 9000)
        self.assertEqual(get_inventory_value(n, "cluster_color"), "red")
        self.assertEqual(get_inventory_value(n, "density"), 2)

    def test_no_guards_written_is_none(self):
        self.assertFalse(UL.universe_landmark_guards_create(MastDataObject({"key": "x"}),
                                                            (0, 0, 0)))


if __name__ == "__main__":
    unittest.main()
