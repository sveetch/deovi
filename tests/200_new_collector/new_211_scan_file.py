import uuid
from pathlib import Path

import pytest

from deovi.collector.new_collect import NewCollector
from deovi.models import MediaInformation, MovieManifest
from deovi.utils.tests import DUMMY_ISO_DATETIME, timestamp_to_isoformat, dummy_uuid4


@pytest.mark.parametrize("path, expected", [
    (
        "SampleVideo_1280x720_1mb.mkv",
        {
            "path": "SampleVideo_1280x720_1mb.mkv",
            "name": "SampleVideo_1280x720_1mb.mkv",
            "absolute_dir": "",
            "relative_dir": ".",
            "name_alt": "",
            "extension": "mkv",
            "container": "Matroska",
            "size": 1052413,
            "mtime": DUMMY_ISO_DATETIME,
            "manifest":  None,
            "checksum":  None,
        },
    ),
    (
        "moo/SampleVideo_720x480_1mb.mp4",
        {
            "path": "moo/SampleVideo_720x480_1mb.mp4",
            "name": "SampleVideo_720x480_1mb.mp4",
            "absolute_dir": "moo",
            "relative_dir": "moo",
            "name_alt": "moo",
            "extension": "mp4",
            "container": "MPEG-4",
            "size": 1057149,
            "mtime": DUMMY_ISO_DATETIME,
            "manifest":  None,
            "checksum":  None,
        },
    ),
    (
        "ping/pong/pang/SampleVideo_176x144_1mb.3gp",
        {
            "path": "ping/pong/pang/SampleVideo_176x144_1mb.3gp",
            "name": "SampleVideo_176x144_1mb.3gp",
            "absolute_dir": "ping/pong/pang",
            "relative_dir": "ping/pong/pang",
            "name_alt": "pang",
            "extension": "3gp",
            "container": "3GPP",
            "size": 1038741,
            "mtime": DUMMY_ISO_DATETIME,
            "manifest":  None,
            "checksum":  None,
        },
    ),
])
def test_collector_scan_file(monkeypatch, media_sample, path, expected):
    """
    Scanning a file should return the right media file datas.

    No manifest is involved here.
    """
    monkeypatch.setattr(NewCollector, "timestamp_to_isoformat", timestamp_to_isoformat)

    # Rewrite path strings to Path objects
    path = media_sample / path
    expected["path"] = media_sample / expected["path"]
    expected["absolute_dir"] = media_sample / expected["absolute_dir"]
    expected["relative_dir"] = Path(expected["relative_dir"])

    collector = NewCollector(media_sample)

    data = collector.scan_file(path)

    assert expected == data.as_dict()


def test_collector_scan_file_manifest(monkeypatch, media_sample):
    """
    Scanning a file with manifest autoload enabled should return the right media file
    datas with its manifest data also.
    """
    monkeypatch.setattr(NewCollector, "timestamp_to_isoformat", timestamp_to_isoformat)
    monkeypatch.setattr(uuid, "uuid4", dummy_uuid4)

    path = media_sample / "ping/pong/SampleVideo_720x480_1mb.mkv"

    collector = NewCollector(media_sample, autoload_manifests=True)

    data = collector.scan_file(path)

    assert isinstance(data, MediaInformation)
    assert isinstance(data.manifest, MovieManifest)

    # import json
    # print(data.as_json())
    assert data.as_dict(preserve=True) == {
        "path": path,
        "size": 1050238,
        "mtime": "1977-06-02T07:35:15",
        "name": "SampleVideo_720x480_1mb.mkv",
        "absolute_dir": media_sample / "ping/pong",
        "relative_dir": Path("ping/pong"),
        "manifest": {
            "path": media_sample / "ping/pong/SampleVideo_720x480_1mb.json",
            "tmdb_id": None,
            "tmdb_type": "movie",
            "locked": False,
            "title": "Sample 720x480 1mb JSON",
            "overview": None,
            "status": None,
            "original_language": None,
            "cover": {
                "checksum": None,
                "destination": Path("dummy_uuid4.jpg"),
                "source": media_sample / "ping/pong/SampleVideo_720x480_1mb.jpg",
            },
            "casting": [],
            "crew": [],
            "genres": [],
            "release_date": ""
        },
        "checksum":  None,
        "name_alt": "pong",
        "extension": "mkv",
        "container": "Matroska"
    }
