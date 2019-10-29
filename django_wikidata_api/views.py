# coding=utf-8
""" Register views here. """
from django.conf import settings
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions


schema_view = get_schema_view(
   openapi.Info(
      title=getattr(settings, 'WD_API_TITLE', 'Wikidata API'),
      default_version=getattr(settings, 'WD_API_DEFAULT_VERSION', 'v0'),
      description=getattr(settings, 'WD_API_DESCRIPTION', '"REST API Layer Connecting To Wikidata.org'),
      terms_of_service=getattr(settings, 'WD_API_TERMS'),
      contact=openapi.Contact(name=getattr(settings, 'WD_API_CONTACT_NAME'),
                              email=getattr(settings, 'WD_API_CONTACT_EMAIL'),
                              url=getattr(settings, 'WD_API_CONTACT_URL')),
      license=openapi.License(name=getattr(settings, 'WD_API_LICENSE_NAME')),
   ),
   public=True,
   permission_classes=(permissions.AllowAny, permissions.IsAuthenticatedOrReadOnly),
)
