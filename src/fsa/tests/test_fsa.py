import unittest
from fsa import build_automaton


class TestFSA(unittest.TestCase):

    def test_fsa(self):
        obj = build_automaton("GLE AB CDX", "and")
        self.assertTrue(obj.is_string_correct("GLEAB"))
        self.assertFalse(obj.is_string_correct("HELLO"))
