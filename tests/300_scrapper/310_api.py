"""
These tests involve requests to TMDb API (and so request an API key).

All tests use sample payload downloaded from TMDB.

.. NOTE::
    TMDb API has a soft limit around 50 requests per second, so since test are pretty
    fast, we expect all runned tests will perform less than 50 requests to API.

    Remember than TmdbScrapper initialization itself involves a request to API, since
    client validate API key and retrieve base API configuration.
"""
import copy
from pathlib import Path

import pytest

import yaml

from tests.utils import (
    API_FILEKEY_FILENAME,
    SAMPLE_TV_ID,
    SAMPLE_TV_PAYLOAD,
    SAMPLE_MOVIE_ID,
    SAMPLE_MOVIE_PAYLOAD,
    get_tmdbapi_key,
)

from deovi.scrapper import TmdbScrapper


# Skip marker decorator for tests depending on a TMDb API key usage
api_allowed = pytest.mark.skipif(
    get_tmdbapi_key() is None,
    reason="No API key found from file '{}'".format(API_FILEKEY_FILENAME)
)


@api_allowed
def test_scrapper_init(settings):
    """
    Initialized scrapper should succeed without error

    NOTE: This involves 1 request to API
    """
    scrapper = TmdbScrapper(settings.tmdbapi_key())

    # Quickly check base url is a proper URL
    assert scrapper.secure_base_url.startswith("https://")
    assert scrapper.secure_base_url.endswith("/")


@api_allowed
def test_scrapper_serialize_tv_payload(settings):
    """
    TV details from API should return expected payload.

    NOTE: This involves 2 requests to API
    """
    scrapper = TmdbScrapper(settings.tmdbapi_key(), language="en")

    payload = scrapper.serialize_tv_payload(SAMPLE_TV_ID)

    # Check poster apart since its filename may change
    poster_path = payload.pop("poster_path")
    assert poster_path.startswith("/")
    assert poster_path.endswith(".jpg")

    # Assert almost full payload
    assert payload == SAMPLE_TV_PAYLOAD


@api_allowed
def test_scrapper_serialize_movie_payload(settings):
    """
    TV details from API should return expected payload.

    NOTE: This involves 2 requests to API
    """
    scrapper = TmdbScrapper(settings.tmdbapi_key(), language="en")

    payload = scrapper.serialize_movie_payload(SAMPLE_MOVIE_ID)

    # Check poster apart since its filename may change
    poster_path = payload.pop("poster_path")
    assert poster_path.startswith("/")
    assert poster_path.endswith(".jpg")

    # Assert almost full payload
    assert payload == SAMPLE_MOVIE_PAYLOAD


@api_allowed
def test_scrapper_fetch_tv(tmp_path, settings):
    """
    From given TV ID the scrapper should retrieve its detail and poster file from API
    payload.

    NOTE: This involves 2 requests to API
    """
    scrapper = TmdbScrapper(settings.tmdbapi_key(), language="en")
    scrapper.fetch_media(tmp_path, SAMPLE_TV_ID, tmdb_type="tv")

    manifest_path = tmp_path / "manifest.yaml"
    assert (tmp_path / "cover.jpg").exists() is True
    assert manifest_path.exists() is True

    manifest = yaml.load(manifest_path.read_text(), Loader=yaml.FullLoader)

    # Patch sample payload to add expected manifest variables
    expected = copy.deepcopy(SAMPLE_TV_PAYLOAD)
    expected["path"] = str(manifest_path)
    expected["locked"] = False
    expected["cover"] = "cover.jpg"

    assert manifest == expected


@api_allowed
def test_scrapper_fetch_movie(tmp_path, settings):
    """
    From given TV ID the scrapper should retrieve its detail and poster file from API
    payload.

    NOTE: This involves 2 requests to API
    """
    scrapper = TmdbScrapper(settings.tmdbapi_key(), language="en")

    # With default filename
    scrapper.fetch_media(tmp_path, SAMPLE_MOVIE_ID, tmdb_type="movie")
    manifest_path = tmp_path / "manifest.yaml"
    # On default a movie cover adopts the filename of the manifest
    assert (tmp_path / "manifest.jpg").exists() is True
    assert manifest_path.exists() is True

    # Patch sample payload to add expected manifest variables
    manifest = yaml.load(manifest_path.read_text(), Loader=yaml.FullLoader)
    expected = copy.deepcopy(SAMPLE_MOVIE_PAYLOAD)
    expected["path"] = str(manifest_path)
    expected["locked"] = False
    expected["cover"] = "manifest.jpg"

    assert manifest == expected

    # With default filename
    scrapper.fetch_media(
        tmp_path,
        SAMPLE_MOVIE_ID,
        tmdb_type="movie",
        filename=Path("foo/custom.mkv")
    )
    manifest_path = tmp_path / "custom.yaml"
    # with custom filename, the cover filename adopt it
    assert (tmp_path / "custom.jpg").exists() is True
    assert manifest_path.exists() is True
