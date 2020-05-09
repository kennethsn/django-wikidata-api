# coding=utf-8
""" django-rest-framework serializers that have specialized Wikidata context """
from rest_framework.fields import (
    BooleanField,
    CharField,
    IntegerField,
    RegexField,
)
from rest_framework.serializers import (
    Serializer,
    SerializerMetaclass,
)

from .constants import (
    WIKIDATA_ENTITY_REGEX,
    WIKIDATA_PROP_REGEX,
)


class WDItemIDField(RegexField):
    """ Wikidata Item Field """

    def __init__(self, regex=WIKIDATA_ENTITY_REGEX, help_text="Wikidata Item Identifier (ex. Q55090238)", min_length=2,
                 max_length=20, **kwargs):
        super(WDItemIDField, self).__init__(regex=regex, help_text=help_text, min_length=min_length,
                                            max_length=max_length, **kwargs)


class WDPropertyIDField(RegexField):
    """ Wikidata Property Field """

    def __init__(self, regex=WIKIDATA_PROP_REGEX, help_text="Wikidata Property Identifier (ex. P31)", min_length=2,
                 max_length=20, **kwargs):
        super(WDPropertyIDField, self).__init__(regex=regex, help_text=help_text, min_length=min_length,
                                                max_length=max_length, **kwargs)


class DjangoWikidataAPIReadOnlySerializer(Serializer):
    """ Base Serializer for Read Only Support. """

    def create(self, validated_data):
        """
        Create an object.

        Notes:
            - This method is not used.

        Returns:

        """
        pass

    def update(self, instance, validated_data):
        """
        Update an object.

        Notes:
            - This method is not used.

        Returns:

        """
        pass


class WikidataItemSerializer(DjangoWikidataAPIReadOnlySerializer):
    """ Stories API Serializer Base Class """

    class Meta(SerializerMetaclass):
        """ Meta class for Story API Serializer. """


class WikidataConformanceSerializer(DjangoWikidataAPIReadOnlySerializer):
    """ Wikidata Conformance Serializer """
    focus = WDItemIDField(allow_blank=False)
    reason = CharField(allow_null=False, allow_blank=False)
    result = BooleanField(allow_null=True)


class WikidataItemQuerySerializer(DjangoWikidataAPIReadOnlySerializer):
    """ Serializer for the Get a Wikidata Item Query Parameters """

    class Meta(SerializerMetaclass):
        """ Meta class for Story API Serializer. """
        ref_name = "Wikidata Item Request"

    conformance = BooleanField(default=False)


class WikidataItemListQuerySerializer(WikidataItemQuerySerializer):
    """ Serializer for the Get Wikidata Items Query Parameters """

    class Meta(WikidataItemQuerySerializer.Meta):
        """ Meta class for Story API Serializer. """

        ref_name = "Wikidata Item List Request"

    page = IntegerField(default=1)


class WikidataItemMinimalSerializer(WikidataItemSerializer):
    """ Wikidata Item List View Serializer """
    class Meta(WikidataItemSerializer.Meta):
        """ Meta Options. """
        ref_name = "Wikidata Item Summary"

    id = WDItemIDField(allow_blank=False)
    label = CharField()
    description = CharField()
