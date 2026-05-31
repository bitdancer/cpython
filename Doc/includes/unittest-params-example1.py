import unittest
from unittest.params import C, ParamsMixin, params

class TestStringMethods(ParamsMixin, unittest.TestCase):

    @params(
        one_lc_letter = C('a', 'A'),
        one_uc_letter = C('A', 'A'),
        one_lc_word = C('word', 'WORD'),
        one_uc_word = C('WORD', 'WORD'),
        mixed_case = C('WoRd', 'WORD'),
        multiple_words = C(
            'test EvErYthing AT ONCE',
            'TEST EVERYTHING AT ONCE',
            ),
        )
    def test_upper(self, teststr, expected):
        self.assertEqual(teststr.upper(), expected)

if __name__ == '__main__':
    unittest.main()
