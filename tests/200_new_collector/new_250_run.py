import json
import uuid
from pathlib import Path

from freezegun import freeze_time

from deovi.collector.new_collect import NewCollector
from deovi.utils.checksum import ChecksumOperator
from deovi.utils.tests import (
    DUMMY_ISO_DATETIME, timestamp_to_isoformat, dummy_uuid4,
    dummy_checksumoperator_filepath,
)
from deovi.models import (
    DirectoryInformation,
    MediaInformation,
)


def test_collector_run_basic(monkeypatch, media_sample):
    """
    Scanning from basepath should return recursive data for directories with media
    files.
    """
    monkeypatch.setattr(NewCollector, "timestamp_to_isoformat", timestamp_to_isoformat)
    monkeypatch.setattr(uuid, "uuid4", dummy_uuid4)

    collector = NewCollector(media_sample, extensions=["mkv"], autoload_manifests=True)
    stats = collector.run()

    payload = {
        key: json.loads(dictinfos.as_json())
        for key, dictinfos in collector.registry.items()
    }
    # print(json.dumps(payload, indent=4))

    assert list(collector.registry.keys()) == [
        "foo/bar",
        "ping/pong",
        ".",
    ]

    root = collector.registry["."]
    assert isinstance(root, DirectoryInformation)
    assert len(root.medias) == 1
    assert root.manifest is not None

    bar = collector.registry["foo/bar"]
    assert isinstance(bar, DirectoryInformation)
    assert len(bar.medias) == 1
    assert bar.manifest is None

    pong = collector.registry["ping/pong"]
    assert isinstance(pong, DirectoryInformation)
    assert len(pong.medias) == 2
    assert pong.manifest is not None

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
    """
    monkeypatch.setattr(NewCollector, "timestamp_to_isoformat", timestamp_to_isoformat)
    monkeypatch.setattr(uuid, "uuid4", dummy_uuid4)

    collector = NewCollector(media_sample, autoload_manifests=True)

    # Storage dir is created from mocked blake2b so we already know the storage dirname
    dump_destination = media_sample / "dump.json"
    storage_dirname = Path("dump_20121015T100000")
    storage_absolutedir = media_sample / storage_dirname

    # Collecting
    collector.run(dump_destination, checksum=False)

    # Load data from created dump
    payload = json.loads(dump_destination.read_text())
    dumped_registry = payload["registry"]

    # Those dirs have no manifest (and so no cover, etc..)
    assert payload["registry"]["moo"]["manifest"] is None
    assert payload["registry"]["foo/bar"]["manifest"] is None
    assert payload["registry"]["ping/pong/pang"]["manifest"] is None

    # Dirs with manifest
    root = payload["registry"]["."]
    pong = payload["registry"]["ping/pong"]
    assert root["manifest"] is not None
    assert root["manifest"]["title"] == "Media sample root YAML"
    assert pong["manifest"] is not None
    assert pong["manifest"]["title"] == "Pong JSON"

    # Expected cover files in storage directory on filesystem
    assert sorted(list(storage_absolutedir.iterdir())) == [
        storage_absolutedir / "dummy_uuid4.gif",
        storage_absolutedir / "dummy_uuid4.png",
    ]

    # Expected item directories with a cover from manifest
    assert root["manifest"]["cover"] == {
        "checksum": None,
        "source": str(media_sample / "cover.png"),
        "destination": "dummy_uuid4.png",
    }
    assert pong["manifest"]["cover"] == {
        "checksum": None,
        "source": str(media_sample / "ping/pong/cover.gif"),
        "destination": "dummy_uuid4.gif",
    }


def test_collector_run_checksum(monkeypatch, media_sample):
    """
    When checksum is enabled, the collector should generate a directory checksum and
    a field file checksum. Also, the directories checksum should be identical for two
    run on the same unchanged content.

    TODO: We moved the checksum computation to models, lets stabilize them in their own
    test before continuing here.
    """
    monkeypatch.setattr(NewCollector, "timestamp_to_isoformat", timestamp_to_isoformat)
    ## Use the right precise mockups for the right content behaviors
    ## Useless ?
    #monkeypatch.setattr(ChecksumOperator, "file", dummy_checksumoperator_filepath)
    #monkeypatch.setattr(ChecksumOperator, "filepath", dummy_checksumoperator_filepath)

    dump_destination = media_sample / "dump.json"

    # First run
    collector = NewCollector(media_sample)
    collector.run(dump_destination, checksum=True)
    payload = json.loads(dump_destination.read_text())
    dumped_registry = payload["registry"]

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
    collector = NewCollector(media_sample)
    collector.run(dump_destination, checksum=True)
    payload = json.loads(dump_destination.read_text())
    dumped_registry = payload["registry"]

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
