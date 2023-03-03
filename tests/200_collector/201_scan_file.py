from pathlib import Path

import pytest

from deovi.collector import Collector
from deovi.utils.tests import DUMMY_ISO_DATETIME, timestamp_to_isoformat


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

    assert expected == data
