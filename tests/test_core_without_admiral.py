"""universe_core has to stand without the admiral addon.

A mission made by `sbs create -t ou` loads universe_core and NOT admiral. Two faults in
the diplomacy menu only showed there (found by the Class 5 author lessons):

  1. `sides_standing`, `side_ceasefire_cost`, ... were ALIASES of library functions.
     Only a function a file DEFINES becomes a MAST global, so the routes in
     universe.mast raised NameError the first time Comms selected a station of an
     authored side.
  2. `officers_captured_by` is the admiral addon's, and universe.mast called it bare.

These load the real files through MAST's own `import`, the way a mission does - a plain
Python import of the module finds an alias perfectly well, which is how this got past
test_foundation.
"""
import ast
import glob
import os
import re
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
OU_CORE = os.path.abspath(os.path.join(_HERE, "..", "universe_core"))
ADMIRAL = os.path.abspath(os.path.join(_HERE, "..", "admiral"))
SBS = os.path.abspath(os.path.join(_HERE, "..", "..", "sbs_utils"))
sys.path.insert(0, SBS)

from sbs_utils.fs import test_set_exe_dir
test_set_exe_dir()

import sbs_utils.mast_sbs.story_nodes  # noqa: F401
from sbs_utils.mast.mast_globals import MastGlobals
from sbs_utils.mast.maststory import MastStory

STANDING_NAMES = (
    "sides_standing", "side_offer_tier", "side_foe_deal_standing", "side_reward_mult",
    "side_ceasefire_cost", "side_alliance_standing", "side_ransom_cost",
)


def _public_defs(folder):
    names = set()
    for path in glob.glob(os.path.join(folder, "*.py")):
        with open(path, encoding="utf-8") as f:
            tree = ast.parse(f.read())
        names |= {n.name for n in tree.body
                  if isinstance(n, ast.FunctionDef) and not n.name.startswith("_")}
    return names


def _compile_core_python():
    """Import universe_core's Python through MAST, with no admiral addon."""
    story = MastStory()
    story.basedir = OU_CORE
    source = "import universe_mode.py\nimport universe_reputation.py\n"
    errors = story.compile(source, "core_only", story)
    return story, errors


class CoreWithoutAdmiral(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.saved = dict(MastGlobals.globals)
        # A leftover from another test file must not stand in for the admiral addon.
        for name in _public_defs(ADMIRAL) - _public_defs(OU_CORE):
            MastGlobals.globals.pop(name, None)
        for name in STANDING_NAMES + ("universe_officers_held_by",):
            MastGlobals.globals.pop(name, None)
        cls.story, cls.errors = _compile_core_python()

    @classmethod
    def tearDownClass(cls):
        MastGlobals.globals.clear()
        MastGlobals.globals.update(cls.saved)

    def test_the_files_compile(self):
        self.assertEqual(self.errors, [])

    def test_STANDING_NAMES_ARE_MAST_GLOBALS(self):
        missing = [n for n in STANDING_NAMES if n not in MastGlobals.globals]
        self.assertEqual(missing, [], "universe.mast calls these; an alias of a library "
                                      "function is not exported to MAST")

    def test_a_standing_name_answers_what_the_library_answers(self):
        from sbs_utils.procedural.reputation import reputation_ransom_cost
        for standing in (-50, 0, 40):
            self.assertEqual(MastGlobals.globals["side_ransom_cost"](standing),
                             reputation_ransom_cost(standing))

    def test_NO_OFFICERS_HELD_WHEN_THERE_IS_NO_ADMIRAL(self):
        self.assertNotIn("officers_captured_by", MastGlobals.globals)
        self.assertEqual(MastGlobals.globals["universe_officers_held_by"]("lantern"), [])

    def test_officers_held_asks_the_admiral_when_it_is_loaded(self):
        def officers_captured_by(side_key):
            return ["vance"] if side_key == "lantern" else None

        MastGlobals.import_python_function(officers_captured_by)
        try:
            held = MastGlobals.globals["universe_officers_held_by"]
            self.assertEqual(held("lantern"), ["vance"])
            self.assertEqual(held("nobody"), [])
        finally:
            MastGlobals.globals.pop("officers_captured_by", None)


class CoreMastCallsOnlyGuardedAdmiralNames(unittest.TestCase):
    """A route in universe_core may call an admiral-only function ONLY where the admiral
    is known to be there. The three brig loops were the ones that were not."""

    def test_the_brig_loops_go_through_the_guarded_accessor(self):
        only_admiral = _public_defs(ADMIRAL) - _public_defs(OU_CORE)
        self.assertIn("officers_captured_by", only_admiral)
        hits = []
        for path in glob.glob(os.path.join(OU_CORE, "*.mast")):
            with open(path, encoding="utf-8") as f:
                for number, line in enumerate(f, 1):
                    if line.lstrip().startswith("#"):
                        continue
                    if re.search(r"\bofficers_captured_by\(", line):
                        hits.append(f"{os.path.basename(path)}:{number}")
        self.assertEqual(hits, [], "call universe_officers_held_by() instead")


if __name__ == "__main__":
    unittest.main()
