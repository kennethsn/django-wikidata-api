# coding=utf-8
""" django-rest-framework serializers that have specialized Wikidata context """
from rest_framework.fields import (
    BooleanField,
    CharField,
    ListField,
    RegexField,
)
from rest_framework.serializers import Serializer


class WikidataItemSerializer(Serializer):
    # TODO: Add QID validator and QIDField
    id = RegexField(regex="(Q|q)\d+", allow_blank=False, min_length=2, max_length=20,
                    help_text="Wikidata Item Identifier (ex. Q59961716)")
    label = CharField(allow_null=False, allow_blank=False)
    alt_labels = ListField(allow_null=True, allow_empty=True)

    def create(self, validated_data):
        # TODO: Add a create method that would call a .create method of the model
        pass

    def update(self, instance, validated_data):
        # TODO: Add a update method that would call a .update method of the model
        pass


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
