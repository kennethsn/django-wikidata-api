# coding=utf-8
""" Django Model-like fields to structure and parse Wikidata Query Service interactions """
from rest_framework import serializers

from .constants import (
    ENGLISH_LANG,
    WIKIDATA_ENTITY_REGEX,
    WIKIDATA_PROP_PREFIX,
)
from .serializers import (
    WDItemIDField,
    WikidataConformanceSerializer,
)
from .utils import (
    extract_from_string_by_regex,
    get_wikidata_field,
    is_private_name,
    set_kwargs,
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
                 serializer_settings=None, public=None, show_in_minimal=False, **kwargs):
        self.entity_name = entity_name
        self.properties = properties
        self.values = values
        self.default = default
        self.required = required
        self.public = public  # used to override private _attrs
        self.show_in_minimal = show_in_minimal  # used to determine if a field should show up in the list view
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

    def _prop_sparql_string(self, prop_prefix=WIKIDATA_PROP_PREFIX, **_):
        return "|".join(f"{prop_prefix}:{prop}" for prop in self.properties or [])

    def to_wikidata_field(self, minimal=False):
        """
        Get the portion of a SPARQL query that specifies the field name.

        Args:
            minimal (Optional[Bool]): True if only need ID, label and description, False otherwise

        Returns (str):

        """
        return "" if self.use_minimal(minimal) else f"?{self.name}"

    def to_wikidata_inner_field(self, minimal=False):
        """
        Get the portion of a SPARQL query that specifies the field name within the inner query.

        Args:
            minimal (Optional[Bool]): True if only need ID, label and description, False otherwise

        Returns (str):

        """
        return self.to_wikidata_field(minimal)

    def to_wikidata_filter(self, **kwargs):
        """
        Get the portion of a SPARQL query that specifies the filtering in the WHERE clause.

        Returns (str):

        Raises (AssertionError): If there are no self.properties defined

        """
        assert isinstance(self.properties, list) and len(self.properties), \
            "There are no properties associated with this field."
        prop_string = self._prop_sparql_string(**kwargs)
        wd_triple = "?{self.entity_name} {props} ?{self.name}.".format(self=self, props=prop_string)
        return wd_triple if self.required else "OPTIONAL {{ {} }}".format(wd_triple)

    def to_wikidata_outer_filter(self, **_):
        """
        Get the portion of a SPARQL query that specifies the filtering in the outer WHERE clause.

        Returns (str):

        """
        return ""

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

    def from_wikidata(self, wikidata_response, **_):
        """
        Get the field's value from Wikidata query service response.
        Args:
            wikidata_response (Dict[str, Dict[str, str]]):

        Returns (str):

        """
        return get_wikidata_field(wikidata_response, self.name, self.default)

    def use_minimal(self, minimal):
        """
        Check if this field should return a minimal version or full version for query building.

        Args:
            minimal (Bool):

        Returns (Bool):

        """
        return minimal and not self.show_in_minimal


class WikidataListResponseMixin(object):
    """ Mixin for List Response. """
    separator = '|'
    name = None
    default = None
    serializer_field_class = serializers.ListField
    default_serializer_settings = {'allow_null': True, 'allow_empty': True}

    def from_wikidata(self, wikidata_response, **_):
        """
        Get the field's value from Wikidata query service response.
        Args:
            wikidata_response (Dict[str, Dict[str, str]]):

        Returns (str):

        """
        field = get_wikidata_field(wikidata_response, self.name, self.default)
        return field.split(self.separator) if field else self.default


class WikidataNoSPARQLMixin(object):
    """ Wikidata Field that does not impact the underlying SPARQL Queries. """

    @staticmethod
    def to_wikidata_field(*_, **__):
        """
        Get the portion of a SPARQL query that specifies the field name.

        Returns (Literal[""]):

        """
        return ""

    @staticmethod
    def to_wikidata_filter(**_):
        """
        Get the portion of a SPARQL query that specifies the filtering in the WHERE clause.

        Notes:
            Labels are not in the WHERE clause in a SPARQL query

        Returns (""):

        """
        return ""

    @staticmethod
    def to_wikidata_service():
        """
        Get the portion of a SPARQL query that handles additional service information.

        Returns (str):

        """
        return ""

    @staticmethod
    def to_wikidata_group():
        """
        Get the portion of a SPARQL query in the GROUP BY clause.

        Returns (str):

        """
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

    def to_wikidata_field(self, minimal=False):
        """
        Get the portion of a SPARQL query that specifies the field name.

        Args:
            minimal (Optional[Bool]): True if only need ID, label and description, False otherwise

        Returns (str):

        """
        return "{self.from_name} ({self.from_name} AS ?{self.name})".format(self=self)

    def to_wikidata_inner_field(self, minimal=False):
        """
        Get the portion of a SPARQL query that specifies the field name within the inner query.

        Args:
            minimal (Optional[Bool]): True if only need ID, label and description, False otherwise

        Returns (str):

        """
        return ""

    def to_wikidata_filter(self, **_):
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
    """ Wikidata Entity Field. """
    # TODO: Add Item and Property SubClasses
    serializer_field_class = WDItemIDField
    default_serializer_settings = {'allow_blank': False}
    wikidata_filter = None

    def __init__(self, triples, **kwargs):
        self.triples = triples
        super(WikidataEntityField, self).__init__(**kwargs)

    def to_wikidata_filter(self, prop_prefix=None, entity_prefix=None, subclass_prop=None):
        """
        Get the portion of a SPARQL query that specifies the filtering in the WHERE clause.

        Args:
             prop_prefix (Optional[str]):
             entity_prefix (Optional[str]):
             subclass_prop (Optional[str]):

        Returns (str):

        """
        self.wikidata_filter = " ".join(triple.format(self.entity_name, prop_prefix, entity_prefix, subclass_prop)
                                        for triple in self.triples)
        return self.wikidata_filter if self.required else "OPTIONAL {{ {} }}".format(self.wikidata_filter)

    def to_wikidata_group(self):
        """
        Get the portion of a SPARQL query in the GROUP BY clause.

        Returns (str):

        """
        return "?{self.name}".format(self=self)

    def from_wikidata(self, wikidata_response, entity_id_regex=WIKIDATA_ENTITY_REGEX, **kwargs):
        """
        Get the field's value from Wikidata query service response.
        Args:
            wikidata_response (Dict[str, Dict[str, str]]):
            entity_id_regex (Optional[str]):

        Returns (str):

        """
        value = super(WikidataEntityField, self).from_wikidata(wikidata_response,
                                                               entity_id_regex=entity_id_regex, **kwargs)
        return extract_from_string_by_regex(entity_id_regex, value, value)


class WikidataMainEntityField(WikidataEntityField):
    """ Field to use as the Main Entity. """

    def to_wikidata_field(self, minimal=False):
        """
        Get the portion of a SPARQL query that specifies the field name.

        Args:
            minimal (Optional[Bool]): True if only need ID, label and description, False otherwise

        Returns (str):

        """
        return f"?{self.name}"


class WikidataEntityFilterField(WikidataField):
    """ Wikidata Entity Filter Field. """

    def to_wikidata_filter(self, **kwargs):
        """
        Get the portion of a SPARQL query that specifies the filtering in the WHERE clause.

        Returns (str):

        """
        prop_string = self._prop_sparql_string(**kwargs)
        wd_filter = "?{self.entity_name} {props} ?{self.name}_qid. FILTER(?{self.name}_qid=wd:{vals}).".format(
            self=self, props=prop_string, vals="|| ?{self.name}_qid=wd:".join(self.values)).format(self=self)
        return wd_filter if self.required else "OPTIONAL {{ {} }}".format(wd_filter)

    def to_wikidata_service(self):
        """
        Get the portion of a SPARQL query that handles additional service information.

        Returns (str):

        """
        # TODO: Merge similarities with entity list label
        return "?{self.name}_qid rdfs:label ?{self.name} . ".format(self=self)

    def to_wikidata_group(self):
        """
        Get the portion of a SPARQL query in the GROUP BY clause.

        Returns (str):

        """
        return "?{self.name}".format(self=self)


class WikidataListField(WikidataListResponseMixin, WikidataField):
    """ Wikidata Field for List Items """

    def __init__(self, properties=None, empty=True, separator='|', **kwargs):
        self.separator = separator
        if empty:
            kwargs['default'] = []
        super(WikidataListField, self).__init__(properties, **kwargs)

    def to_wikidata_field(self, minimal=False):
        """
        Get the portion of a SPARQL query that specifies the field name.

        Args:
            minimal (Optional[Bool]): True if only need ID, label and description, False otherwise

        Returns (str):

        """
        return "" if self.use_minimal(minimal) else \
            f"(GROUP_CONCAT(DISTINCT ?{self.name}_item; SEPARATOR='{self.separator}') AS ?{self.name})"

    def to_wikidata_inner_field(self, minimal=False):
        """
        Get the portion of a SPARQL query that specifies the field name within the inner query.

        Args:
            minimal (Optional[Bool]): True if only need ID, label and description, False otherwise

        Returns (str):

        """
        return "" if self.use_minimal(minimal) else f"?{self.name}_item"

    def to_wikidata_filter(self, **kwargs):
        """
        Get the portion of a SPARQL query that specifies the filtering in the WHERE clause.

        Returns (str):

        """
        prop_string = self._prop_sparql_string(**kwargs)
        wd_filter = "?{self.entity_name} {props} ?{self.name}_item .".format(self=self, props=prop_string)
        return wd_filter if self.required else "OPTIONAL {{ {} }}".format(wd_filter)

    def to_wikidata_group(self):
        """
        Get the portion of a SPARQL query in the GROUP BY clause.
        Returns (Literal[""]):

        """
        return ""


class WikidataAltLabelField(WikidataListField):
    """ Field to get the Alternative Labels of an Item. """
    suffix = '_alt_label'

    def to_wikidata_field(self, minimal=False):
        """
        Get the portion of a SPARQL query that specifies the field name.

        Args:
            minimal (Optional[Bool]): True if only need ID, label and description, False otherwise

        Returns (str):

        """
        return "" if self.use_minimal(minimal) else \
            f"(GROUP_CONCAT(DISTINCT ?{self.entity_name}_alt_label; SEPARATOR='{self.separator}') AS ?{self.name})"

    def to_wikidata_inner_field(self, minimal=False):
        """
        Get the portion of a SPARQL query that specifies the field name within the inner query.

        Args:
            minimal (Optional[Bool]): True if only need ID, label and description, False otherwise

        Returns (str):

        """
        return ""

    def to_wikidata_filter(self, **_):
        """
        Get the portion of a SPARQL query that specifies the filtering in the WHERE clause.

        Returns (str):

        """
        return ""

    def to_wikidata_outer_filter(self, language=ENGLISH_LANG, **_):
        """
        Get the portion of a SPARQL query that specifies the filtering in the outer WHERE clause.

        Args:
            language (Optional[str]):

        Returns (str):

        """
        wd_filter = f"?{self.entity_name} skos:altLabel ?{self.entity_name}_alt_label ." \
                    f"FILTER (lang(?{self.entity_name}_alt_label)='{language}')"
        return wd_filter if self.required else "OPTIONAL {{ {} }}".format(wd_filter)


class WikidataEntityListField(WikidataListField):
    """ Field to get values as Wikidata Items. """

    def __init__(self, properties=None, **kwargs):
        assert properties, "There must be a list/tuple of properties"
        super(WikidataEntityListField, self).__init__(properties, **kwargs)

    def to_wikidata_field(self, minimal=False):
        """
        Get the portion of a SPARQL query that specifies the field name.

        Args:
            minimal (Optional[Bool]): True if only need ID, label and description, False otherwise

        Returns (str):

        """
        return "" if self.use_minimal(minimal) else \
            f"(GROUP_CONCAT(DISTINCT ?{self.name}_itemLabel; SEPARATOR='{self.separator}') AS ?{self.name})"

    def to_wikidata_service(self):
        """
        Get the portion of a SPARQL query that handles additional service information.

        Returns (str):

        """
        return "?{self.name}_item rdfs:label ?{self.name}_itemLabel . ".format(self=self)


class SchemaAboutField(WikidataField):
    """ Field used to connect SPARQL to another external resource. """
    serializer_field_class = serializers.URLField
    default_serializer_settings = {'allow_null': True, 'allow_blank': True}

    def __init__(self, url, **kwargs):
        super(SchemaAboutField, self).__init__(**kwargs)
        self.url = url

    def to_wikidata_filter(self, **_):
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
    """ Wikidata Conformance Field. """
    serializer_field_class = WikidataConformanceSerializer
    default_serializer_settings = {}


class ModelPropertyField(object):
    """ Meta-Object used to register a model property as a view field. """

    def __init__(self, name, serializer):
        self.name = name
        self.serializer = serializer
