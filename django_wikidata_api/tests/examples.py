# coding=utf-8
""" Reusable examples of the django-wikidata-api package for tests. """
from rest_framework.fields import CharField

from django_wikidata_api.models import (
    WDTriple,
    WikidataItemBase,
)
from django_wikidata_api.fields import (
    ModelPropertyField,
    WikidataMainEntityField,
    WikidataEntityListField,
    WikidataListField,
)


class CustomTestModel(WikidataItemBase):
    """ Custom model. """

    class Meta(WikidataItemBase.Meta):
        """ Meta options for Custom models """
        verbose_name = 'Test Model'
        verbose_name_plural = 'Test Model Instances'
        property_fields = (
            ModelPropertyField("test_property", CharField()),
            ModelPropertyField("color", CharField(source='test_property_2')),
            ModelPropertyField("test_attr", CharField()),
            ModelPropertyField("age", CharField(source="test_attr_2"))
        )

    test_field = WikidataEntityListField(properties=['P123'], required=True)
    _private_field = WikidataEntityListField(properties=['P321'], required=True)
    _public_field = WikidataEntityListField(properties=['P4321'], required=True, public=True)
    hidden_field = WikidataEntityListField(properties=['P1234'], required=True, public=False)
    test_attr = "Test Attr"
    test_attr_2 = 37

    @property
    def test_property(self):
        """Example property"""
        return "Test Value"

    @property
    def test_property_2(self):
        """Another example property that should resolve to 'color'"""
        return "blue"

    @property
    def hidden_property(self):
        """Example hidden property"""
        return "Test Hidden Value"


class Taxon(WikidataItemBase):
    """ Wikidata Taxon with Spanish as the Primary Langauge """
    class Meta(WikidataItemBase.Meta):
        """Meta Options"""
        language = "es"
        fallback_languages = ""
    main = WikidataMainEntityField(triples=(WDTriple(prop="P31", values=("Q16521",)),), required=True)
    grin_ids = WikidataListField(properties=("P1421",), required=True)
    parents = WikidataEntityListField(properties=("P171",), required=True)
    ranks = WikidataEntityListField(properties=("P105",), required=True)
