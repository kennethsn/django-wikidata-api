# coding=utf-8
""" Unit tests for models.py """
from mock import (
    Mock,
    patch,
)

from django.test import TestCase
from django.urls import URLResolver

from django_wikidata_api.exceptions import DjangoWikidataAPIException
from django_wikidata_api.fields import WikidataField
from django_wikidata_api.models import (
    WDTriple,
    WikidataItemBase,
)
from django_wikidata_api.serializers import WikidataItemSerializer

from .examples import CustomTestModel


class WikidataItemBaseTests(TestCase):
    def setUp(self):
        """ Setup WikidataItemBase tests. """
        self.test_item = WikidataItemBase()
        self.test_item_full = WikidataItemBase(label="Test Item", description="Some Test Description", main="Q123",
                                               id=123, alt_labels=["Test"])

        self.mocked_query_response = Mock()
        self.mocked_query_response.json.return_value = {
            'results': {
                'bindings': [
                    {
                        'main': {'type': 'uri', 'value': 'http://www.wikidata.org/entity/Q123'},
                        'mainLabel': {'xml:lang': 'en', 'type': 'literal', 'value': 'Test Item'},
                        'label': {'xml:lang': 'en', 'type': 'literal', 'value': 'Test Item'},
                        'description': {'xml:lang': 'en', 'type': 'literal', 'value': 'Some Test Description'},
                        'alt_labels': {'type': 'literal', 'value': ''}
                    },
                    {
                        'main': {'type': 'uri', 'value': 'http://www.wikidata.org/entity/Q321'},
                        'mainLabel': {'xml:lang': 'en', 'type': 'literal', 'value': 'Some Other Item'},
                        'label': {'xml:lang': 'en', 'type': 'literal', 'value': 'Some Other Item'},
                        'description': {'xml:lang': 'en', 'type': 'literal', 'value': 'Some Other Test Description'},
                        'alt_labels': {'type': 'literal', 'value': 'alt name 1|alt name 2'}
                    }
                ]
            }
        }

        self.mocked_query_response_empty = Mock()
        self.mocked_query_response_empty.json.return_value = {'results': {'bindings': []}}
        self.mocked_query_response_count = Mock()
        self.mocked_query_response_count.json.return_value = {'results': {'bindings': [{'count': {'value': 100}}]}}
        self.CustomTestModel = CustomTestModel
        self.custom_test_item = self.CustomTestModel()
        self.custom_test_item_full = self.CustomTestModel(label="Test Item", main="Q123", id=123,
                                                          description="Some Test Description", alt_labels=["Test"],
                                                          test_field=["Test"], _private_field=["TestPrivate"],
                                                          hidden_field=["TestHidden"], _public_field=["TestPublic"])

    def test___init__(self):
        self.assertIsNone(self.test_item.alt_labels)
        self.assertIsNone(self.test_item.main)
        self.assertIsNone(self.test_item.label)
        self.assertIsNone(self.test_item.description)
        self.assertIsNone(self.test_item.conformance)
        self.assertIsNone(self.test_item.id)
        self.assertIsNone(self.test_item.schema)
        self.assertEqual(self.test_item.Meta.verbose_name, "Wikidata Item")
        self.assertIsNone(self.test_item.Meta.verbose_name_plural)

        self.assertIsNone(self.custom_test_item.alt_labels)
        self.assertIsNone(self.custom_test_item.main)
        self.assertIsNone(self.custom_test_item.label)
        self.assertIsNone(self.custom_test_item.description)
        self.assertIsNone(self.custom_test_item.conformance)
        self.assertIsNone(self.custom_test_item.id)
        self.assertIsNone(self.custom_test_item.schema)
        self.assertIsNone(self.custom_test_item.hidden_field)
        self.assertIsNone(self.custom_test_item._public_field)
        self.assertIsNone(self.custom_test_item.test_field)
        self.assertIsNone(self.custom_test_item._private_field)
        self.assertEqual(self.custom_test_item.test_property, "Test Value")
        self.assertEqual(self.custom_test_item.test_property_2, "blue")
        self.assertEqual(self.custom_test_item.test_attr, "Test Attr")
        self.assertEqual(self.custom_test_item.test_attr_2, 37)
        self.assertEqual(self.custom_test_item.Meta.verbose_name, "Test Model")
        self.assertEqual(self.custom_test_item.Meta.verbose_name_plural, "Test Model Instances")

    def test___init__with_kwargs(self):
        self.assertEqual(self.test_item_full.label, "Test Item")
        self.assertEqual(self.test_item_full.main, "Q123")
        self.assertEqual(self.test_item_full.description, "Some Test Description")
        self.assertEqual(self.test_item_full.alt_labels, ["Test"])
        self.assertEqual(self.test_item_full.id, 123)
        self.assertEqual(self.test_item.Meta.verbose_name, "Wikidata Item")
        self.assertIsNone(self.test_item.Meta.verbose_name_plural)

        self.assertEqual(self.custom_test_item_full.label, "Test Item")
        self.assertEqual(self.custom_test_item_full.description, "Some Test Description")
        self.assertEqual(self.custom_test_item_full.main, "Q123")
        self.assertEqual(self.custom_test_item_full.alt_labels, ["Test"])
        self.assertEqual(self.custom_test_item_full.id, 123)
        self.assertEqual(self.custom_test_item_full.hidden_field, ["TestHidden"])
        self.assertEqual(self.custom_test_item_full.test_field, ["Test"])
        self.assertEqual(self.custom_test_item_full._public_field, ["TestPublic"])
        self.assertEqual(self.custom_test_item_full._private_field, ["TestPrivate"])
        self.assertEqual(self.custom_test_item_full.test_property, "Test Value")
        self.assertEqual(self.custom_test_item_full.test_property_2, "blue")
        self.assertEqual(self.custom_test_item_full.test_attr, "Test Attr")
        self.assertEqual(self.custom_test_item_full.test_attr_2, 37)
        self.assertEqual(self.custom_test_item_full.Meta.verbose_name, "Test Model")
        self.assertEqual(self.custom_test_item_full.Meta.verbose_name_plural, "Test Model Instances")

    def test_get_model_name(self):
        self.assertEqual(self.test_item.get_model_name(), "Wikidata Item")
        self.assertEqual(self.custom_test_item.get_model_name(), "Test Model")

    def test_get_model_name_plural(self):
        self.assertEqual(self.test_item.get_model_name_plural(), "Wikidata Items")
        self.assertEqual(self.custom_test_item.get_model_name_plural(), "Test Model Instances")

    def test_get_wikidata_fields(self):
        fields = WikidataItemBase.get_wikidata_fields()
        field_names = []
        for field in fields:
            self.assertIsInstance(field, WikidataField)
            field_names.append(field.name)
        self.assertEqual(len(field_names), 5)
        self.assertIn("main", field_names)
        self.assertIn("label", field_names)
        self.assertIn("description", field_names)
        self.assertIn("alt_labels", field_names)
        self.assertIn("conformance", field_names)

    def test_get_wikidata_fields__with_keys(self):
        fields = sorted(WikidataItemBase.get_wikidata_fields(with_keys=True), key=lambda x: x[0])
        self.assertEqual(len(fields), 5)
        self.assertEqual("alt_labels", fields[0][0])
        self.assertIsInstance(fields[0][1], WikidataField)
        self.assertEqual("conformance", fields[1][0])
        self.assertIsInstance(fields[1][1], WikidataField)
        self.assertEqual("description", fields[2][0])
        self.assertIsInstance(fields[2][1], WikidataField)
        self.assertEqual("label", fields[3][0])
        self.assertIsInstance(fields[3][1], WikidataField)
        self.assertEqual("main", fields[4][0])
        self.assertIsInstance(fields[4][1], WikidataField)

    def test_build_serializer(self):
        serializer_class = WikidataItemBase.build_serializer()
        self.assertTrue(issubclass(serializer_class, WikidataItemSerializer))
        self.assertEqual("Wikidata Item", serializer_class.Meta.ref_name)
        self.test_item_full.set_conformance()
        serializer = serializer_class(self.test_item_full)
        self.assertIsInstance(serializer, WikidataItemSerializer)
        serializer_data = serializer.data
        self.assertEqual(serializer_data['id'], '123')
        self.assertEqual(serializer_data['alt_labels'], ["Test"])
        self.assertEqual(serializer_data['label'], "Test Item")
        self.assertEqual(serializer_data['description'], "Some Test Description")
        self.assertEqual(serializer_data['conformance']['focus'], '123')
        self.assertEqual(serializer_data['conformance']['reason'], 'No Schema associated with this model')
        self.assertTrue(serializer_data['conformance']['result'])

    def test_build_serializer__custom_model(self):
        serializer_class = self.CustomTestModel.build_serializer()
        self.assertTrue(issubclass(serializer_class, WikidataItemSerializer))
        self.assertEqual("Test Model", serializer_class.Meta.ref_name)
        self.custom_test_item_full.set_conformance()
        serializer = serializer_class(self.custom_test_item_full)
        self.assertIsInstance(serializer, WikidataItemSerializer)
        serializer_data = serializer.data
        self.assertEqual(serializer_data['id'], '123')
        self.assertEqual(serializer_data['alt_labels'], ["Test"])
        self.assertEqual(serializer_data['label'], "Test Item")
        self.assertEqual(serializer_data['description'], "Some Test Description")
        self.assertEqual(serializer_data['conformance']['focus'], '123')
        self.assertEqual(serializer_data['conformance']['reason'], 'No Schema associated with this model')
        self.assertTrue(serializer_data['conformance']['result'])
        self.assertNotIn('_private_field', serializer_data)
        self.assertNotIn('hidden_field', serializer_data)
        self.assertEqual("Test Hidden Value", self.custom_test_item_full.hidden_property)
        self.assertNotIn('hidden_property', serializer_data)
        self.assertEqual(serializer_data['_public_field'], ['TestPublic'])
        self.assertEqual(serializer_data['test_field'], ["Test"])
        self.assertEqual(serializer_data['test_property'], "Test Value")
        self.assertNotIn("test_property_2", serializer_data)
        self.assertEqual(serializer_data["color"], "blue")
        self.assertEqual(serializer_data['test_attr'], "Test Attr")
        self.assertNotIn("test_attr_2", serializer_data)
        self.assertEqual(serializer_data["age"], "37")
        self.assertEqual(serializer_data["wd_prop"], "P123")

    @patch('django_wikidata_api.models.requests.get')
    def test_get_all(self, mocked_requests):
        mocked_requests.return_value = self.mocked_query_response_empty
        self.assertEqual(WikidataItemBase.get_all(), [])

        mocked_requests.return_value = self.mocked_query_response
        output_list = WikidataItemBase.get_all(limit=100)
        self.assertEqual(len(output_list), 2)
        self.assertIsInstance(output_list[0], WikidataItemBase)
        self.assertEqual(output_list[0].id, 'Q123')
        self.assertEqual(output_list[0].main, 'Q123')
        self.assertEqual(output_list[0].label, 'Test Item')
        self.assertEqual(output_list[0].description, "Some Test Description")
        self.assertEqual(output_list[0].alt_labels, [])
        self.assertIsNone(output_list[0].conformance)
        self.assertIsInstance(output_list[1], WikidataItemBase)
        self.assertEqual(output_list[1].id, 'Q321')
        self.assertEqual(output_list[1].main, 'Q321')
        self.assertEqual(output_list[1].label, 'Some Other Item')
        self.assertEqual(output_list[1].description, "Some Other Test Description")
        self.assertEqual(output_list[1].alt_labels, ['alt name 1', 'alt name 2'])
        self.assertIsNone(output_list[1].conformance)

    @patch('django_wikidata_api.models.requests.get')
    def test_get_all__with_conformance(self, mocked_requests):
        mocked_requests.return_value = self.mocked_query_response_empty
        self.assertEqual(WikidataItemBase.get_all(with_conformance=True), [])

        mocked_requests.return_value = self.mocked_query_response
        output_list = WikidataItemBase.get_all(with_conformance=True)
        self.assertEqual(len(output_list), 2)
        self.assertIsInstance(output_list[0], WikidataItemBase)
        self.assertEqual(output_list[0].id, 'Q123')
        self.assertEqual(output_list[0].main, 'Q123')
        self.assertEqual(output_list[0].label, 'Test Item')
        self.assertEqual(output_list[0].description, "Some Test Description")
        self.assertEqual(output_list[0].conformance['focus'], 'Q123')
        self.assertEqual(output_list[0].conformance['reason'], 'No Schema associated with this model')
        self.assertTrue(output_list[0].conformance['result'])
        self.assertEqual(output_list[0].alt_labels, [])
        self.assertIsInstance(output_list[1], WikidataItemBase)
        self.assertEqual(output_list[1].id, 'Q321')
        self.assertEqual(output_list[1].main, 'Q321')
        self.assertEqual(output_list[1].label, 'Some Other Item')
        self.assertEqual(output_list[1].description, "Some Other Test Description")
        self.assertEqual(output_list[1].alt_labels, ['alt name 1', 'alt name 2'])
        self.assertEqual(output_list[1].conformance['focus'], 'Q321')
        self.assertEqual(output_list[1].conformance['reason'], 'No Schema associated with this model')
        self.assertTrue(output_list[1].conformance['result'])

    @patch('django_wikidata_api.models.requests.get')
    def test_get_all__with_values(self, mocked_requests):
        mocked_requests.return_value = self.mocked_query_response_empty
        self.assertEqual(WikidataItemBase.get_all(values=("Q1", "Q2")), [])

        mocked_requests.return_value = self.mocked_query_response
        output_list = WikidataItemBase.get_all(values=("Q1", "Q2"))
        self.assertEqual(len(output_list), 2)
        self.assertIsInstance(output_list[0], WikidataItemBase)
        self.assertEqual(output_list[0].id, 'Q123')
        self.assertEqual(output_list[0].main, 'Q123')

    @patch('django_wikidata_api.models.requests.get')
    def test_get_all__all_pages(self, mocked_requests):
        mocked_requests.return_value = self.mocked_query_response_empty
        self.assertEqual(WikidataItemBase.get_all(page=None), [])

        mocked_requests.return_value = self.mocked_query_response
        output_list = WikidataItemBase.get_all(page=None, limit=5)
        self.assertEqual(len(output_list), 2)
        self.assertIsInstance(output_list[0], WikidataItemBase)
        self.assertEqual(output_list[0].id, 'Q123')
        self.assertEqual(output_list[0].main, 'Q123')

    @patch('django_wikidata_api.models.requests.get')
    def test_get(self, mocked_requests):
        mocked_requests.return_value = self.mocked_query_response_empty
        self.assertIsNone(WikidataItemBase.get('Q123'))

        mocked_requests.return_value = self.mocked_query_response
        output = WikidataItemBase.get('Q123')
        self.assertIsInstance(output, WikidataItemBase)
        self.assertEqual(output.id, 'Q123')
        self.assertEqual(output.main, 'Q123')
        self.assertEqual(output.label, 'Test Item')
        self.assertEqual(output.description, 'Some Test Description')
        self.assertIsNone(output.conformance)
        self.assertEqual(output.alt_labels, [])

    @patch('django_wikidata_api.models.requests.get')
    def test_get__with_conformance(self, mocked_requests):
        mocked_requests.return_value = self.mocked_query_response_empty
        self.assertIsNone(WikidataItemBase.get('Q123', with_conformance=True))

        mocked_requests.return_value = self.mocked_query_response
        output = WikidataItemBase.get('Q123', with_conformance=True)
        self.assertIsInstance(output, WikidataItemBase)
        self.assertEqual(output.id, 'Q123')
        self.assertEqual(output.main, 'Q123')
        self.assertEqual(output.label, 'Test Item')
        self.assertEqual(output.description, 'Some Test Description')
        self.assertEqual(output.conformance['focus'], 'Q123')
        self.assertEqual(output.conformance['reason'], 'No Schema associated with this model')
        self.assertTrue(output.conformance['result'])
        self.assertEqual(output.alt_labels, [])

    @patch('django_wikidata_api.models.WikidataItemBase.get_all')
    def test_search(self, mocked_get_all):
        mocked_get_all.return_value = []
        self.assertEqual(WikidataItemBase.search("something"), [])

        mocked_get_all.return_value = [
            WikidataItemBase._from_wikidata(self.mocked_query_response.json()['results']['bindings'][0]),
            WikidataItemBase._from_wikidata(self.mocked_query_response.json()['results']['bindings'][1]),
        ]

        self.assertEqual(WikidataItemBase.search("something"), [])
        # search by label
        self.assertEqual(len(WikidataItemBase.search("item")), 2)
        self.assertEqual(len(WikidataItemBase.search("Some Other item")), 1)
        # search by description
        self.assertEqual(len(WikidataItemBase.search("description")), 2)
        self.assertEqual(len(WikidataItemBase.search("other description")), 1)
        # search by id
        self.assertEqual(len(WikidataItemBase.search('Q123')), 1)
        self.assertEqual(len(WikidataItemBase.search('Q321')), 1)
        # search by alt_labels
        self.assertEqual(len(WikidataItemBase.search('alt name 2')), 1)

    @patch('django_wikidata_api.models.requests.get')
    def test_count(self, mocked_requests):
        mocked_requests.return_value = self.mocked_query_response_count
        self.assertEqual(WikidataItemBase.count(), 100)
        mocked_requests.return_value = self.mocked_query_response_empty
        self.assertEqual(WikidataItemBase.count(), 0)

    def test_build_query(self):
        output = WikidataItemBase.build_query()
        # test minified
        self.assertNotIn("  ", output)
        self.assertNotIn("\n", output)
        self.assertNotIn("\t", output)
        # test values empty
        self.assertNotIn("VALUES", output)
        self.assertIn("?main ?mainLabel (?mainLabel AS ?label) ?mainDescription (?mainDescription AS ?description) "
                      "(GROUP_CONCAT(DISTINCT ?main_alt_label; SEPARATOR=\'|\') AS ?alt_labels)", output)
        self.assertIn("WHERE", output)
        self.assertIn("SERVICE wikibase:label { bd:serviceParam wikibase:language 'en,[AUTO_LANGUAGE]", output)
        self.assertIn("?main rdfs:label ?mainLabel . ?main schema:description ?mainDescription . }", output)
        self.assertIn("GROUP BY ?main ?mainLabel ?mainDescription", output)

        output = WikidataItemBase.build_query(values=("Q123", "Q321"))
        self.assertIn("VALUES ?main {wd:Q123 wd:Q321}", output)
        self.assertNotIn("  ", output)
        self.assertNotIn("\n", output)
        self.assertNotIn("\t", output)

        output = WikidataItemBase.build_query(limit=30)
        self.assertIn("LIMIT 30", output)
        self.assertNotIn("  ", output)
        self.assertNotIn("\n", output)
        self.assertNotIn("\t", output)

    def test_get_viewset_urls(self):
        urls = WikidataItemBase.get_viewset_urls()
        self.assertIsInstance(urls, URLResolver)
        self.assertEqual(len(urls.url_patterns), 8)
        for pattern in urls.url_patterns:
            if pattern.name != 'api-root':
                self.assertIn("wikidata_item", pattern.name)

        urls = WikidataItemBase.get_viewset_urls('some_other_slug')
        self.assertIsInstance(urls, URLResolver)
        self.assertEqual(len(urls.url_patterns), 8)
        for pattern in urls.url_patterns:
            if pattern.name != 'api-root':
                self.assertIn("some_other_slug", pattern.name)

    @patch('django_wikidata_api.models.requests.get')
    def test__query_wikidata(self, mocked_requests):
        mocked_requests.return_value = self.mocked_query_response_empty
        self.assertEqual(WikidataItemBase._query_wikidata(), [])
        self.assertEqual(WikidataItemBase._query_wikidata(("Q123", "Q321")), [])
        self.assertEqual(WikidataItemBase._query_wikidata(limit=20), [])
        self.assertEqual(WikidataItemBase._query_wikidata(("Q123", "Q321"), 20), [])

        mocked_requests.return_value = self.mocked_query_response
        expected_out = self.mocked_query_response.json()['results']['bindings']
        self.assertEqual(WikidataItemBase._query_wikidata(), expected_out)
        self.assertEqual(WikidataItemBase._query_wikidata(("Q123", "Q321")), expected_out)
        self.assertEqual(WikidataItemBase._query_wikidata(limit=20), expected_out)
        self.assertEqual(WikidataItemBase._query_wikidata(("Q123", "Q321"), 20), expected_out)

        mocked_requests.side_effect = KeyError('test')
        with self.assertRaises(DjangoWikidataAPIException):
            WikidataItemBase._query_wikidata(("Q123", "Q321"), 20)

    @patch('django_wikidata_api.models.requests.get')
    @patch('django_wikidata_api.models.requests.post')
    def test__execute_query(self, mocked_requests_post, mocked_requests_get):
        mocked_requests_post.return_value = self.mocked_query_response_empty
        mocked_requests_get.return_value = self.mocked_query_response_empty
        self.assertEqual(WikidataItemBase._execute_query("test"), [])
        self.assertEqual(WikidataItemBase._execute_query("a"*1500), [])

        mocked_requests_post.return_value = self.mocked_query_response
        mocked_requests_get.return_value = self.mocked_query_response
        expected_out = self.mocked_query_response.json()['results']['bindings']
        self.assertEqual(WikidataItemBase._execute_query("test"), expected_out)
        self.assertEqual(WikidataItemBase._execute_query("a"*1500), expected_out)

        mocked_requests_post.side_effect = KeyError('test')
        mocked_requests_get.side_effect = KeyError('test')
        with self.assertRaises(DjangoWikidataAPIException):
            WikidataItemBase._execute_query("test")
        with self.assertRaises(DjangoWikidataAPIException):
            WikidataItemBase._execute_query("a"*1500)

    def test__from_wikidata(self):
        output = WikidataItemBase._from_wikidata(self.mocked_query_response.json()['results']['bindings'][1])
        self.assertIsInstance(output, WikidataItemBase)
        self.assertEqual(output.id, 'Q321')
        self.assertEqual(output.main, 'Q321')
        self.assertEqual(output.label, 'Some Other Item')
        self.assertEqual(output.alt_labels, ['alt name 1', 'alt name 2'])
        self.assertIsNone(output.conformance)

        output = WikidataItemBase._from_wikidata(self.mocked_query_response.json()['results']['bindings'][1],
                                                 with_conformance=True)
        self.assertIsInstance(output, WikidataItemBase)
        self.assertEqual(output.id, 'Q321')
        self.assertEqual(output.main, 'Q321')
        self.assertEqual(output.label, 'Some Other Item')
        self.assertEqual(output.alt_labels, ['alt name 1', 'alt name 2'])
        self.assertEqual(output.conformance['focus'], 'Q321')
        self.assertEqual(output.conformance['reason'], 'No Schema associated with this model')
        self.assertTrue(output.conformance['result'])

    def test__attr_is_public(self):
        self.assertTrue(self.test_item._attr_is_public('schema'))
        self.assertFalse(self.test_item._attr_is_public('_wikidata_fields'))

    def test__has_substring(self):
        self.assertFalse(self.test_item._has_substring("something"))
        self.assertFalse(self.test_item._has_substring("Test"))
        self.assertFalse(self.test_item._has_substring("Test"))
        self.assertFalse(self.test_item_full._has_substring("something"))
        self.assertFalse(self.test_item_full._has_substring("Q123"))
        self.assertTrue(self.test_item_full._has_substring("item"))
        self.assertTrue(self.test_item_full._has_substring("Test Item"))
        self.assertTrue(self.test_item_full._has_substring("123"))
        self.assertFalse(self.custom_test_item_full._has_substring("something"))
        self.assertFalse(self.custom_test_item_full._has_substring("TestPrivate"))
        self.assertTrue(self.custom_test_item_full._has_substring("TestPublic"))
        self.assertFalse(self.custom_test_item_full._has_substring("TestHidden"))
        self.assertFalse(self.custom_test_item_full._has_substring("Q123"))
        self.assertTrue(self.custom_test_item_full._has_substring("item"))
        self.assertTrue(self.custom_test_item_full._has_substring("Test Item"))
        self.assertTrue(self.custom_test_item_full._has_substring("123"))

    def test___repr__(self):
        self.assertEqual(repr(self.test_item), "<Wikidata Item: None (None)>")
        self.assertEqual(repr(self.test_item_full), "<Wikidata Item: Test Item (Q123)>")
        self.assertEqual(repr(self.custom_test_item), "<Test Model: None (None)>")
        self.assertEqual(repr(self.custom_test_item_full), "<Test Model: Test Item (Q123)>")

    def test___str__(self):
        self.assertEqual(str(self.test_item), "None (None)")
        self.assertEqual(str(self.test_item_full), "Test Item (Q123)")
        self.assertEqual(str(self.custom_test_item), "None (None)")
        self.assertEqual(str(self.custom_test_item_full), "Test Item (Q123)")

    def test_find_entity_id(self):
        self.assertEqual(WikidataItemBase.find_entity_id("some_random_Q123_string"), "Q123")
        self.assertEqual(WikidataItemBase.find_entity_id("some_random_q123_string"), "q123")
        self.assertIsNone(WikidataItemBase.find_entity_id("some_random_QR123_string"))

    def test_find_prop_id(self):
        self.assertEqual(WikidataItemBase.find_prop_id("some_random_P123_string"), "P123")
        self.assertEqual(WikidataItemBase.find_prop_id("some_random_p123_string"), "p123")
        self.assertIsNone(WikidataItemBase.find_prop_id("some_random_PR123_string"))


class WDTripleTests(TestCase):

    def setUp(self):
        """ Setup WDTriple tests. """
        self.test_triple = WDTriple('P1', [])

    def test___init__(self):
        self.assertEqual(self.test_triple.prop, "P1")
        self.assertEqual(self.test_triple.values, [])
        self.assertFalse(self.test_triple.minus)
        self.assertFalse(self.test_triple.subclass)
        self.assertEqual(self.test_triple.subclass_prop, "P279")
        self.assertEqual(self.test_triple.subclass_prop, "P279")
        self.assertEqual(self.test_triple.entity_prefix, "wd")
        self.assertEqual(self.test_triple.prop_prefix, "wdt")

    def test_format(self):
        self.assertEqual(self.test_triple.format("test"), "")
