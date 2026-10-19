"""A universe title nobody registered loads NO universe - not the Default's files.

Class 5, Lecture 2 has the student spell the title one letter differently on the
`display:` line and promises "the game still starts, with no sides and no landmark, and
home is called Home Port". Measured in the engine (2026-10-19), the miss fell through
`universe_file` to the legacy `sides.amd` - the shipped Default universe's split file,
which a student's folder does not have - so the game raised "AMD error: sides.amd not
found" and started with no station at all.

    python -m unittest tests.test_universe_select_missing
"""
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
OU_CORE = os.path.abspath(os.path.join(_HERE, "..", "universe_core"))
SBS = os.path.abspath(os.path.join(_HERE, "..", "..", "sbs_utils"))
sys.path.insert(0, SBS)
sys.path.insert(0, OU_CORE)

from sbs_utils.fs import test_set_exe_dir
test_set_exe_dir()

import universe_doc as UD  # noqa: E402


class _Label:
    def __init__(self, **fields):
        self.fields = fields

    def get_inventory_value(self, key, default=None):
        return self.fields.get(key, default)


class AMissingTitle(unittest.TestCase):
    def setUp(self):
        self.saved = UD.universe_registry
        UD.universe_registry = lambda: [
            _Label(display="Default", key="default", sides="sides.amd"),
            _Label(display="The Kestrel Verge", key="my_universe", universe="kestrel_verge.amd"),
        ]

    def tearDown(self):
        UD.universe_registry = self.saved

    def test_a_registered_title_finds_its_file(self):
        self.assertEqual(UD.universe_file("The Kestrel Verge"), "kestrel_verge.amd")

    def test_a_title_spelled_another_way_loads_nothing(self):
        self.assertIsNone(UD.universe_file("The Kestral Verge"))

    def test_the_default_still_finds_its_legacy_file(self):
        self.assertEqual(UD.universe_file("Default"), "sides.amd")


if __name__ == "__main__":
    unittest.main()
