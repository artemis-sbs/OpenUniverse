"""The Admiral's right-hand panel actually DRAWS, and says where you are.

The column used to be `comms_face` + `comms_control` and one hard-coded list. It is now
the xESS shell on its own surface, with this console's content as apps. Two things here
are load-bearing and neither is visible without building the screen:

* **The bar names the system.** The complaint that started this was "I don't know what
  system the admiral is in easily" - neither view said so anywhere. A bar that draws the
  coordinates but not the name is the same bug with more pixels.
* **A tile is a click region, not just words.** The failure mode of every strip this
  replaced was a widget that drew and did nothing.

Plus the thing that cannot be seen at all: the app area must NOT rebuild on a timer, or
the Build queue's row is replaced under the cursor as it is clicked.

Run from the OpenUniverse folder with sbs_utils on the path:
    PYTHONPATH=../sbs_utils python -m unittest tests.test_admiral_apps
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sbs_utils.fs import test_set_exe_dir

test_set_exe_dir()

import cosmos_dev.mock.sbs as mock_sbs

# The GUI modules do `import sbs`, which only resolves inside the engine or under the
# mission runner. Bind it before importing anything that needs it.
sys.modules.setdefault("sbs", mock_sbs)

import sbs_utils.mast_sbs.story_nodes  # noqa: F401  (registers the gui/route nodes)
from sbs_utils.agent import clear_shared
from sbs_utils.gui import Gui, GuiClient
from sbs_utils.helpers import Context, FakeEvent, FrameContext
from sbs_utils.mast.maststory import MastStory
from sbs_utils.mast.mastscheduler import MastScheduler
from sbs_utils.mast_sbs.maststorypage import StoryPage
from sbs_utils.procedural.execution import set_shared_variable
from sbs_utils.procedural.gui import xess as X
from sbs_utils.procedural.inventory import set_inventory_value
from sbs_utils.procedural.query import to_id
from sbs_utils.procedural.sides import side_ensure
from sbs_utils.procedural.spawn import player_spawn
from sbs_utils.spaceobject import SpaceObject

from sbs_utils.mast.mast_globals import MastGlobals
from admiral import universe_admiralty
from universe_core import universe_helpers

from admiral import admiral_apps as AA

CID = 1


def _publish(mod):
    """Put a mission module's public functions in the MAST namespace.

    In the game every mission .py execs into ONE dict, so `ship_cell` and the `admiralty_*`
    family are simply in scope for each other. Imported as a plain package they are not -
    so the panel would see an empty namespace and report "No system" for every cell, which
    is the state this fixture exists to rule out.
    """
    import inspect
    for name, fn in inspect.getmembers(mod, inspect.isfunction):
        if not name.startswith("_") and fn.__module__ == mod.__name__:
            MastGlobals.globals[name] = fn


def _publish_stub(name, fn):
    MastGlobals.globals[name] = fn

#: The panel under test, as a story. Deliberately tiny - the panel is the subject and the
#: console around it is not.
STORY = """
gui_xess_panel(client_id, "admiral")
await gui()
"""


class PanelPage(StoryPage):
    story = None


class _Emitted:
    """Every rect the page sent this present, by kind."""

    def __init__(self):
        self.texts = []
        self.clicks = []
        self.buttons = []

    def install(self):
        self._orig = {}
        for name, sink in (("send_gui_text", self.texts),
                           ("send_gui_clickregion", self.clicks),
                           ("send_gui_button", self.buttons)):
            orig = getattr(mock_sbs, name)
            self._orig[name] = orig
            setattr(mock_sbs, name, self._rec(sink, orig))

    def remove(self):
        for name, fn in self._orig.items():
            setattr(mock_sbs, name, fn)

    def _rec(self, sink, orig):
        def _fn(client_id, parent, tag, props, left, top, right, bottom):
            sink.append((tag, props or "", left, top, right, bottom))
            return orig(client_id, parent, tag, props, left, top, right, bottom)
        return _fn

    def clear(self):
        self.texts.clear()
        self.clicks.clear()
        self.buttons.clear()

    def saying(self, needle):
        return [t for t in self.texts + self.buttons if needle in (t[1] or "")]

    def click_tags(self):
        return [c[0] for c in self.clicks]


class _PanelBase(unittest.TestCase):
    def setUp(self):
        clear_shared()
        SpaceObject.clear()
        Gui.clients = {}
        Gui.widget_list_sent = {}
        mock_sbs.create_new_sim()
        mock_sbs.resume_sim()
        FrameContext.context = Context(mock_sbs.sim, mock_sbs, FakeEvent(0, "test"))
        FrameContext.page = None
        FrameContext.task = None
        # The client agent FIRST, and registered with Gui: every per-console value here -
        # which app is open, which camera this console rides - is inventory on the client,
        # and `Gui.push` replaces an unregistered one, taking those values with it.
        Gui.clients[CID] = GuiClient(CID)
        X.xess_clear()
        AA.admiral_apps_clear()
        self.addCleanup(X.xess_clear)
        self.addCleanup(AA.admiral_apps_clear)

        # The overseer's camera, and the cell it is in. `ship_cell` is a sibling global in
        # the game; here the inventory it reads is set directly.
        self.cam = to_id(player_spawn(0, 1000, 0, "Cam", "tsn,admiral_cam", "invisible"))
        set_inventory_value(self.cam, "universe_cell_i", 0)
        set_inventory_value(self.cam, "universe_cell_j", 1)
        set_inventory_value(CID, "ADMIRAL_CAM", self.cam)
        set_shared_variable("ADMIRALTY_ECONOMY", True)


        # The mission namespace the panel reads through. `universe_helpers` is the real
        # thing (ship_cell, universe_system_kind, universe_system_title); the Admiralty's
        # economy is stubbed, because what is under test is the panel, not the pools - and
        # a stub keeps this file from depending on the whole worldlet chain.
        _publish(universe_helpers)
        # The Admiralty is the real thing: the panel reads this side's queue and status
        # line through it, which is what keeps one admiral's war out of another's.
        _publish(universe_admiralty)
        side_ensure("tsn")
        self.builds_key = [0]
        _publish_stub("admiralty_build_count_key",
                      lambda builds, msg: (len(builds or []), msg))
        _publish_stub("admiralty_status_line",
                      lambda builds, msg: msg or ("%d building" % len(builds or [])))
        _publish_stub("admiralty_build_queue_area", lambda builds, msg: msg or "")
        _publish_stub("universe_console_side", lambda cid: "tsn")

        AA.admiral_apps_register()
        AA.admiral_app_drawing(CID, AA.SURFACE_SYSTEM)

        self.emitted = _Emitted()
        self.emitted.install()
        self.addCleanup(self.emitted.remove)

        story = MastStory()
        errors = story.compile(STORY, "admiralpanel", story)
        self.assertEqual([], errors, "compile errors: %s" % errors)
        story.compiler_errors = []
        PanelPage.story = story
        FrameContext.mast = story

        self.errors = []
        self._orig_rte = MastScheduler.on_runtime_error
        MastScheduler.on_runtime_error = self.errors.append
        self.page = None

    def tearDown(self):
        MastScheduler.on_runtime_error = self._orig_rte
        Gui.clients = {}
        Gui.widget_list_sent = {}
        PanelPage.story = None
        FrameContext.task = None
        FrameContext.page = None
        FrameContext.mast = None
        FrameContext.context = None
        SpaceObject.clear()

    def build(self):
        """(Re)build the panel from the CURRENT state and record what it draws."""
        Gui.widget_list_sent = {}
        self.page = PanelPage()
        Gui.push(CID, self.page)
        self.present()
        return self.page

    def present(self):
        self.emitted.clear()
        mock_sbs.sim._time_tick_counter += 30
        self.page.gui_state = "repaint"
        self.page.present(FakeEvent(CID, "gui_present"))
        self.assertEqual([], self.errors, "runtime errors: %s" % self.errors)

    def click(self, click_tag):
        FrameContext.context = Context(mock_sbs.sim, mock_sbs,
                                       FakeEvent(CID, "gui_message"))
        Gui.on_message(FakeEvent(client_id=CID, tag="gui_message", sub_tag=click_tag))


class ItDrawsWithoutRaising(_PanelBase):
    def test_the_panel_builds(self):
        self.build()
        self.assertTrue(self.emitted.texts, "the panel drew nothing at all")

    def test_the_bar_says_which_system_this_is(self):
        """The whole reason for the bar. An uncharted cell still answers with its
        coordinates rather than a blank - not knowing a name is ordinary."""
        self.build()
        self.assertTrue(self.emitted.saying("(0, 1)"),
                        "the bar does not name the system: %s"
                        % [t[1] for t in self.emitted.texts][:6])

    def test_every_tile_is_a_click_region(self):
        self.build()
        tags = self.emitted.click_tags()
        for key in ("info", "build", "forces", "log"):
            self.assertIn("xess-app-admiral-%s" % key, tags,
                          "no click region for the %s tile" % key)

    def test_opening_a_tile_draws_that_app(self):
        self.build()
        self.click("xess-app-admiral-info")
        self.build()
        self.assertEqual(X.xess_opened(CID, AA.SURFACE_SYSTEM), "info")
        self.assertTrue(self.emitted.saying("Coords"), "the Info app did not draw")

    def test_each_app_draws(self):
        """A raising app costs only its own tile, so a broken one is SILENT - the panel
        still draws, with an apology where the app was. Assert on the content instead."""
        for key, needle in (("info", "Coords"), ("build", "Nothing under construction"),
                            ("forces", "No ships or fleets"), ("log", "Nothing to report")):
            X.xess_open(CID, key, AA.SURFACE_SYSTEM)
            self.build()
            self.assertTrue(self.emitted.saying(needle),
                            "the %s app drew nothing recognisable" % key)


class TheGalaxyPanelIsItsOwnSurface(_PanelBase):
    def test_an_app_opened_here_does_not_follow_you_to_the_other_view(self):
        X.xess_open(CID, "forces", AA.SURFACE_GALAXY)
        self.assertEqual(X.xess_opened(CID, AA.SURFACE_GALAXY), "forces")
        self.assertIsNone(X.xess_opened(CID, AA.SURFACE_SYSTEM))

    def test_build_is_only_on_the_system_view(self):
        """The theater is not where you build - and a tile that does nothing where it is
        shown is worse than no tile."""
        self.assertIn("build", X.xess_registered(AA.SURFACE_SYSTEM))
        self.assertNotIn("build", X.xess_registered(AA.SURFACE_GALAXY))


class WhatTheAppAreaRebuildsFor(_PanelBase):
    """A timer in here replaces the queue row under a cursor. The countdown belongs to the
    bar, which is compared separately."""

    def test_a_passing_second_changes_nothing(self):
        before = AA.admiral_app_revision(CID, AA.SURFACE_SYSTEM)
        mock_sbs.sim._time_tick_counter += 300
        self.assertEqual(before, AA.admiral_app_revision(CID, AA.SURFACE_SYSTEM))

    def test_a_new_build_does(self):
        before = AA.admiral_app_revision(CID, AA.SURFACE_SYSTEM)
        universe_admiralty.admiralty_builds("tsn").append({"name": "Extractor"})
        self.assertNotEqual(before, AA.admiral_app_revision(CID, AA.SURFACE_SYSTEM))

    def test_moving_the_overseer_does(self):
        before = AA.admiral_app_revision(CID, AA.SURFACE_SYSTEM)
        set_inventory_value(self.cam, "universe_cell_i", 3)
        self.assertNotEqual(before, AA.admiral_app_revision(CID, AA.SURFACE_SYSTEM))


class TheStatusLineHasRoomForASentence(_PanelBase):
    """A mission writes the status line, so its length is not ours to control. On the bar
    it wrapped to six lines and drew over the tiles; it belongs in the prose band above
    them, which is a text area with the panel's width and its own scroll."""

    def test_it_is_not_on_the_bar(self):
        universe_admiralty.admiralty_say("tsn", "No extractors yet - build an Extractor "
                                                "on a worldlet to produce ore and gas.")
        name, job, at = AA.admiral_app_identity(CID, AA.SURFACE_SYSTEM)
        self.assertNotIn("Extractor", job)
        self.assertNotIn("Extractor", at)
        self.assertNotIn("Extractor", name)

    def test_the_bar_is_two_short_lines(self):
        name, job, at = AA.admiral_app_identity(CID, AA.SURFACE_SYSTEM)
        self.assertLess(len(job), 24, "the coords line will wrap onto the tiles")
        self.assertEqual(at.strip(), "")

    def test_it_draws_above_the_tiles(self):
        universe_admiralty.admiralty_say("tsn", "Construction started: Extractor.")
        self.build()
        self.assertTrue(self.emitted.saying("Construction started"),
                        "the status line is nowhere on the panel")


class Cancelling(_PanelBase):
    def test_it_marks_the_record_and_says_so(self):
        from sbs_utils.mast.mast_node import MastDataObject
        rec = MastDataObject({"name": "Extractor"})
        self.assertTrue(AA.admiral_app_cancel(rec))
        self.assertTrue(rec.cancel)

    def test_a_legacy_string_row_is_refused_rather_than_crashed_on(self):
        """A research run files a bare string; `admiralty_build_row` already tolerates
        them in the list, so Cancel must too."""
        self.assertFalse(AA.admiral_app_cancel("Researching shields"))
        self.assertFalse(AA.admiral_app_cancel(None))


class ThePaddScreensAreScopedToThisConsole(_PanelBase):
    """The PADD came back to the Admiral for what the panel has no room for - quests,
    the research tree, the requisition catalog. It enters under the ENGINE name the
    console activates, which is not the word anything else in the mission uses for it."""

    def test_the_padd_is_allowed_on_this_console_under_its_engine_name(self):
        from sbs_utils.procedural.gui.epadd import epadd_console_allowed
        self.assertTrue(epadd_console_allowed("gamemaster_overseer_comms"))
        self.assertTrue(epadd_console_allowed("admiral"))

    def test_it_is_still_not_on_the_other_overseer_screens(self):
        from sbs_utils.procedural.gui.epadd import epadd_console_allowed
        for console in ("director", "gamemaster", "cinematic"):
            self.assertFalse(epadd_console_allowed(console), console)

    def test_the_research_badge_counts_what_could_be_started(self):
        _publish_stub("research_list", lambda: [{"key": "shields"}, {"key": "drives"}])
        _publish_stub("research_state", lambda side, key: "available" if key == "shields" else "done")

        class _Page:
            client_id = CID
        FrameContext.page = _Page()
        self.assertEqual(AA.admiral_padd_research_badge(), "1")

    def test_the_badge_is_quiet_with_no_console(self):
        """A status provider takes no arguments, so with no page it must answer nothing
        rather than a number belonging to somebody else."""
        FrameContext.page = None
        self.assertEqual(AA.admiral_padd_research_badge(), "")


class InfoGridHelpers(unittest.TestCase):
    """The Info app is one text-area grid: yes/no facts are icons, and a value can
    never split a row."""

    def test_yes_no_are_icons(self):
        self.assertIn("icon://check.on", AA._yes_no(True))
        self.assertIn("icon://check.off", AA._yes_no(False))
        self.assertIn("icon://skull", AA._yes_no(True, yes_icon="skull", yes_color="Crimson"))

    def test_stock_against_capacity_is_a_gauge(self):
        self.assertEqual(AA._ticker_line("ORE 2400/4800"), "[ORE](gauge://2400?max=4800&show=frac)")
        self.assertEqual(AA._ticker_line("CMD 0/3"), "[CMD](gauge://0?max=3&show=frac)")
        self.assertEqual(AA._ticker_line("War: none"), "War: none")

    def test_a_pipe_cannot_split_a_row(self):
        self.assertNotIn("|", AA._cell("Kralien | Torgoth"))


if __name__ == "__main__":
    unittest.main()
