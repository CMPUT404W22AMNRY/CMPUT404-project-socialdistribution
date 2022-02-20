from collections import OrderedDict
from rest_framework import renderers
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination


class Pagination(PageNumberPagination):
    page_size_query_param = 'size'

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('items', data)
        ]))


def getNamedRenderer(resource_type: str) -> renderers.JSONRenderer:
    class NamedJsonRenderer(renderers.JSONRenderer):
        def render(self, data, accepted_media_type=None, renderer_context=None):
            data['type'] = resource_type
            return super().render(data, accepted_media_type, renderer_context)
    return NamedJsonRenderer
