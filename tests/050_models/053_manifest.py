from pathlib import Path

from freezegun import freeze_time

from deovi.models import CollectionManifest, MovieManifest, SerieManifest

from tests.utils import (
    SAMPLE_MOVIE_PAYLOAD,
    SAMPLE_TV_PAYLOAD,
)


@freeze_time("2012-10-15 10:00:00.001007")
def test_serie_creation():
    """
    Basic creation of a Tv show manifest using the sample payload.
    """
    the_outer_limits = SerieManifest(
        Path("/series/the_outer_limits"),
        **SAMPLE_TV_PAYLOAD,
    )

    assert the_outer_limits.tmdb_id == "21567"
    assert the_outer_limits.tmdb_type == "tv"
    assert the_outer_limits.title == "The Outer Limits"


@freeze_time("2012-10-15 10:00:00.001007")
def test_movie_creation():
    """
    Basic creation of a Movie manifest using the sample payload.
    """
    the_pit = MovieManifest(
        Path("/movies/the-pit-and-the-pendulum.mp4"),
        **SAMPLE_MOVIE_PAYLOAD,
    )

    assert the_pit.tmdb_id == "273204"
    assert the_pit.tmdb_type == "movie"
    assert the_pit.title == "The Pit and the Pendulum"


@freeze_time("2012-10-15 10:00:00.001007")
def test_collection_creation():
    """
    Basic creation of a Collection manifest.
    """
    first_hope = MovieManifest(
        Path("/movies/the-first-hope.mp4"),
        **SAMPLE_MOVIE_PAYLOAD,
    )

    starwors = CollectionManifest(
        Path("/movies/starwors"),
        movies=[first_hope],
    )

    assert starwors.tmdb_id is None
    assert starwors.tmdb_type == "collection"
    assert starwors.title == "starwors"
    assert first_hope.parent == starwors
