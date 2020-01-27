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


class WikidataItemSerializer(Serializer):
    """ Stories API Serializer Base Class """

    class Meta(SerializerMetaclass):
        """ Meta class for Story API Serializer. """


class WikidataConformanceSerializer(Serializer):
    # TODO: Add QID validator and QIDField
    focus = RegexField(regex="(Q|q)\d+", allow_blank=False, min_length=2, max_length=20,
                       help_text="Wikidata Item Identifier (ex. Q59961716)")
    reason = CharField(allow_null=False, allow_blank=False)
    result = BooleanField(allow_null=True)

    def create(self, validated_data):
        # TODO: Add a create method that would call a .create method of the model
        pass

    def update(self, instance, validated_data):
        # TODO: Add a update method that would call a .update method of the model
        pass


class WikidataItemQuerySerializer(Serializer):
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

    class Meta(WikidataItemSerializer.Meta):
        ref_name = "Wikidata Item Summary"

    id = RegexField(regex="(Q|q)\d+", allow_blank=False, min_length=2, max_length=20,
                    help_text="Wikidata Item Identifier (ex. Q59961716)")
    label = CharField()
    description = CharField()
