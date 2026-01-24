import unittest
from pprint import pprint

from glom import assign


class TestGlom(unittest.TestCase):

    def test_glom(self):
        target = {'a': [{'b': 'c'}, {'d': None}]}
        _ = assign(target, 'a.1.d', 'e')
        pprint(target)
