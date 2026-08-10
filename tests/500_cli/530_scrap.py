import logging

import pytest
import yaml
from click.testing import CliRunner

from deovi import __pkgname__
from deovi.cli.entrypoint import cli_frontend

from tests.utils import (
    API_FILEKEY_FILENAME, SAMPLE_TV_ID, SAMPLE_TV_PAYLOAD, get_tmdbapi_key,
)


# Skip marker decorator for tests depending on a TMDb API key usage
api_allowed = pytest.mark.skipif(
    get_tmdbapi_key() is None,
    reason="No API key found from file '{}'".format(API_FILEKEY_FILENAME)
)


def test_scrap_required_args(caplog):
    """
    Command expected at least the 'tvid' argument, the 'destination' argument and
    either 'key' or 'filekey' option.
    """
    runner = CliRunner()

    result = runner.invoke(cli_frontend, ["scrap"])
    assert result.exit_code == 2
    assert caplog.record_tuples == []
    assert "Error: Missing argument 'TMDB_TYPE'" in result.output

    result = runner.invoke(cli_frontend, ["scrap", "tv"])
    assert result.exit_code == 2
    assert caplog.record_tuples == []
    assert "Error: Missing argument 'TMDB_ID'" in result.output

    result = runner.invoke(cli_frontend, ["scrap", "tv", "noid"])
    assert result.exit_code == 2
    assert caplog.record_tuples == []
    assert "Error: Missing argument 'DESTINATION'" in result.output

    result = runner.invoke(cli_frontend, ["scrap", "tv", "noid", "/foo/"])
    assert result.exit_code == 1
    assert caplog.record_tuples == [
        (
            __pkgname__,
            logging.CRITICAL,
            "A TMDb API key is required either from 'key' or 'filekey' option.",
        ),
    ]


@api_allowed
def test_scrap_basic_success(caplog, tmp_path, settings):
    """
    With all required arguments and options command should succeed to retrieve TV Serie
    details and cover in the right language.

    NOTE: This involves 2 requests to API
    """
    manifest_path = tmp_path / "manifest.yaml"
    poster_path = tmp_path / "cover.jpg"

    runner = CliRunner()

    result = runner.invoke(cli_frontend, [
        "scrap",
        "tv",
        SAMPLE_TV_ID,
        str(tmp_path),
        "--key", settings.tmdbapi_key(),
        "--language", "en",
        "--write-diff",
    ])

    assert manifest_path.exists() is True
    assert poster_path.exists() is True

    assert result.exit_code == 0
    assert caplog.record_tuples == [
        (
            __pkgname__,
            logging.INFO,
            "TMDB Type: tv",
        ),
        (
            __pkgname__,
            logging.INFO,
            "TMDB ID: {}".format(SAMPLE_TV_ID),
        ),
        (
            __pkgname__,
            logging.INFO,
            "Manifest: {}".format(tmp_path / "manifest.yaml")
        ),
        (
            __pkgname__,
            logging.INFO,
            "Cover: {}".format(str(poster_path))
        ),
        (
            __pkgname__,
            logging.INFO,
            "Title: {}".format(SAMPLE_TV_PAYLOAD["title"])
        ),
    ]


@api_allowed
def test_scrap_diff_success(caplog, tmp_path, settings):
    """
    Success with a diff against a previous existing manifest.

    NOTE: This involves 2 requests to API
    """
    manifest_path = tmp_path / "manifest.yaml"
    diff_path = tmp_path / "manifest.diff.txt"

    # Write existing manifest file with dummy details to trigger differences
    manifest_path.write_text(
        yaml.dump({"foo": "bar"}, Dumper=yaml.Dumper)
    )

    runner = CliRunner()

    result = runner.invoke(cli_frontend, [
        "scrap",
        "tv",
        SAMPLE_TV_ID,
        str(tmp_path),
        "--key", settings.tmdbapi_key(),
        "--language", "en",
        "--write-diff",
    ])

    assert result.exit_code == 0
    assert diff_path.exists() is True


@api_allowed
def test_scrap_basic_dry(caplog, tmp_path, settings):
    """
    With dry mode enabled everything is runned but nothing should be written.

    NOTE: This involves 2 requests to API
    """
    runner = CliRunner()

    poster_path = tmp_path / "cover.jpg"

    result = runner.invoke(cli_frontend, [
        "scrap",
        "tv",
        SAMPLE_TV_ID,
        str(tmp_path),
        "--key", settings.tmdbapi_key(),
        "--language", "en",
        "--write-diff",
        "--dry",
    ])
    assert result.exit_code == 0

    assert list(tmp_path.iterdir()) == []

    assert caplog.record_tuples == [
        (
            __pkgname__,
            logging.INFO,
            "TMDB Type: tv",
        ),
        (
            __pkgname__,
            logging.INFO,
            "TMDB ID: {}".format(SAMPLE_TV_ID),
        ),
        (
            __pkgname__,
            logging.INFO,
            "Manifest: {}".format(tmp_path / "manifest.yaml")
        ),
        (
            __pkgname__,
            logging.INFO,
            "Cover: {}".format(str(poster_path))
        ),
        (
            __pkgname__,
            logging.INFO,
            "Title: {}".format(SAMPLE_TV_PAYLOAD["title"])
        ),
    ]
