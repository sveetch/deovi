import json

import yaml

from deovi.scrapper import TmdbScrapper


def test_for_serie(media_sample, disable_api):
    """
    Scrapper should correctly write manifest for a TV show no matter it already exists
    or not.
    """
    new_serie = media_sample / "new_serie"
    new_serie.mkdir()
    new_serie_manifest = new_serie / "manifest.json"

    # Write an original manifest
    new_serie_manifest.write_text(
        json.dumps({
            "path": str(new_serie_manifest),
            "tmdb_id": 42,
            "tmdb_type": "serie",
            "title": "Old plop",
        })
    )

    # Process ID
    scrapper = TmdbScrapper("nokey", manifest_format="json")
    manifest, diff = scrapper.fetch_from_id(new_serie, 42, tmdb_type="tv")

    # Check result of processed manifest as returned from method
    assert manifest.as_coerced() == {
        "path": new_serie / "manifest.json",
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
    }
    assert diff == [
        (
            "Type of root['cover'] changed from NoneType to str and value changed from "
            'None to "dummy_serie-cover.png".'
        ),
        'Value of root[\'title\'] changed from "manifest.json" to "changed-serie".',
    ]

    written_new_manifest = json.loads(new_serie_manifest.read_text())
    assert written_new_manifest["title"] == "changed-serie"
    assert written_new_manifest["cover"] == "dummy_serie-cover.png"

    # Again with diff
    scrapper = TmdbScrapper("nokey", manifest_format="json")
    manifest, diff = scrapper.fetch_from_id(
        new_serie,
        42,
        tmdb_type="tv",
        write_diff=True
    )

    assert diff == [
        (
            "Type of root['cover'] changed from NoneType to str and value changed from "
            'None to "dummy_serie-cover.png".'
        ),
        'Value of root[\'title\'] changed from "manifest.json" to '
        '"changed-serie".',
    ]


def test_for_movie_default(media_sample, disable_api):
    """
    Scrapper should correctly write manifest for a Movie using a default filename.
    """
    new_movie = media_sample / "new_movie"
    new_movie_manifest = new_movie / "manifest.json"

    # Process ID
    scrapper = TmdbScrapper("nokey", manifest_format="json")
    manifest, diff = scrapper.fetch_from_id(new_movie, 42, tmdb_type="movie")

    # Check result of processed manifest as returned from method
    assert diff == []
    assert manifest.as_coerced() == {
        "path": new_movie / "manifest.json",
        "tmdb_id": 42,
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
    }

    written_new_manifest = json.loads(new_movie_manifest.read_text())
    assert written_new_manifest["title"] == "changed-movie"
    assert written_new_manifest["cover"] == "dummy_movie-cover.png"


def test_for_movie_filename(media_sample, disable_api):
    """
    Scrapper should correctly write manifest for a Movie with a custom filename.
    """
    new_movie = media_sample / "new_movie"
    new_movie_manifest = new_movie / "SampleVideo_720x480_1mb.json"

    # Process ID
    scrapper = TmdbScrapper("nokey", manifest_format="json")
    manifest, diff = scrapper.fetch_from_id(
        new_movie,
        42,
        tmdb_type="movie",
        filename=(new_movie / "SampleVideo_720x480_1mb.mkv"),
    )

    # Check result of processed manifest as returned from method
    assert diff == []
    assert manifest.as_coerced() == {
        "path": new_movie / "SampleVideo_720x480_1mb.json",
        "tmdb_id": 42,
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
    }

    written_new_manifest = json.loads(new_movie_manifest.read_text())
    assert written_new_manifest["title"] == "changed-movie"
    assert written_new_manifest["cover"] == "dummy_movie-cover.png"


def test_yaml(media_sample, disable_api):
    """
    Scrapper should support for output with YAML format on demand.
    """
    new_movie = media_sample / "new_movie"
    new_movie_manifest = new_movie / "SampleVideo_720x480_1mb.yaml"

    # Process ID
    scrapper = TmdbScrapper("nokey", manifest_format="yaml")
    manifest, diff = scrapper.fetch_from_id(
        new_movie,
        42,
        tmdb_type="movie",
        filename=(new_movie / "SampleVideo_720x480_1mb.mkv"),
    )

    # Check result of processed manifest as returned from method
    assert manifest.as_coerced() == {
        "path": new_movie / "SampleVideo_720x480_1mb.yaml",
        "tmdb_id": 42,
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
    }

    written_new_manifest = yaml.load(
        new_movie_manifest.read_text(),
        Loader=yaml.FullLoader
    )
    assert written_new_manifest["title"] == "changed-movie"
    assert written_new_manifest["cover"] == "dummy_movie-cover.png"
