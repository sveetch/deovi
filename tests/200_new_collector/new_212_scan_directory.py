import json
import uuid
from pathlib import Path

import pytest

from deovi.collector.new_collect import NewCollector
from deovi.exceptions import CollectorError
from deovi.utils.tests import DUMMY_ISO_DATETIME, timestamp_to_isoformat, dummy_uuid4
from deovi.models import (
    DirectoryInformation,
    MediaInformation,
)


def test_outofbasepath(media_sample):
    """
    Trying to scan a directory which is out of basepath should raise an error.
    """
    collector = NewCollector((media_sample / "foo/bar"))

    with pytest.raises(CollectorError):
        collector.scan_directory(media_sample)


@pytest.mark.parametrize("empty, expected", [
    (
        False,
        {"directories": 3, "files": 3, "size": 4233015, "asset_storage": None},
    ),
    (
        True,
        {"directories": 8, "files": 3, "size": 4253495, "asset_storage": None},
    ),
])
def test_allow_empty_dir(media_sample, empty, expected):
    """
    Option "allow_empty_dir" may change the number of collected directories (if
    targeted structure does have directories without any direct media files).
    """
    collector = NewCollector(
        media_sample,
        allow_empty_dir=empty,
        extensions=["mp4"],
    )

    collector.scan_directory(media_sample)

    assert collector.stats == expected


def test_empty(tmp_path):
    """
    Directory without any file is not discovered.
    """
    serie_path = tmp_path / "the_outer_limits"
    serie_path.mkdir()

    # Create a dummy manifest
    manifest_path = Path(serie_path) / "manifest.json"
    manifest_path.write_text(
        json.dumps({"title": "The Outer Limits", "tmdb_type": "tv"})
    )

    collector = NewCollector(tmp_path, extensions=["mkv"])
    collector.scan_directory(serie_path)
    assert len(collector.registry) == 0
    assert list(collector.registry.keys()) == []


def test_no_autoload(monkeypatch, tmp_path):
    """
    Without manifest autoload no manifest should be discovered.
    """
    monkeypatch.setattr(NewCollector, "timestamp_to_isoformat", timestamp_to_isoformat)
    monkeypatch.setattr(uuid, "uuid4", dummy_uuid4)

    serie_path = tmp_path / "the_outer_limits"
    serie_path.mkdir()

    # Create a dummy cover
    cover = serie_path / "cover.jpg"
    cover.write_text("dummy cover.jpg")

    # Create a dummy mediafile
    media_path = serie_path / "dummy.mkv"
    media_path.write_text("dummy media_path")

    # Create a dummy manifest
    manifest_path = serie_path / "manifest.json"
    manifest_path.write_text(
        json.dumps({"title": "The Outer Limits", "tmdb_type": "tv"})
    )

    # Collect and check expected result
    collector = NewCollector(tmp_path, extensions=["mkv"], autoload_manifests=False)
    collector.scan_directory(serie_path)
    assert len(collector.registry) == 1
    assert list(collector.registry.keys()) == ["the_outer_limits"]
    assert isinstance(collector.registry["the_outer_limits"], DirectoryInformation)
    assert json.loads(collector.registry["the_outer_limits"].as_json()) == {
        "path": str(serie_path),
        "size": 4096,
        "mtime": "1977-06-02T07:35:15",
        "name": "the_outer_limits",
        "absolute_dir": str(tmp_path),
        "relative_dir": "the_outer_limits",
        "manifest": None,
        "checksum": None,
        "medias": [
            {
                "path": str(serie_path / "dummy.mkv"),
                "size": 16,
                "mtime": "1977-06-02T07:35:15",
                "name": "dummy.mkv",
                "absolute_dir": str(serie_path),
                "relative_dir": "the_outer_limits",
                "manifest": None,
                "checksum": None,
                "name_alt": "the_outer_limits",
                "extension": "mkv",
                "container": "Matroska"
            }
        ]
    }


def test_with_cover_and_mediafile(monkeypatch, media_sample):
    """
    Collector should collect required directory, its media files, manifest, cover and
    an empty child directory.
    """
    monkeypatch.setattr(NewCollector, "timestamp_to_isoformat", timestamp_to_isoformat)
    monkeypatch.setattr(uuid, "uuid4", dummy_uuid4)

    # Collect directory
    collector = NewCollector(media_sample, extensions=["mkv"], autoload_manifests=True)
    collector.scan_directory((media_sample / "ping/pong"))
    assert len(collector.registry) == 1
    assert list(collector.registry.keys()) == ["ping/pong"]
    assert isinstance(collector.registry["ping/pong"], DirectoryInformation)
    assert json.loads(collector.registry["ping/pong"].as_json()) == {
        "path": str(media_sample / "ping/pong"),
        "size": 4096,
        "mtime": "1977-06-02T07:35:15",
        "name": "pong",
        "absolute_dir": str(media_sample / "ping"),
        "relative_dir": "ping/pong",
        "manifest": {
            "path": str(media_sample / "ping/pong/manifest.json"),
            "tmdb_id": None,
            "tmdb_type": "tv",
            "locked": False,
            "title": "Pong JSON",
            "overview": None,
            "status": None,
            "original_language": None,
            "cover": {
                "checksum": None,
                "source": str(media_sample / "ping/pong/cover.gif"),
                "destination": "dummy_uuid4.gif"
            },
            "casting": [],
            "crew": [],
            "genres": [],
            "first_air_date": "",
            "number_of_seasons": None,
            "number_of_episodes": None
        },
        "checksum": None,
        "medias": [
            {
                "path": str(media_sample / "ping/pong/SampleVideo_720x480_1mb.mkv"),
                "size": 1050238,
                "mtime": "1977-06-02T07:35:15",
                "name": "SampleVideo_720x480_1mb.mkv",
                "absolute_dir": str(media_sample / "ping/pong"),
                "relative_dir": "ping/pong",
                "manifest": {
                    "path": str(
                        media_sample / "ping/pong/SampleVideo_720x480_1mb.json"
                    ),
                    "tmdb_id": None,
                    "tmdb_type": "movie",
                    "locked": False,
                    "title": "Sample 720x480 1mb JSON",
                    "overview": None,
                    "status": None,
                    "original_language": None,
                    "cover": {
                        "checksum": None,
                        "source": str(media_sample / "ping/pong/SampleVideo_720x480_1mb.jpg"),
                        "destination": "dummy_uuid4.jpg"
                    },
                    "casting": [],
                    "crew": [],
                    "genres": [],
                    "release_date": ""
                },
                "checksum": None,
                "name_alt": "pong",
                "extension": "mkv",
                "container": "Matroska"
            },
            {
                "path": str(media_sample / "ping/pong/SampleVideo_720x480_2mb.mkv"),
                "size": 2106944,
                "mtime": "1977-06-02T07:35:15",
                "name": "SampleVideo_720x480_2mb.mkv",
                "absolute_dir": str(media_sample / "ping/pong"),
                "relative_dir": "ping/pong",
                "manifest": None,
                "checksum": None,
                "name_alt": "pong",
                "extension": "mkv",
                "container": "Matroska"
            }
        ]
    }

    assert collector.stats == {
        "directories": 1,
        "files": 2,
        "size": 3161278,
        "asset_storage": None,
    }
