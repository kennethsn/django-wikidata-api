# coding=utf-8
""" Django-Style Wikidata Models. """
import logging
import requests
from wikidataintegrator.wdi_core import WDItemEngine

from .constants import (
    ALL_LANGUAGES,
    ENGLISH_LANG,
    WIKIDATA_ENTITY_PREFIX,
    WIKIDATA_ENTITY_PREFIX_URL,
    WIKIDATA_ENTITY_REGEX,
    WIKIDATA_PROP_PREFIX,
    WIKIDATA_PROP_PREFIX_URL,
    WIKIDATA_PROP_REGEX,
    WIKIDATA_SPARQL_ENDPOINT,
    WIKIDATA_SUBCLASS_PROP,
)
from .exceptions import DjangoWikidataAPIException
from .fields import (
    WikidataAltLabelField,
    WikidataConformanceField,
    WikidataDescriptionField,
    WikidataField,
    WikidataLabelField,
    WikidataMainEntityField,
)
from .serializers import WikidataItemSerializer
from .utils import (
    dict_has_substring,
    extract_from_string_by_regex,
    is_private_name,
    set_kwargs
)
from .viewsets import generate_wikidata_item_viewset

_logger = logging.getLogger(__name__)


# TODO: Support nested model responses
# TODO: (currently child must declare a "main" in order to build query in proper order)
class WikidataItemBase(object):
    """ Base Wikidata Item Model """
    class Meta(object):
        """ Meta options for this model. """
        verbose_name = 'Wikidata Item'
        verbose_name_plural = None
        property_fields = None  # TODO: Make a property_field decorator
        language = ENGLISH_LANG
        fallback_languages = ALL_LANGUAGES  # Use comma-separated string. To enforce only primary language, set to ""
        entity_id_regex = WIKIDATA_ENTITY_REGEX
        prop_id_regex = WIKIDATA_PROP_REGEX
        sparql_endpoint = WIKIDATA_SPARQL_ENDPOINT
        prop_prefix = WIKIDATA_PROP_PREFIX
        entity_prefix = WIKIDATA_ENTITY_PREFIX
        prefix_map = {
            entity_prefix: WIKIDATA_ENTITY_PREFIX_URL,
            prop_prefix: WIKIDATA_PROP_PREFIX_URL,
        }
        subclass_prop = WIKIDATA_SUBCLASS_PROP
        user_agent = "django-wikidata-api/application"
        default_page_size = 100
        query_max_get_request_length = 1000

    main = WikidataMainEntityField(triples=[], required=True, show_in_minimal=True)
    label = WikidataLabelField(required=True, show_in_minimal=True)
    description = WikidataDescriptionField(show_in_minimal=True)
    alt_labels = WikidataAltLabelField()
    schema = None
    logger = _logger
    # Instance Attributes set dynamically:
    id = None
    conformance = WikidataConformanceField()

    # dynamically set class attributes:
    _wikidata_fields = None  # Set by _load_wikidata_fields()

    def __init__(self, **kwargs):
        for key, field in self.get_wikidata_fields(with_keys=True):
            setattr(self, key, None)
        set_kwargs(self, kwargs)

    # CLASS METHODS
    @classmethod
    def get_model_name(cls):
        """
        Get the name of this Model.
        Returns (str):

        """
        return cls.Meta.verbose_name

    @classmethod
    def get_model_name_plural(cls):
        """
        Get the plural name of this Model.
        Returns (str):

        """
        # TODO: add pluralize utility
        return cls.Meta.verbose_name_plural or "{}s".format(cls.get_model_name())

    @classmethod
    def _load_wikidata_fields(cls):
        """
        Load Wikidata Fields for this model by setting names based on model attribute.
        Returns (Class[WikidataItemBase]): cls

        """
        fields = []
        keys = []
        for sub_cls in cls.__mro__:
            for key, field in sub_cls.__dict__.items():
                if isinstance(field, WikidataField) and key not in keys:
                    field.set_name(key)
                    keys.append(key)
                    fields.append(field)
        cls._wikidata_fields = zip(keys, fields)
        assert cls._wikidata_fields is not None, "No Wikidata Fields Loaded"
        return cls

    @classmethod
    def get_wikidata_fields(cls, with_keys=False):
        """
        Get all wikidata fields associated with this model.
        Args:
            with_keys (Optional[bool]): True to make the return zipped tuples by keys,
                                        False if iterable fields

        Returns (Union[zip[str, WikidataField], List[WikidataField]]):

        """
        cls._load_wikidata_fields()
        return cls._wikidata_fields if with_keys else [field for key, field in cls._wikidata_fields]

    @classmethod
    def get_view_fields(cls):
        """
        Get all public fields that will be represent this model in a Rest API response
        Returns (List[Tuple[str, Class[Union[WikidataField, Field]]]]):

        """
        view_fields = [(key, field) for key, field
                       in cls.get_wikidata_fields(with_keys=True)
                       if cls._attr_is_public(key)]
        if cls.Meta.property_fields:
            view_fields.extend((field.name, field) for field in cls.Meta.property_fields)
        return view_fields

    @classmethod
    def build_serializer(cls):
        """
        Build a serializer class to support this object.
        Returns (Class[WikidataItemSerializer]):

        """
        attrs = {}
        for key, field in cls.get_view_fields():
            # TODO: Add documentation explaining relationship between main and id
            if key == 'main':
                key = 'id'
            attrs[key] = field.serializer
        serializer_class = type('{}Serializer'.format(cls.__name__), (WikidataItemSerializer,), attrs)
        serializer_class.Meta.ref_name = cls.Meta.verbose_name
        return serializer_class

    @classmethod
    def get_all(cls, page=1, **kwargs):
        """
        Query Wikidata to get all instances of this model.

        Notes:
            TODO: Consider use the .objects.all() style

        Args:
            page (Optional[Int]): Page position, If None, get all pages
            kwargs (Dict): Keyword args to pass through to the ._get_all method

        Returns (List[WikidataItemBase]): Returns a list of this model's instances

        """
        single_page = isinstance(page, int)  # To make multi-page, use 'None'
        item_generator = cls._get_all(page=page, **kwargs)
        if single_page:
            return list(item_generator)
        merged_items = cls._merge_duplicates(item_generator)
        return list(merged_items)

    @classmethod
    def _merge_duplicates(cls, items):
        qid_to_item = {}
        for item in items:
            qid = item.id
            if qid in qid_to_item:
                # TODO: For now take the first result, but in the future we could add a method that combines
                #       the metadata between both so we can "append" in this condition.
                cls.logger.debug("Need To Merge QIDs: %s", qid)
            else:
                qid_to_item[qid] = item
        return qid_to_item.values()

    @classmethod
    def _get_all(cls, with_conformance=False, limit=None, minimal=True, page_size=None, page=1, values=None,
                 language=None):
        """
        Query Wikidata to get all instances of this model.

        Notes:
            - Based on the way the query is optimized, the page_size and limit will provide UPPER bounds, but
              the response count can at times be less than the number provided due to post-query clean-up
              such as merging duplicates.

            - TODO: Consider use the .objects.all() style
        Args:
            with_conformance (Optional[Bool]): True if intending to use SheX validation, False otherwise
            limit (Optional[Int]): The maximum records to query Wikidata for
            minimal (Optional[Bool]): True if only need ID, label and description, False otherwise
            page_size (Optional[Int]): Maximum Number of records per API Request
            page (Optional[Int]): Page position, If None, get all pages
            values (Optional[List[str]]): List of QID values to use in the query.
            language (Optional[str]): Set the Primary language. If not set, will default to Meta Option.

        Returns (Generator[WikidataItemBase]): Generator of this model's instances

        """
        finished = False
        single_page = isinstance(page, int)  # To make multi-page, use 'None'
        page_size = page_size or cls.Meta.default_page_size
        unknown_depth = not values
        page = page or 1
        remaining_limit = limit
        value_total = len(values) if values else None
        if value_total:
            remaining_limit = min(remaining_limit, value_total) if remaining_limit else value_total

        while not finished:
            offset = (page - 1) * page_size
            query_limit = min(remaining_limit, page_size) if limit else page_size
            if values:
                query_values = list(values)[offset:offset+query_limit]
                query_offset = 0
            else:
                query_values = values
                query_offset = offset

            cls.logger.debug("Querying for Page: %s  Limit: %s  Offset: %s  Minimal: %s",
                             page, query_limit, offset, minimal)
            wikidata_response = cls._query_wikidata(limit=query_limit, minimal=minimal, offset=query_offset,
                                                    values=query_values, language=language)
            for item in wikidata_response:
                yield cls._from_wikidata(item, with_conformance=with_conformance)
            api_count = len(wikidata_response)
            cls.logger.debug("... found %s item(s)", api_count)
            if remaining_limit:
                remaining_limit -= api_count
            finished = single_page \
                or (unknown_depth and not api_count) \
                or (isinstance(remaining_limit, int) and remaining_limit <= 0) \
                or (value_total and offset >= value_total)
            page += 1

    @classmethod
    def get(cls, entity_id, with_conformance=False, language=None):
        """
        Query Wikidata to get an instance by Wikidata Entity id.
        Notes:
            TODO: Consider use the .objects.get() style
        Args:
            entity_id (str): Wikidata Entity identifier (ex. "Q1234")
            with_conformance (Optional[Bool]): True if intending to use SheX validation, False otherwise
            language (Optional[str]): Set the Primary language. If not set, will default to Meta Option.

        Returns (Optional[WikidataItemBase]): Returns this model's instance with id=entity_id if found, None otherwise

        """

        wikidata_response = cls._query_wikidata((entity_id,), language=language)
        if wikidata_response:
            return cls._from_wikidata(wikidata_response[0], with_conformance)
        cls.logger.warning("Unable to find %s with Wikidata Entity ID '%s'", cls.Meta.verbose_name, entity_id)
        return None

    @classmethod
    def search(cls, search_string, language=None):
        """
        Get all instances of this model that have an attribute with the given search_string.
        Args:
            search_string (str): Used to perform a substring match of all objects
            language (Optional[str]): Set the Primary language. If not set, will default to Meta Option.

        Returns (List[WikidataItemBase]):

        """
        return [obj for obj in cls.get_all(page=None, minimal=False, language=language)
                if obj._has_substring(search_string)]

    @classmethod
    def count(cls):
        """
        Get the total number of instances.

        Returns (Int):

        """
        wikidata_response = cls._query_wikidata(count=True)
        if wikidata_response:
            return int(wikidata_response[0].get('count', {}).get('value') or 0)
        return 0

    @classmethod
    def _get_primary_language(cls, language=None):
        """
        Get the primary language.

        Args:
            language (Optional[str]): Set the Primary language. If not set, will default to Meta Option.

        Returns (str):

        """
        return language or cls.Meta.language

    @classmethod
    def _build_query_languages(cls, language=None):
        """
        Build the languages used to provide the Label Service within the SPARQL Query.

        Args:
            language (Optional[str]): Set the Primary language. If not set, will default to Meta Option.

        Returns (str):

        """
        return f"{cls._get_primary_language(language)},{cls.Meta.fallback_languages}"

    @classmethod
    def _build_query_filters(cls, fields, minimal=False):
        """
        Build the portion of a SPARQL query that specifies the filtering in the WHERE clause of all fields.

        Args:
            fields (List[WikidataField]):
            minimal (Optional[bool]):

        Returns (str):

        """
        prop_prefix = cls.Meta.prop_prefix
        entity_prefix = cls.Meta.entity_prefix
        subclass_prop = cls.Meta.subclass_prop
        return ' '.join(field.to_wikidata_filter(prop_prefix=prop_prefix, entity_prefix=entity_prefix,
                                                 subclass_prop=subclass_prop)
                        for field in fields if field.required or not field.use_minimal(minimal))

    @classmethod
    def _build_query_prefixes(cls):
        """
        Build the portion of a SPARQL query that defines all prefixes used.

        Returns (str):

        """
        return " ".join(
             f"PREFIX {prefix}: <{url}>"
             for prefix, url in cls.Meta.prefix_map.items()
        )

    @classmethod
    def _build_query_values(cls, values):
        """
        Build the values portion of a SPARQL query.

        Args:
            values (Optional[Iterable[str]]): list-like structure containing Wikidata Entity ID's, ex. ['Q123', 'Q321']

        Returns (str):

        """
        if not values:
            return ""
        formatted_entities = " ".join(f"{cls.Meta.entity_prefix}:{value}" for value in values)
        return f"VALUES ?main {{{formatted_entities}}}"

    @classmethod
    def _build_query_service_clause(cls, fields, minimal, language=None):
        """
        Build the values portion of a SPARQL query.

        Args:
            fields (List[WikidataField]):
            minimal (Optional[bool]):
            language (Optional[str]): Set the Primary language. If not set, will default to Meta Option.

        Returns (str):

        """
        query_services = ' '.join(f.to_wikidata_service() for f in fields if not f.use_minimal(minimal)).strip()
        languages = cls._build_query_languages(language)
        return f"SERVICE wikibase:label {{ bd:serviceParam wikibase:language '{languages}'. {query_services} }}"

    @classmethod
    def _build_query_order_by(cls, count=False):
        """
        Build the ORDER portion of a SPARQL query.

        Args:
            count (Optional[Bool]):

        Returns (str):

        """
        return "" if count else "ORDER BY ?main"

    @classmethod
    def build_query(cls, values=None, limit=None, minimal=False, offset=None, count=False, language=None):
        """
        Build a SPARQL query to fetch data that instantiates instances of models from the Wikidata Query Service.
        Args:
            values (Optional[Iterable[str]]): list-like structure containing Wikidata Entity ID's, ex. ['Q123', 'Q321']
            limit (Optional[int]): used to set a maximum return value in the query
            minimal (Optional[Bool]): True if only need ID, label and description, False otherwise
            offset (Optional[int]): used to position the maximum return value's starting bound
            count (Optional[Bool]): True if only need the count total, False otherwise
            language (Optional[str]): Set the Primary language. If not set, will default to Meta Option.

        Returns (str): minified SPARQL Query string

        """
        if count:
            minimal = True
        fields = cls().get_wikidata_fields()
        primary_language = cls._get_primary_language(language)

        query_fields = ' '.join(f.to_wikidata_field(minimal) for f in fields)
        query_inner_fields = ' '.join(f.to_wikidata_inner_field(minimal) for f in fields)
        query_filters = cls._build_query_filters(fields, minimal)
        query_outer_filters = ' '.join(f.to_wikidata_outer_filter(language=primary_language)
                                       for f in fields if f.required or not f.use_minimal(minimal))
        _group_by_text = ' '.join(f.to_wikidata_group() for f in fields).strip()
        group_by = f"GROUP BY {_group_by_text}" if _group_by_text else ""
        values_filter = cls._build_query_values(values)
        order_by = cls._build_query_order_by(count=count)
        prefixes = cls._build_query_prefixes()
        query_service = cls._build_query_service_clause(fields, minimal, language)
        limit_by = f"LIMIT {limit}" if limit else ""
        offset_by = f"OFFSET {offset}" if offset else ""
        if values_filter:
            subquery = f"""
                SELECT DISTINCT {query_fields}
                WHERE {{
                    {values_filter} {query_filters} {query_outer_filters} {query_service}
                }}
                {group_by} {order_by} {limit_by} {offset_by}
            """
            query = subquery
        else:
            subquery = f"SELECT DISTINCT {query_inner_fields} " \
                       f"WHERE {{{query_filters}}} {order_by} {limit_by} {offset_by}"
            query = f"""
                SELECT DISTINCT {query_fields} WHERE {{
                    {{ {subquery} }} {query_outer_filters} {query_service}
                }}
                {group_by}
            """
        if count:
            query = f"SELECT (COUNT(?main) AS ?count) WHERE {{ {subquery} }}"
        query = f"{prefixes} {query}"
        return " ".join(query.split())

    @classmethod
    def get_viewset_urls(cls, slug='wikidata_item'):
        """
        Get viewset router urls to append to the django URLConf.
        Notes:
            For reference on url return types, check out the django docs:
            https://docs.djangoproject.com/en/2.2/ref/urls/
        Args:
            slug (Optional[str]): Base slug to set the path of the url patterns.

        Returns (URLResolver): An object that can be added to urlpatterns

        """
        viewset = generate_wikidata_item_viewset(cls, slug)
        return viewset.get_viewset_urls()

    @classmethod
    def _query_wikidata(cls, values=None, limit=None, minimal=False, offset=None, count=False, query=None,
                        language=None):
        """
        Query Wikidata for data related to this model.
        Args:
            values (Optional[Iterable[str]]): list-like structure containing Wikidata Entity ID's, ex. ['Q123', 'Q321']
            limit (Optional[int]): used to set a maximum return value in the query
            minimal (Optional[Bool]): True if only need ID, label and description, False otherwise
            offset (Optional[int]): used to position the maximum return value's starting bound
            count (Optional[Bool]): True if only need the count total, False otherwise
            query (Optional[str]): Pass in a custom query.
            language (Optional[str]): Set the Primary language. If not set, will default to Meta Option.

        Returns (List[Dict]]): The results->bindings of the Wikidata Query Service response

        """
        cls.logger.debug("Executing Wikidata Query - <limit: %s, minimal: %s, offset: %s, count: %s>",
                         limit, minimal, offset, count)
        query = query or cls.build_query(values, limit, minimal, offset, count, language)
        return cls._execute_query(query)

    @classmethod
    def _execute_query(cls, query, sparql_endpoint=None, user_agent=None):
        """
        Execute a SPARQL Query to a Wikibase.

        Args:
            query (str):
            sparql_endpoint (Optional[str]):
            user_agent (Optional[str]):

        Returns (List[Dict]): The results->bindings of the Wikidata Query Service response

        Raises:
            DjangoWikidataAPIException: If there is an error processing the query.

        """
        sparql_endpoint = sparql_endpoint or cls.Meta.sparql_endpoint
        user_agent = user_agent or cls.Meta.user_agent
        query = f"#Tool: django-wikidata-api\n{query}"
        data = {'query': query}
        headers = {'Accept': 'application/sparql-results+json', 'User-Agent': user_agent}
        try:
            if len(query) < cls.Meta.query_max_get_request_length:
                data["format"] = "json"
                response = requests.get(sparql_endpoint, params=data, headers=headers)
            else:
                response = requests.post(sparql_endpoint, data=data, headers=headers)
            response.raise_for_status()
            response_json = response.json()
            return response_json['results']['bindings']
        except Exception as e:
            raise DjangoWikidataAPIException(f"Error Executing Query to Wikidata Query Service: {e}")

    @classmethod
    def _from_wikidata(cls, wikidata_response, with_conformance=False):
        """
        Parse Wikidata Query Service response to instantiate a model object.
        Args:
            wikidata_response (Dict[str, Dict[str, str]]):
            with_conformance (Optional[Bool]): True if intending to use SheX validation, False otherwise

        Returns (WikidataItemBase):

        """
        obj = cls()
        for field in cls.get_wikidata_fields():
            obj._set_wikidata_field(field, wikidata_response)
        obj.id = obj.main
        assert obj.id, "Wikidata Item Must Have Identifier"
        return obj.set_conformance() if with_conformance else obj

    @classmethod
    def _attr_is_public(cls, attr):
        """
        Check if an attribute is public to the view layer.
        Args:
             attr (str): Name of attribute

        Returns (Bool): True if attribute can be shown in the view layer, False otherwise.

        """
        if cls._attr_is_wikidata_field(attr):
            return getattr(cls, attr).public
        return not is_private_name(attr)

    @classmethod
    def _attr_is_wikidata_field(cls, attr):
        """
        Check if an attribute is a field to be used for Wikidata interactions
        Args:
            attr (str): Name of attribute

        Returns (Bool): True if attribute is instance of WikidataField, False otherwise

        """
        return isinstance(getattr(cls, attr), WikidataField)

    # INSTANCE METHODS

    def set_conformance(self):
        """
        Compare Item with ShEx schema.

        Returns (WikidataItemBase): self

        """
        if self.schema:
            self.conformance = WDItemEngine.check_shex_conformance(self.id, self.schema, output="all")
        else:
            self.logger.debug("No schema associated with this model: Setting result to 'n/a' "
                              "(Consider adding a model schema before using this functionality)")
            self.conformance = {
                'focus': self.id,
                'reason': 'No Schema associated with this model',
                'result': 'n/a'
            }
        return self

    def _set_wikidata_field(self, field, wikidata_response):
        """
        Parse Wikidata Query Service response to set a corresponding attribute
        Args:
            field (WikidataField):
            wikidata_response (Dict[str, Dict[str, str]]):

        Returns (WikidataItemBase): self

        """
        setattr(self, field.name, field.from_wikidata(wikidata_response, entity_id_regex=self.Meta.entity_id_regex))
        return self

    def _has_substring(self, substring):
        """
        Check if substring matches any (public) attributes in model.
        Args:
            substring (str):

        Returns (Bool): True if there is a match, False otherwise

        """
        return dict_has_substring(self._get_public_dict(), substring)

    def _get_public_dict(self):
        """
        Get a dictionary representation of this instance that is safe for the view layer.
        Returns (Dict):

        """
        # TODO: consider a caching or performance boost to build serializer so that it only
        #       needs to be built once
        return self.build_serializer()(self).data

    @classmethod
    def find_entity_id(cls, search_string):
        """
        Find the Entity Id in a string.

        Returns (Optional[str]):
        """
        return extract_from_string_by_regex(cls.Meta.entity_id_regex, search_string)

    @classmethod
    def find_prop_id(cls, search_string):
        """
        Find the Property Id in a string.

        Returns (Optional[str]):
        """
        return extract_from_string_by_regex(cls.Meta.prop_id_regex, search_string)

    def __repr__(self):
        return "<{}: {}>".format(self.Meta.verbose_name, self.__str__())

    def __str__(self):
        return "{} ({})".format(self.label, self.main or self.id)


class WDTriple(object):
    """ Wikidata SPARQL Triple. """
    def __init__(self, prop, values, subclass=False, minus=False,
                 prop_prefix=WIKIDATA_PROP_PREFIX, entity_prefix=WIKIDATA_ENTITY_PREFIX,
                 subclass_prop=WIKIDATA_SUBCLASS_PROP):
        assert not (len(values) > 1 and minus), "Union and Minus should not be used in the same clause"
        self.prop = prop
        self.prop_prefix = prop_prefix
        self.entity_prefix = entity_prefix
        self.subclass_prop = subclass_prop
        self.values = values
        self.subclass = subclass
        self.minus = minus

    def format(self, field_name, prop_prefix=None, entity_prefix=None, subclass_prop=None):
        """
        Format for a SPARQL Query.

        Args:
             field_name (str):
             prop_prefix (Optional[str]):
             entity_prefix (Optional[str]):
             subclass_prop (Optional[str]):

        Returns (str):

        """
        prop_prefix = prop_prefix or self.prop_prefix
        entity_prefix = entity_prefix or self.entity_prefix
        subclass_prop = subclass_prop or self.subclass_prop

        query_prop = f"{self.prop}/{prop_prefix}:{subclass_prop}*" if self.subclass else self.prop
        query = " UNION ".join(f"{{{{ ?{{name}} {prop_prefix}:{query_prop} {entity_prefix}:{val}.}}}}"
                               for val in self.values)
        query = f"MINUS {query}" if self.minus else query
        return query.format(name=field_name)
