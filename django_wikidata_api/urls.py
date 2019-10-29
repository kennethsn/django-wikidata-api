# coding=utf-8
""" Register builtin url's here. """
from django.conf.urls import url
from django.urls import include
from .views import schema_view

urlpatterns = [
    url(r'^$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    url(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    url(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    url(r'^api-auth/', include('rest_framework.urls'))
]
