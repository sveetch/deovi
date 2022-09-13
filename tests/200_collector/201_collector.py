from pathlib import Path

import pytest

from deovi.collector import Collector
from deovi.exceptions import CollectorError
from deovi.utils.tests import DUMMY_ISO_DATETIME, timestamp_to_isoformat


@pytest.mark.parametrize("timestamp, expected", [
    (
        1642296817.279053,
        "2022-01-16T01:33:37+00:00",
    ),
    (
        1642296817.3030524,
        "2022-01-16T01:33:37+00:00",
    ),
    (
        1541793812.3030524,
        "2018-11-09T20:03:32+00:00",
    ),
])
def test_collector_timestamp_to_isoformat(timestamp, expected):
    """
    Given timestamp should be correctly formatted to datetime in ISO format.
    """
    collector = Collector(None)

    assert collector.timestamp_to_isoformat(timestamp) == expected


@pytest.mark.parametrize("path, expected", [
    (
        "SampleVideo_1280x720_1mb.mkv",
        {
            "path": "SampleVideo_1280x720_1mb.mkv",
            "name": "SampleVideo_1280x720_1mb.mkv",
            "absolute_dir": "",
            "relative_dir": ".",
            "directory": "",
            "extension": "mkv",
            "container": "Matroska",
            "size": 1052413,
            "mtime": DUMMY_ISO_DATETIME,
        },
    ),
    (
        "moo/SampleVideo_720x480_1mb.mp4",
        {
            "path": "moo/SampleVideo_720x480_1mb.mp4",
            "name": "SampleVideo_720x480_1mb.mp4",
            "absolute_dir": "moo",
            "relative_dir": "moo",
            "directory": "moo",
            "extension": "mp4",
            "container": "MPEG-4",
            "size": 1057149,
            "mtime": DUMMY_ISO_DATETIME,
        },
    ),
    (
        "ping/pong/pang/SampleVideo_176x144_1mb.3gp",
        {
            "path": "ping/pong/pang/SampleVideo_176x144_1mb.3gp",
            "name": "SampleVideo_176x144_1mb.3gp",
            "absolute_dir": "ping/pong/pang",
            "relative_dir": "ping/pong/pang",
            "directory": "pang",
            "extension": "3gp",
            "container": "3GPP",
            "size": 1038741,
            "mtime": DUMMY_ISO_DATETIME,
        },
    ),
])
def test_collector_scan_file(monkeypatch, media_sample, path, expected):
    """
    Scanning a file should return the right media file datas.
    """
    monkeypatch.setattr(Collector, "timestamp_to_isoformat", timestamp_to_isoformat)

    # Rewrite path strings to Path objects
    path = media_sample / path
    expected["path"] = media_sample / expected["path"]
    expected["absolute_dir"] = media_sample / expected["absolute_dir"]
    expected["relative_dir"] = Path(expected["relative_dir"])

    collector = Collector(media_sample)

    data = collector.scan_file(path)

    # print()
    # print(data)
    # print()
    # print(json.dumps(data, indent=4, cls=ExtendedJsonEncoder))
    # print()

    assert expected == data


def test_collector_scan_directory_outofbasepath(media_sample):
    """
    Trying to scan a directory which is out of give basepath should raise an error.
    """
    collector = Collector((media_sample / "foo/bar"))

    with pytest.raises(CollectorError):
        collector.scan_directory(media_sample)


@pytest.mark.parametrize("allowed, expected", [
    (
        False,
        {"directories": 3, "files": 3, "size": 4233015},
    ),
    (
        True,
        {"directories": 8, "files": 3, "size": 4253495},
    ),
])
def test_collector_scan_directory_allowempty(media_sample, allowed, expected):
    """
    Option "allow_empty_dir" may change the number of collected directories (if
    targeted structure does have directories without any direct media files).
    """
    collector = Collector(
        media_sample,
        allow_empty_dir=allowed,
        extensions=["mp4"],
    )

    collector.scan_directory(media_sample)

    assert collector.stats == expected


def test_collector_scan_directory_full(monkeypatch, media_sample):
    """
    Scanning from basepath should return recursive data for directories with media
    files.
    """
    monkeypatch.setattr(Collector, "timestamp_to_isoformat", timestamp_to_isoformat)

    expected = {
        "ping/pong": {
            "path": media_sample / "ping/pong",
            "name": "pong",
            "absolute_dir": media_sample / "ping",
            "relative_dir": Path("ping/pong"),
            "size": 4096,
            "mtime": DUMMY_ISO_DATETIME,
            "children_files": [
                "SampleVideo_720x480_1mb.mkv",
                "SampleVideo_720x480_2mb.mkv",
            ],
        },
        "foo/bar": {
            "path": media_sample / "foo/bar",
            "name": "bar",
            "absolute_dir": media_sample / "foo",
            "relative_dir": Path("foo/bar"),
            "size": 4096,
            "mtime": DUMMY_ISO_DATETIME,
            "children_files": [
                "SampleVideo_360x240_1mb.mkv",
            ],
        },
        ".": {
            "path": media_sample,
            "name": "media_sample",
            "absolute_dir": media_sample.parent,
            "relative_dir": Path("."),
            "size": 4096,
            "mtime": DUMMY_ISO_DATETIME,
            "children_files": [
                "SampleVideo_1280x720_1mb.mkv",
            ],
        },
    }
    collector = Collector(media_sample, extensions=["mkv"])

    stats = collector.run()

    # Alter registry to only retain the file names in children, so the expected data to
    # assert is lighter
    for k, v in collector.registry.items():
        if "children_files" in v:
            collector.registry[k]["children_files"] = [
                item["name"]
                for item in collector.registry[k]["children_files"]
            ]

    # print(json.dumps(expected, indent=4, cls=ExtendedJsonEncoder))
    # print("--- AGAINST ---")
    # print(json.dumps(collector.registry, indent=4, cls=ExtendedJsonEncoder))

    assert expected == collector.registry
    assert stats == {
        "directories": 3,
        "files": 4,
        "size": 5277604,
    }


def test_collector_scan_directory_single(monkeypatch, media_sample):
    """
    Scanning a single directory should return the right directory data and media files.
    """
    monkeypatch.setattr(Collector, "timestamp_to_isoformat", timestamp_to_isoformat)

    expected = {
        "foo/bar": {
            "path": media_sample / "foo/bar",
            "name": "bar",
            "absolute_dir": media_sample / "foo",
            "relative_dir": Path("foo/bar"),
            "size": 4096,
            "mtime": DUMMY_ISO_DATETIME,
            "children_files": [
                "SampleVideo_360x240_1mb.mkv"
            ]
        },
    }
    collector = Collector(media_sample, extensions=["mkv"])

    collector.scan_directory((media_sample / "foo/bar"))

    # Alter registry to only retain the file names in children, so the expected data to
    # assert is lighter
    for k, v in collector.registry.items():
        if "children_files" in v:
            collector.registry[k]["children_files"] = [
                item["name"]
                for item in collector.registry[k]["children_files"]
            ]

    # print(json.dumps(expected, indent=4, cls=ExtendedJsonEncoder))
    # print("--- AGAINST ---")
    # print(json.dumps(collector.registry, indent=4, cls=ExtendedJsonEncoder))

    assert expected == collector.registry
    assert collector.stats == {
        "directories": 1,
        "files": 1,
        "size": 1059817,
    }
