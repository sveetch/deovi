import json
import logging
import uuid
from pathlib import Path
from dataclasses import (
    dataclass,
    fields as dataclasses_fields,
)
from typing import Any, ClassVar

from ..conf import settings
from ..utils.jsons import ExtendedJsonEncoder
from .. import __pkgname__


LOGGER = logging.getLogger(__pkgname__)


@dataclass
class Asset:
    """
    Asset model.

    The purpose of this is to be an "enveloppe" to carry an asset source path and its
    destination so it can be used in a queue.

    This is useful because during collecting stages both source and destination are to
    be used. But finally we only want to export the destination, but source is still
    needed.

    Arguments:
        source (Path): The original asset file path.

    Keyword Arguments:
        destination (Path): Filename path for destination to be possibly applied from
            processors. This is only a filename without any directory path, that is
            on charge of processors. When empty this is filled with a filename computed
            from an UUID4 and a suffix (copied from original file).
    """
    EXPORT_PRIVATES: ClassVar[list[str]] = []
    source: Path
    destination: Path = None

    def __post_init__(self):
        if not self.destination:
            self.destination = Path(str(uuid.uuid4()) + self.source.suffix)

    def as_dict(self, preserve=False):
        """
        A safe way to convert to a dict without recursion issues.

        Keyword Arguments:
            preserve (bool): If enabled all values which have the method ``as_dict()``
                will use it instead of returning their object. This is almost only
                implemented internally in Deovi models so you can get an output of
                ``as_dict()`` only with Python builtin types.

        Returns:
            dict: This model object attribute serialized in a dictionnary, items named
                after one of names from EXPORT_PRIVATES won't be in the output.
        """
        return {
            f.name: (
                getattr(self, f.name).as_dict(preserve=preserve)
                if preserve is True and hasattr(getattr(self, f.name), "as_dict")
                else getattr(self, f.name)
            )
            for f in dataclasses_fields(self)
            if f.name not in self.EXPORT_PRIVATES
        }

    def as_json(self):
        """
        Returns the output of ``as_dict()`` in a JSON string.
        """
        return json.dumps(self.as_dict(), indent=4, cls=ExtendedJsonEncoder)
