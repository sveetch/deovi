import json
from pathlib import Path


class ExtendedJsonEncoder(json.JSONEncoder):
    """
    Add support for more basic object types.
    """
    def default(self, obj):
        # Support for pathlib.Path to a string
        if isinstance(obj, Path):
            return str(obj)
        # Support for set to a list
        if isinstance(obj, set):
            return list(obj)

        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)
