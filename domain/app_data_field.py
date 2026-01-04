from enum import Enum, auto
import json
import datetime as dt
from uuid import UUID

_CONVERTERS = {
    int: int,
    float: float,
    str: str,
    bool: lambda s: s.strip().lower() in {"1", "true", "yes", "on"},
    dt.datetime: lambda s: dt.datetime.fromisoformat(s.replace("Z", "+00:00")),
    UUID: UUID,
    list: json.loads,   # expects JSON arrays
    dict: json.loads,   # expects JSON objects
}

def parse_to(type, s: str):
    # exact match in registry
    if type in _CONVERTERS:
        return _CONVERTERS[type](s)

    # try JSON first (handles numbers/bools/null cleanly if string is valid JSON)
    try:
        return json.loads(s)
    except Exception:
        pass

    # safe Python literal fallback
    try:
        import ast
        return ast.literal_eval(s)
    except Exception:
        pass

    # last resort: call the type on the string
    return type(s)

class AppDataField(Enum):
    EXIFTOOL_VERSION = (auto(), str, None)
    THUMBNAIL_GENERATION = (auto(), bool, True)
    THUMBNAIL_SIZE_PX = (auto(), int, 150)

    def __new__(cls, value, field_type, default_value):
        obj = object.__new__(cls)
        obj._value_ = value  # unique, so no aliasing
        obj.field_type = field_type
        obj.default_value = default_value
        return obj

    def parse(self, s: str):
        return parse_to(self.field_type, s)
