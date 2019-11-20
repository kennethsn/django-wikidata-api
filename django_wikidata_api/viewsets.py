# coding=utf-8
""" Viewset helper functions. """
from django.conf.urls import (
    include,
    url
)
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import (
    routers,
    viewsets
)
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response


def generate_wikidata_item_viewset(wikidata_model, slug='wikidata_item', permission_classes=None):
    """
    Generate a Viewset class from a WikidataItem model.

    Args:
        wikidata_model (WikidataItemBase):
        slug (Optional[str]): the url slug to be used for the api route patterns
        permission_classes (Optional[List[BasePermission]]): any permission classes to set to access this viewset

    Returns (WikidataItemViewSet):

    """
    name = wikidata_model.get_model_name()
    name_plural = wikidata_model.get_model_name_plural()
    serializer = wikidata_model.build_serializer()
    _permission_classes = permission_classes or []

    class WikidataItemViewSet(viewsets.ViewSet):
        """
        A ViewSet for listing and retrieving Wikidata Item objects.
        """
        serializer_class = serializer
        model = wikidata_model
        lookup_field = 'wikidata_id'
        permission_classes = _permission_classes

        @swagger_auto_schema(operation_summary="List All {}".format(name_plural),
                             operation_description="Get all {} from querying Wikidata using the Wikidata "
                                                   "SPARQL endpoint.".format(name_plural),
                             responses={200: serializer(many=True)},
                             tags=[name_plural])
        def list(self, request):
            """
            Get all objects.
            Args:
                request:

            Returns:

            """
            with_conformance = request.query_params.get('conformance', False)
            queryset = self.model.get_all(with_conformance=with_conformance)
            _serializer = self.serializer_class(queryset, many=True)
            return Response(_serializer.data)

        @swagger_auto_schema(operation_summary=f"Get {name} By QID",
                             operation_description=f"Retrieve a {name} by querying Wikidata for the corresponding"
                                                   f" Item's Statements.",
                             responses={200: serializer(), 404: f"No {name} Found with ID: <QID>"},
                             tags=[name_plural])
        def retrieve(self, request, wikidata_id=None):
            """
            Return metadata if the provided QID is found in Wikidata and the item's statements matches the
            schema.

            **Note:** *For more details on how we determine the Schema, [see here][ref].*

            [ref]: http://example.com/activating-accounts
            """
            with_conformance = request.query_params.get('conformance', False)
            obj = self.model.get(wikidata_id, with_conformance=with_conformance)
            if not obj:
                raise NotFound(detail=f"No {name} Found with ID: {wikidata_id}")
            _serializer = self.serializer_class(obj)
            return Response(_serializer.data)

        @swagger_auto_schema(operation_summary="Search for {}".format(name_plural),
                             operation_description="Perform a keyword lookup of metadata from all {} using the "
                                                   "Wikidata SPARQL endpoint".format(name_plural),
                             manual_parameters=[
                                 openapi.Parameter(name="query", in_="query", required=True, type="string",
                                                   description='Search For {}'.format(name_plural)),
                             ],
                             responses={200: serializer(many=True), 404: "No Search Results Found for 'query'"},
                             tags=[name_plural])
        @action(detail=False, methods=['POST'])
        def search(self, request):
            """
            Args:
                request:

            Returns:

            """
            # TODO: Add 404
            search_string = request.query_params.get('query')
            queryset = self.model.search(search_string)
            if not queryset:
                raise NotFound(detail="No Search Results Found for '{}'".format(search_string))
            _serializer = self.serializer_class(queryset, many=True)
            return Response(_serializer.data)

        @classmethod
        def get_viewset_urls(cls):
            # TODO: Possibly add slugify function to pull from class name/model name
            router = routers.DefaultRouter()
            router.register(r'{}'.format(slug), cls, base_name=slug)
            return url(r'^'.format(slug), include(router.urls), name=slug)

    return WikidataItemViewSet
