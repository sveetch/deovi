"""
These tests involve requests to TMDb API (and so request an API key).

All tests use a TV id for the old serie 'The Outer Limits', hoping it won't never
change its informations which would break tests.

.. NOTE::
    TMDb API has a soft limit around 50 requests per second, so since test are pretty
    fast, we assume all these test runned will perform less than 50 requests to API.

    Remember than TmdbScrapper initialization itself involves a request to API, since
    client validate API key and retrieve base API configuration.
"""
import pytest

import yaml

from tests.utils import (
    API_FILEKEY_FILENAME, SAMPLE_TV_ID, SAMPLE_TV_PAYLOAD, get_tmdbapi_key,
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

    print(scrapper.secure_base_url)

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

    payload = scrapper.serialize_tv_payload(scrapper.get_provider(), SAMPLE_TV_ID)

    # Check poster apart since its filename may change
    poster_path = payload.pop("poster_path")
    assert poster_path.startswith("/")
    assert poster_path.endswith(".jpg")

    # Assert almost full payload
    assert payload == SAMPLE_TV_PAYLOAD


@api_allowed
def test_scrapper_fetch_tv(tmp_path, settings):
    """
    From given TV ID the scrapper should retrieve its detail and poster file from API
    payload.

    NOTE: This involves 2 requests to API
    """
    scrapper = TmdbScrapper(settings.tmdbapi_key(), language="en")
    scrapper.fetch_tv(tmp_path, SAMPLE_TV_ID)

    manifest_path = tmp_path / "manifest.yaml"
    assert (tmp_path / "cover.jpg").exists()
    assert manifest_path.exists()

    manifest = yaml.load(manifest_path.read_text(), Loader=yaml.FullLoader)

    assert manifest == SAMPLE_TV_PAYLOAD
