# coding=utf-8
""" Django Model-like fields to structure and parse Wikidata Query Service interactions """
from rest_framework import serializers

from .serializers import WikidataConformanceSerializer
from .utils import (
    get_wikidata_field,
    is_private_name,
    set_kwargs
)

# TODO: Fields
# BindField - Example: BIND(wd:Q937 AS ?item).


class WikidataField(object):
    """Base WikidataItem Model field used to build and parse SPARQL queries."""
    name = None
    serializer_field_class = serializers.Field
    default_serializer_settings = {}
    serializer = None
    sparql_field_suffix = ""

    def __init__(self, properties=None, values=None, default=None, required=False, entity_name='main',
                 serializer_settings=None, public=None, **kwargs):
        self.entity_name = entity_name
        self.properties = properties
        self.values = values
        self.default = default
        self.required = required
        self.public = public  # used to override private _attrs
        self.from_name = "?{}{}".format(self.entity_name, self.sparql_field_suffix)
        set_kwargs(self, kwargs)
        self.set_serializer(serializer_settings or {})

    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, self.name)

    def set_name(self, name):
        """
        Set self.name and keep self.public consistent based on python convention.
        Args:
            name (str):

        Returns (WikidataField): self

        """
        self.name = name
        if self.public is None:
            self.public = not is_private_name(name)
        return self

    def set_serializer(self, serializer_settings):
        """
        Instantiate self.serializer with self.serializer_field_class.
        Args:
            serializer_settings (dict) options to be passed into the field class:

        Returns (WikidataField): self

        """
        for key, value in self.default_serializer_settings.items():
            if key not in serializer_settings:
                serializer_settings[key] = value
        self.serializer = self.serializer_field_class(**serializer_settings)
        return self

    def _prop_sparql_string(self):
        return "wdt:{}".format('|wdt:'.join(self.properties))

    def to_wikidata_field(self):
        """
        Get the portion of a SPARQL query that specifies the field name.
        Returns (str):

        """
        return "?{self.name}".format(self=self)

    def to_wikidata_filter(self):
        """
        Get the portion of a SPARQL query that specifies the filtering in the WHERE clause.
        Returns (str):

        Raises (AssertionError): If there are no self.properties defined

        """
        assert isinstance(self.properties, list) and len(self.properties), \
            "There are no properties associated with this field."
        prop_string = self._prop_sparql_string()
        wd_triple = "?{self.entity_name} {props} ?{self.name}.".format(self=self, props=prop_string)
        return wd_triple if self.required else "OPTIONAL {{ {} }}".format(wd_triple)

    def to_wikidata_service(self):
        """
        Get the portion of a SPARQL query that handles additional service information.
        Returns (""):

        """
        return ""

    def to_wikidata_group(self):
        """
        Get the portion of a SPARQL query in the GROUP BY clause.
        Returns (str):

        """
        return self.from_name

    def from_wikidata(self, wikidata_response):
        """
        Get the field's value from Wikidata query service response.
        Args:
            wikidata_response (Dict[str, Dict[str, str]]):

        Returns (str):

        """
        return get_wikidata_field(wikidata_response, self.name, self.default)


class WikidataListResponseMixin(object):
    separator = '|'
    name = None
    default = None
    serializer_field_class = serializers.ListField
    default_serializer_settings = {'allow_null': True, 'allow_empty': True}

    def from_wikidata(self, wikidata_response):
        field = get_wikidata_field(wikidata_response, self.name, self.default)
        return field.split(self.separator) if field else self.default


class WikidataNoSPARQLMixin(object):
    def to_wikidata_field(self):
        return ""

    def to_wikidata_filter(self):
        return ""

    def to_wikidata_service(self):
        return ""

    def to_wikidata_group(self):
        return ""


class WikidataCharField(WikidataField):
    """ WikidataItem Model field used to build and parse SPARQL queries as a string. """
    serializer_field_class = serializers.CharField


class WikidataLabelField(WikidataCharField):
    """ WikidataItem Model field used to build and parse entity labels in SPARQL queries. """
    default_serializer_settings = {'allow_null': False, 'allow_blank': False}
    service_property = "rdfs:label"
    sparql_field_suffix = 'Label'

    def __init__(self, **kwargs):
        super(WikidataLabelField, self).__init__(**kwargs)

    def to_wikidata_field(self):
        """
        Get the portion of a SPARQL query that specifies the field name.
        Returns (str):

        """
        return "{self.from_name} ({self.from_name} AS ?{self.name})".format(self=self)

    def to_wikidata_filter(self):
        """
        Get the portion of a SPARQL query that specifies the filtering in the WHERE clause.

        Notes:
            Labels are not in the WHERE clause in a SPARQL query

        Returns (""):

        """
        return ""

    def to_wikidata_service(self):
        """
        Get the portion of a SPARQL query that handles additional service information.
        Returns (str):

        """
        # TODO: Merge similarities with entity list label
        return "?{self.entity_name} {self.service_property} {self.from_name} . ".format(self=self)


class WikidataDescriptionField(WikidataLabelField):
    """ Wikidata Field to bind a description to an entity field. """
    default_serializer_settings = {'allow_null': True, 'allow_blank': True}
    service_property = "schema:description"
    sparql_field_suffix = 'Description'


class WikidataEntityField(WikidataField):
    # TODO: Add Item and Property SubClasses
    serializer_field_class = serializers.RegexField
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

    def to_wikidata_group(self):
        """
        Get the portion of a SPARQL query in the GROUP BY clause.
        Returns (""):

        """
        return ""


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


class SchemaAboutField(WikidataField):
    """ Field used to connect SPARQL to another external resource. """
    serializer_field_class = serializers.URLField
    default_serializer_settings = {'allow_null': True, 'allow_blank': True}

    def __init__(self, url, **kwargs):
        super(SchemaAboutField, self).__init__(**kwargs)
        self.url = url

    def to_wikidata_filter(self):
        """
        Get the portion of a SPARQL query that specifies the filtering in the WHERE clause.
        Returns (str):
        """
        wd_filter = f"?{self.name} schema:about ?{self.entity_name}; schema:isPartOf <{self.url}>."
        return wd_filter if self.required else "OPTIONAL {{ {} }}".format(wd_filter)

    def to_wikidata_group(self):
        """
        Get the portion of a SPARQL query in the GROUP BY clause.
        Returns (str):

        """
        return f"?{self.name}"


class WikidataConformanceField(WikidataNoSPARQLMixin, WikidataField):
    serializer_field_class = WikidataConformanceSerializer
    default_serializer_settings = {}


class ModelPropertyField(object):
    """ Meta-Object used to register a model property as a view field. """

    def __init__(self, name, serializer):
        self.name = name
        self.serializer = serializer
