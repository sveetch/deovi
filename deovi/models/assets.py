import logging
import uuid
from pathlib import Path
from dataclasses import (
    dataclass,
    InitVar,
)
from typing import Any, ClassVar

from ..conf import settings
from .. import __pkgname__

from .abstracts import ChecksumAbstract, ExportAbstract


LOGGER = logging.getLogger(__pkgname__)


@dataclass
class Asset(ChecksumAbstract, ExportAbstract):
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
        checksum (str): Checksum (this is expected to be a long blake2b string).
        autochecksum (bool): If enabled the model will compute and set the ``checksum``
            attribute with a checksum of the source file content.
    """
    EXPORT_PRIVATES: ClassVar[list[str]] = []
    CHECKSUM_FIELD: ClassVar[str] = "source"
    source: Path
    destination: Path = None
    checksum: str = None
    autochecksum: InitVar[bool] = False

    def __post_init__(self, autochecksum):
        if not self.destination:
            self.destination = Path(str(uuid.uuid4()) + self.source.suffix)

        if autochecksum:
            self.set_checksum()
