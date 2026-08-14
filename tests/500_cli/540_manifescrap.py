import copy
import json
import logging

import pytest
from click.testing import CliRunner

from deovi import __pkgname__
from deovi.cli.entrypoint import cli_frontend
from deovi.models import MovieManifest, SerieManifest

from tests.utils import (
    API_FILEKEY_FILENAME,
    SAMPLE_TV_ID,
    SAMPLE_TV_PAYLOAD,
    SAMPLE_MOVIE_ID,
    SAMPLE_MOVIE_PAYLOAD,
    get_tmdbapi_key,
)


# Skip marker decorator for tests depending on a TMDb API key usage
api_allowed = pytest.mark.skipif(
    get_tmdbapi_key() is None,
    reason="No API key found from file '{}'".format(API_FILEKEY_FILENAME)
)


def test_required_args(caplog):
    """
    Command expected at least the 'basedir' argument.
    """
    runner = CliRunner()

    result = runner.invoke(cli_frontend, ["manifescrap"])
    assert result.exit_code == 2
    assert caplog.record_tuples == []
    assert "Error: Missing argument 'BASEDIR'" in result.output


@api_allowed
def test_basic_success(caplog, settings, tmp_path):
    """
    Manifescrap should scrap data and cover for all valid found manifests.

    NOTE: This involves 2 requests to API
    """
    caplog.set_level(logging.DEBUG, logger=__pkgname__)

    # Create some manifest files in temporary path
    the_serie_path = tmp_path / "manifest.json"
    the_serie = SerieManifest(
        the_serie_path,
        tmdb_id=SAMPLE_TV_ID,
        tmdb_type="tv"
    )
    the_serie_path.write_text(the_serie.as_json())

    the_movie_path = tmp_path / "the-movie.json"
    the_movie = MovieManifest(
        the_movie_path,
        tmdb_id=SAMPLE_MOVIE_ID,
        tmdb_type="movie",
    )
    the_movie_path.write_text(the_movie.as_json())

    # Run command on temporary path
    runner = CliRunner()
    result = runner.invoke(
        cli_frontend,
        [
            "-v", "5",
            "manifescrap",
            str(tmp_path),
            "--key", settings.tmdbapi_key(),
            "--language", "en",
        ],
    )

    assert result.exit_code == 0
    assert caplog.record_tuples == [
        (__pkgname__, logging.INFO, "basedir: {}".format(tmp_path)),
        (__pkgname__, logging.DEBUG, "Language: en"),
        (__pkgname__, logging.DEBUG, "Chunk size: 10"),
        (__pkgname__, logging.DEBUG, "Pause time: 1"),
        (__pkgname__, logging.DEBUG, "API Key from string"),
        (__pkgname__, logging.INFO, "Validating manifests"),
        (
            __pkgname__,
            logging.DEBUG,
            "Loading content from: {}/manifest.json".format(tmp_path)
        ),
        (
            __pkgname__,
            logging.DEBUG,
            "Loading content from: {}/the-movie.json".format(tmp_path)
        ),
        (
            __pkgname__,
            logging.INFO,
            "Successfuly scrapped: {}/manifest.json".format(tmp_path)
        ),
        (__pkgname__, logging.INFO, "├─ ID: 21567"),
        (__pkgname__, logging.INFO, "├─ Type: tv"),
        (__pkgname__, logging.INFO, "├─ Title: The Outer Limits"),
        (__pkgname__, logging.INFO, "┕━ Cover: cover.jpg"),
        (
            __pkgname__,
            logging.INFO,
            "Successfuly scrapped: {}/the-movie.json".format(tmp_path)
        ),
        (__pkgname__, logging.INFO, "├─ ID: 273204"),
        (__pkgname__, logging.INFO, "├─ Type: movie"),
        (__pkgname__, logging.INFO, "├─ Title: The Pit and the Pendulum"),
        (__pkgname__, logging.INFO, "┕━ Cover: the-movie.jpg"),
    ]

    assert the_serie_path.exists() is True
    assert the_movie_path.exists() is True

    # Load update manifest file just as simple Python object (not model)
    the_serie_updated = json.loads(the_serie_path.read_text())
    the_movie_updated = json.loads(the_movie_path.read_text())

    # Update payloads to include some (variable) fields not shared in samples
    the_serie_expected = copy.deepcopy(SAMPLE_TV_PAYLOAD)
    the_serie_expected["path"] = str(the_serie_path)
    the_serie_expected["locked"] = False
    the_serie_expected["cover"] = "cover.jpg"

    the_movie_expected = copy.deepcopy(SAMPLE_MOVIE_PAYLOAD)
    the_movie_expected["path"] = str(the_movie_path)
    the_movie_expected["locked"] = False
    the_movie_expected["cover"] = "the-movie.jpg"

    assert the_serie_updated == the_serie_expected
    assert the_movie_updated == the_movie_expected
