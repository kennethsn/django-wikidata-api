from rest_framework import serializers

from .serializers import WikidataConformanceSerializer
from .utils import (
    get_wikidata_field,
    set_kwargs
)

# TODO: Fields
# BindField - Example: BIND(wd:Q937 AS ?item).


class WikidataField(object):
    name = None
    serializer_class = serializers.Field
    default_serializer_settings = {}
    serializer = None

    def __init__(self, properties=None, values=None, default=None, required=False, entity_name='main',
                 serializer_settings=None, **kwargs):
        self.entity_name = entity_name
        self.properties = properties
        self.values = values
        self.default = default
        self.required = required
        set_kwargs(self, kwargs)
        self.set_serializer(serializer_settings or {})

    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, self.name)

    def set_serializer(self, serializer_settings):
        for key, value in self.default_serializer_settings.items():
            if key not in serializer_settings:
                serializer_settings[key] = value
        self.serializer = self.serializer_class(**serializer_settings)

    def _prop_sparql_string(self):
        return "wdt:{}".format('|wdt:'.join(self.properties))

    def to_wikidata_field(self):
        return "?{self.name}".format(self=self)

    def to_wikidata_filter(self):
        prop_string = self._prop_sparql_string()
        wd_triple = "?{self.entity_name} {props} ?{self.name}.".format(self=self, props=prop_string)
        return wd_triple if self.required else "OPTIONAL {{}}".format(wd_triple)

    def to_wikidata_service(self):
        return ""

    def to_wikidata_group(self):
        return ""

    def from_wikidata(self, wikidata_response):
        return get_wikidata_field(wikidata_response, self.name, self.default)


class WikidataListResponseMixin(object):
    separator = '|'
    name = None
    default = None
    serializer_class = serializers.ListField
    default_serializer_settings = {'allow_null': True, 'allow_empty': True}

    def from_wikidata(self, wikidata_response):
        field = get_wikidata_field(wikidata_response, self.name, self.default)
        return field.split(self.separator) if field else self.default


class WikidataStringField(WikidataField):
    pass


class WikidataLabelField(WikidataField):
    suffix = 'Label'
    serializer_class = serializers.CharField
    default_serializer_settings = {'allow_null': False, 'allow_blank': False}

    def __init__(self, **kwargs):
        super(WikidataLabelField, self).__init__(**kwargs)
        self.from_name = "{}{}".format(self.entity_name, self.suffix)

    def to_wikidata_field(self):
        return "?{self.from_name} (?{self.from_name} AS ?{self.name})".format(self=self)

    def to_wikidata_filter(self):
        return ''  # Labels are not in the WHERE clause in a SPARQL query

    def to_wikidata_service(self):
        # TODO: Merge similarities with entity list label
        return "?{self.entity_name} rdfs:label ?{self.from_name} . ".format(self=self)

    def to_wikidata_group(self):
        return "?{self.from_name}".format(self=self)


class WikidataEntityField(WikidataField):
    # TODO: Add Item and Property SubClasses
    serializer_class = serializers.RegexField
    default_serializer_settings = {'allow_blank': False, 'regex': "(Q|q)\d+", 'min_length': 2, 'max_length': 20,
                                   'help_text': "Wikidata Item Identifier (ex. Q59961716)"}
    wikidata_filter = None

    def __init__(self, triples, **kwargs):
        super(WikidataEntityField, self).__init__(**kwargs)
        self.wikidata_filter = " ".join(triple.format(self.entity_name) for triple in triples)

    def to_wikidata_filter(self):
        return self.wikidata_filter if self.required else "OPTIONAL {{ {} }}".format(self.wikidata_filter)

    def to_wikidata_group(self):
        return "?{self.name}".format(self=self)

    def from_wikidata(self, wikidata_response):
        field = super(WikidataEntityField, self).from_wikidata(wikidata_response)
        return field.replace('http://www.wikidata.org/entity/', '')


class WikidataEntityFilterField(WikidataField):
    def to_wikidata_filter(self):
        prop_string = self._prop_sparql_string()
        wd_filter = "?{self.entity_name} {props} ?{self.name}_qid. FILTER(?{self.name}_qid=wd:{vals}).".format(
            self=self, props=prop_string, vals="|| ?{self.name}_qid=wd:".join(self.values)).format(self=self)
        return wd_filter if self.required else "OPTIONAL {{ {} }}".format(wd_filter)

    def to_wikidata_service(self):
        # TODO: Merge similarities with entity list label
        return "?{self.name}_qid rdfs:label ?{self.name} . ".format(self=self)

    def to_wikidata_group(self):
        return "?{self.name}".format(self=self)


class WikidataListField(WikidataListResponseMixin, WikidataField):
    def __init__(self, properties=None, empty=True, separator='|', **kwargs):
        self.separator = separator
        if empty:
            kwargs['default'] = []
        super(WikidataListField, self).__init__(properties, **kwargs)

    def to_wikidata_field(self):
        return "(GROUP_CONCAT(DISTINCT ?{self.name}_item; SEPARATOR='{self.separator}') AS ?{self.name})".format(
            self=self)

    def to_wikidata_filter(self):
        prop_string = self._prop_sparql_string()
        wd_filter = "?{self.entity_name} {props} ?{self.name}_item .".format(self=self, props=prop_string)
        return wd_filter if self.required else "OPTIONAL {{ {} }}".format(wd_filter)


class WikidataAltLabelField(WikidataListField):
    suffix = '_alt_label'

    def to_wikidata_field(self):
        return "(GROUP_CONCAT(DISTINCT ?{self.entity_name}_alt_label; SEPARATOR='{self.separator}') AS " \
               "?{self.name})".format(self=self)

    def to_wikidata_filter(self):
        # TODO: add language support in here
        wd_filter = "?{self.entity_name} skos:altLabel ?{self.entity_name}_alt_label ." \
               "FILTER (lang(?{self.entity_name}_alt_label)='en')".format(self=self)
        return wd_filter if self.required else "OPTIONAL {{ {} }}".format(wd_filter)


class WikidataEntityListField(WikidataListField):
    def __init__(self, properties=None, **kwargs):
        assert properties, "There must be a list/tuple of properties"
        super(WikidataEntityListField, self).__init__(properties, **kwargs)

    def to_wikidata_field(self):
        return "(GROUP_CONCAT(DISTINCT ?{self.name}_itemLabel; SEPARATOR='{self.separator}') AS ?{self.name})".format(
            self=self)

    def to_wikidata_service(self):
        return "?{self.name}_item rdfs:label ?{self.name}_itemLabel . ".format(self=self)


class WikidataConformanceField(WikidataField):
    serializer_class = WikidataConformanceSerializer
    default_serializer_settings = {}

    # def __init__(self, **kwargs):
    #     super(WikidataLabelField, self).__init__(**kwargs)
    #     self.from_name = "{}{}".format(self.entity_name, self.suffix)

    def to_wikidata_field(self):
        return ""

    def to_wikidata_filter(self):
        return ""

    def to_wikidata_service(self):
        return ""

    def to_wikidata_group(self):
        return ""
