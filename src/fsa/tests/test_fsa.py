import random
import unittest
from src.fsa import build_automaton


class TestFSA(unittest.TestCase):

    def assertGeneratedStrings(self, obj):
        for i in range(100):
            self.assertTrue(obj.is_string_correct(obj.get_correct_string(random.randint(1, 20))))
            self.assertFalse(obj.is_string_correct(obj.get_wrong_string(random.randint(1, 20), 0)))

    def test_fsa_1_1(self):
        obj = build_automaton("C", "and")
        self.assertTrue(obj.is_string_correct("C"))
        self.assertTrue(obj.is_string_correct("CCC"))
        self.assertTrue(obj.is_string_correct("CCCCCCCCC"))
        self.assertFalse(obj.is_string_correct("CCY"))
        self.assertFalse(obj.is_string_correct("ABGD"))
        self.assertFalse(obj.is_string_correct(""))
        self.assertGeneratedStrings(obj)

    def test_fsa_1_2(self):
        obj = build_automaton("C", "or")
        self.assertTrue(obj.is_string_correct("C"))
        self.assertTrue(obj.is_string_correct("CCC"))
        self.assertTrue(obj.is_string_correct("CCCCCCCCC"))
        self.assertFalse(obj.is_string_correct("CCY"))
        self.assertFalse(obj.is_string_correct("ABGD"))
        self.assertTrue(obj.is_string_correct(""))
        self.assertGeneratedStrings(obj)

    def test_fsa_1_3(self):
        obj = build_automaton("AB", "and")
        self.assertTrue(obj.is_string_correct("AB"))
        self.assertTrue(obj.is_string_correct("ABABAB"))
        self.assertFalse(obj.is_string_correct("ABABABAA"))
        self.assertFalse(obj.is_string_correct("AXBGD"))
        self.assertGeneratedStrings(obj)

    def test_fsa_1_4(self):
        obj = build_automaton("FJG", "and")
        self.assertTrue(obj.is_string_correct("FJG"))
        self.assertTrue(obj.is_string_correct("FJGFJGFJG"))
        self.assertTrue(obj.is_string_correct("FJGFJGFJGFJGFJGFJG"))
        self.assertFalse(obj.is_string_correct("FFF"))
        self.assertFalse(obj.is_string_correct("EFGTR"))
        self.assertFalse(obj.is_string_correct(""))
        self.assertGeneratedStrings(obj)

    def test_fsa_1_5(self):
        obj = build_automaton("XYX", "or")
        self.assertTrue(obj.is_string_correct("XYX"))
        self.assertTrue(obj.is_string_correct("XYXXYXXYX"))
        self.assertTrue(obj.is_string_correct("XYXYXYXXYX"))
        self.assertFalse(obj.is_string_correct("XYXY"))
        self.assertFalse(obj.is_string_correct("OUAJHFLJAH"))
        self.assertTrue(obj.is_string_correct(""))
        self.assertGeneratedStrings(obj)

    def test_fsa_1_6(self):
        obj = build_automaton("XX", "and")
        self.assertTrue(obj.is_string_correct("XXX"))  # even odd length should be "true"
        self.assertTrue(obj.is_string_correct("XXXX"))
        self.assertFalse(obj.is_string_correct("XXY"))
        self.assertFalse(obj.is_string_correct("ABGD"))
        self.assertGeneratedStrings(obj)

    def test_fsa_2_1(self):
        obj = build_automaton("anything", "or")
        self.assertTrue(obj.is_string_correct("X"))
        self.assertTrue(obj.is_string_correct("Y"))
        self.assertTrue(obj.is_string_correct("ABC"))
        self.assertTrue(obj.is_string_correct("XYYYYYABCYXXXYXYXYYYYABC"))
        self.assertTrue(obj.is_string_correct("XXYZABC"))
        self.assertTrue(obj.is_string_correct("ABCGDTRW"))
        # self.assertGeneratedStrings(obj)  # cannot generate a wrong string in this case

    def test_fsa_2_2(self):
        obj = build_automaton("AB CD", "or")
        self.assertTrue(obj.is_string_correct("AB"))
        self.assertTrue(obj.is_string_correct("CD"))
        self.assertTrue(obj.is_string_correct("ABABAB"))
        self.assertFalse(obj.is_string_correct("CDA"))
        self.assertFalse(obj.is_string_correct("ABGDTRW"))
        self.assertGeneratedStrings(obj)

    def test_fsa_2_3(self):
        obj = build_automaton("FAB GG MIL", "or")
        self.assertTrue(obj.is_string_correct("FAB"))
        self.assertTrue(obj.is_string_correct("GG"))
        self.assertTrue(obj.is_string_correct("MIL"))
        self.assertTrue(obj.is_string_correct("FABFAB"))
        self.assertTrue(obj.is_string_correct("FABGGGMIL"))
        self.assertFalse(obj.is_string_correct("FABGGGMILFA"))
        self.assertFalse(obj.is_string_correct("ABCGDTRW"))
        self.assertGeneratedStrings(obj)

    def test_fsa_2_4(self):
        obj = build_automaton("X Y", "or")
        self.assertTrue(obj.is_string_correct("X"))
        self.assertTrue(obj.is_string_correct("Y"))
        self.assertTrue(obj.is_string_correct("XYYYYYYXXXYXYXYYYY"))
        self.assertFalse(obj.is_string_correct("XXYZ"))
        self.assertFalse(obj.is_string_correct("ABGDTRW"))
        self.assertGeneratedStrings(obj)

    def test_fsa_2_5(self):
        obj = build_automaton("X Y ABC", "or")
        self.assertTrue(obj.is_string_correct("X"))
        self.assertTrue(obj.is_string_correct("Y"))
        self.assertTrue(obj.is_string_correct("ABC"))
        self.assertTrue(obj.is_string_correct("XYYYYYABCYXXXYXYXYYYYABC"))
        self.assertFalse(obj.is_string_correct("XXYZABC"))
        self.assertFalse(obj.is_string_correct("ABCGDTRW"))
        self.assertGeneratedStrings(obj)

    def test_fsa_2_6(self):
        obj = build_automaton("C CAB ABC", "or")
        self.assertTrue(obj.is_string_correct("CABCAB"))
        self.assertTrue(obj.is_string_correct("ABCABC"))
        self.assertTrue(obj.is_string_correct("ABCAB"))
        self.assertTrue(obj.is_string_correct("CABCABCCCC"))
        self.assertFalse(obj.is_string_correct("ABCABCA"))
        self.assertFalse(obj.is_string_correct("ABCGDTRW"))
        self.assertGeneratedStrings(obj)

    def test_fsa_2_7(self):
        obj = build_automaton("ZJA J Y", "or")
        self.assertTrue(obj.is_string_correct("JYJYJ"))
        self.assertTrue(obj.is_string_correct("JJJJJJJJ"))
        self.assertTrue(obj.is_string_correct("YZJAZJA"))
        self.assertTrue(obj.is_string_correct("ZJAJY"))
        self.assertFalse(obj.is_string_correct("YJZJ"))
        self.assertFalse(obj.is_string_correct("ZJAJD"))
        self.assertGeneratedStrings(obj)

    def test_fsa_3_1(self):
        obj = build_automaton("AB CF", "and")
        self.assertTrue(obj.is_string_correct("ABABABCF"))
        self.assertTrue(obj.is_string_correct("ABCFABCFCF"))
        self.assertTrue(obj.is_string_correct("CFCFCFAB"))
        self.assertFalse(obj.is_string_correct("CFCF"))
        self.assertFalse(obj.is_string_correct("ABABABAB"))
        self.assertFalse(obj.is_string_correct("AB"))
        self.assertFalse(obj.is_string_correct("ABCAFAB"))
        self.assertFalse(obj.is_string_correct("AOPYQEG"))
        self.assertGeneratedStrings(obj)

    def test_fsa_3_2(self):
        obj = build_automaton("HL RM BT", "and")
        self.assertTrue(obj.is_string_correct("RMBTBTHLHLBT"))
        self.assertTrue(obj.is_string_correct("HLRMBT"))
        self.assertTrue(obj.is_string_correct("BTRMHLHL"))
        self.assertFalse(obj.is_string_correct("BTRMHLHLL"))
        self.assertFalse(obj.is_string_correct("BTBTRMRM"))
        self.assertFalse(obj.is_string_correct("HL"))
        self.assertFalse(obj.is_string_correct("HLRMBBT"))
        self.assertFalse(obj.is_string_correct("AOPYQEG"))
        self.assertGeneratedStrings(obj)

    def test_fsa_3_3(self):
        obj = build_automaton("GLE EA ABC", "and")
        self.assertTrue(obj.is_string_correct("GLEABCEA"))
        self.assertTrue(obj.is_string_correct("GLEABC"))
        self.assertTrue(obj.is_string_correct("GLEABCGLEA"))
        self.assertFalse(obj.is_string_correct("GLEEA"))
        self.assertFalse(obj.is_string_correct("GLEABCA"))
        self.assertFalse(obj.is_string_correct("ABCABCABCGLE"))
        self.assertFalse(obj.is_string_correct("AOPYQEG"))
        self.assertGeneratedStrings(obj)

    def test_fsa_3_4(self):
        obj = build_automaton("AB anything", "and")
        self.assertTrue(obj.is_string_correct("FKGABJJKJKSD"))
        self.assertTrue(obj.is_string_correct("GLEABC"))
        self.assertTrue(obj.is_string_correct("GLEABCGLEA"))
        self.assertTrue(obj.is_string_correct("ABABAB"))
        self.assertTrue(obj.is_string_correct("AB"))  # this has to be confirmed with Tomas/Marco
        self.assertFalse(obj.is_string_correct("GLEEA"))
        self.assertFalse(obj.is_string_correct("GLEAACA"))
        self.assertFalse(obj.is_string_correct("AOPYQEG"))
        self.assertGeneratedStrings(obj)

    def test_fsa_3_5(self):
        obj = build_automaton("AB CF anything", "and")
        self.assertTrue(obj.is_string_correct("FJGKJKJKJKJDCFCFDJKJKJKSJAB"))
        self.assertTrue(obj.is_string_correct("ABCF"))
        self.assertTrue(obj.is_string_correct("GLEABCGLEACF"))
        self.assertTrue(obj.is_string_correct("ABABABCFCF"))
        self.assertTrue(obj.is_string_correct("ABCF"))
        self.assertFalse(obj.is_string_correct("GLEEAB"))
        self.assertFalse(obj.is_string_correct("GLEAACFA"))
        self.assertFalse(obj.is_string_correct("AOPYQEG"))
        self.assertGeneratedStrings(obj)

    def test_fsa_4_1(self):
        obj = build_automaton("not AB anything", "and")
        self.assertTrue(obj.is_string_correct("ADFCFHGHADDDB"))
        self.assertTrue(obj.is_string_correct("FJGKJKJKJKJDCFCFDJKJKJKSJA"))
        self.assertTrue(obj.is_string_correct("ACF"))
        self.assertTrue(obj.is_string_correct("GLEACGLEACF"))
        self.assertTrue(obj.is_string_correct("AACFCF"))
        self.assertTrue(obj.is_string_correct("ACF"))
        self.assertFalse(obj.is_string_correct("GLEEAB"))
        self.assertFalse(obj.is_string_correct("GLEABACFA"))
        self.assertFalse(obj.is_string_correct("ABOPYQEG"))
        self.assertGeneratedStrings(obj)

    def test_fsa_4_2(self):
        obj = build_automaton("not AB CF anything", "and")
        self.assertTrue(obj.is_string_correct("DJFKJKJSCFDSFG"))
        self.assertTrue(obj.is_string_correct("FJGKJKJKJKJDCFCFDJKJKJKSJA"))
        self.assertTrue(obj.is_string_correct("ACF"))
        self.assertTrue(obj.is_string_correct("GLEACGLEACF"))
        self.assertTrue(obj.is_string_correct("AACFCF"))
        self.assertTrue(obj.is_string_correct("ACF"))
        self.assertFalse(obj.is_string_correct("GLEEABCF"))
        self.assertFalse(obj.is_string_correct("GLEABACFA"))
        self.assertFalse(obj.is_string_correct("ABOPYQEG"))
        self.assertGeneratedStrings(obj)

    def test_fsa_4_3(self):
        obj = build_automaton("not AB not CF anything", "and")
        self.assertTrue(obj.is_string_correct("DJFKJKJSCEFDSFG"))
        self.assertTrue(obj.is_string_correct("FJGKJKJKJKJDCAFCAFDJKJKJKSJA"))
        self.assertTrue(obj.is_string_correct("ACDF"))
        self.assertTrue(obj.is_string_correct("GLEACGLEAC"))
        self.assertTrue(obj.is_string_correct("AACAFB"))
        self.assertTrue(obj.is_string_correct("AC"))
        self.assertFalse(obj.is_string_correct("GLEEACF"))
        self.assertFalse(obj.is_string_correct("GLEABACA"))
        self.assertFalse(obj.is_string_correct("GLEABACFA"))
        self.assertFalse(obj.is_string_correct("ABOPYQEG"))
        self.assertGeneratedStrings(obj)

    def test_fsa_generator_1(self):
        obj = build_automaton("C", "and")
        for ind in range(100):
            self.assertFalse(obj.is_string_correct(obj.get_wrong_string(random.randint(1, 20), 1)))

    def test_fsa_generator_2(self):
        obj = build_automaton("AB CF ABC", "or")
        for ind in range(100):
            string = obj.get_correct_string(random.randint(1, 20))
            self.assertTrue(obj.is_string_correct(string))

    def test_fsa_generator_3(self):
        obj = build_automaton("AB CF ABC", "and")
        for ind in range(100):
            string = obj.get_correct_string(random.randint(1, 20))
            self.assertTrue(obj.is_string_correct(string))

    def test_fsa_generator_4(self):
        obj = build_automaton("MNO KL not CF not ABC anything", "and")
        for ind in range(100):
            string = obj.get_correct_string(random.randint(1, 20))
            self.assertTrue(obj.is_string_correct(string))

# obj = build_automaton("AB anything", "or")  # this is not handled

# obj = build_automaton("AB CF", "and")
# for ind in range(1000):
#     string = obj.get_wrong_string(0)
#     assert(not obj.is_string_correct(string))
