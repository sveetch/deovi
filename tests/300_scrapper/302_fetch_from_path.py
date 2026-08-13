import json

import yaml

from deovi.scrapper import TmdbScrapper


def test_basic(media_sample, disable_api):
    """
    Scrapper will retrieve all valid manifest and proceed to update them with
    fetched data payload. Also the original manifest format is respected.

    No request is done here and cover file is not written on FS.
    """
    # We only expect valid manifests from 'ping/pong'
    pong = media_sample / "ping/pong"
    pong_manifest = pong / "manifest.json"
    samplevideo_manifest = pong / "SampleVideo_720x480_1mb.json"

    # Patch original pong manifests to add an attribute
    patched_pong = json.loads(pong_manifest.read_text())
    patched_pong["status"] = "zap"
    pong_manifest.write_text(json.dumps(patched_pong))

    # Patch bar YAML manifest to make it valid
    bar = media_sample / "foo/bar"
    bar_manifest = bar / "manifest.yaml"
    bar_manifest.write_text((
        "title: \"Foo bar YAML\"\n"
        "tmdb_id: 001\n"
        "tmdb_type: \"tv\"\n"
    ))

    # Process manifests
    scrapper = TmdbScrapper("nokey")
    processed = list(scrapper.fetch_from_path(media_sample))

    # Check result of processed manifest as returned from method
    assert [v[0].as_coerced() for v in processed] == [
        {
            "path": pong / "SampleVideo_720x480_1mb.json",
            "tmdb_id": 273204,
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
        {
            "path": pong / "manifest.json",
            "tmdb_id": 21567,
            "tmdb_type": "tv",
            "locked": False,
            "title": "changed-serie",
            "overview": None,
            "status": "zap",
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
            "path": bar / "manifest.yaml",
            "tmdb_id": 1,
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
    ]

    # Written manifest files have been well updated
    written_samplevideo_manifest = json.loads(samplevideo_manifest.read_text())
    assert written_samplevideo_manifest["title"] == "changed-movie"
    assert written_samplevideo_manifest["cover"] == "dummy_movie-cover.png"
    assert written_samplevideo_manifest["status"] is None

    written_pong_manifest = json.loads(pong_manifest.read_text())
    assert written_pong_manifest["title"] == "changed-serie"
    assert written_pong_manifest["cover"] == "dummy_serie-cover.png"
    assert written_pong_manifest["status"] == "zap"

    written_bar_manifest = yaml.load(bar_manifest.read_text(), Loader=yaml.FullLoader)
    assert written_bar_manifest["title"] == "changed-serie"
    assert written_bar_manifest["cover"] == "dummy_serie-cover.png"
    assert written_bar_manifest["status"] is None


def test_with_diff(media_sample, disable_api):
    """
    Differences between original and new data are properly returned.

    No request is done here and cover file is not written on FS.
    """
    # We only expect valid manifests from 'ping/pong'
    pong = media_sample / "ping/pong"

    # Remove useless manifest
    (pong / "SampleVideo_720x480_1mb.json").unlink()

    # Process manifests
    scrapper = TmdbScrapper("nokey")
    processed = list(scrapper.fetch_from_path(pong, write_diff=True))

    # Check result of processed manifest as returned from method
    assert [v[0].as_coerced() for v in processed] == [
        {
            "path": pong / "manifest.json",
            "tmdb_id": 21567,
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
    ]

    assert [v[1] for v in processed] == [
        [
            (
                "Type of root['cover'] changed from NoneType to str and value "
                "changed from None to \"dummy_serie-cover.png\"."
            ),
            "Value of root['title'] changed from \"Pong JSON\" to \"changed-serie\"."
        ],
    ]
