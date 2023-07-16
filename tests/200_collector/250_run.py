import json
import uuid
from pathlib import Path

from freezegun import freeze_time

from deovi.collector import Collector
from deovi.utils.checksum import ChecksumOperator
from deovi.utils.tests import (
    DUMMY_ISO_DATETIME, timestamp_to_isoformat, dummy_uuid4,
    dummy_checksumoperator_filepath,
)


@freeze_time("2012-10-15 10:00:00")
def test_collector_run_basic(monkeypatch, media_sample):
    """
    Scanning from basepath should return recursive data for directories with media
    files.
    """
    monkeypatch.setattr(Collector, "timestamp_to_isoformat", timestamp_to_isoformat)

    monkeypatch.setattr(uuid, "uuid4", dummy_uuid4)

    expect_asset_storagedir = Path("attachment_20121015T100000")

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
            "cover": expect_asset_storagedir / Path("dummy_uuid4.gif"),
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
            "cover": expect_asset_storagedir / Path("dummy_uuid4.png"),
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
        "asset_storage": None,
    }


@freeze_time("2012-10-15 10:00:00")
def test_collector_run_manifest(monkeypatch, media_sample):
    """
    Collector should correctly find directory manifest files, directory covers and
    add them to directory payload.

    We mock the hash modules to be able to retrieve created cover directory and cover
    files since we enable checksum mechanism but don't want the variadic values.
    """
    monkeypatch.setattr(Collector, "timestamp_to_isoformat", timestamp_to_isoformat)
    monkeypatch.setattr(uuid, "uuid4", dummy_uuid4)
    # Use the right precise mockups for the right content behaviors
    monkeypatch.setattr(ChecksumOperator, "file", dummy_checksumoperator_filepath)
    monkeypatch.setattr(ChecksumOperator, "filepath", dummy_checksumoperator_filepath)

    collector = Collector(media_sample)

    # Storage dir is created from mocked blake2b so we already know the storage dirname
    dump_destination = media_sample / "dump.json"
    assets_storage = Path("dump_dump.json_2012-10-15T10:00:00")
    absolute_assets_storage = media_sample / assets_storage

    # Run collect and load dump
    collector.run(dump_destination, checksum=True)
    dumped_registry = json.loads(dump_destination.read_text())

    # Expected item titles
    assert dumped_registry["."]["title"] == "Media sample root"
    assert dumped_registry["foo/bar"]["title"] == "Foo bar"

    # Expected item cover files
    assert list(absolute_assets_storage.iterdir()) == [
        absolute_assets_storage / "dummy_uuid4.png",
        absolute_assets_storage / "dummy_uuid4.jpg",
        absolute_assets_storage / "dummy_uuid4.gif",
    ]

    # Expected item directories with a cover
    assert dumped_registry["."]["cover"] == str(
        assets_storage / "dummy_uuid4.png"
    )
    assert dumped_registry["moo"]["cover"] == str(
        assets_storage / "dummy_uuid4.png"
    )
    assert dumped_registry["ping/pong"]["cover"] == str(
        assets_storage / "dummy_uuid4.gif"
    )
    assert dumped_registry["ping/pong/pang"]["cover"] == str(
        assets_storage / "dummy_uuid4.jpg"
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
    a field file checksum. Also, the directories checksum should be identical for two
    run on the same unchanged content.
    """
    monkeypatch.setattr(Collector, "timestamp_to_isoformat", timestamp_to_isoformat)

    dump_destination = media_sample / "dump.json"

    # First run
    collector = Collector(media_sample)
    collector.run(dump_destination, checksum=True)
    dumped_registry = json.loads(dump_destination.read_text())

    # All entries should have a checksum
    for dirpath, dirdata in dumped_registry.items():
        assert ("checksum" in dirdata) is True
        # If directory has a cover file, its checksum should be there also
        if dirdata.get("cover"):
            assert dirdata.get("cover_checksum") is not None

    # Store some dir checksum for later compare
    first_root_checksum = dumped_registry["."]["checksum"]
    first_moo_checksum = dumped_registry["moo"]["checksum"]
    first_ping_pong_checksum = dumped_registry["ping/pong"]["checksum"]
    first_foo_bar_checksum = dumped_registry["foo/bar"]["checksum"]

    # Run collect a second time
    collector = Collector(media_sample)
    collector.run(dump_destination, checksum=True)
    dumped_registry = json.loads(dump_destination.read_text())

    # Store some dir checksum for later compare
    second_root_checksum = dumped_registry["."]["checksum"]
    second_moo_checksum = dumped_registry["moo"]["checksum"]
    second_ping_pong_checksum = dumped_registry["ping/pong"]["checksum"]
    second_foo_bar_checksum = dumped_registry["foo/bar"]["checksum"]

    # Checksum should be identical since nothing has changed in processed directories
    assert first_root_checksum == second_root_checksum
    assert second_moo_checksum == first_moo_checksum
    assert second_ping_pong_checksum == first_ping_pong_checksum
    assert second_foo_bar_checksum == first_foo_bar_checksum
