import json
import logging

from deovi import __pkgname__
from deovi.scrapper import TmdbScrapper
from deovi.models import CollectionManifest, MovieManifest, SerieManifest


def test_basic(caplog, disable_api, tmp_path):
    """
    Scrap from a list of crafted Manifest objects.
    """

    # Basic definition with payload and without cover
    the_serie_path = tmp_path / "manifest.json"
    the_serie = SerieManifest(
        the_serie_path,
        tmdb_id=42,
        tmdb_type="tv"
    )

    the_movie_path = tmp_path / "the-movie.json"
    the_movie = MovieManifest(
        the_movie_path,
        tmdb_id=33,
        tmdb_type="movie",
    )

    the_collection_path = tmp_path / "manifest.json"
    the_collection = CollectionManifest(
        the_collection_path,
        tmdb_id=77,
        tmdb_type="movie",
    )

    manifests = [the_serie, the_movie, the_collection]

    # Process manifests
    scrapper = TmdbScrapper("nokey")
    processed = scrapper.fetch_from_manifests(manifests)

    # Check result of processed manifest as returned from method
    assert [v[0].as_coerced() for v in processed] == [
        {
            "path": the_serie_path,
            "tmdb_id": 42,
            "tmdb_type": "tv",
            "locked": False,
            "title": "changed-serie",
            "overview": None,
            "status": None,
            "original_language": None,
            "cover": "dummy_serie-cover.png",
            "casting": [],
            "crew": [],
            "genres": [],
            "first_air_date": "",
            "number_of_seasons": None,
            "number_of_episodes": None
        },
        {
            "path": the_movie_path,
            "tmdb_id": 33,
            "tmdb_type": "movie",
            "locked": False,
            "title": "changed-movie",
            "overview": None,
            "status": None,
            "original_language": None,
            "cover": "dummy_movie-cover.png",
            "casting": [],
            "crew": [],
            "genres": [],
            "release_date": ""
        },
    ]

    # Written manifest files have been well updated
    written_serie_manifest = json.loads(the_serie_path.read_text())
    assert written_serie_manifest["title"] == "changed-serie"
    assert written_serie_manifest["cover"] == "dummy_serie-cover.png"
    assert written_serie_manifest["status"] is None

    written_movie_manifest = json.loads(the_movie_path.read_text())
    assert written_movie_manifest["title"] == "changed-movie"
    assert written_movie_manifest["cover"] == "dummy_movie-cover.png"
    assert written_movie_manifest["status"] is None

    # Since it is a single chunk, there is no pause
    assert caplog.record_tuples == [
        (
            __pkgname__,
            logging.WARNING,
            "Given tmdb_type 'collection' is not supported for processing: {}".format(
                the_collection_path
            )
        ),
    ]


def test_many_chunks_with_pause(caplog, disable_api, tmp_path):
    """
    When the amount of manifest to process is over the limit, manifests should be
    processed per chunk with a pause time between them.
    """
    caplog.set_level(logging.DEBUG)
    scrapper = TmdbScrapper("nokey")

    # Force execution of generator
    list(
        scrapper.fetch_from_manifests([
            MovieManifest(
                tmp_path / "the-movie-{}.json".format(i),
                tmdb_id=i,
                tmdb_type="movie",
            )
            for i in range(1, 22)
        ])
    )

    # There is a pause time between chunks but not after the last one
    assert caplog.record_tuples == [
        (__pkgname__, logging.INFO, "💬 Batch pausing for 1s"),
        (__pkgname__, logging.INFO, "💬 Batch pausing for 1s"),
    ]
