"""A landmark's `Site:` is a place the party WALKS when the universe has a map for it.

No new word. A site is walked when the universe's folder holds a tile area file whose
header says `area: <the site's key>`; otherwise it is the text site it always was.

Drives the REAL files - `universe_sites.py`, `universe_landmarks.py`, and the routes of
`universe_sites.mast`, compiled through MAST's own `import` the way a mission loads them -
against the mock, on a temp mission folder holding the files a writer adds
(`tests/site_sample.py`). The landmark loop of `universe.mast` is cut out of the real
file and run as it stands.

What is proved here:

  * Open Universe's own text site (`quiet_shore.amd`, Ferrow Landing) loads exactly as it
    did, declares nothing, and plays through the same routes;
  * a universe with no `.tiles` file makes no call into the tile world;
  * the tile files load at universe start, a site's own things when its file is read,
    and a system rebuilt on return finds them as they were left;
  * docking at a walked site opens a party onto its map; the visit ends when the LAST of
    the party is back aboard; docking again offers it again;
  * a walked site and a text site live in one universe, one visit at a time, each with
    its own facts;
  * a system torn down with a party on the ground brings them home;
  * `Site:` on a derelict and on a worldlet landmark binds, each with a way to arrive.

Run (from a COPY of the OpenUniverse folder - `DEBUG()` writes debug.log where it runs):

    python -m unittest discover -s tests -p "test_tile_sites.py"
"""
import logging
import os
import re
import shutil
import sys
import tempfile
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
OU = os.path.abspath(os.path.join(_HERE, ".."))
OU_CORE = os.path.join(OU, "universe_core")
SBS = os.path.abspath(os.path.join(_HERE, "..", "..", "sbs_utils"))
sys.path.insert(0, SBS)
sys.path.insert(0, _HERE)

from sbs_utils.fs import test_set_exe_dir
test_set_exe_dir()

import cosmos_dev.mock.sbs as mock_sbs
sys.modules.setdefault("sbs", mock_sbs)

import sbs_utils.fs as fs
import sbs_utils.mast_sbs.story_nodes  # noqa: F401
import sbs_utils.mast_sbs.mast_sbs_procedural  # noqa: F401
from sbs_utils.agent import Agent
from sbs_utils.delete_queue import DeleteQueue
from sbs_utils.gui import Gui, GuiClient
from sbs_utils.handlerhooks import reset_mission_state
from sbs_utils.helpers import Context, FakeEvent, FrameContext
from sbs_utils.mast.mast_globals import MastGlobals
from sbs_utils.mast.mastscheduler import MastScheduler
from sbs_utils.mast.maststory import MastStory
from sbs_utils.mast_sbs.maststorypage import StoryPage
from sbs_utils.procedural import boarding as B
from sbs_utils.procedural import boarding_combat as K
from sbs_utils.procedural import boarding_ground as BG
from sbs_utils.procedural import boarding_props as P
from sbs_utils.procedural import boarding_quests as Q
from sbs_utils.procedural import crew
from sbs_utils.procedural import docking
from sbs_utils.procedural import hail as HAIL
from sbs_utils.procedural import tilemap as T
from sbs_utils.procedural.amd import amd_choice_label
from sbs_utils.procedural.amd_dialogue import dialogue_scenes
from sbs_utils.procedural.amd_doc import amd_document, amd_section
from sbs_utils.procedural.amd_mission import amd_mission_data
from sbs_utils.procedural.gui import boarding_gui as G
from sbs_utils.procedural.gui.console_tab import gui_tab_back_while_boarded
from sbs_utils.procedural.inventory import get_inventory_value, set_inventory_value
from sbs_utils.procedural.links import link
from sbs_utils.procedural.query import to_id, to_object
from sbs_utils.procedural.roles import has_role, add_role
from sbs_utils.procedural.sides import side_ensure
from sbs_utils.procedural.signal import signal_emit, signal_observe, signal_unobserve
from sbs_utils.procedural.spawn import npc_spawn, player_spawn, terrain_spawn
from sbs_utils.tickdispatcher import TickDispatcher

import site_sample as SAMPLE

HELM = 0x8000000000000001
WEAP = 0x8000000000000002

# The site's file with no arrival call: such a site goes down as the ship docks.
SITE_NO_HAIL = SAMPLE.SITE.replace(
    SAMPLE.SITE[SAMPLE.SITE.index("## [Voices](voices)"):
                SAMPLE.SITE.index("## [Side Stories](side_stories)")], "")

# A walked site with nothing to say: a map, a door and a key.
SITE_NO_SCENES = """# [Tally Yard](tally_yard)

## [Props](props)

### [Tally house door](yard_door)
---
Area: tally_yard
Mark: yard_door
Blocks: yes
Opens with: key yard_key
---
The only way in.
"""


def _landmark_loop():
    """The landmark loop of the real `universe.mast`, as it stands: from its `for` line
    to the line before the terrain envelope."""
    with open(os.path.join(OU_CORE, "universe.mast"), encoding="utf-8") as f:
        text = f.read().replace("\r\n", "\n")
    m = re.search(r"^    for lm in universe_landmarks_in_system\(.*?(?=^        # Terrain envelope)",
                  text, re.S | re.M)
    assert m, "universe.mast no longer has the landmark loop this test cuts out"
    return m.group(0)


# The files under test; the park; then the real landmark loop as a label of its own, with
# stand-ins for the two docking brains that live in the LegendaryMissions docking addon.
HARNESS_STORY = "\n".join([
    "import universe_helpers.py",
    "import universe_mode.py",
    "import universe_doc.py",
    "import universe_sides.py",
    "import universe_amd.py",
    "import universe_landmarks.py",
    "import universe_relics.py",
    "import universe_sites.py",
    "import universe_sites.mast",
    "gui_text('$text:harness;')",
    "await gui()",
    "",
    "=== harness_landmarks",
    _landmark_loop().rstrip("\n"),
    "    ->END",
    "",
    "=== docking_dock_with_friendly_station",
    "+++ enable",
    "    yield fail if DOCKING_NPC_ID == 0",
    "",
    "=== docking_dock_with_gas_giant",
    "+++ enable",
    "    yield fail if DOCKING_NPC_ID == 0",
    "+++ docked",
    "    signal_emit('ship_orbiting', {'ORBIT_SHIP_ID': DOCKING_PLAYER_ID, 'ORBIT_BODY_ID': DOCKING_NPC_ID})",
    "",
])


class SitePage(StoryPage):
    story = None


def universe_worldlet_spawn(type_key, x, y, z, radius=None):
    """Stands in for the admiral addon's spawner: a body with the `worldlet` role."""
    return terrain_spawn(x, y, z, "Worldlet", "#,worldlet", "planet", "behav_planet")


class _Base(unittest.TestCase):
    """A temp mission folder, the real files compiled, a ship with two consoles."""

    tiles = True                    # does the universe's folder hold the tile files?
    site_text = SAMPLE.SITE

    @classmethod
    def setUpClass(cls):
        cls.saved_globals = dict(MastGlobals.globals)
        cls.old_script_dir = fs.script_dir

    @classmethod
    def tearDownClass(cls):
        MastGlobals.globals.clear()
        MastGlobals.globals.update(cls.saved_globals)
        fs.script_dir = cls.old_script_dir

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="ou_site_test_")
        self.addCleanup(shutil.rmtree, self.root, True)
        self.mission = os.path.join(self.root, "mission")
        os.makedirs(os.path.join(self.mission, "ground"))
        fs.script_dir = self.mission
        reset_mission_state()
        fs.script_dir = self.mission
        Gui.clients = {}
        Gui.widget_list_sent = {}
        mock_sbs.create_new_sim()
        mock_sbs.resume_sim()
        DeleteQueue.clear()
        TickDispatcher.clear()
        crew.crew_clear()
        T.tilemap_clear_tilesets()
        # The docking tick is started once per PROCESS (a module latch that outlives
        # `TickDispatcher.clear()`), and its pairs are never dropped: both begin again.
        setattr(docking, "__docking_tick_task", None)
        getattr(docking, "__docking_pairs").clear()
        FrameContext.context = Context(mock_sbs.sim, mock_sbs, FakeEvent(0, "test"))
        Agent.SHARED.set_inventory_value("sim", mock_sbs.sim)

        self.write("customs.amd", SAMPLE.TEXT_SITE)
        self.write("tally_yard.amd", self.site_text)
        with open(os.path.join(OU, "quiet_shore.amd"), encoding="utf-8") as f:
            self.quiet_shore = f.read().replace("\r\n", "\n")
        self.write("quiet_shore.amd", self.quiet_shore)
        if self.tiles:
            self.write("ground/starter.tileset", SAMPLE.TILESET)
            self.write("ground/tally_yard.tiles", SAMPLE.AREA)

        self.runtime = []
        test = self

        class _H(logging.Handler):
            def emit(self, record):
                test.runtime.append(record.getMessage())
        self._handler = _H()
        logging.getLogger("mast.runtime").addHandler(self._handler)

        MastGlobals.import_python_function(universe_worldlet_spawn)
        story = MastStory()
        story.basedir = OU_CORE
        errors = story.compile(HARNESS_STORY, "tilesites", story)
        self.assertEqual(errors, [], f"compile errors: {errors}")
        story.compiler_errors = []
        SitePage.story = story
        FrameContext.mast = story
        self.story = story
        # The LegendaryMissions `boarding` addon says where a boarded console's Back
        # goes; without it the library complains, rightly, that there is no screen.
        gui_tab_back_while_boarded("boarding_crew")

        self.rte = []
        self._orig_rte = MastScheduler.on_runtime_error
        MastScheduler.on_runtime_error = self.rte.append
        self.seen = []
        signal_observe(self._watch)

        side_ensure("tsn")
        self.ship = to_id(player_spawn(0, 0, 0, "Artemis", "tsn", "tsn_light_cruiser"))
        self.server = SitePage()
        Gui.push(0, self.server)
        self.sit(HELM, "helm")
        self.sit(WEAP, "weapons")
        self.present()
        self.fn("universe_sites_clear")()

    def tearDown(self):
        logging.getLogger("mast.runtime").removeHandler(self._handler)
        signal_unobserve(self._watch)
        MastScheduler.on_runtime_error = self._orig_rte
        Gui.clients = {}
        Gui.widget_list_sent = {}
        SitePage.story = None
        FrameContext.task = None
        FrameContext.page = None
        FrameContext.mast = None
        TickDispatcher.clear()
        crew.crew_clear()
        reset_mission_state()
        T.tilemap_clear_tilesets()
        FrameContext.context = None

    # --- helpers ----------------------------------------------------------------------
    def write(self, name, text):
        path = os.path.join(self.mission, *name.split("/"))
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)

    def fn(self, name):
        return MastGlobals.globals[name]

    def _watch(self, name, data=None):
        self.seen.append(name)

    def sit(self, client_id, console):
        GuiClient(client_id)
        mock_sbs.assign_client_to_ship(client_id, self.ship)
        set_inventory_value(client_id, "CONSOLE_TYPE", console)
        link(self.ship, "consoles", client_id)
        crew.crew_assign(client_id, self.ship, console)

    def present(self, n=2):
        """One second each: the server page painted, then the tick the engine runs."""
        for _ in range(n):
            mock_sbs.sim._time_tick_counter += 30
            FrameContext.context = Context(mock_sbs.sim, mock_sbs,
                                           FakeEvent(0, "gui_present"))
            self.server.gui_state = "repaint"
            self.server.present(FakeEvent(0, "gui_present"))
            TickDispatcher.dispatch_tick()
        self.assertEqual(self.rte, [], f"MAST runtime errors: {self.rte}")

    def emit(self, name, data=None):
        FrameContext.context = Context(mock_sbs.sim, mock_sbs, FakeEvent(0, "test"))
        signal_emit(name, data)
        self.present()

    def begin(self):
        """What `universe_map_begin` does about the tile world, by the function it calls.
        (Looked up, not called by name: against a build from before walked sites, the
        text-site tests should still run - and pass - rather than stop on a NameError.)"""
        begin = MastGlobals.globals.get("universe_site_ground_begin")
        return begin() if begin is not None else None

    def station(self, name, key, cell=(0, 0), fname=None):
        """A station landmark carrying `Site: key`, bound the way the landmark loop does."""
        obj = to_id(npc_spawn(1000, 0, 1000, name, "tsn, station, landmark",
                              "starbase_civil", "behav_station"))
        self.fn("universe_site_load")(key, fname or key + ".amd")
        self.fn("universe_site_place")(key, obj, cell[0], cell[1], name)
        return obj

    def dock(self, obj, accept=True):
        """The ship ties up; the crew takes the call if the site has one."""
        self.emit("ship_docked", {"DOCK_SHIP_ID": self.ship, "DOCK_STATION_ID": obj})
        self.present(6)                       # the call waits out the docking clunk
        if accept and B.boarding_visiting() is None:
            self.emit("boarding_down")

    def down(self, client_id=HELM):
        self.assertIsNotNone(B.boarding_beam_down(client_id))
        self.assertTrue(G.boarding_go_down(client_id))
        self.present(1)
        return B.boarding_me(client_id)

    def up(self, client_id=HELM):
        """BEAM UP, as the ePADD button does it."""
        FrameContext.context = Context(mock_sbs.sim, mock_sbs, FakeEvent(0, "test"))
        self.assertTrue(G.boarding_go_up(client_id))
        self.present(1)

    def beside(self, client_id, key):
        """Stand this console's character next to a prop."""
        lf = B.boarding_me(client_id)
        at = T.tilemap_where(P.boarding_prop(key)["id"])
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            if T.tilemap_is_open(at[0], at[1] + dx, at[2] + dy, ignore=lf):
                T.tilemap_place(lf, at[0], at[1] + dx, at[2] + dy)
                return
        self.fail("no open cell beside " + key)

    def use(self, client_id, key):
        self.beside(client_id, key)
        return P.boarding_interact(client_id, key)

    def pick(self, client_id, starts_with):
        labels = [amd_choice_label(c.get("label")) for c in B.boarding_choices(client_id)]
        index = next((i for i, text in enumerate(labels) if text.startswith(starts_with)),
                     None)
        self.assertIsNotNone(index, f"no choice {starts_with!r} in {labels}")
        self.assertTrue(B.boarding_answer(client_id, index, B.boarding_seq_for(client_id)))
        self.present(1)

    def put_down(self, key):
        at = T.tilemap_where(K.boarding_hostile(key)["id"])
        for _ in range(6):
            if K.boarding_hostile_state(key) == "down":
                return
            K.boarding_strike(at[0], at[1], at[2], 0, "full")
        self.fail(key + " would not go down")


# --- the text site: unchanged ----------------------------------------------------------

class TheTextSiteIsUnchanged(_Base):
    """Open Universe's own site, in a universe WITH a tile world beside it."""

    def expected(self):
        doc = amd_document(self.quiet_shore, data_parser=amd_mission_data)
        return (dialogue_scenes(amd_section(doc, "boarding")),
                dialogue_scenes(amd_section(doc, "hails")))

    def test_ferrow_landing_loads_as_the_record_it_always_was(self):
        self.begin()
        rec = self.fn("universe_site_load")("quiet_shore", "quiet_shore.amd")
        scenes, hails = self.expected()
        self.assertEqual(rec["key"], "quiet_shore")
        self.assertEqual(rec["file"], "quiet_shore.amd")
        self.assertIsNone(rec["name"])
        self.assertEqual(rec["scenes"], scenes)
        self.assertEqual(list(rec["scenes"]), list(scenes))        # the first room is the first
        self.assertEqual(next(iter(rec["scenes"])), "arrival")
        self.assertEqual(rec["hails"], hails)
        self.assertEqual(len(rec["scenes"]), 14)
        self.assertEqual(list(rec["hails"]), ["shore_call"])

    def test_it_is_not_walked_and_puts_nothing_on_any_map(self):
        self.begin()
        self.fn("universe_site_load")("quiet_shore", "quiet_shore.amd")
        area = MastGlobals.globals.get("universe_site_area")
        self.assertIsNone(area("quiet_shore") if area is not None else None)
        self.assertEqual(P._PROPS, {})
        self.assertEqual(K._HOSTILES, {})
        self.assertEqual(BG.boarding_ground_scenes(), {})
        self.assertEqual(self.runtime, [])

    def test_docking_there_plays_the_same_visit(self):
        self.begin()
        shore = self.station("Ferrow Landing", "quiet_shore")
        self.dock(shore, accept=False)
        self.assertIsNone(B.boarding_visiting(), "the call is offered, not taken")
        self.assertTrue(get_inventory_value(shore, "SITE_ASKED", False))
        self.emit("boarding_down")
        visit = B.boarding_visiting()
        self.assertEqual((visit.get("first"), visit.get("place"), visit.get("title")),
                         ("arrival", "quiet_shore", "FERROW LANDING"))
        self.assertFalse(visit.get("tile"))
        self.assertIsNone(B.boarding_invite_area())
        self.assertEqual(B.boarding_scene(), "arrival")
        self.assertEqual(get_inventory_value(self.ship, "SITE_VISITING", None), shore)

    def test_a_text_visit_ends_when_its_scene_closes_not_when_somebody_beams_up(self):
        self.begin()
        house = self.station("Customs House", "customs")
        self.dock(house)
        self.down(HELM)
        self.down(WEAP)
        self.up(WEAP)                         # one of two comes home...
        self.assertIsNotNone(B.boarding_visiting())
        self.emit("boarding_came_back", {"BOARDING_CLIENT": WEAP, "BOARDING_HOME": self.ship})
        self.assertIsNotNone(B.boarding_visiting(), "a text visit is not ended by this")
        self.pick(HELM, "Read the manifest")
        self.pick(HELM, "Beam back up")       # ...and the scene closing is what ends it
        self.present(2)
        self.assertIsNone(B.boarding_visiting())
        self.assertEqual(self.seen.count("boarding_visit_ended"), 1)
        self.assertEqual(B.boarding_facts("customs"), ["the manifest"])
        self.assertFalse(get_inventory_value(house, "SITE_ASKED", True))


class AUniverseWithNoTileFiles(_Base):
    tiles = False

    def test_the_start_makes_no_call_into_the_tile_world(self):
        calls = []
        real = BG.boarding_ground_load
        BG.boarding_ground_load = lambda *a, **k: calls.append(a) or real(*a, **k)
        self.addCleanup(setattr, BG, "boarding_ground_load", real)
        self.assertIsNone(self.begin())
        self.fn("universe_site_load")("quiet_shore", "quiet_shore.amd")
        self.fn("universe_site_load")("customs", "customs.amd")
        self.assertEqual(calls, [])
        self.assertIsNone(BG.boarding_ground_loaded())
        self.assertEqual(list(T.tilemap_areas()), [])
        self.assertEqual(self.runtime, [])
        self.assertEqual(BG.boarding_ground_count(), 0)

    def test_a_site_with_things_for_a_map_and_no_map_is_the_text_site_and_says_so(self):
        """`tally_yard.amd` is there; the area file is not."""
        said = []
        log = self.fn("universe_site_load").__globals__["log"]
        self.fn("universe_site_load").__globals__["log"] = \
            lambda message, *a, **k: said.append(message)
        self.addCleanup(self.fn("universe_site_load").__globals__.__setitem__, "log", log)
        self.begin()
        rec = self.fn("universe_site_load")("tally_yard", "tally_yard.amd")
        # Its scenes are headed `(scenes)`, which a TEXT site does not read, so it has
        # no first room: refused, as a text site with no beats always was.
        self.assertIsNone(rec)
        self.assertEqual(P._PROPS, {})
        self.assertEqual(len(said), 1)
        self.assertIn("this site does not exist", said[0])
        self.assertIn("area: tally_yard", said[0])

    def test_a_text_site_that_also_lists_props_plays_as_text_and_says_they_are_unused(self):
        said = []
        log = self.fn("universe_site_load").__globals__["log"]
        self.fn("universe_site_load").__globals__["log"] = \
            lambda message, *a, **k: said.append(message)
        self.addCleanup(self.fn("universe_site_load").__globals__.__setitem__, "log", log)
        self.write("mixed.amd", SAMPLE.TEXT_SITE + "\n" + SITE_NO_SCENES.split("\n", 2)[2])
        rec = self.fn("universe_site_load")("mixed", "mixed.amd")
        self.assertEqual(next(iter(rec["scenes"])), "customs_counter")
        self.assertEqual(P._PROPS, {})
        self.assertEqual(len(said), 1)
        self.assertIn("played as a site of rooms and choices", said[0])
        self.assertIn("area: mixed", said[0])


# --- the tile world loads in two stages -----------------------------------------------------

class TheGroundLoads(_Base):
    def test_the_start_loads_the_areas_and_puts_nothing_on_them(self):
        result = self.begin()
        self.assertEqual((result["tilesets"], result["areas"], result["props"],
                          result["people"]), (1, 1, 0, 0))
        self.assertIsNotNone(T.tilemap_area("tally_yard"))
        self.assertEqual(self.fn("universe_site_area")("tally_yard"), "tally_yard")
        self.assertIsNone(self.fn("universe_site_area")("customs"))
        self.assertEqual(P._PROPS, {})
        self.assertEqual(self.runtime, [])

    def test_reading_the_sites_file_stands_its_things_on_the_map(self):
        self.begin()
        rec = self.fn("universe_site_load")("tally_yard", "tally_yard.amd")
        self.assertIsNotNone(rec["doc"])
        self.assertEqual(sorted(P._PROPS), ["yard_door", "yard_keycard", "yard_ledger",
                                           "yard_terminal"])
        self.assertEqual(sorted(K._HOSTILES), ["yard_keeper", "yard_loader"])
        self.assertTrue(all(r["id"] is not None for r in P._PROPS.values()))
        self.assertTrue(all(r["id"] is not None for r in K._HOSTILES.values()))
        self.assertEqual(BG.boarding_ground_unplaced(), [])
        self.assertEqual(T.tilemap_where(P.boarding_prop("yard_door")["id"]),
                         ("tally_yard", 16, 5))
        self.assertEqual(K.boarding_hostile_state("yard_keeper"), "calm")
        self.assertIn("yard_terminal", rec["scenes"])
        self.assertEqual(list(rec["hails"]), ["yard_call"])
        self.assertIsNotNone(self.fn("universe_site_stories")("tally_yard"))
        self.assertEqual(self.runtime, [])

    def test_a_walked_site_with_nothing_to_say_is_still_a_place(self):
        self.write("tally_yard.amd", SITE_NO_SCENES)
        self.begin()
        rec = self.fn("universe_site_load")("tally_yard", "tally_yard.amd")
        self.assertIsNotNone(rec, "an area to stand in is enough")
        self.assertEqual(rec["scenes"], {})
        self.assertEqual(sorted(P._PROPS), ["yard_door"])
        yard = self.station("Tally Yard", "tally_yard")
        self.dock(yard)
        self.assertTrue(B.boarding_visiting().get("tile"))

    def test_a_system_rebuilt_on_return_finds_the_door_as_it_was_left(self):
        self.begin()
        self.fn("universe_site_load")("tally_yard", "tally_yard.amd")
        self.assertTrue(P.boarding_prop_open("yard_door"))
        door = P.boarding_prop("yard_door")["id"]
        # The crew leaves; the cell is torn down; they come back and it is built again.
        self.fn("universe_site_release_cell")(0, 0)
        rec = self.fn("universe_site_load")("tally_yard", "tally_yard.amd")
        self.assertIsNotNone(rec)
        self.assertTrue(P.boarding_prop_is_open("yard_door"))
        self.assertEqual(P.boarding_prop("yard_door")["id"], door, "not declared twice")
        self.assertEqual(len(P._PROPS), 4)


# --- arriving, and leaving ------------------------------------------------------------------

class DockingAtAWalkedSite(_Base):
    def setUp(self):
        super().setUp()
        self.begin()
        self.yard = self.station("Tally Yard", "tally_yard")

    def test_the_call_is_offered_and_taking_it_opens_a_party_onto_the_map(self):
        self.dock(self.yard, accept=False)
        self.assertIsNone(B.boarding_visiting())
        self.emit("boarding_down")
        visit = B.boarding_visiting()
        self.assertTrue(visit.get("tile"))
        self.assertEqual((visit.get("area"), visit.get("place"), visit.get("title")),
                         ("tally_yard", "tally_yard", "TALLY YARD"))
        self.assertIsNone(visit.get("first"))
        self.assertEqual(B.boarding_invite_area(), "tally_yard")
        self.assertFalse(B.boarding_is_open(), "no party scene on a map")
        self.assertEqual(get_inventory_value(self.ship, "SITE_VISITING", None), self.yard)
        self.assertEqual(self.runtime, [])

    def test_going_down_stands_you_at_the_entry_and_hands_out_the_side_story(self):
        self.dock(self.yard)
        me = self.down(WEAP)
        self.assertEqual(T.tilemap_where(me), ("tally_yard", 4, 3))
        self.present(2)
        self.assertEqual(Q.boarding_quest_owner("yard_clear"), me)

    def test_the_things_there_work_and_what_is_learned_is_the_sites(self):
        self.dock(self.yard)
        self.down(HELM)
        self.assertEqual(self.use(HELM, "yard_terminal")[0], "scene")
        self.pick(HELM, "Read the log")
        self.assertEqual(B.boarding_facts("tally_yard"), ["the count is short"])
        self.assertEqual(B.boarding_facts(""), [], "not the campaign's")
        self.assertNotEqual(self.use(HELM, "yard_door")[0], "opened")     # no key yet
        self.assertFalse(P.boarding_prop_is_open("yard_door"))
        self.use(HELM, "yard_keycard")
        self.assertTrue(P.boarding_prop("yard_keycard")["taken"])
        self.use(HELM, "yard_door")
        self.assertTrue(P.boarding_prop_is_open("yard_door"))

    def test_a_site_with_no_call_goes_down_as_the_ship_docks(self):
        self.fn("universe_sites_clear")()
        self.write("tally_yard.amd", SITE_NO_HAIL)
        from sbs_utils.procedural.amd_doc import amd_content_cache_clear
        amd_content_cache_clear()
        yard = self.station("Tally Yard", "tally_yard")
        self.dock(yard, accept=False)
        self.assertTrue(B.boarding_visiting().get("tile"))

    def test_the_visit_ends_when_the_LAST_of_the_party_is_back_aboard(self):
        self.dock(self.yard)
        self.down(HELM)
        self.down(WEAP)
        self.up(HELM)
        self.assertIsNotNone(B.boarding_visiting(), "somebody is still down there")
        self.assertEqual(self.seen.count("boarding_visit_ended"), 0)
        self.up(WEAP)
        self.assertIsNone(B.boarding_visiting())
        self.assertIsNone(B.boarding_invitation())
        self.assertEqual(self.seen.count("boarding_visit_ended"), 1)
        self.assertIsNone(get_inventory_value(self.ship, "SITE_VISITING", None))
        self.assertFalse(get_inventory_value(self.yard, "SITE_ASKED", True))
        self.assertEqual(get_inventory_value(HELM, "CONSOLE_TYPE", None), "helm")
        self.assertEqual(get_inventory_value(WEAP, "CONSOLE_TYPE", None), "weapons")

    def test_it_is_not_ended_while_nobody_has_gone_down_yet(self):
        self.dock(self.yard)
        self.present(10)
        self.assertIsNotNone(B.boarding_visiting())
        self.assertEqual(self.fn("universe_site_visit_leave")(), True,
                         "asked outright with nobody on the map, it does end")

    def test_docking_again_offers_it_again_and_the_place_is_as_it_was_left(self):
        self.dock(self.yard)
        self.down(HELM)
        self.use(HELM, "yard_keycard")
        self.use(HELM, "yard_door")
        self.put_down("yard_loader")
        self.up(HELM)
        self.assertIsNone(B.boarding_visiting())
        self.dock(self.yard, accept=False)
        self.assertIsNone(B.boarding_visiting(), "the call again, not a party")
        self.emit("boarding_down")
        self.assertTrue(B.boarding_visiting().get("tile"))
        self.down(HELM)
        self.assertTrue(P.boarding_prop_is_open("yard_door"))
        self.assertTrue(P.boarding_prop("yard_keycard")["taken"])
        self.assertEqual(K.boarding_hostile_state("yard_loader"), "down")
        self.up(HELM)
        self.assertEqual(self.seen.count("boarding_visit_ended"), 2)

    def test_the_route_that_ends_it_is_a_server_route(self):
        with open(os.path.join(OU_CORE, "universe_sites.mast"), encoding="utf-8") as f:
            routes = [line.split()[0] for line in f.read().split("\n") if line.startswith("//")]
        self.assertEqual(sorted(routes), ["//shared/signal/boarding_came_back",
                                          "//shared/signal/boarding_down",
                                          "//shared/signal/boarding_visit_ended",
                                          "//shared/signal/ship_docked",
                                          "//shared/signal/ship_orbiting"])


class AWalkedSiteAndATextSite(_Base):
    def setUp(self):
        super().setUp()
        self.begin()
        self.yard = self.station("Tally Yard", "tally_yard")
        self.house = self.station("Customs House", "customs")

    def test_one_visit_at_a_time(self):
        self.dock(self.yard)
        self.down(HELM)
        self.dock(self.house)
        self.assertEqual(B.boarding_visiting().get("place"), "tally_yard")
        self.assertFalse(get_inventory_value(self.house, "SITE_ASKED", False))
        self.up(HELM)
        self.dock(self.house)
        self.assertEqual(B.boarding_visiting().get("place"), "customs")
        self.assertFalse(B.boarding_visiting().get("tile"))

    def test_each_has_its_own_scenes_and_its_own_facts(self):
        self.dock(self.house)
        self.down(HELM)
        self.pick(HELM, "Read the manifest")
        self.pick(HELM, "Beam back up")
        self.present(2)
        self.assertIsNone(B.boarding_visiting())
        self.dock(self.yard)
        self.down(HELM)
        self.use(HELM, "yard_terminal")
        self.pick(HELM, "Read the log")
        self.assertEqual(B.boarding_facts("customs"), ["the manifest"])
        self.assertEqual(B.boarding_facts("tally_yard"), ["the count is short"])
        self.assertEqual(sorted(self.fn("universe_site_scenes")("customs")),
                         ["customs_counter", "customs_manifest"])
        self.assertNotIn("customs_counter", self.fn("universe_site_scenes")("tally_yard"))
        self.up(HELM)
        self.assertEqual(self.seen.count("boarding_visit_ended"), 2)


class ASystemTornDown(_Base):
    def setUp(self):
        super().setUp()
        self.begin()

    def test_a_party_on_the_ground_there_is_brought_home(self):
        yard = self.station("Tally Yard", "tally_yard", cell=(2, 1))
        self.dock(yard)
        me = self.down(HELM)
        self.assertIsNotNone(T.tilemap_where(me))
        self.assertEqual(self.fn("universe_site_release_cell")(2, 1), 1)
        self.present(1)
        self.assertIsNone(B.boarding_visiting())
        self.assertIsNone(T.tilemap_where(me))
        self.assertFalse(B.boarding_held(HELM))
        self.assertEqual(get_inventory_value(HELM, "CONSOLE_TYPE", None), "helm")
        self.assertEqual(self.seen.count("boarding_visit_ended"), 1)

    def test_another_systems_teardown_leaves_them_where_they_are(self):
        yard = self.station("Tally Yard", "tally_yard", cell=(2, 1))
        self.station("Customs House", "customs", cell=(5, 5))
        self.dock(yard)
        self.down(HELM)
        self.assertEqual(self.fn("universe_site_release_cell")(5, 5), 1)
        self.assertEqual(self.fn("universe_site_release_cell")(9, 9), 0)
        self.assertTrue(B.boarding_visiting().get("tile"))

    def test_a_text_visit_is_left_alone(self):
        house = self.station("Customs House", "customs", cell=(2, 1))
        self.dock(house)
        self.down(HELM)
        self.fn("universe_site_release_cell")(2, 1)
        self.assertIsNotNone(B.boarding_visiting(), "the text flow is unchanged")


# --- a site on a wreck, and on a worldlet ---------------------------------------------------

LANDMARK_UNIVERSE = """# [Test](test)
---
Universe
---

## [Landmarks](landmarks)

### [The Tern](the_tern)
---
At: 0, 0
Kind: derelict
Site: tally_yard
---
A wreck.

### [Grey Moon](grey_moon)
---
At: 0, 0
Kind: worldlet
Type: rock
Site: customs
---
A moon.

### [Assay Office](assay_office)
---
At: 0, 0
Kind: station
Side: tsn
Site: quiet_shore
---
A station.

### [Plain Wreck](plain_wreck)
---
At: 0, 0
Kind: derelict
---
Just a wreck.
"""


class SiteOnAWreckAndAWorldlet(_Base):
    site_text = SITE_NO_HAIL

    def setUp(self):
        super().setUp()
        self.begin()
        landmarks = self.fn("universe_parse_landmarks")(self.fn("universe_doc")(LANDMARK_UNIVERSE))
        self.assertEqual(len(landmarks), 4)
        main = self.server.story_scheduler.tasks[0]
        FrameContext.task = main
        main.start_task(self.story.labels["harness_landmarks"],
                        {"UNIVERSE_LANDMARKS": landmarks, "key": 7, "ei": 0, "ej": 0,
                         "co": mock_sbs.vec3(0.0, 0.0, 0.0)})
        self.present()
        self.tern = self.fn("universe_site_object")("tally_yard", 0, 0)
        self.moon = self.fn("universe_site_object")("customs", 0, 0)
        self.office = self.fn("universe_site_object")("quiet_shore", 0, 0)

    def brain(self, obj):
        pairs = getattr(docking, "__docking_pairs").get(self.ship) or {}
        return pairs[obj].label.name if obj in pairs else None

    def test_all_three_kinds_of_landmark_bind_their_site(self):
        self.assertEqual(sorted(self.fn("universe_sites_in_cell")(0, 0)),
                         ["customs", "quiet_shore", "tally_yard"])
        for obj, role_name in ((self.tern, "universe_derelict"), (self.moon, "worldlet"),
                               (self.office, "station")):
            self.assertIsNotNone(obj)
            self.assertTrue(has_role(obj, "boarding_site"))
            self.assertTrue(has_role(obj, role_name))
        self.assertEqual(get_inventory_value(self.tern, "SITE_KEY", None), "tally_yard")
        self.assertEqual(self.fn("universe_site_title")("tally_yard"), "THE TERN")

    def test_each_has_the_way_to_arrive_that_fits_it(self):
        self.assertEqual(self.brain(self.tern), "universe_site_dock_with_derelict")
        self.assertEqual(self.brain(self.moon), "docking_dock_with_gas_giant")
        self.assertEqual(self.brain(self.office), "docking_dock_with_friendly_station")

    def test_a_wreck_with_no_site_is_still_just_a_wreck(self):
        wrecks = [o for o in Agent.all.values()
                  if has_role(o.id, "universe_derelict") and not has_role(o.id, "boarding_site")]
        self.assertEqual(len(wrecks), 1)
        self.assertIsNone(self.brain(wrecks[0].id))

    def dock_for_real(self, obj):
        """The docking tick's own states, with the ship beside the thing."""
        ship = to_object(self.ship)
        target = to_object(obj)
        ship.pos = mock_sbs.vec3(target.pos.x + 100.0, target.pos.y, target.pos.z)
        ship.data_set.set("dock_state", "undocked", 0)
        self.present(2)
        self.assertEqual(ship.data_set.get("dock_base_id", 0), obj, "`enable` let it in")
        ship.data_set.set("dock_state", "dock_start", 0)
        self.present(2)
        self.assertEqual(ship.data_set.get("dock_state", 0), "docked")
        self.present(3)

    def test_docking_with_the_wreck_sends_ship_docked_once_and_opens_its_site(self):
        self.dock_for_real(self.tern)
        self.assertEqual(self.seen.count("ship_docked"), 1)
        visit = B.boarding_visiting()
        self.assertIsNotNone(visit, "the wreck's site opened")
        self.assertEqual((visit.get("place"), visit.get("tile")), ("tally_yard", True))

    def test_orbiting_the_worldlet_opens_its_site(self):
        self.dock_for_real(self.moon)
        self.assertGreaterEqual(self.seen.count("ship_orbiting"), 1)
        self.present(6)
        self.emit("boarding_down")
        visit = B.boarding_visiting()
        self.assertIsNotNone(visit)
        self.assertEqual(visit.get("place"), "customs")


# --- a site that cannot be made says so where a writer reads ------------------------------

# A text site with its rooms under the heading a WALKED site uses (the lesson's D2).
TEXT_SITE_WRONG_KEY = SAMPLE.TEXT_SITE.replace("## [Scenes](boarding)", "## [Scenes](scenes)")
# A call nobody can accept: the answer's signal is left off, then misspelled (D3).
TEXT_SITE_NO_DOWN = SAMPLE.TEXT_SITE.replace(" ; signal boarding_down", "")
TEXT_SITE_MISSPELLED = SAMPLE.TEXT_SITE.replace("signal boarding_down", "signal boarding_dwon")


class ASiteThatCannotBeMadeSaysSo(_Base):
    """Every refusal used to go to a logger with no handler: `mast.runtime.log` was
    empty beside a site that did not exist (`agent_c5d_report.md` D1, D2, D3)."""
    tiles = False

    def load(self, key, text=None, fname=None):
        if text is not None:
            self.write(fname or key + ".amd", text)
        return self.fn("universe_site_load")(key, fname or key + ".amd")

    def said(self, word):
        return [line for line in self.runtime if word in line]

    def test_a_good_site_says_nothing(self):
        self.assertIsNotNone(self.load("customs"))
        self.assertIsNotNone(self.load("quiet_shore"))
        self.assertEqual(self.runtime, [])

    def test_a_walked_file_with_no_matching_area_does_not_exist_and_says_so_once(self):
        """D1: `area: yard` beside `Site: tally_yard`. It is NOT played as text."""
        self.write("ground/starter.tileset", SAMPLE.TILESET)
        self.write("ground/tally_yard.tiles", SAMPLE.AREA.replace("area: tally_yard",
                                                                  "area: yard"))
        self.begin()
        for _ in range(3):                    # the system is rebuilt on every return
            self.assertIsNone(self.load("tally_yard"))
        said = self.said("tally_yard")
        self.assertEqual(len(said), 1, self.runtime)
        self.assertIn("this site does not exist", said[0])
        self.assertIn("area: tally_yard", said[0])
        self.assertIn("## [Scenes](boarding)", said[0])
        # ... and it really is not there: nothing to dock into.
        obj = to_id(npc_spawn(1000, 0, 1000, "Tally Yard", "tsn, station, landmark",
                              "starbase_civil", "behav_station"))
        self.assertIsNone(self.fn("universe_site_place")("tally_yard", obj, 0, 0, "Tally Yard"))
        self.assertFalse(has_role(obj, "boarding_site"))

    def test_a_text_site_with_its_rooms_under_the_wrong_key(self):
        """D2: `## [Scenes](scenes)` in a site with no map."""
        self.assertIsNone(self.load("customs", TEXT_SITE_WRONG_KEY))
        said = self.said("customs")
        self.assertEqual(len(said), 1, self.runtime)
        self.assertIn("## [Scenes](boarding)", said[0])
        self.assertIn("does not exist", said[0])

    def test_a_site_with_no_rooms_at_all(self):
        text = SAMPLE.TEXT_SITE[:SAMPLE.TEXT_SITE.index("## [Scenes](boarding)")]
        self.assertIsNone(self.load("customs", text))
        self.assertEqual(len(self.said("has no rooms")), 1, self.runtime)

    def test_a_call_no_answer_of_which_sends_a_party(self):
        """D3: the accept answer with no `; signal boarding_down`."""
        rec = self.load("customs", TEXT_SITE_NO_DOWN)
        self.assertIsNotNone(rec, "the site exists: it is the call that is broken")
        said = self.said("signal boarding_down")
        self.assertEqual(len(said), 1, self.runtime)
        self.assertIn("can never go down", said[0])

    def test_a_call_whose_signal_is_misspelled(self):
        self.load("customs", TEXT_SITE_MISSPELLED)
        self.assertEqual(len(self.said("can never go down")), 1, self.runtime)

    def test_a_file_that_is_not_there(self):
        self.assertIsNone(self.load("nowhere"))
        said = self.said("nowhere")
        self.assertTrue(any("was not found" in line for line in said), self.runtime)

    def test_a_new_game_says_it_again(self):
        self.load("customs", TEXT_SITE_NO_DOWN)
        self.fn("universe_sites_clear")()
        self.load("customs")
        self.assertEqual(len(self.said("can never go down")), 2)

    def test_every_warning_in_the_file_goes_through_the_one_function(self):
        with open(os.path.join(OU_CORE, "universe_sites.py"), encoding="utf-8") as f:
            text = f.read()
        loose = [line for line in text.split(chr(10))
                 if '"universe", "warning")' in line and "log(message" not in line
                 and "`log(" not in line and "visit watcher stopped" not in line]
        self.assertEqual(loose, [])
        with open(os.path.join(OU_CORE, "universe_sites.mast"), encoding="utf-8") as f:
            self.assertNotIn('"universe", "warning")', f.read())


# --- "Stay aboard" is not for good ------------------------------------------------------------

class StayAboardThenDockAgain(_Base):
    """`build_report_site.md` and `agent_c5d_report.md` D4: a declined call left
    `SITE_ASKED` set, and that site never called again until its system was rebuilt."""

    def setUp(self):
        super().setUp()
        self.begin()
        self.house = self.station("Customs House", "customs")

    def calls(self):
        return [str(getattr(c, "scene", "")) for c in HAIL.hail_pending(self.ship)]

    def answer(self, starts_with):
        self.assertIsNotNone(HAIL.hail_accept(self.ship))
        while HAIL.hail_advance(self.ship):
            pass
        labels = [amd_choice_label(c.get("label"))
                  for c in (HAIL.hail_active(self.ship) or {}).get("choices") or []]
        index = next(i for i, text in enumerate(labels) if text.startswith(starts_with))
        FrameContext.context = Context(mock_sbs.sim, mock_sbs, FakeEvent(0, "test"))
        self.assertTrue(HAIL.hail_answer(self.ship, index))
        self.present(2)

    def test_declined_it_calls_again_on_the_next_dock(self):
        self.dock(self.house, accept=False)
        self.assertEqual(self.calls(), ["customs_call"])
        self.answer("Stay aboard")
        self.assertIsNone(B.boarding_visiting())
        self.assertEqual(self.calls(), [])
        # The ship lets go and ties up again.
        self.dock(self.house, accept=False)
        self.assertEqual(self.calls(), ["customs_call"], "the site was silenced for good")
        self.answer("Assemble a boarding party")
        self.assertIsNotNone(B.boarding_visiting())
        self.assertEqual(B.boarding_visiting().get("place"), "customs")

    def test_a_call_still_waiting_is_not_placed_twice(self):
        self.dock(self.house, accept=False)
        self.dock(self.house, accept=False)          # a second `ship_docked`, unanswered
        self.assertEqual(self.calls(), ["customs_call"])

    def test_a_second_dock_in_the_seconds_before_the_call_is_placed(self):
        self.emit("ship_docked", {"DOCK_SHIP_ID": self.ship, "DOCK_STATION_ID": self.house})
        self.emit("ship_docked", {"DOCK_SHIP_ID": self.ship, "DOCK_STATION_ID": self.house})
        self.present(8)
        self.assertEqual(self.calls(), ["customs_call"])

    def test_a_call_the_crew_never_picked_up_and_that_was_withdrawn(self):
        self.dock(self.house, accept=False)
        HAIL.hail_cancel(self.ship)
        self.dock(self.house, accept=False)
        self.assertEqual(self.calls(), ["customs_call"])


# --- a visit nobody went down to ---------------------------------------------------------------

class AVisitNobodyWentDownTo(_Base):
    """`agent_c5d_report.md` D5: a site with no `## Hails` opens its party on docking; a
    crew that flew off without going down left that visit open for good, and every other
    site then offered nothing."""
    site_text = SITE_NO_HAIL

    def setUp(self):
        super().setUp()
        self.write("customs.amd", SAMPLE.TEXT_SITE.replace(
            SAMPLE.TEXT_SITE[SAMPLE.TEXT_SITE.index("## [Hails](hails)"):
                             SAMPLE.TEXT_SITE.index("## [Scenes](boarding)")], ""))
        self.begin()
        self.yard = self.station("Tally Yard", "tally_yard", cell=(2, 1))
        self.house = self.station("Customs House", "customs", cell=(2, 1))

    def tie_up(self, obj):
        """Docked for real, as far as the ship's own state says."""
        to_object(self.ship).data_set.set("dock_state", "docked", 0)
        self.dock(obj, accept=False)
        self.assertIsNotNone(B.boarding_visiting(), "a site with no call opens on docking")
        self.present(4)

    def cast_off(self):
        to_object(self.ship).data_set.set("dock_state", "undocked", 0)
        self.present(5)

    def test_a_walked_visit_ends_when_the_ship_undocks(self):
        self.tie_up(self.yard)
        self.assertIsNotNone(B.boarding_visiting())
        self.cast_off()
        self.assertIsNone(B.boarding_visiting(), "left open with nobody down")
        self.assertEqual(self.seen.count("boarding_visit_ended"), 1)
        self.assertIsNone(get_inventory_value(self.ship, "SITE_VISITING", None))

    def test_a_text_visit_ends_when_the_ship_undocks(self):
        self.tie_up(self.house)
        self.assertFalse(B.boarding_visiting().get("tile"))
        self.cast_off()
        self.assertIsNone(B.boarding_visiting(), "left open with nobody down")
        self.assertEqual(self.seen.count("boarding_visit_ended"), 1)

    def test_and_then_the_other_site_can_be_boarded(self):
        self.tie_up(self.yard)
        self.cast_off()
        self.tie_up(self.house)
        self.assertEqual(B.boarding_visiting().get("place"), "customs")

    def test_with_somebody_down_undocking_ends_nothing(self):
        self.tie_up(self.yard)
        self.down(HELM)
        self.cast_off()
        self.assertIsNotNone(B.boarding_visiting(), "pulled off the ground by the helm")
        # ... and a text visit somebody is in is theirs to end.
        self.up(HELM)
        self.assertIsNone(B.boarding_visiting())
        self.tie_up(self.house)
        self.down(HELM)
        self.cast_off()
        self.assertIsNotNone(B.boarding_visiting())

    def test_while_the_ship_stays_docked_nothing_ends(self):
        self.tie_up(self.yard)
        self.present(30)
        self.assertIsNotNone(B.boarding_visiting())

    def test_a_text_visit_nobody_is_in_ends_with_its_system(self):
        self.tie_up(self.house)
        self.assertEqual(self.fn("universe_site_release_cell")(2, 1), 2)
        self.present(1)
        self.assertIsNone(B.boarding_visiting())
        self.assertEqual(self.seen.count("boarding_visit_ended"), 1)

    def test_the_watcher_is_dropped_with_the_game(self):
        self.tie_up(self.yard)
        watch = self.fn("universe_site_load").__globals__["_UNIVERSE_SITE_WATCH"]
        self.assertEqual(len(watch), 1)
        self.fn("universe_sites_clear")()
        self.assertEqual(len(watch), 0)


if __name__ == "__main__":
    unittest.main()
