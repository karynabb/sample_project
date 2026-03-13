from json import JSONDecoder
from typing import ClassVar, Type

from django.core.serializers.json import Deserializer as JSONDeserializer
from django.core.serializers.json import DjangoJSONEncoder
from django.core.serializers.json import Serializer as JSONSerializer
from pydantic import BaseModel, parse_obj_as


class Serializer(JSONSerializer):
    """Convert a queryset to JSON."""

    internal_use_only = False

    def _init_options(self):
        self._current = None
        self.json_kwargs = self.options.copy()
        self.json_kwargs.pop("stream", None)
        self.json_kwargs.pop("fields", None)
        if self.options.get("indent"):
            # Prevent trailing spaces
            self.json_kwargs["separators"] = (",", ": ")
        self.json_kwargs.setdefault("cls", PydanticEncoder)
        self.json_kwargs.setdefault("ensure_ascii", False)


def Deserializer(stream_or_string, **options):
    yield from JSONDeserializer(stream_or_string, **options)


class PydanticEncoder(DjangoJSONEncoder):
    def default(self, o):
        if isinstance(o, BaseModel):
            return o.dict()
        else:
            return super().default(o)


class PydanticDecoder(JSONDecoder):
    model: ClassVar[Type[BaseModel]]

    def __init__(self, *args, **kwargs):
        JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, dct):
        return parse_obj_as(self.model, dct)
