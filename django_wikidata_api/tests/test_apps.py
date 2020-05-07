# coding=utf-8
""" Unit tests for apps.py """
from django.test import TestCase

from django_wikidata_api.apps import DjangoWikidataAPIConfig


class DjangoWikidataAPIConfigTests(TestCase):
    def setUp(self):
        """ Setup Tests. """

    def test_config(self):
        self.assertEqual(DjangoWikidataAPIConfig.name, "django_wikidata_api")
