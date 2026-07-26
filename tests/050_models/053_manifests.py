import uuid
from pathlib import Path

from freezegun import freeze_time
from freezegun.api import FakeDatetime

from deovi.models import Asset, CollectionManifest, MovieManifest, SerieManifest
from deovi.utils.tests import dummy_uuid4

from tests.utils import (
    SAMPLE_MOVIE_PAYLOAD,
    SAMPLE_TV_PAYLOAD,
)


@freeze_time("2012-10-15 10:00:00.001007")
def test_movie_creation(monkeypatch, tmp_path):
    """
    Basic creation of a Movie manifest using the sample payload.

    Possible cover is expected to be a file aside of the movie file with the same
    filename (without extension).

    .
    └── movies/
        ├── the-pit.mp4
        ├── the-pit.json
        └── the-pit.jpg
    """
    monkeypatch.setattr(uuid, "uuid4", dummy_uuid4)

    directory_path = tmp_path / "movies"
    directory_path.mkdir()

    # Create a dummy manifest file
    manifest_path = directory_path / "the-pit.json"
    manifest_path.write_text("dummy manifest the-pit.json")

    # Create a dummy movie file
    movie_path = directory_path / "the-pit.mp4"
    movie_path.write_text("dummy the-pit.mp4")

    # Create a dummy cover
    cover = directory_path / "the-pit.jpg"
    cover.write_text("dummy the-pit.jpg")

    # Basic definition with payload and without cover
    the_pit = MovieManifest(manifest_path, **SAMPLE_MOVIE_PAYLOAD)
    assert the_pit.tmdb_id == "273204"
    assert the_pit.tmdb_type == "movie"
    assert the_pit.title == "The Pit and the Pendulum"

    # Cover enabled but not matching the existing one
    the_pit = MovieManifest(manifest_path, cover_extensions=(".png",))
    assert the_pit.cover is None

    # With existing cover matching allowed extensions
    the_pit = MovieManifest(manifest_path, cover_extensions=(".jpg",))
    assert isinstance(the_pit.cover, Asset) is True
    assert the_pit.cover.source == cover
    assert the_pit.cover.destination.suffix == ".jpg"

    # Serialized
    assert the_pit.as_dict(preserve=True) == {
        "casting": [],
        "cover": {
            "checksum": None,
            "destination": Path("dummy_uuid4.jpg"),
            "source": tmp_path / "movies/the-pit.jpg",
        },
        "crew": [],
        "genres": [],
        "locked": False,
        "original_language": None,
        "overview": None,
        "path": tmp_path / "movies/the-pit.json",
        "release_date": "",
        "status": None,
        "title": "the-pit.json",
        "tmdb_id": None,
        "tmdb_type": "movie",
    }


@freeze_time("2012-10-15 10:00:00.001007")
def test_collection_creation(monkeypatch, tmp_path):
    """
    Basic creation of a Collection manifest.

    Possible cover is expected to be a file in the collection directory.

    .
    └── saga_starworse/
        ├── cover.jpg
        ├── manifest.json
        ├── the-first-nope.mp4
        ├── the-first-nope.json
        └── the-first-nope.jpg
    """
    monkeypatch.setattr(uuid, "uuid4", dummy_uuid4)

    collection_path = tmp_path / "saga_starworse"
    collection_path.mkdir()

    # here the manifest file itself do not need to exists on FS
    manifest_path = collection_path / "manifest.json"

    # Create a dummy collection cover
    cover = collection_path / "cover.jpg"
    cover.write_text("dummy collection cover.jpg")

    # Create a dummy movie in collection dir
    movie_path = collection_path / "the-first-nope.mp4"
    movie_path.write_text("dummy the-first-nope.mp4")
    first_nope = MovieManifest(movie_path)

    # Basic definition with payload and without cover
    starworse = CollectionManifest(manifest_path, movies=[first_nope])
    assert starworse.tmdb_id is None
    assert starworse.tmdb_type == "collection"
    assert starworse.title == "manifest.json"
    assert starworse.cover is None
    assert first_nope.parent == starworse

    # Cover enabled but not matching the existing one
    starworse = CollectionManifest(manifest_path, cover_extensions=(".png",))
    assert starworse.cover is None

    # With existing cover matching allowed extensions
    starworse = CollectionManifest(manifest_path, cover_extensions=(".jpg",))
    assert isinstance(starworse.cover, Asset) is True
    assert starworse.cover.source == cover
    assert starworse.cover.destination.suffix == ".jpg"

    # Serialized
    assert starworse.as_dict(preserve=True) == {
        "casting": [],
        "cover": {
            "checksum": None,
            "destination": Path("dummy_uuid4.jpg"),
            "source": tmp_path / "saga_starworse/cover.jpg",
        },
        "crew": [],
        "genres": [],
        "locked": False,
        "movies": [],
        "original_language": None,
        "overview": None,
        "path": tmp_path / "saga_starworse/manifest.json",
        "status": None,
        "title": "manifest.json",
        "tmdb_id": None,
        "tmdb_type": "collection",
    }

@freeze_time("2012-10-15 10:00:00.001007")
def test_serie_creation(monkeypatch, tmp_path):
    """
    Basic creation of a Tv show manifest using the sample payload.

    Possible cover is expected to be a file in the serie directory.

    .
    └── the_outer_limits/
        ├── ...
        ├── manifest.json
        └── cover.jpg
    """
    monkeypatch.setattr(uuid, "uuid4", dummy_uuid4)

    serie_path = tmp_path / "the_outer_limits"
    serie_path.mkdir()

    # here the manifest file itself do not need to exists on FS
    manifest_path = serie_path / "manifest.json"

    # Create a dummy serie cover
    cover = serie_path / "cover.jpg"
    cover.write_text("dummy serie cover.jpg")

    # Basic definition with payload and without cover
    the_outer_limits = SerieManifest(manifest_path, **SAMPLE_TV_PAYLOAD)
    assert the_outer_limits.tmdb_id == "21567"
    assert the_outer_limits.tmdb_type == "tv"
    assert the_outer_limits.title == "The Outer Limits"
    assert the_outer_limits.cover is None

    # Cover enabled but not matching the existing one
    the_outer_limits = SerieManifest(manifest_path, cover_extensions=(".png",))
    assert the_outer_limits.cover is None

    # With existing cover matching allowed extensions
    the_outer_limits = SerieManifest(manifest_path, cover_extensions=(".jpg",))
    assert isinstance(the_outer_limits.cover, Asset) is True
    assert the_outer_limits.cover.source == cover
    assert the_outer_limits.cover.destination.suffix == ".jpg"

    # Serialized
    assert the_outer_limits.as_dict(preserve=True) == {
        "casting": [],
        "cover": {
            "checksum": None,
            "destination": Path("dummy_uuid4.jpg"),
            "source": tmp_path / "the_outer_limits/cover.jpg",
        },
        "crew": [],
        "first_air_date": "",
        "genres": [],
        "locked": False,
        "number_of_episodes": None,
        "number_of_seasons": None,
        "original_language": None,
        "overview": None,
        "path": tmp_path / "the_outer_limits/manifest.json",
        "status": None,
        "title": "manifest.json",
        "tmdb_id": None,
        "tmdb_type": "tv",
    }
