from rest_framework import serializers


class WikidataItemSerializer(serializers.Serializer):
    # TODO: Add QID validator and QIDField
    id = serializers.RegexField(regex="(Q|q)\d+", allow_blank=False, min_length=2, max_length=20,
                                help_text="Wikidata Item Identifier (ex. Q59961716)")
    label = serializers.CharField(allow_null=False, allow_blank=False)
    alt_labels = serializers.ListField(allow_null=True, allow_empty=True)

    def create(self, validated_data):
        # TODO: Add a create method that would call a .create method of the model
        pass

    def update(self, instance, validated_data):
        # TODO: Add a update method that would call a .update method of the model
        pass


class WikidataConformanceSerializer(serializers.Serializer):
    # TODO: Add QID validator and QIDField
    focus = serializers.RegexField(regex="(Q|q)\d+", allow_blank=False, min_length=2, max_length=20,
                                   help_text="Wikidata Item Identifier (ex. Q59961716)")
    reason = serializers.CharField(allow_null=False, allow_blank=False)
    result = serializers.BooleanField(allow_null=True)

    def create(self, validated_data):
        # TODO: Add a create method that would call a .create method of the model
        pass

    def update(self, instance, validated_data):
        # TODO: Add a update method that would call a .update method of the model
        pass
