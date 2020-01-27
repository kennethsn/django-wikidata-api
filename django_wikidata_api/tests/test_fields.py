# coding=utf-8
""" Unit tests for fields.py """
from rest_framework.fields import (
    CharField,
    Field,
    ReadOnlyField,
    URLField,
)
from django.test import TestCase

from django_wikidata_api.fields import (
    SchemaAboutField,
    WikidataCharField,
    WikidataDescriptionField,
    WikidataEntityFilterField,
    WikidataField,
    WikidataLabelField,
)


class WikidataFieldTests(TestCase):
    def setUp(self):
        """ Setup WikidataField tests. """
        self.test_field = WikidataField()
        self.test_field_full = WikidataField(properties=["P123", "P321"], values=['Q123'], default="Test",
                                             entity_name='test_entity', serializer_settings={"read_only": True},
                                             public=True, serializer_field_class=ReadOnlyField, required=True)
        self.mocked_query_response = {
            'main': {'type': 'uri', 'value': 'http://www.wikidata.org/entity/Q123'},
            'mainLabel': {'xml:lang': 'en', 'type': 'literal', 'value': 'Test Item'},
            'label': {'xml:lang': 'en', 'type': 'literal', 'value': 'Test Item'},
            'description': {'xml:lang': 'en', 'type': 'literal', 'value': 'Some Test Description'},
            'alt_labels': {'type': 'literal', 'value': ''}
        }

    def test___init__(self):
        self.assertEqual(self.test_field.entity_name, "main")
        self.assertIsNone(self.test_field.properties)
        self.assertIsNone(self.test_field.values)
        self.assertIsNone(self.test_field.default)
        self.assertFalse(self.test_field.required)
        self.assertIsNone(self.test_field.public)
        self.assertEqual(self.test_field.from_name, "?main")
        self.assertIsInstance(self.test_field.serializer, Field)
        self.assertFalse(self.test_field.serializer.read_only)

    def test___init__with_kwargs(self):
        self.assertEqual(self.test_field_full.entity_name, "test_entity")
        self.assertEqual(self.test_field_full.properties, ['P123', "P321"])
        self.assertEqual(self.test_field_full.values, ["Q123"])
        self.assertEqual(self.test_field_full.default, "Test")
        self.assertTrue(self.test_field_full.required)
        self.assertTrue(self.test_field_full.public)
        self.assertIsInstance(self.test_field_full.serializer, ReadOnlyField)
        self.assertTrue(self.test_field_full.serializer.read_only)

    def test___repr__(self):
        self.assertEqual(repr(self.test_field_full), "<WikidataField: None>")
        self.assertEqual(repr(WikidataField(name="Test")), "<WikidataField: Test>")

    def test_set_name(self):
        test_field = WikidataField().set_name("test")
        self.assertEqual(test_field.name, "test")
        self.assertTrue(test_field.public)
        test_field = WikidataField().set_name("_test")
        self.assertEqual(test_field.name, "_test")
        self.assertFalse(test_field.public)
        test_field = WikidataField(public=True).set_name("test")
        self.assertEqual(test_field.name, "test")
        self.assertTrue(test_field.public)
        test_field = WikidataField(public=True).set_name("_test")
        self.assertEqual(test_field.name, "_test")
        self.assertTrue(test_field.public)
        test_field = WikidataField(public=False).set_name("_test")
        self.assertEqual(test_field.name, "_test")
        self.assertFalse(test_field.public)
        test_field = WikidataField(public=False).set_name("test")
        self.assertEqual(test_field.name, "test")
        self.assertFalse(test_field.public)

    def test_set_serializer(self):
        self.test_field.set_serializer({})
        self.assertIsInstance(self.test_field.serializer, Field)
        self.assertFalse(self.test_field.serializer.read_only)
        self.test_field_full.set_serializer({"read_only": True})
        self.assertIsInstance(self.test_field_full.serializer, ReadOnlyField)
        self.assertTrue(self.test_field_full.serializer.read_only)

    def test__prop_sparql_string(self):
        self.assertEqual(self.test_field_full._prop_sparql_string(), "wdt:P123|wdt:P321")

    def test_to_wikidata_field(self):
        self.assertEqual(WikidataField(name="test").to_wikidata_field(), "?test")

    def test_to_wikidata_filter(self):
        test_field = WikidataField(name="test", properties=["P123", "P321"])
        self.assertEqual(test_field.to_wikidata_filter(), "OPTIONAL { ?main wdt:P123|wdt:P321 ?test. }")
        test_field.required = True
        self.assertEqual(test_field.to_wikidata_filter(), "?main wdt:P123|wdt:P321 ?test.")

    def test_to_wikidata_service(self):
        self.assertEqual(self.test_field.to_wikidata_service(), "")
        self.assertEqual(self.test_field_full.to_wikidata_service(), "")

    def test_to_wikidata_group(self):
        self.assertEqual(self.test_field.to_wikidata_group(), "?main")
        self.assertEqual(self.test_field_full.to_wikidata_group(), "?test_entity")

    def test_from_wikidata(self):
        self.assertEqual(WikidataField(name="main").from_wikidata(self.mocked_query_response),
                         "http://www.wikidata.org/entity/Q123")
        self.assertEqual(WikidataField(name="label").from_wikidata(self.mocked_query_response),
                         "Test Item")
        self.assertEqual(WikidataField(name="test", default="Test").from_wikidata(self.mocked_query_response),
                         "Test")


class WikidataCharFieldTests(TestCase):
    def setUp(self):
        """ Setup WikidataCharField tests. """
        self.test_field = WikidataCharField()

    def test___init__(self):
        self.assertEqual(self.test_field.serializer_field_class, CharField)


class WikidataLabelFieldTests(TestCase):
    def setUp(self):
        """ Setup WikidataItemBase tests. """
        self.test_field = WikidataLabelField(name="test")

    def test___init__(self):
        self.assertEqual(self.test_field.entity_name, "main")
        self.assertEqual(self.test_field.sparql_field_suffix, "Label")
        self.assertEqual(self.test_field.from_name, "?mainLabel")
        self.assertEqual(self.test_field.service_property, "rdfs:label")

    def test_to_wikidata_field(self):
        self.assertEqual(self.test_field.to_wikidata_field(), "?mainLabel (?mainLabel AS ?test)")

    def test_to_wikidata_filter(self):
        self.assertEqual(self.test_field.to_wikidata_filter(), "")

    def test_to_wikidata_service(self):
        self.assertEqual(self.test_field.to_wikidata_service(), "?main rdfs:label ?mainLabel . ")


class WikidataDescriptionFieldTests(TestCase):
    def setUp(self):
        """ Setup WikidataCharField tests. """
        self.test_field = WikidataDescriptionField()

    def test___init__(self):
        self.assertEqual(self.test_field.serializer_field_class, CharField)
        self.assertEqual(self.test_field.service_property, "schema:description")
        self.assertTrue(self.test_field.serializer.allow_null)
        self.assertTrue(self.test_field.serializer.allow_blank)
        self.assertEqual(self.test_field.sparql_field_suffix, 'Description')


class WikidataEntityFilterFieldTests(TestCase):
    def setUp(self):
        """ Setup WikidataEntityFilterField tests. """
        self.test_field = WikidataEntityFilterField(name="test", properties=["P123", "P321"], values=[])

    def test_to_wikidata_filter(self):
        self.assertEqual(self.test_field.to_wikidata_filter(),
                         "OPTIONAL { ?main wdt:P123|wdt:P321 ?test_qid. FILTER(?test_qid=wd:). }")

    def test_to_wikidata_service(self):
        self.assertEqual(self.test_field.to_wikidata_service(), "?test_qid rdfs:label ?test . ")

    def test_to_wikidata_group(self):
        self.assertEqual(self.test_field.to_wikidata_group(), "?test")


class SchemaAboutFieldTests(TestCase):
    def setUp(self):
        """ Setup WikidataCharField tests. """
        self.test_field = SchemaAboutField(url="example.com", entity_name="test", name="about")

    def test___init__(self):
        self.assertEqual(self.test_field.serializer_field_class, URLField)
        self.assertEqual(self.test_field.url, "example.com")
        self.assertTrue(self.test_field.serializer.allow_null)
        self.assertTrue(self.test_field.serializer.allow_blank)
        self.assertEqual(self.test_field.sparql_field_suffix, '')

    def test_to_wikidata_filter(self):
        self.assertEqual(self.test_field.to_wikidata_filter(),
                         "OPTIONAL { ?about schema:about ?test; schema:isPartOf <example.com>. }")
        self.test_field.required = True
        self.assertEqual(self.test_field.to_wikidata_filter(),
                         "?about schema:about ?test; schema:isPartOf <example.com>.")
        self.test_field.required = False

    def test_to_wikidata_group(self):
        self.assertEqual(self.test_field.to_wikidata_group(), "?about")
