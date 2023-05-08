from pathlib import Path

import pytest

from deovi.collector import Collector
from deovi.exceptions import CollectorError
from deovi.utils.tests import DUMMY_ISO_DATETIME, timestamp_to_isoformat


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


def test_collector_scan_directory_single(monkeypatch, media_sample):
    """
    Scanning a single directory should return the right directory data and media files.
    """
    monkeypatch.setattr(Collector, "timestamp_to_isoformat", timestamp_to_isoformat)

    expected = {
        "foo/bar": {
            "path": media_sample / "foo/bar",
            "name": "bar",
            "title": "Foo bar",
            "absolute_dir": media_sample / "foo",
            "relative_dir": Path("foo/bar"),
            "size": 4096,
            "mtime": DUMMY_ISO_DATETIME,
            "children_files": [
                "SampleVideo_360x240_1mb.mkv"
            ],
            "cover": None,
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

    assert expected == collector.registry
    assert collector.stats == {
        "directories": 1,
        "files": 1,
        "size": 1059817,
    }
