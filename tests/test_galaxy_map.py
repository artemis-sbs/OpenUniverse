"""The galaxy map as a TILE MAP - one map for Navigation and the Admiral's Galaxy tab.

What a player would notice, and what cannot be seen without building it:

* **North is up and each system is a 3x3 block** - the glyph in the middle, its frame
  round it - so a click ANYWHERE in a block picks that system.
* **The frame says what the system is to YOU**, strongest last: whose it is, a quest
  target, where you are, what you picked. Two sides see the same system differently.
* **Nothing stacks**: ships ride the top of a frame and fleets the bottom, three a row,
  and a fourth becomes a "+".
* **A quiet refresh changes nothing** - the panel built on the map's revision is not
  torn down under a click once a second.
* **Click a unit, then a system**: the Orders list is what that pair can do, and never
  "send a ship where it already is".
* **The real pages compile and draw**, and a click on the drawn map reaches the map.

Run from the OpenUniverse folder:
    PYTHONPATH=../sbs_utils python -m unittest tests.test_galaxy_map
"""
import glob
import os
import sys
import tempfile
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
OU_CORE = os.path.join(_HERE, "..", "universe_core")
ADMIRAL = os.path.join(_HERE, "..", "admiral")
sys.path.insert(0, os.path.abspath(os.path.join(_HERE, "..", "..", "sbs_utils")))

from sbs_utils.fs import test_set_exe_dir

test_set_exe_dir()

import cosmos_dev.mock.sbs as mock_sbs

sys.modules.setdefault("sbs", mock_sbs)

import sbs_utils.mast_sbs.story_nodes  # noqa: F401  (registers the gui/route nodes)
from sbs_utils.agent import clear_shared
from sbs_utils.gui import Gui, GuiClient
from sbs_utils.helpers import Context, FakeEvent, FrameContext
from sbs_utils.mast.mast_globals import MastGlobals
from sbs_utils.mast.mast_node import MastDataObject
from sbs_utils.mast.mastscheduler import MastScheduler
from sbs_utils.mast.maststory import MastStory
from sbs_utils.mast_sbs.maststorypage import StoryPage
from sbs_utils.procedural import tilemap as T
from sbs_utils.procedural.execution import set_shared_variable
from sbs_utils.procedural.gui import xess as X
from sbs_utils.procedural.inventory import set_inventory_value
from sbs_utils.procedural.query import to_id
from sbs_utils.procedural.spawn import player_spawn
from sbs_utils.spaceobject import SpaceObject

# Every OU .py in ONE namespace, the way MAST's `import file.py` shares them: the map's
# calls into universe_helpers / universe_sides resolve exactly as they do in the game.
NS = {"__name__": "ou_merged", "__builtins__": __builtins__}
for _dir in (OU_CORE, ADMIRAL):
    for _path in sorted(glob.glob(os.path.join(_dir, "*.py"))):
        with open(_path, "r", encoding="utf-8") as f:
            exec(compile(f.read(), os.path.basename(_path), "exec"), NS)

CID = 0x8000000000000001
RIVAL = 0x8000000000000002

SIDES = [
    MastDataObject({"key": "tsn", "name": "TSN", "color": "#33aaff", "homes": [[0, 0]],
                    "diplomacy": "player"}),
    MastDataObject({"key": "kralien", "name": "Kralien", "color": "#ff8800",
                    "homes": [[3, 1]], "diplomacy": "foe"}),
]


class _Base(unittest.TestCase):
    def setUp(self):
        clear_shared()
        SpaceObject.clear()
        T.tilemap_clear()
        T.tilemap_clear_tilesets()
        X.xess_clear()
        self.addCleanup(T.tilemap_clear)
        self.addCleanup(X.xess_clear)
        Gui.clients = {}
        Gui.widget_list_sent = {}
        mock_sbs.create_new_sim()
        mock_sbs.resume_sim()
        FrameContext.context = Context(mock_sbs.sim, mock_sbs, FakeEvent(0, "test"))
        FrameContext.page = None
        FrameContext.task = None
        Gui.clients[CID] = GuiClient(CID)
        Gui.clients[RIVAL] = GuiClient(RIVAL)
        for name, value in (("universe_seed", 7), ("UNIVERSE_SIDES", SIDES),
                            ("DANGER", "Quiet"), ("universe_systems", {}),
                            ("MAP_REVEAL", "Full Chart"), ("UNIVERSE_REGIONS", []),
                            ("UNIVERSE_LANDMARKS", []), ("GALAXY_MAP_MODE", "tiles")):
            set_shared_variable(name, value)

        # The Admiralty's fleets and voice are stubbed: what is under test is the map.
        self.fleets = {}
        self.said = []
        self.orders_set = []
        self._stub("universe_console_side",
                   lambda cid: "kralien" if cid == RIVAL else "tsn")
        self._stub("admiralty_fleets_of_side",
                   lambda side: [f for f in self.fleets.values() if f.side == side])
        self._stub("admiralty_fleet_cell", lambda key: self.fleets[key].cell)
        self._stub("admiralty_fleet_officer_name", lambda key: "Cmdr " + key.title())
        self._stub("admiralty_fleet_current_order",
                   lambda key: self.fleets[key].get("order", "hold"))
        self._stub("admiralty_fleet_set_order",
                   lambda key, order: (self.orders_set.append((key, order)), "Aye, " + order)[1])
        self._stub("admiralty_say", lambda side, msg: self.said.append((side, msg)))

        self.ship = self.player("Artemis", 2, 5)
        mock_sbs.assign_client_to_ship(CID, self.ship)
        self.errors = []
        self._orig_rte = MastScheduler.on_runtime_error
        MastScheduler.on_runtime_error = self.errors.append
        self.addCleanup(setattr, MastScheduler, "on_runtime_error", self._orig_rte)

    def tearDown(self):
        Gui.clients = {}
        FrameContext.task = None
        FrameContext.page = None
        FrameContext.mast = None
        SpaceObject.clear()

    def _stub(self, name, fn):
        old = NS.get(name)
        NS[name] = fn
        self.addCleanup(NS.__setitem__, name, old)

    def player(self, name, i, j, side="tsn"):
        sid = to_id(player_spawn(0, 0, 0, name, side, "tsn_light_cruiser"))
        set_inventory_value(sid, "universe_cell_i", i)
        set_inventory_value(sid, "universe_cell_j", j)
        return sid

    def fleet(self, key, i, j, side="tsn"):
        self.fleets[key] = MastDataObject({"key": key, "side": side, "alive": 3,
                                           "cell": (i, j)})

    def gm(self, name, *args, **kwargs):
        return NS[name](*args, **kwargs)

    def middle(self, i, j, cid=CID):
        return self.gm("galaxy_map_system_to_cell", cid, i, j)

    def area(self, cid=CID):
        return self.gm("galaxy_map_area", cid)


class TheWindow(_Base):
    def test_it_opens_on_the_ship_and_picks_its_system(self):
        self.gm("galaxy_map_open", CID, "nav")
        self.assertEqual(self.gm("galaxy_map_focus_cell", CID), (2, 5))
        self.assertEqual(self.gm("galaxy_map_selected", CID), (2, 5))
        w, h = T.tilemap_size(self.area())
        self.assertEqual(w, 3 * NS["GALAXY_MAP_ZOOMS"][0])
        self.assertGreater(h, w)

    def test_each_system_is_a_glyph_in_a_frame(self):
        self.gm("galaxy_map_open", CID, "nav")
        x, y = self.middle(2, 5)
        self.assertTrue(T.tilemap_kind(self.area(), x, y).startswith("sys_"))
        frame = {T.tilemap_kind(self.area(), x + dx, y + dy)
                 for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)}
        self.assertEqual(frame, {"frame_nw", "frame_n", "frame_ne", "frame_w", "frame_e",
                                 "frame_sw", "frame_s", "frame_se"})

    def test_north_is_up(self):
        self.gm("galaxy_map_open", CID, "nav")
        self.assertLess(self.middle(2, 6)[1], self.middle(2, 5)[1])
        self.assertGreater(self.middle(3, 5)[0], self.middle(2, 5)[0])

    def test_the_kinds_are_the_generators(self):
        self.gm("galaxy_map_open", CID, "nav")
        for i, j in ((0, 2), (3, 1), (1, 4), (4, 7), (-1, 3), (5, 9)):
            base = NS["universe_system_kind"](7, i, j, "Quiet")
            want = NS["universe_system_side"](SIDES, 7, i, j, base)[1]
            self.assertEqual(T.tilemap_kind(self.area(), *self.middle(i, j)), "sys_" + want,
                             "(%d, %d)" % (i, j))

    def test_UNCHARTED_SPACE_SAYS_NOTHING(self):
        """Fog: the glyph is the unknown square and the info names no owner."""
        set_shared_variable("MAP_REVEAL", "Fog")
        self.gm("galaxy_map_open", CID, "nav")
        self.assertEqual(T.tilemap_kind(self.area(), *self.middle(4, 7)), "sys_fog")
        self.gm("galaxy_map_focus", CID, 4, 7, True)
        text = self.gm("galaxy_map_info_text", CID)
        self.assertIn("Unknown", text)

    def test_a_click_anywhere_in_a_block_picks_that_system(self):
        self.gm("galaxy_map_open", CID, "nav")
        x, y = self.middle(3, 4)
        for dx, dy in ((-1, -1), (1, 0), (0, 1), (0, 0)):
            self.gm("galaxy_map_click", CID, self.area(), x + dx, y + dy)
            self.assertEqual(self.gm("galaxy_map_selected", CID), (3, 4))

    def test_panning_keeps_the_size(self):
        self.gm("galaxy_map_open", CID, "nav")
        size = T.tilemap_size(self.area())
        self.gm("galaxy_map_pan", CID, 3, 0)
        self.assertEqual(self.gm("galaxy_map_focus_cell", CID), (5, 5))
        self.assertEqual(T.tilemap_size(self.area()), size)

    def test_zooming_says_the_page_must_rebuild(self):
        self.gm("galaxy_map_open", CID, "nav")
        self.assertTrue(self.gm("galaxy_map_zoom", CID, 1))
        self.assertEqual(self.gm("galaxy_map_cols", CID), 3 * NS["GALAXY_MAP_ZOOMS"][1])
        self.assertFalse(self.gm("galaxy_map_zoom", CID, -5) and
                         self.gm("galaxy_map_zoom", CID, -1))


class TheFrame(_Base):
    def frame_tint(self, i, j, cid=CID):
        x, y = self.middle(i, j, cid)
        return T.tilemap_tint_at(self.area(cid), x, y - 1)

    def test_picked_beats_here_beats_nothing(self):
        self.gm("galaxy_map_open", CID, "nav")
        picked = self.frame_tint(2, 5)
        self.gm("galaxy_map_click", CID, self.area(), *self.middle(3, 5))
        here = self.frame_tint(2, 5)
        self.assertNotEqual(picked, here)
        self.assertEqual(self.frame_tint(3, 5), picked)
        # A system nobody owns, nobody is in and nobody picked wears the plain frame.
        plain = next((i, j) for i in range(-1, 6) for j in range(2, 9)
                     if (i, j) not in ((2, 5), (3, 5)) and NS["universe_system_side"](
                         SIDES, 7, i, j, NS["universe_system_kind"](7, i, j, "Quiet"))[0] is None)
        self.assertEqual(self.frame_tint(*plain), NS["_GM_FRAME"])

    def test_A_FOES_HOME_IS_RED_TO_YOU_AND_NOT_TO_THEM(self):
        """The same system, two consoles: the map is drawn from where you sit."""
        rival_ship = self.player("Vrak", 3, 2, side="kralien")
        mock_sbs.assign_client_to_ship(RIVAL, rival_ship)
        self.gm("galaxy_map_open", CID, "nav")
        self.gm("galaxy_map_open", RIVAL, "nav")
        mine = T.tilemap_tint_at(self.area(), *self.middle(3, 1))
        theirs = T.tilemap_tint_at(self.area(RIVAL), *self.middle(3, 1, RIVAL))
        self.assertEqual(mine, NS["_GM_HOSTILE"])
        self.assertNotEqual(mine, theirs)

    def test_every_frame_color_is_opaque(self):
        """The engine's handling of a translucent image tint is unmeasured."""
        set_shared_variable("UNIVERSE_REGIONS", [
            {"name": "Veil", "center": [2, 5], "radius": 1, "kind": "antimatter"}])
        self.gm("galaxy_map_open", CID, "nav")
        tints = set(T.tilemap_area(self.area())["tints"].values())
        for t in tints:
            self.assertRegex(t, r"^#[0-9a-f]{6}$")

    def test_a_quest_target_is_flagged(self):
        self._stub("universe_quest_target_sectors", lambda side=None: {(4, 6)})
        self.gm("galaxy_map_open", CID, "nav")
        badges = self.gm("galaxy_map_hints", CID, self.area())
        x, y = self.middle(4, 6)
        self.assertEqual(badges.get((x + 1, y)), ("galaxy_map:quest", NS["_GM_QUEST"]))


class Tokens(_Base):
    def tokens(self):
        return {T.tilemap_where(a)[1:]: a for a in T.tilemap_actors(self.area())}

    def test_ships_ride_the_top_and_fleets_the_bottom(self):
        self.fleet("alpha", 2, 5)
        self.gm("galaxy_map_open", CID, "nav")
        x, y = self.middle(2, 5)
        cells = self.tokens()
        self.assertIn((x - 1, y - 1), cells)               # the ship, top-left
        self.assertIn((x - 1, y + 1), cells)               # the fleet, bottom-left
        self.assertIn(":s:", cells[(x - 1, y - 1)])
        self.assertIn(":f:", cells[(x - 1, y + 1)])

    def test_a_fourth_ship_is_a_plus(self):
        for n in range(3):
            self.player("Extra %d" % n, 2, 5)
        self.gm("galaxy_map_open", CID, "nav")
        x, y = self.middle(2, 5)
        self.assertEqual(len([c for c in self.tokens() if c[1] == y - 1]), 3)
        self.assertEqual(self.gm("galaxy_map_hints", CID, self.area()).get((x + 1, y - 1)),
                         ("galaxy_map:more", "white"))

    def test_A_JUMP_MOVES_THE_MAP_WITH_THE_SHIP(self):
        self.gm("galaxy_map_open", CID, "nav")
        set_inventory_value(self.ship, "universe_cell_i", 4)
        self.gm("galaxy_map_sync", CID)
        self.assertEqual(self.gm("galaxy_map_focus_cell", CID), (4, 5))
        x, y = self.middle(4, 5)
        self.assertIn((x - 1, y - 1), self.tokens())

    def test_A_QUIET_SYNC_CHANGES_NOTHING(self):
        self.gm("galaxy_map_open", CID, "nav")
        rev, map_rev = self.gm("galaxy_map_revision", CID), T.tilemap_revision(self.area())
        for _ in range(3):
            self.gm("galaxy_map_sync", CID)
        self.assertEqual(self.gm("galaxy_map_revision", CID), rev)
        self.assertEqual(T.tilemap_revision(self.area()), map_rev)

    def test_clicking_a_token_picks_its_unit(self):
        self.fleet("alpha", 2, 5)
        self.gm("galaxy_map_open", CID, "admiral")
        x, y = self.middle(2, 5)
        self.gm("galaxy_map_click", CID, self.area(), x - 1, y + 1)
        self.assertEqual(self.gm("galaxy_map_selected_unit", CID), ("fleet", "alpha"))
        # ...and picking a system next KEEPS it: that is the order gesture.
        self.gm("galaxy_map_click", CID, self.area(), *self.middle(4, 4))
        self.assertEqual(self.gm("galaxy_map_selected_unit", CID), ("fleet", "alpha"))
        self.assertEqual(self.gm("galaxy_map_selected", CID), (4, 4))


class Orders(_Base):
    def setUp(self):
        super().setUp()
        set_inventory_value(CID, "ADMIRAL_CAM", self.ship)
        self.gm("galaxy_map_open", CID, "admiral")

    def orders(self):
        return self.gm("admiral_galaxy_map_orders", CID)

    def test_NEVER_SEND_A_SHIP_WHERE_IT_ALREADY_IS(self):
        self.gm("galaxy_map_focus", CID, 2, 5, True)
        self.assertFalse([t for t, d in self.orders() if d.get("act") == "send"])
        self.gm("galaxy_map_focus", CID, 3, 5, True)
        sends = [d for t, d in self.orders() if d.get("act") == "send"]
        self.assertEqual(sends, [{"act": "send", "ships": [self.ship], "i": 3, "j": 5}])

    def test_a_picked_fleet_and_a_system_deploy(self):
        self.fleet("alpha", 2, 5)
        self.gm("galaxy_map_select_unit", CID, ("fleet", "alpha"))
        self.gm("galaxy_map_focus", CID, 4, 4, True)
        acts = [(d["act"], d.get("order")) for t, d in self.orders()]
        self.assertIn(("deploy", None), acts)
        self.assertIn(("deploy", "strike"), acts)
        self.assertIn(("deselect", None), acts)

    def test_a_fleet_at_home_takes_standing_orders_but_not_its_current_one(self):
        self.fleet("alpha", 2, 5)
        self.fleets["alpha"].order = "patrol"
        self.gm("galaxy_map_select_unit", CID, ("fleet", "alpha"))
        self.gm("galaxy_map_focus", CID, 2, 5, True)
        orders = [d.get("order") for t, d in self.orders() if d.get("act") == "order"]
        self.assertNotIn("patrol", orders)
        self.assertIn("withdraw", orders)

    def test_a_standing_order_is_given_and_the_unit_let_go(self):
        self.fleet("alpha", 2, 5)
        self.gm("galaxy_map_select_unit", CID, ("fleet", "alpha"))
        self.gm("admiral_galaxy_map_do", CID, {"act": "order", "fleets": ["alpha"],
                                                "order": "strike"})
        self.assertEqual(self.orders_set, [("alpha", "strike")])
        self.assertEqual(self.said, [("tsn", "Aye, strike")])
        self.assertIsNone(self.gm("galaxy_map_selected_unit", CID))

    def test_no_order_line_carries_style_punctuation(self):
        self.player("Odd; Name: {x}", 4, 4)
        self.gm("galaxy_map_focus", CID, 3, 3, True)
        for text, _ in self.orders():
            clean = NS["_agm_text"](text)
            for ch in ";{}":
                self.assertNotIn(ch, clean)

    def test_the_mode_knob(self):
        self.assertTrue(self.gm("galaxy_map_tiles"))
        set_shared_variable("GALAXY_MAP_MODE", "classic")
        self.assertFalse(self.gm("galaxy_map_tiles"))


# --- the real pages ------------------------------------------------------------------

def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


class _Page(StoryPage):
    story = None


class _RealPage(_Base):
    PRELUDE = ""
    FILES = ()
    LABEL = ""

    def setUp(self):
        super().setUp()
        # Only the mission's OWN functions, and put back exactly what was there: the
        # merged namespace also holds library functions it imported.
        self.published = {}
        for name, fn in NS.items():
            if callable(fn) and not name.startswith("_") and \
                    getattr(fn, "__module__", "") == "ou_merged":
                self.published[name] = MastGlobals.globals.get(name)
                MastGlobals.globals[name] = fn
        self.addCleanup(self._unpublish)
        from sbs_utils.pages.layout import tilemap_view as TV
        orig_init = TV.TileView.__init__
        self.views = views = []

        def init(view, *a, **k):
            orig_init(view, *a, **k)
            views.append(view)
        TV.TileView.__init__ = init
        self.addCleanup(setattr, TV.TileView, "__init__", orig_init)
        self.clicks = []
        orig = mock_sbs.send_gui_clickregion
        mock_sbs.send_gui_clickregion = lambda c, p, tag, props, *r: (
            self.clicks.append(tag), orig(c, p, tag, props, *r))
        self.addCleanup(setattr, mock_sbs, "send_gui_clickregion", orig)
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        story = MastStory()
        story.basedir = tmp.name
        src = self.PRELUDE + "jump " + self.LABEL + "\n\n" + "\n".join(
            _read(p) for p in self.FILES)
        errors = story.compile(src, "galaxypage", story)
        self.assertEqual(errors, [], "compile errors: %s" % errors)
        _Page.story = story
        FrameContext.mast = story
        self.page = _Page()
        Gui.push(CID, self.page)
        self.present()

    def _unpublish(self):
        for name, old in self.published.items():
            if old is None:
                MastGlobals.globals.pop(name, None)
            else:
                MastGlobals.globals[name] = old

    def present(self):
        for _ in range(2):
            mock_sbs.sim._time_tick_counter += 30
            FrameContext.context = Context(mock_sbs.sim, mock_sbs, FakeEvent(CID, "gui_present"))
            self.page.gui_state = "repaint"
            self.page.present(FakeEvent(CID, "gui_present"))
        self.assertEqual(self.errors, [], "runtime errors: %s" % self.errors)

    def click_tile(self, x, y):
        view = self.view()
        vx, vy = view.view_cell(x, y)
        FrameContext.context = Context(mock_sbs.sim, mock_sbs, FakeEvent(CID, "gui_message"))
        Gui.on_message(FakeEvent(client_id=CID, tag="gui_message",
                                 sub_tag="%s:c%d_%d" % (view.tag, vx, vy)))

    def view(self):
        self.assertTrue(self.views, "the page drew no tile view")
        return self.views[-1]


class TheNavigationPage(_RealPage):
    PRELUDE = 'shared UNIVERSE_ACTIVE = True\nCONSOLE_SELECT = "jump"\n'
    FILES = (os.path.join(OU_CORE, "universe_galaxy_map.mast"),)
    LABEL = "universe_galaxy_map_tiles"

    def test_it_draws_the_map(self):
        self.assertTrue([t for t in self.clicks if ":c" in str(t)],
                        "the page sent no tile click regions")

    def test_A_CLICK_ON_THE_DRAWN_MAP_PICKS_THE_SYSTEM(self):
        self.click_tile(*self.middle(3, 6))
        self.assertEqual(self.gm("galaxy_map_selected", CID), (3, 6))
        self.present()


class TheAdmiralPage(_RealPage):
    PRELUDE = 'shared UNIVERSE_ACTIVE = True\nshared ADMIRALTY_ECONOMY = False\n'
    FILES = (os.path.join(ADMIRAL, "admiral_galaxy_map.mast"),)
    LABEL = "admiral_galaxy_tiles"

    def setUp(self):
        set_inventory_value(CID, "ADMIRAL_CAM", 0)
        super().setUp()

    def test_a_click_opens_orders(self):
        self.click_tile(*self.middle(1, 1))
        self.assertEqual(X.xess_opened(CID, "admiral_galaxy"), "orders")
        self.present()

    def test_the_panel_is_about_the_picked_system(self):
        self.click_tile(*self.middle(1, 1))
        self.assertEqual(NS["admiral_app_cell"](CID, "admiral_galaxy"), (1, 1))


if __name__ == "__main__":
    unittest.main()
