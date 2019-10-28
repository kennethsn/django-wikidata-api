# coding=utf-8
""" Unit tests for models.py """
from mock import patch
from rest_framework.serializers import Serializer

from django.test import TestCase
from django.urls import URLResolver

from django_wikidata_api.fields import (
    WikidataEntityListField,
    WikidataField,
)
from django_wikidata_api.models import (
    WikidataItemBase
)


class WikidataItemBaseTests(TestCase):
    def setUp(self):
        """ Setup WikidataItemBase tests. """
        self.test_item = WikidataItemBase()
        self.test_item_full = WikidataItemBase(label="Test Item", main="Q123", id=123, alt_labels=["Test"])
        self.mocked_query_response = {
            'results': {
                'bindings': [
                    {
                        'main': {'type': 'uri', 'value': 'http://www.wikidata.org/entity/Q123'},
                        'mainLabel': {'xml:lang': 'en', 'type': 'literal', 'value': 'Test Item'},
                        'label': {'xml:lang': 'en', 'type': 'literal', 'value': 'Test Item'},
                        'alt_labels': {'type': 'literal', 'value': ''}
                    },
                    {
                        'main': {'type': 'uri', 'value': 'http://www.wikidata.org/entity/Q321'},
                        'mainLabel': {'xml:lang': 'en', 'type': 'literal', 'value': 'Some Other Item'},
                        'label': {'xml:lang': 'en', 'type': 'literal', 'value': 'Some Other Item'},
                        'alt_labels': {'type': 'literal', 'value': 'alt name 1|alt name 2'}
                    }
                ]
            }
        }
        self.mocked_query_response_empty = {'results': {'bindings': []}}

        class CustomTestModel(WikidataItemBase):
            model_name = 'Test Model'
            model_name_plural = 'Test Models'
            test_field = WikidataEntityListField(properties=['P123'], required=True)
            _hidden_field = WikidataEntityListField(properties=['P321'], required=True)

        self.CustomTestModel = CustomTestModel
        self.custom_test_item = self.CustomTestModel()
        self.custom_test_item_full = self.CustomTestModel(label="Test Item", main="Q123", id=123, alt_labels=["Test"],
                                                          test_field=["Test"], _hidden_field=["TestHidden"])

    def test___init__(self):
        self.assertIsNone(self.test_item.alt_labels)
        self.assertIsNone(self.test_item.main)
        self.assertIsNone(self.test_item.label)
        self.assertIsNone(self.test_item.conformance)
        self.assertIsNone(self.test_item.id)
        self.assertIsNone(self.test_item.schema)
        self.assertEqual(self.test_item.model_name, "Wikidata Item")
        self.assertEqual(self.test_item.model_name_plural, "Wikidata Items")

    def test___init__with_kwargs(self):
        self.assertEqual(self.test_item_full.label, "Test Item")
        self.assertEqual(self.test_item_full.main, "Q123")
        self.assertEqual(self.test_item_full.alt_labels, ["Test"])
        self.assertEqual(self.test_item_full.id, 123)
        self.assertEqual(self.test_item.model_name, "Wikidata Item")
        self.assertEqual(self.test_item.model_name_plural, "Wikidata Items")

    def test_get_wikidata_fields(self):
        fields = WikidataItemBase.get_wikidata_fields()
        field_names = []
        for field in fields:
            self.assertIsInstance(field, WikidataField)
            field_names.append(field.name)
        self.assertEqual(len(field_names), 4)
        self.assertIn("main", field_names)
        self.assertIn("label", field_names)
        self.assertIn("alt_labels", field_names)
        self.assertIn("conformance", field_names)

    def test_get_wikidata_fields__with_keys(self):
        fields = sorted(WikidataItemBase.get_wikidata_fields(with_keys=True), key=lambda x: x[0])
        self.assertEqual(len(fields), 4)
        self.assertEqual("alt_labels", fields[0][0])
        self.assertIsInstance(fields[0][1], WikidataField)
        self.assertEqual("conformance", fields[1][0])
        self.assertIsInstance(fields[1][1], WikidataField)
        self.assertEqual("label", fields[2][0])
        self.assertIsInstance(fields[2][1], WikidataField)
        self.assertEqual("main", fields[3][0])
        self.assertIsInstance(fields[3][1], WikidataField)

    def test_build_serializer(self):
        serializer_class = WikidataItemBase.build_serializer()
        self.assertTrue(issubclass(serializer_class, Serializer))
        self.test_item_full.set_conformance()
        serializer = serializer_class(self.test_item_full)
        self.assertIsInstance(serializer, Serializer)
        serializer_data = serializer.data
        self.assertEqual(serializer_data['id'], '123')
        self.assertEqual(serializer_data['alt_labels'], ["Test"])
        self.assertEqual(serializer_data['label'], "Test Item")
        self.assertEqual(serializer_data['conformance']['focus'], '123')
        self.assertEqual(serializer_data['conformance']['reason'], 'No Schema associated with this model')
        self.assertTrue(serializer_data['conformance']['result'])

    def test_build_serializer__custom_model(self):
        serializer_class = self.CustomTestModel.build_serializer()
        self.assertTrue(issubclass(serializer_class, Serializer))
        self.custom_test_item_full.set_conformance()
        serializer = serializer_class(self.custom_test_item_full)
        self.assertIsInstance(serializer, Serializer)
        serializer_data = serializer.data
        self.assertEqual(serializer_data['id'], '123')
        self.assertEqual(serializer_data['alt_labels'], ["Test"])
        self.assertEqual(serializer_data['label'], "Test Item")
        self.assertEqual(serializer_data['conformance']['focus'], '123')
        self.assertEqual(serializer_data['conformance']['reason'], 'No Schema associated with this model')
        self.assertTrue(serializer_data['conformance']['result'])
        self.assertNotIn('_hidden_field', serializer_data)
        self.assertTrue(serializer_data['test_field'], ["Test"])

    @patch('django_wikidata_api.models.WDItemEngine.execute_sparql_query')
    def test_get_all(self, mocked_execute_query):
        mocked_execute_query.return_value = self.mocked_query_response_empty
        self.assertEqual(WikidataItemBase.get_all(), [])

        mocked_execute_query.return_value = self.mocked_query_response
        output_list = WikidataItemBase.get_all()
        self.assertEqual(len(output_list), 2)
        self.assertIsInstance(output_list[0], WikidataItemBase)
        self.assertEqual(output_list[0].id, 'Q123')
        self.assertEqual(output_list[0].main, 'Q123')
        self.assertEqual(output_list[0].label, 'Test Item')
        self.assertEqual(output_list[0].alt_labels, [])
        self.assertIsNone(output_list[0].conformance)
        self.assertIsInstance(output_list[1], WikidataItemBase)
        self.assertEqual(output_list[1].id, 'Q321')
        self.assertEqual(output_list[1].main, 'Q321')
        self.assertEqual(output_list[1].label, 'Some Other Item')
        self.assertEqual(output_list[1].alt_labels, ['alt name 1', 'alt name 2'])
        self.assertIsNone(output_list[1].conformance)

    @patch('django_wikidata_api.models.WDItemEngine.execute_sparql_query')
    def test_get_all__with_conformance(self, mocked_execute_query):
        mocked_execute_query.return_value = self.mocked_query_response_empty
        self.assertEqual(WikidataItemBase.get_all(with_conformance=True), [])

        mocked_execute_query.return_value = self.mocked_query_response
        output_list = WikidataItemBase.get_all(with_conformance=True)
        self.assertEqual(len(output_list), 2)
        self.assertIsInstance(output_list[0], WikidataItemBase)
        self.assertEqual(output_list[0].id, 'Q123')
        self.assertEqual(output_list[0].main, 'Q123')
        self.assertEqual(output_list[0].label, 'Test Item')
        self.assertEqual(output_list[0].conformance['focus'], 'Q123')
        self.assertEqual(output_list[0].conformance['reason'], 'No Schema associated with this model')
        self.assertTrue(output_list[0].conformance['result'])
        self.assertEqual(output_list[0].alt_labels, [])
        self.assertIsInstance(output_list[1], WikidataItemBase)
        self.assertEqual(output_list[1].id, 'Q321')
        self.assertEqual(output_list[1].main, 'Q321')
        self.assertEqual(output_list[1].label, 'Some Other Item')
        self.assertEqual(output_list[1].alt_labels, ['alt name 1', 'alt name 2'])
        self.assertEqual(output_list[1].conformance['focus'], 'Q321')
        self.assertEqual(output_list[1].conformance['reason'], 'No Schema associated with this model')
        self.assertTrue(output_list[1].conformance['result'])

    @patch('django_wikidata_api.models.WDItemEngine.execute_sparql_query')
    def test_get(self, mocked_execute_query):
        mocked_execute_query.return_value = self.mocked_query_response_empty
        self.assertIsNone(WikidataItemBase.get('Q123'))

        mocked_execute_query.return_value = self.mocked_query_response
        output = WikidataItemBase.get('Q123')
        self.assertIsInstance(output, WikidataItemBase)
        self.assertEqual(output.id, 'Q123')
        self.assertEqual(output.main, 'Q123')
        self.assertEqual(output.label, 'Test Item')
        self.assertIsNone(output.conformance)
        self.assertEqual(output.alt_labels, [])

    @patch('django_wikidata_api.models.WDItemEngine.execute_sparql_query')
    def test_get__with_conformance(self, mocked_execute_query):
        mocked_execute_query.return_value = self.mocked_query_response_empty
        self.assertIsNone(WikidataItemBase.get('Q123', with_conformance=True))

        mocked_execute_query.return_value = self.mocked_query_response
        output = WikidataItemBase.get('Q123', with_conformance=True)
        self.assertIsInstance(output, WikidataItemBase)
        self.assertEqual(output.id, 'Q123')
        self.assertEqual(output.main, 'Q123')
        self.assertEqual(output.label, 'Test Item')
        self.assertEqual(output.conformance['focus'], 'Q123')
        self.assertEqual(output.conformance['reason'], 'No Schema associated with this model')
        self.assertTrue(output.conformance['result'])
        self.assertEqual(output.alt_labels, [])

    @patch('django_wikidata_api.models.WDItemEngine.execute_sparql_query')
    def test_search(self, mocked_execute_query):
        mocked_execute_query.return_value = self.mocked_query_response_empty
        self.assertEqual(WikidataItemBase.search("something"), [])

        mocked_execute_query.return_value = self.mocked_query_response
        self.assertEqual(WikidataItemBase.search("something"), [])
        # search by label
        self.assertEqual(len(WikidataItemBase.search("item")), 2)
        self.assertEqual(len(WikidataItemBase.search("Some Other item")), 1)
        # search by id
        self.assertEqual(len(WikidataItemBase.search('Q123')), 1)
        self.assertEqual(len(WikidataItemBase.search('Q321')), 1)
        # search by alt_labels
        self.assertEqual(len(WikidataItemBase.search('alt name 2')), 1)

    def test_build_query(self):
        output = WikidataItemBase.build_query()
        # test minified
        self.assertNotIn("  ", output)
        self.assertNotIn("\n", output)
        self.assertNotIn("\t", output)
        # test values empty
        self.assertNotIn("VALUES", output)
        self.assertIn("?main ?mainLabel (?mainLabel AS ?label) (GROUP_CONCAT(DISTINCT ?main_alt_label; SEPARATOR=\'|\')"
                      " AS ?alt_labels)", output)
        self.assertIn("WHERE", output)
        self.assertIn("SERVICE wikibase:label { bd:serviceParam wikibase:language \"[AUTO_LANGUAGE],en\". ?main rdfs:"
                      "label ?mainLabel . }", output)
        self.assertIn("GROUP BY ?main ?mainLabel", output)

        output = WikidataItemBase.build_query(values=("Q123", "Q321"))
        self.assertIn("VALUES (?main) { (wd:Q123) (wd:Q321) }", output)
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

    @patch('django_wikidata_api.models.WDItemEngine.execute_sparql_query')
    def test__query_wikidata(self, mocked_execute_query):
        mocked_execute_query.return_value = self.mocked_query_response_empty
        self.assertEqual(WikidataItemBase._query_wikidata(), [])
        self.assertEqual(WikidataItemBase._query_wikidata(("Q123", "Q321")), [])
        self.assertEqual(WikidataItemBase._query_wikidata(limit=20), [])
        self.assertEqual(WikidataItemBase._query_wikidata(("Q123", "Q321"), 20), [])

        mocked_execute_query.return_value = self.mocked_query_response
        expected_out = self.mocked_query_response['results']['bindings']
        self.assertEqual(WikidataItemBase._query_wikidata(), expected_out)
        self.assertEqual(WikidataItemBase._query_wikidata(("Q123", "Q321")), expected_out)
        self.assertEqual(WikidataItemBase._query_wikidata(limit=20), expected_out)
        self.assertEqual(WikidataItemBase._query_wikidata(("Q123", "Q321"), 20), expected_out)

    def test__from_wikidata(self):
        output = WikidataItemBase._from_wikidata(self.mocked_query_response['results']['bindings'][1])
        self.assertIsInstance(output, WikidataItemBase)
        self.assertEqual(output.id, 'Q321')
        self.assertEqual(output.main, 'Q321')
        self.assertEqual(output.label, 'Some Other Item')
        self.assertEqual(output.alt_labels, ['alt name 1', 'alt name 2'])
        self.assertIsNone(output.conformance)

        output = WikidataItemBase._from_wikidata(self.mocked_query_response['results']['bindings'][1],
                                                 with_conformance=True)
        self.assertIsInstance(output, WikidataItemBase)
        self.assertEqual(output.id, 'Q321')
        self.assertEqual(output.main, 'Q321')
        self.assertEqual(output.label, 'Some Other Item')
        self.assertEqual(output.alt_labels, ['alt name 1', 'alt name 2'])
        self.assertEqual(output.conformance['focus'], 'Q321')
        self.assertEqual(output.conformance['reason'], 'No Schema associated with this model')
        self.assertTrue(output.conformance['result'])

    def test__has_substring(self):
        self.assertFalse(self.test_item._has_substring("something"))
        self.assertFalse(self.test_item._has_substring("Test"))
        self.assertFalse(self.test_item._has_substring("Test"))
        self.assertFalse(self.test_item_full._has_substring("something"))
        self.assertTrue(self.test_item_full._has_substring("Q123"))
        self.assertTrue(self.test_item_full._has_substring("item"))
        self.assertTrue(self.test_item_full._has_substring("Test Item"))
        self.assertTrue(self.test_item_full._has_substring("123"))
        self.assertFalse(self.custom_test_item_full._has_substring("something"))
        self.assertFalse(self.custom_test_item_full._has_substring("TestHidden"))
        self.assertTrue(self.custom_test_item_full._has_substring("Q123"))
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
