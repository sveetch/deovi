from pathlib import Path

import pytest
import yaml

from deovi.scrapper import TmdbScrapper


@pytest.mark.parametrize(
    ("manifest_from, manifest_to, expected_diffs, write_diff, has_diff_file"),
    [
        (
            {
                "foo": "bar",
                "ping": "pong",
                "length": 1,
                "items": ["one", "two"],
            },
            {
                "foo": "bar",
                "ping": "pong",
                "items": ["one", "two"],
                "length": 1,
            },
            [],
            True,
            False,
        ),
        (
            {
                "foo": "bar",
            },
            {
                "foo": "bar",
                "ping": "pong",
            },
            ["Item root['ping'] added to dictionary."],
            False,
            False,
        ),
        (
            {
                "foo": "bar",
                "ping": "pong",
                "length": 1,
                "items": ["one", "two"],
            },
            {
                "foo": "bar",
                "bim": "bam",
                "length": "long",
                "items": ["one", "three", "four"],
            },
            [
                "Item root['bim'] added to dictionary.",
                "Item root['ping'] removed from dictionary.",
                "Item root['items'][2] added to iterable.",
                (
                    "Type of root['length'] changed from int to str and value changed "
                    "from 1 to \"long\"."
                ),
                "Value of root['items'][1] changed from \"two\" to \"three\"."
            ],
            True,
            True,
        ),
    ]
)
def test_scrapper_fetch_tv_diffs(monkeypatch, tmp_path, settings, manifest_from,
                                 manifest_to, expected_diffs, write_diff,
                                 has_diff_file):
    """
    When TV serie destination already have a manifest, fetcher should diff it with new
    payload and store differences if there is any and if 'write_diff' option is enabled.

    NOTE: Here we patch a lot of methods to neutralize any request to API since we
    don't test for its accuracy here.
    """
    manifest_path = tmp_path / "manifest.yaml"
    manifest_diff_path = tmp_path / "manifest.diff.txt"

    # Write existing manifest file to tmp dir
    manifest_path.write_text(
        yaml.dump(manifest_from, Dumper=yaml.Dumper)
    )

    def dummy_client(cls, *args, **kwargs):
        # No client object needed
        return None

    def dummy_configurations(cls):
        # Dummy media URL
        cls.secure_base_url = "nope://niet/"

    def dummy_poster(cls, *args, **kwargs):
        # Dummy poster path
        return Path("/nope/niet/dummy.jpg")

    def dummy_payload(cls, *args, **kwargs):
        # Return a dummy payload
        return manifest_to

    monkeypatch.setattr(TmdbScrapper, "get_client", dummy_client)
    monkeypatch.setattr(TmdbScrapper, "get_api_configurations", dummy_configurations)
    monkeypatch.setattr(TmdbScrapper, "fetch_poster", dummy_poster)
    monkeypatch.setattr(TmdbScrapper, "serialize_tv_payload", dummy_payload)

    # Run the scrapper with dummy key and id
    scrapper = TmdbScrapper("nokey", language="en")
    data, manifest, fetched_poster, diff = scrapper.fetch_tv(
        tmp_path, "noid", write_diff=write_diff
    )

    assert data == manifest_to
    assert fetched_poster is None
    assert str(manifest) == str(manifest_path)
    assert diff == expected_diffs
    assert manifest_diff_path.exists() is has_diff_file
