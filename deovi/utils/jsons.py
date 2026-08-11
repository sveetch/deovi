import datetime
import json
from pathlib import Path
import types

try:
    import tmdbv3api  # NOQA: F401
    TMDB_AVAILABLE = True
except ImportError:
    TMDB_AVAILABLE = False


class ExtendedJsonEncoder(json.JSONEncoder):
    """
    Add support to serialize a Callable

    Usage sample: ::

        json.dumps(..., cls=ExtendedJsonEncoder)
    """
    def default(self, obj):
        if isinstance(obj, bytes):
            return obj.decode("utf-8")
        # Support for pathlib.Path to a string
        if isinstance(obj, Path):
            return str(obj)
        # Support for set to a list
        if isinstance(obj, set):
            return list(obj)
        # Support for date and time
        if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
            return obj.isoformat()
        # Convert callable to its name as a string
        if callable(obj):
            return obj.__name__
        # Convert generator to its name as a string
        if isinstance(obj, types.GeneratorType):
            return obj.__name__

        # Support for tmdb AsObj
        if TMDB_AVAILABLE is True:
            if isinstance(obj, tmdbv3api.as_obj.AsObj):
                return dict(obj.items())

        # Support for models without to import them (from their specific class name)
        # NOTE: This is to be as a last resort
        if hasattr(obj, "serialize"):
            return obj.serialize()

        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)
