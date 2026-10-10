"""A broken save on Continue stops at the start screen.

A save that is there and will not load used to start an unsaved new game behind one card.
Now `universe_map_begin` asks first (`universe_save_unusable`), and when the answer is a
sentence it does not start: the sentence goes where the start screen shows its text, the
server console goes back to the picker, the sim is paused again and the game is not
"started". The file is still never written over and still copied aside, and New Game on
the same slot still works.

Two layers, both on the REAL files:

  * `universe_save_unusable` itself (universe_helpers.py, through MAST's own `import`);
  * the top of `universe_map_begin`, CUT OUT OF THE REAL universe.mast - from its label
    to the line that reads the universe file - and run as a scheduled task, the way the
    start screen's Start schedules the map. A marker after the cut says whether it went
    on. `show_server_menu` and `client_main` (the LegendaryMissions consoles addon's
    labels) are stood in for by labels that only say they were reached.

Headless, `--map 0` starts the map without the start screen. "Stopped" there is the same
thing this test reads: nothing of the universe was built, the sim is paused, and
`GAME_STARTED` is False (see the build report for the run).

Run (from a COPY of the OpenUniverse folder - `DEBUG()` writes debug.log where it runs):

    python -m unittest discover -s tests -p "test_save_stop.py"
"""
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
if os.path.isdir(SBS):
    sys.path.insert(0, SBS)

from sbs_utils.fs import test_set_exe_dir
test_set_exe_dir()

import cosmos_dev.mock.sbs as mock_sbs
sys.modules.setdefault("sbs", mock_sbs)

import sbs_utils.fs as fs
import sbs_utils.mast_sbs.story_nodes  # noqa: F401
import sbs_utils.mast_sbs.mast_sbs_procedural  # noqa: F401
from sbs_utils.agent import Agent
from sbs_utils.delete_queue import DeleteQueue
from sbs_utils.gui import Gui
from sbs_utils.handlerhooks import reset_mission_state
from sbs_utils.helpers import Context, FakeEvent, FrameContext
from sbs_utils.mast.mast_globals import MastGlobals
from sbs_utils.mast.mastscheduler import MastScheduler
from sbs_utils.mast.maststory import MastStory
from sbs_utils.mast_sbs.maststorypage import StoryPage
from sbs_utils.tickdispatcher import TickDispatcher

STOP_FIXTURES = os.path.join(_HERE, "saves")
STOP_USUAL_TEXT = "Pick a universe and press Start."


def _stop_map_begin_top():
    """The top of the real `universe_map_begin`: every line from its label to the one
    that reads the universe file (not included)."""
    with open(os.path.join(OU_CORE, "universe.mast"), encoding="utf-8") as f:
        text = f.read().replace("\r\n", "\n")
    m = re.search(r"^=== universe_map_begin\n(.*?)^    shared UNIVERSE_DOC = ",
                  text, re.S | re.M)
    assert m, "universe.mast no longer has the top of universe_map_begin this test cuts"
    return m.group(1)


def _stop_story(mode):
    return "\n".join([
        "import universe_helpers.py",
        "import universe_mode.py",
        "import universe_doc.py",
        "import universe_sides.py",
        "import universe_amd.py",
        "import universe_landmarks.py",
        "import universe_relics.py",
        "import universe_sites.py",
        'shared UNIVERSE_SELECT = "Stop Test"',
        "shared SAVE_SLOT = 1",
        'shared START_MODE = "%s"' % mode,
        'shared START_TEXT = "%s"' % STOP_USUAL_TEXT,
        # What Start (or the runner's --map) has already done by the time the map runs.
        "shared GAME_STARTED = True",
        "shared AUTO_START = True",
        "shared UNIVERSE_ACTIVE = False",
        "shared STOP_WENT_ON = False",
        'shared STOP_SERVER_AT = "started"',
        "task_schedule(universe_map_begin)",
        "gui_text('$text:harness;')",
        "await gui()",
        "",
        "=== universe_map_begin",
        _stop_map_begin_top().rstrip("\n"),
        "    shared STOP_WENT_ON = True",
        "    ->END",
        "",
        "=== show_server_menu",
        '    shared STOP_SERVER_AT = "show_server_menu"',
        "    gui_text('$text:menu;')",
        "    await gui()",
        "",
        "=== client_main",
        "    gui_text('$text:client;')",
        "    await gui()",
        "",
    ])


class StopPage(StoryPage):
    story = None


def _stop_bytes(path):
    with open(path, "rb") as f:
        return f.read()


class _StopBase(unittest.TestCase):
    mode = "Continue"

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
        self.root = tempfile.mkdtemp(prefix="ou_save_stop_")
        self.addCleanup(shutil.rmtree, self.root, True)
        self.mission = os.path.join(self.root, "mission")
        os.makedirs(self.mission)
        fs.script_dir = self.mission
        reset_mission_state()
        fs.script_dir = self.mission
        Gui.clients = {}
        Gui.widget_list_sent = {}
        mock_sbs.create_new_sim()
        mock_sbs.resume_sim()
        DeleteQueue.clear()
        TickDispatcher.clear()
        FrameContext.context = Context(mock_sbs.sim, mock_sbs, FakeEvent(0, "test"))
        Agent.SHARED.set_inventory_value("sim", mock_sbs.sim)
        self.rte = []
        self._orig_rte = MastScheduler.on_runtime_error
        MastScheduler.on_runtime_error = self.rte.append
        # The save the map will be pointed at: common_data is the mission's SIBLING.
        self.path = os.path.join(self.root, "common_data", "saves",
                                 "universe_save_stop_test_1.yaml")
        os.makedirs(os.path.dirname(self.path))
        self.original = self.put_save()

    def tearDown(self):
        MastScheduler.on_runtime_error = self._orig_rte
        Gui.clients = {}
        Gui.widget_list_sent = {}
        StopPage.story = None
        FrameContext.task = None
        FrameContext.page = None
        FrameContext.mast = None
        TickDispatcher.clear()
        reset_mission_state()
        FrameContext.context = None

    def put_save(self):
        """The slot's file. A broken one, unless a test says otherwise."""
        with open(self.path, "w", encoding="utf-8", newline="\n") as f:
            f.write("players: [unclosed\n  nope: : :\n")
        return _stop_bytes(self.path)

    def start(self):
        """Press Start: the story is compiled and run, and the map task with it."""
        story = MastStory()
        story.basedir = OU_CORE
        errors = story.compile(_stop_story(self.mode), "savestop", story)
        self.assertEqual(errors, [], f"compile errors: {errors}")
        story.compiler_errors = []
        StopPage.story = story
        FrameContext.mast = story
        self.server = StopPage()
        Gui.push(0, self.server)
        for _ in range(4):
            mock_sbs.sim._time_tick_counter += 30
            FrameContext.context = Context(mock_sbs.sim, mock_sbs,
                                           FakeEvent(0, "gui_present"))
            self.server.gui_state = "repaint"
            self.server.present(FakeEvent(0, "gui_present"))
            TickDispatcher.dispatch_tick()
        self.assertEqual(self.rte, [], f"MAST runtime errors: {self.rte}")
        inside = os.path.normcase(os.path.abspath(
            MastGlobals.globals["universe_save_path"]())) == os.path.normcase(self.path)
        self.assertTrue(inside, "the map was pointed at another file than the test's")

    def shared(self, name):
        return Agent.SHARED.get_inventory_value(name)

    def files(self):
        return sorted(os.listdir(os.path.dirname(self.path)))


class ABrokenSaveOnContinueStops(_StopBase):

    def test_the_map_does_not_go_on(self):
        self.start()
        self.assertIs(self.shared("STOP_WENT_ON"), False, "it played on behind a card")
        self.assertIs(self.shared("UNIVERSE_ACTIVE"), False)

    def test_the_server_is_back_at_the_picker_with_the_game_not_started(self):
        self.start()
        self.assertEqual(self.shared("STOP_SERVER_AT"), "show_server_menu")
        self.assertIs(self.shared("GAME_STARTED"), False)
        self.assertTrue(mock_sbs.sim._paused, "the sim was left running")
        # Left on, the start screen would press Start again by itself.
        self.assertIs(self.shared("AUTO_START"), False)

    def test_the_start_screen_says_which_file_and_why_and_what_to_do(self):
        self.start()
        text = self.shared("START_TEXT")
        self.assertNotEqual(text, STOP_USUAL_TEXT)
        self.assertIn("universe_save_stop_test_1.yaml", text)
        self.assertIn("could not be loaded", text)
        self.assertIn("not a file this game can read", text)
        self.assertIn("universe_save_stop_test_1.yaml.unreadable.bak", text)
        self.assertIn("New Game", text)
        self.assertIn("Save Slot", text)
        self.assertTrue(text.isascii())
        for ch in "{}`[]#^":
            self.assertNotIn(ch, text)

    def test_the_file_is_untouched_and_copied_aside(self):
        self.start()
        self.assertEqual(_stop_bytes(self.path), self.original)
        self.assertEqual(_stop_bytes(self.path + ".unreadable.bak"), self.original)
        self.assertEqual(self.files(), ["universe_save_stop_test_1.yaml",
                                        "universe_save_stop_test_1.yaml.unreadable.bak"])

    def test_pressing_start_again_on_continue_stops_again_and_makes_no_second_copy(self):
        self.start()
        self.start()
        self.assertIs(self.shared("STOP_WENT_ON"), False)
        self.assertEqual(self.files(), ["universe_save_stop_test_1.yaml",
                                        "universe_save_stop_test_1.yaml.unreadable.bak"])


class ASaveThatWillNotUpgradeStopsToo(_StopBase):
    def put_save(self):
        shutil.copyfile(os.path.join(STOP_FIXTURES, "v1_default.yaml"), self.path)
        return _stop_bytes(self.path)

    def test_the_function_itself(self):
        """A step of the upgrade ladder that raises, as a build with a bad migration
        has. Asked of the function: the story's own `import` re-reads the ladder."""
        story = MastStory()
        story.basedir = OU_CORE
        self.assertEqual(story.compile("import universe_helpers.py\n", "savestop_fn",
                                       story), [])
        fn = MastGlobals.globals
        g = fn["universe_save_players"].__globals__
        old = g["_MIGRATIONS"]

        def boom(data):
            raise ValueError("migration step 1 is broken")
        g["_MIGRATIONS"] = {1: boom}
        self.addCleanup(g.__setitem__, "_MIGRATIONS", old)
        fn["universe_set_active_save"]("Stop Test", 1)
        text = fn["universe_save_unusable"]("Continue")
        self.assertIn("older version", text)
        self.assertIn("universe_save_stop_test_1.yaml.v1.bak", text)
        self.assertEqual(_stop_bytes(self.path), self.original)
        self.assertEqual(_stop_bytes(self.path + ".v1.bak"), self.original)
        # New Game is never refused.
        self.assertEqual(fn["universe_save_unusable"]("New Game"), "")


class NewGameOnThatSlotStillStarts(_StopBase):
    mode = "New Game"

    def test_the_map_goes_on_and_nothing_is_said(self):
        self.start()
        self.assertIs(self.shared("STOP_WENT_ON"), True)
        self.assertEqual(self.shared("START_TEXT"), STOP_USUAL_TEXT)
        self.assertIs(self.shared("GAME_STARTED"), True)
        self.assertFalse(mock_sbs.sim._paused)
        self.assertNotEqual(self.shared("STOP_SERVER_AT"), "show_server_menu")
        # The check itself wrote nothing and copied nothing.
        self.assertEqual(_stop_bytes(self.path), self.original)
        self.assertEqual(self.files(), ["universe_save_stop_test_1.yaml"])

    def test_and_the_save_begin_that_follows_keeps_the_copy(self):
        """What the map does next, a few hundred lines on: `universe_save_begin`."""
        self.start()
        MastGlobals.globals["universe_save_begin"]("New Game")
        self.assertEqual(_stop_bytes(self.path + ".previous.bak"), self.original)
        self.assertEqual(MastGlobals.globals["universe_save_blocked"](), "")


class AGoodSaveAndNoSaveStart(_StopBase):
    def put_save(self):
        shutil.copyfile(os.path.join(STOP_FIXTURES, "v2_story.yaml"), self.path)
        return _stop_bytes(self.path)

    def test_continue_with_a_save_that_loads_goes_on(self):
        self.start()
        self.assertIs(self.shared("STOP_WENT_ON"), True)
        self.assertEqual(self.shared("START_TEXT"), STOP_USUAL_TEXT)
        self.assertEqual(_stop_bytes(self.path), self.original)

    def test_continue_with_no_file_goes_on(self):
        os.remove(self.path)
        self.start()
        self.assertIs(self.shared("STOP_WENT_ON"), True)
        self.assertEqual(self.files(), [])

    def test_a_save_from_a_newer_build_is_played_as_before(self):
        with open(self.path, "w", encoding="utf-8", newline="\n") as f:
            f.write("save_version: 9\nuniverse_seed: 5\ncurrent_system:\n- 4\n- 4\n")
        self.start()
        self.assertIs(self.shared("STOP_WENT_ON"), True)


if __name__ == "__main__":
    unittest.main()
