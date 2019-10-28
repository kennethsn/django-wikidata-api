# coding=utf-8
""" Django-Style Wikidata Models. """
import logging
from rest_framework.serializers import Serializer
from wikidataintegrator.wdi_core import WDItemEngine

from .fields import (
    WikidataAltLabelField,
    WikidataConformanceField,
    WikidataEntityField,
    WikidataField,
    WikidataLabelField
)
from .utils import (
    dict_has_substring,
    set_kwargs
)
from .viewsets import generate_wikidata_item_viewset

_logger = logging.getLogger(__name__)


# TODO: Add Language Support
# TODO: Support nested model responses
# TODO: (currently child must declare a "main" in order to build query in proper order)
class WikidataItemBase(object):
    """ Base Wikidata Item Model """
    model_name = 'Wikidata Item'
    model_name_plural = 'Wikidata Items'
    main = WikidataEntityField(triples=[], required=True)
    label = WikidataLabelField(required=True)
    alt_labels = WikidataAltLabelField()
    schema = None
    # Instance Attributes set dynamically:
    id = None
    conformance = WikidataConformanceField()

    def __init__(self, **kwargs):
        for key, field in self.get_fields(with_keys=True):
            field.name = key
            setattr(self, key, None)
        set_kwargs(self, kwargs)

    @classmethod
    def get_fields(cls, with_keys=False):
        """
        Get all fields associated with this model.
        Args:
            with_keys (Optional[bool]): True to make the return zipped tuples by keys,
                                        False if iterable fields

        Returns (Union[zip[str, WikidataField], List[WikidataField]]):

        """
        fields = []
        keys = []
        for sub_cls in cls.__mro__:
            for key, field in sub_cls.__dict__.items():
                if isinstance(field, WikidataField) and key not in keys:
                    keys.append(key)
                    fields.append(field)
        return zip(keys, fields) if with_keys else fields

    @classmethod
    def build_serializer(cls):
        """
        Build a serializer class to support this object.
        Returns (Class[Serializer]):

        """
        attrs = {}
        for key, field in cls.get_fields(with_keys=True):
            # TODO: Addd documentation explaining relationship between main and id
            if key == 'main':
                key = 'id'
            attrs[key] = field.serializer
        return type('{}Serializer'.format(cls.__name__), (Serializer,), attrs)

    @classmethod
    def get_all(cls, with_conformance=False, limit=None):
        """
        Query Wikidata to get all instances of this model.
        Notes:
            TODO: Consider structuring as a generator return like Django does, and use the .objects.all() style
        Args:
            with_conformance (Optional[Bool]): True if intending to use SheX validation, False otherwise
            limit (Optional[Int]): The maximum records to query Wikidata for

        Returns (List[WikidataItemBase]): Returns a list of this model's instances

        """
        wikidata_response = cls._query_wikidata(limit=limit)
        return [cls._from_wikidata(x, with_conformance) for x in wikidata_response]

    @classmethod
    def get(cls, entity_id, with_conformance=False):
        """
        Query Wikidata to get an instance by Wikidata Entity id.
        Notes:
            TODO: Consider use the .objects.get() style
        Args:
            entity_id (str): Wikidata Entity identifier (ex. "Q1234")
            with_conformance (Optional[Bool]): True if intending to use SheX validation, False otherwise

        Returns (Optional[WikidataItemBase]): Returns this model's instance with id=entity_id if found, None otherwise

        """

        wikidata_response = cls._query_wikidata((entity_id,), limit=1)
        if wikidata_response:
            return cls._from_wikidata(wikidata_response[0], with_conformance)
        _logger.warning("Unable to find %s with Wikidata Entity ID '%s'", cls.model_name, entity_id)
        return None

    @classmethod
    def search(cls, search_string):
        """
        Get all instances of this model that have an attribute with the given search_string.
        Args:
            search_string (str): Used to perform a substring match of all objects

        Returns (List[WikidataItemBase]):

        """
        return [obj for obj in cls.get_all() if obj._has_substring(search_string)]

    @classmethod
    def build_query(cls, values=None, limit=None):
        """
        Build a SPARQL query to fetch data that instantiates instances of models from the Wikidata Query Service.
        Args:
            values (Optional[Iterable[str]]): list-like structure containing Wikidata Entity ID's, ex. ['Q123', 'Q321']
            limit (Optional[int]): used to set a maximum return value in the query

        Returns (str): minified SPARQL Query string

        """
        # TODO: Add Offset
        fields = cls().get_fields()
        to_fields = ' '.join(f.to_wikidata_field() for f in fields)
        to_filters = ' '.join(f.to_wikidata_filter() for f in fields)
        to_services = ' '.join(f.to_wikidata_service() for f in fields)
        to_group = ' '.join(f.to_wikidata_group() for f in fields)
        value_filter = "VALUES (?main) {{ (wd:{vals}) }}".format(vals=") (wd:".join(val for val in values)) \
            if values else ''
        limit_by = f"LIMIT {limit}" if limit else ""

        query = f"""
                SELECT DISTINCT {to_fields}
                WHERE {{
                    {value_filter}
                    {to_filters}
                    SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". {to_services} }}
                }}
                GROUP BY {to_group}
                {limit_by}

            """
        return " ".join(query.split())

    @classmethod
    def get_viewset_urls(cls, slug='wikidata_item'):
        """
        Get viewset router urls to append to the django URLconf.
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
    def _query_wikidata(cls, values=None, limit=None):
        """
        Query Wikidata for data related to this model.
        Args:
            values (Optional[Iterable[str]]): list-like structure containing Wikidata Entity ID's, ex. ['Q123', 'Q321']
            limit (Optional[int]): used to set a maximum return value in the query

        Returns (List[Dict]]): The results->bindings of the Wikidata Query Service response

        """
        # TODO: Add some custom error handling
        results_json = WDItemEngine.execute_sparql_query(cls.build_query(values, limit))
        return results_json['results']['bindings']

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
        for field in cls.get_fields():
            setattr(obj, field.name, field.from_wikidata(wikidata_response))
        obj.id = obj.main
        assert obj.id, "Wikidata Item Must Have Identifier"
        return obj.set_conformance() if with_conformance else obj

    def _has_substring(self, substring):
        return dict_has_substring(self.__dict__, substring)

    def __repr__(self):
        return "<{}: {}>".format(self.model_name, self.__str__())

    def __str__(self):
        return "{} ({})".format(self.label, self.main)

    def set_conformance(self):
        if self.schema:
            self.conformance = WDItemEngine.check_shex_conformance(self.id, self.schema, output="all")
        else:
            _logger.debug("No schema associated with this model: Setting result to 'n/a' "
                          "(Consider adding a model schema before using this functionality)")
            self.conformance = {
                'focus': self.id,
                'reason': 'No Schema associated with this model',
                'result': 'n/a'
            }
        return self


class WDTriple(object):
    def __init__(self, prop, values, subclass=False, minus=False):
        assert not (len(values) > 1 and minus), "Union and Minus should not be used in the same clause"
        self.prop = "{}/wdt:P279*".format(prop) if subclass else prop
        self.values = values
        query = " UNION ".join(f"{{{{ ?{{name}} wdt:{self.prop} wd:{val}.}}}}" for val in self.values)
        self._query = f"MINUS {query}" if minus else query

    def format(self, field_name):
        return self._query.format(name=field_name)
