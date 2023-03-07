import json
import uuid
import hashlib
from pathlib import Path

from freezegun import freeze_time

from deovi.collector import Collector
from deovi.utils.tests import (
    DUMMY_ISO_DATETIME, timestamp_to_isoformat, dummy_uuid4, dummy_blake2b
)


def test_collector_run_basic(monkeypatch, media_sample):
    """
    Scanning from basepath should return recursive data for directories with media
    files.
    """
    monkeypatch.setattr(Collector, "timestamp_to_isoformat", timestamp_to_isoformat)

    monkeypatch.setattr(uuid, "uuid4", dummy_uuid4)

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
            "cover": Path("dummy_uuid4.gif"),
        },
        "foo/bar": {
            "path": media_sample / "foo/bar",
            "name": "bar",
            "title": "Foo bar",
            "absolute_dir": media_sample / "foo",
            "relative_dir": Path("foo/bar"),
            "size": 4096,
            "mtime": DUMMY_ISO_DATETIME,
            "children_files": [
                "SampleVideo_360x240_1mb.mkv",
            ],
            "cover": None,
        },
        ".": {
            "path": media_sample,
            "title": "Media sample root",
            "name": "media_sample",
            "absolute_dir": media_sample.parent,
            "relative_dir": Path("."),
            "size": 4096,
            "mtime": DUMMY_ISO_DATETIME,
            "children_files": [
                "SampleVideo_1280x720_1mb.mkv",
            ],
            "cover": Path("dummy_uuid4.png"),
        },
    }
    collector = Collector(media_sample, extensions=["mkv"])

    stats = collector.run()

    # Alter registry to only retain the file names from children instead of their whole
    # payload, so the expected data to assert is lighter
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


@freeze_time("2012-10-15 10:00:00")
def test_collector_run_manifest(monkeypatch, media_sample):
    """
    Collector should correctly find directory manifest files, directory covers and
    add them to directory payload.

    We mock the hash modules to be able to retrieve created cover directory and cover
    files.
    """
    monkeypatch.setattr(Collector, "timestamp_to_isoformat", timestamp_to_isoformat)
    monkeypatch.setattr(uuid, "uuid4", dummy_uuid4)
    monkeypatch.setattr(hashlib, "blake2b", dummy_blake2b)

    collector = Collector(media_sample)

    dump_destination = media_sample / "dump.json"
    # Storage dir is created from mocked blake2b so we got the dump file along datetime
    directory_storage = media_sample / "dump_dump.json_2012-10-15T10:00:00"
    collector.run(dump_destination)
    dumped_registry = json.loads(dump_destination.read_text())

    assert dumped_registry["."]["title"] == "Media sample root"
    assert dumped_registry["foo/bar"]["title"] == "Foo bar"

    # Expected cover files
    assert list(directory_storage.iterdir()) == [
        directory_storage / "dummy_uuid4.png",
        directory_storage / "dummy_uuid4.jpg",
        directory_storage / "dummy_uuid4.gif",
    ]

    # Expected directories with a cover
    assert dumped_registry["."]["cover"] == str(
        directory_storage / "dummy_uuid4.png"
    )
    assert dumped_registry["moo"]["cover"] == str(
        directory_storage / "dummy_uuid4.png"
    )
    assert dumped_registry["ping/pong"]["cover"] == str(
        directory_storage / "dummy_uuid4.gif"
    )
    assert dumped_registry["ping/pong/pang"]["cover"] == str(
        directory_storage / "dummy_uuid4.jpg"
    )

    # Expected directories without a cover
    assert any([
        data["cover"]
        for path, data in dumped_registry.items()
        if path not in (".", "moo", "ping/pong", "ping/pong/pang")
    ]) is False


def test_collector_run_checksum(monkeypatch, media_sample):
    """
    When checksum is enabled, the collector should generate a directory checksum and
    a field file checksum also if there is some
    """
    collector = Collector(media_sample)

    dump_destination = media_sample / "dump.json"
    collector.run(dump_destination, checksum=True)
    dumped_registry = json.loads(dump_destination.read_text())

    # All entries should have a checksum
    for dirpath, dirdata in dumped_registry.items():
        assert ("checksum" in dirdata) is True
        # If directory has a cover file, its checksum should be there also
        if dirdata.get("cover"):
            assert dirdata.get("cover_checksum") is not None
