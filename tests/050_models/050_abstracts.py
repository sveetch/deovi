import datetime
import logging
import uuid
from dataclasses import (
    dataclass,
    field as dataclasses_field,
)
from pathlib import Path
from typing import Any, ClassVar

from freezegun import freeze_time
from freezegun.api import FakeDatetime

from deovi import __pkgname__
from deovi.models import CollectionManifest, MovieManifest, SerieManifest
from deovi.models.mixins.export import ExportMixin
from deovi.models.mixins.loader import ManifestLoaderMixin
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
def test_export_list(monkeypatch):
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

    assert franky.serialize() == {
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

    assert franky.as_coerced() == {
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


@freeze_time("2012-10-15 10:00:00")
def test_loader_discover_manifest(caplog, tmp_path):
    """
    Original mixin method should be able to discover path for every type of manifest.
    """
    caplog.set_level(logging.DEBUG, logger=__pkgname__)

    loader = ManifestLoaderMixin()

    # Build manifest for each model
    series = tmp_path / "series"
    series.mkdir()
    the_serie_path = series / "manifest.json"
    the_serie = SerieManifest(
        the_serie_path,
        tmdb_id=42,
        tmdb_type="tv",
        title="The SERIE",
    )
    the_serie_path.write_text(the_serie.as_json())

    movies = tmp_path / "movies"
    movies.mkdir()
    the_movie_path = movies / "the-movie.yaml"
    the_movie = MovieManifest(
        the_movie_path,
        tmdb_id=33,
        tmdb_type="movie",
        title="The MOVIE",
    )
    the_movie_path.write_text(the_movie.as_yaml())

    collections = tmp_path / "collections"
    collections.mkdir()
    the_collection_path = collections / "manifest.json"
    the_collection = CollectionManifest(
        the_collection_path,
        tmdb_id=77,
        tmdb_type="movie",
        title="The COLLECTION",
    )
    the_collection_path.write_text(the_collection.as_json())

    loaded_serie = loader.discover_manifest(series)
    assert loaded_serie.title == "The SERIE"

    loaded_collection = loader.discover_manifest(collections)
    assert loaded_collection.title == "The COLLECTION"

    loaded_movie = loader.discover_manifest(movies)
    assert loaded_movie is None

    loaded_movie = loader.discover_manifest(movies, name="the-movie")
    assert loaded_movie.title == "The MOVIE"

    assert caplog.record_tuples == []
