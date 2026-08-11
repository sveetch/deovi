import datetime
import uuid
from dataclasses import (
    dataclass,
    field as dataclasses_field,
)
from pathlib import Path
from typing import Any, ClassVar

from freezegun import freeze_time
from freezegun.api import FakeDatetime

from deovi.models.mixins.export import ExportMixin
from deovi.models.assets import Asset
from deovi.models.lists import SerializableList
from deovi.utils.tests import dummy_uuid4


@dataclass
class DummyModel(ExportMixin):
    """
    Base model for information models.
    """
    EXPORT_PRIVATES: ClassVar[list[str]] = []
    path: Path
    size: int
    mtime: datetime.datetime
    parent: Any = None
    name: str = None
    casting: SerializableList = dataclasses_field(default_factory=SerializableList)
    cover: Asset = None


@freeze_time("2012-10-15 10:00:00")
def test_as_dict(monkeypatch):
    """
    ExportMixin inheriter model using SerializableList (instead of builtin
    list) should serialize its included models to Python builtin.
    """
    monkeypatch.setattr(uuid, "uuid4", dummy_uuid4)

    ping = Asset(source=Path("/home/foo/ping.png"))
    pong = Asset(source=Path("/home/foo/pong.png"))

    home = DummyModel(
        path=Path("/home"),
        size=101,
        mtime=datetime.datetime.now(),
        name="Home",
        casting=SerializableList([ping]),
        cover=ping,
    )

    franky = DummyModel(
        path=Path("/home/foo"),
        size=42,
        mtime=datetime.datetime.now(),
        parent=home,
        name="Foo",
        casting=SerializableList([ping, pong]),
        cover=pong,
    )

    assert franky.as_dict() == {
        "casting": [
            Asset(
                source=Path("/home/foo/ping.png"),
                destination=Path("dummy_uuid4.png"),
                checksum=None,
            ),
            Asset(
                source=Path("/home/foo/pong.png"),
                destination=Path("dummy_uuid4.png"),
                checksum=None,
            ),
        ],
        "cover": Asset(
            source=Path("/home/foo/pong.png"),
            destination=Path("dummy_uuid4.png"),
            checksum=None,
        ),
        "mtime": FakeDatetime(2012, 10, 15, 10, 0),
        "name": "Foo",
        "parent": DummyModel(
            path=Path("/home"),
            size=101,
            mtime=FakeDatetime(2012, 10, 15, 10, 0),
            parent=None,
            name="Home",
            casting=[
                Asset(
                    source=Path("/home/foo/ping.png"),
                    destination=Path("dummy_uuid4.png"),
                    checksum=None,
                ),
            ],
            cover=Asset(
                source=Path("/home/foo/ping.png"),
                destination=Path("dummy_uuid4.png"),
                checksum=None,
            ),
        ),
        "path": Path("/home/foo"),
        "size": 42,
    }

    assert franky.as_dict(preserve=True) == {
        "casting": [
            {
                "checksum": None,
                "destination": Path("dummy_uuid4.png"),
                "source": Path("/home/foo/ping.png"),
            },
            {
                "checksum": None,
                "destination": Path("dummy_uuid4.png"),
                "source": Path("/home/foo/pong.png"),
            },
        ],
        "cover": {
            "checksum": None,
            "destination": Path("dummy_uuid4.png"),
            "source": Path("/home/foo/pong.png"),
        },
        "mtime": FakeDatetime(2012, 10, 15, 10, 0),
        "name": "Foo",
        "parent": {
            "casting": [
                {
                    "checksum": None,
                    "destination": Path("dummy_uuid4.png"),
                    "source": Path("/home/foo/ping.png"),
                },
            ],
            "cover": {
                "checksum": None,
                "destination": Path("dummy_uuid4.png"),
                "source": Path("/home/foo/ping.png"),
            },
            "mtime": FakeDatetime(2012, 10, 15, 10, 0),
            "name": "Home",
            "parent": None,
            "path": Path("/home"),
            "size": 101,
        },
        "path": Path("/home/foo"),
        "size": 42,
    }
