import json
from rest_framework import renderers


def getNamedRenderer(resource_type: str) -> renderers.JSONRenderer:
    class NamedJsonRenderer(renderers.JSONRenderer):
        def render(self, data, accepted_media_type=None, renderer_context=None):
            data['type'] = resource_type
            return super().render(data, accepted_media_type, renderer_context)
    return NamedJsonRenderer
