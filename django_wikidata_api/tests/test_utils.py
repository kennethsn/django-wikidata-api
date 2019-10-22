from django.test import TestCase

from django_wikidata_api.utils import some_function


class UtilsTests(TestCase):
    def test_some_function(self):
        self.assertTrue(some_function())


class Utils2Tests(TestCase):
    def test_some_function_again(self):
        self.assertTrue(some_function())
