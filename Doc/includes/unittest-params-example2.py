import unicodedata
import unittest
from unittest.params import C, ParamsMixin, params, Params

charname = lambda c: unicodedata.name(c).lower().replace(' ', '_')

class TestStringMethods(ParamsMixin, unittest.TestCase):

    @params
    def test_split(self, teststr, *args, expected=None, exception=None):
        if exception:
            with self.assertRaises(exception):
                teststr.split(*args)
            return
        self.assertEqual(teststr.split(*args), expected)

    params_test_split = Params(
        one_word = C('word', expected=['word']),
        two_words = C('a test', expected=['a', 'test']),
        bad_split_char = C('word', 2, exception=TypeError),
        )

    params_test_split__on = Params(
        **{
            charname(c): C(f'spl {c}it', c, expected=['spl ', 'it'])
            for c in 'z&+7'
            }
        )


if __name__ == '__main__':
    unittest.main()
