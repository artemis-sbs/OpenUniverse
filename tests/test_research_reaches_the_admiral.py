"""A research run tells the Admiral when it is done, and its button does not stay offered.

Seen in the engine (C5-15 stills, 2026-10-22): the Admiral pressed "Research Deeper
Silos", the status line said "Research started: Deeper Silos." and then said it for good.
The run did finish - the Lab offered the next step - but "Research complete" went out
only as an info card, which reaches the crew's Comms, not the Admiral. And the Lab's menu
stayed up after the press still offering the step just started; a build refreshes its
worldlet's buttons, research did not.

The two labels are CUT OUT OF THE REAL admiral.mast (`admiral_overseer_research`, which
the Lab's button runs, and `admiralty_research_task`, which it schedules) and run as
tasks. What they call into the rest of the addon is stood in for by a small module that
only records what it was told.

Run from the OpenUniverse folder:
    python -m unittest discover -s tests -p "test_research_reaches_the_admiral.py"
"""
import os
import re
import shutil
import sys
import tempfile
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
OU = os.path.abspath(os.path.join(_HERE, ".."))
ADMIRAL_MAST = os.path.join(OU, "admiral", "admiral.mast")
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


def _research_cut(label):
    """One label of the real admiral.mast, from its `===` line to the next label."""
    with open(ADMIRAL_MAST, encoding="utf-8") as f:
        text = f.read().replace("\r\n", "\n")
    m = re.search(r"^=== " + label + r"\n.*?(?=^(?:===|//|@)|\Z)", text, re.S | re.M)
    assert m, "admiral.mast no longer has " + label
    return m.group(0).rstrip("\n")


# What the labels call, recording what they were told. RESEARCH_TIME is seconds of sim.
_STUB = '''
from sbs_utils.mast.mast_node import MastDataObject

RESEARCH_SAID = []
RESEARCH_CARDS = []
RESEARCH_NAVIGATED = []
RESEARCH_DONE = []
_RESEARCH_BUILDS = []


def research_record():
    """Only functions become MAST globals - the lists are read through this."""
    return {"said": RESEARCH_SAID, "cards": RESEARCH_CARDS,
            "navigated": RESEARCH_NAVIGATED, "done": RESEARCH_DONE}


def research_def(key):
    return MastDataObject({"key": key, "name": "Deeper Silos", "time": 3})


def research_try_start(side, key):
    return None


def research_complete(side, key):
    RESEARCH_DONE.append(key)


def universe_save_players():
    pass


def universe_primary_side():
    return "tsn"


def universe_info_card(line, title, color):
    RESEARCH_CARDS.append(line)


def admiralty_builds(side):
    return _RESEARCH_BUILDS


def admiralty_say(side, msg):
    RESEARCH_SAID.append(msg)
    return msg


def admiralty_msg(side):
    return RESEARCH_SAID[-1] if RESEARCH_SAID else ""


def comms_navigate_override(origins, selected):
    RESEARCH_NAVIGATED.append(selected)
'''


def _research_story():
    return "\n".join([
        "import research_stub.py",
        'task_schedule(admiral_overseer_research, {"RESEARCH_PICK": "silos", '
        '"ADM_ACT_SIDE": "tsn", "ADM_LAB_ID": 1234})',
        "gui_text('$text:harness;')",
        "await gui()",
        "",
        _research_cut("admiral_overseer_research"),
        "",
        "",
        _research_cut("admiralty_research_task"),
        "",
    ])


class ResearchPage(StoryPage):
    story = None


class ResearchReachesTheAdmiral(unittest.TestCase):

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
        self.mission = tempfile.mkdtemp(prefix="ou_research_")
        self.addCleanup(shutil.rmtree, self.mission, True)
        with open(os.path.join(self.mission, "research_stub.py"), "w", encoding="utf-8") as f:
            f.write(_STUB)
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

    def tearDown(self):
        MastScheduler.on_runtime_error = self._orig_rte
        Gui.clients = {}
        Gui.widget_list_sent = {}
        ResearchPage.story = None
        FrameContext.task = None
        FrameContext.page = None
        FrameContext.mast = None
        TickDispatcher.clear()
        reset_mission_state()
        FrameContext.context = None

    def run_for(self, seconds):
        """Press the Lab's button, then let `seconds` of sim go by, a second a tick."""
        story = MastStory()
        story.basedir = self.mission
        errors = story.compile(_research_story(), "research", story)
        self.assertEqual(errors, [], f"compile errors: {errors}")
        story.compiler_errors = []
        ResearchPage.story = story
        FrameContext.mast = story
        page = ResearchPage()
        Gui.push(0, page)
        for _ in range(seconds + 1):
            mock_sbs.sim._time_tick_counter += 30
            FrameContext.context = Context(mock_sbs.sim, mock_sbs, FakeEvent(0, "gui_present"))
            page.gui_state = "repaint"
            page.present(FakeEvent(0, "gui_present"))
            TickDispatcher.dispatch_tick()
        self.assertEqual(self.rte, [], f"MAST runtime errors: {self.rte}")
        self.seen = MastGlobals.globals["research_record"]()
        return MastGlobals.globals

    def test_THE_ADMIRAL_IS_TOLD_WHEN_IT_IS_DONE(self):
        g = self.run_for(6)
        self.assertEqual(self.seen["done"], ["silos"])
        self.assertEqual(g["admiralty_msg"]("tsn"), "Research complete: Deeper Silos.")
        # The crew still hears it, as before.
        self.assertIn("Research complete: Deeper Silos.", self.seen["cards"])

    def test_it_says_started_until_then(self):
        g = self.run_for(1)
        self.assertEqual(self.seen["done"], [])
        self.assertEqual(g["admiralty_msg"]("tsn"), "Research started: Deeper Silos.")

    def test_THE_LABS_BUTTONS_ARE_REFRESHED_ON_THE_PRESS(self):
        g = self.run_for(1)
        self.assertEqual(self.seen["navigated"], [1234])


if __name__ == "__main__":
    unittest.main()
