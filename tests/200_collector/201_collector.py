import json
import uuid
import hashlib
from pathlib import Path

import pytest

from deovi.collector import MANIFEST_FILENAME, MANIFEST_FORBIDDEN_VARS, Collector
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

    assert expected == data


def test_collector_get_directory_manifest_nofile(manifests_sample):
    """
    Collector should silently fail if there is no manifest.
    """
    collector = Collector(None)
    manifest = collector.get_directory_manifest(manifests_sample)

    assert manifest == {}


def test_collector_get_directory_manifest_invalid(caplog, warning_logger, manifests_sample):
    """
    Collector should not break process if found manifest file is invalid and emits
    a warning log.
    """
    collector = Collector(None)
    sample_dir = manifests_sample / "invalid"
    manifest_path = sample_dir / MANIFEST_FILENAME
    manifest = collector.get_directory_manifest(sample_dir)

    assert manifest == {}

    assert caplog.record_tuples == [
        (
            "deovi",
            30,
            "No YAML object could be decoded for manifest: {}".format(manifest_path)
        ),
    ]


def test_collector_get_directory_manifest_forbidden(caplog, warning_logger,
                                                    manifests_sample):
    """
    Collector should not break process if manifest contains forbidden keywords but it
    results to a warning and ignored manifest.
    """
    collector = Collector(None)
    sample_dir = manifests_sample / "forbidden"
    manifest_path = sample_dir / MANIFEST_FILENAME
    manifest = collector.get_directory_manifest(sample_dir)

    assert manifest == {}

    msg = "Ignored manifest because it has forbidden keywords '{}': {}"
    assert caplog.record_tuples == [
        (
            "deovi",
            30,
            msg.format(", ".join(MANIFEST_FORBIDDEN_VARS), manifest_path)
        ),
    ]


def test_collector_get_directory_manifest_basic(manifests_sample):
    """
    Collector should find manifest if any and correctly load it.
    """
    collector = Collector(None)
    manifest = collector.get_directory_manifest(manifests_sample / "basic")

    assert manifest == {
        "foo": "bar",
        "ping": {
            "pong": True,
            "pang": 4
        },
        "nope": None,
        "plop": [
            True,
            False,
            True,
            False,
            "plip"
        ],
        "pika": [
            "chu",
            {
                "pika": "map"
            }
        ]
    }


@pytest.mark.parametrize("basepath, storage, expected_found", [
    ("", "", "cover.png"),
    ("ping/pong/pang", "", "cover.jpg"),
    ("foo/bar", "", None),
    ("", "thumbs", "cover.png"),
    ("ping/pong/pang", "thumbs", "cover.jpg"),
    ("foo/bar", "thumbs", None),
])
def test_collector_get_directory_cover(media_sample, basepath, storage, expected_found):
    """
    Collector should find elligible cover image file from a directory.

    Every basepath are searched in media_sample dir from fixtures.
    """
    collector = Collector(None)
    collector.file_storage_directory = storage
    dir_path = media_sample / basepath
    cover = collector.get_directory_cover(dir_path)

    # None is expected when no cover has been found
    if expected_found is None:
        assert cover is None
    # For expected found cover tuple
    else:
        cover_source, cover_destination = cover
        assert cover_source == (dir_path / expected_found)
        # We got the uuid of expected length as destination file name
        assert len(cover_destination.stem) == 36
        # Destination adopted the source file extension
        assert cover_destination.suffix == Path(expected_found).suffix
        # Destination is prefixed with possible storage directory
        assert cover_destination.parents[0] == Path(storage)


@pytest.mark.parametrize("filepath, parent, basename", [
    ("dump.json", Path("."), "dump"),
    ("foo/dump.json", Path("foo"), "dump"),
    ("/home/foo/dump.bar.json", Path("/home/foo"), "dump"),
])
def test_collector_get_directory_storage(filepath, parent, basename):
    """
    A directory should be computed from given filename plus a hashid with an exact
    length.
    """
    collector = Collector(None)
    dirname = collector.get_directory_storage(Path(filepath))

    name, hashid = str(dirname).split("_")

    assert dirname.parent == parent
    assert Path(name).stem == basename
    assert len(hashid) == 20


@pytest.mark.parametrize("fields, payload, expected_queue, expected_payload", [
    (
        ["cover"],
        {
            "foo": "foo",
            "cover": None,
        },
        [],
        {
            "foo": "foo",
            "cover": None,
        },
    ),
    (
        ["cover"],
        {
            "foo": "foo",
            "cover": (Path("source.jpg"), Path("destination.jpg")),
        },
        [(Path("source.jpg"), Path("destination.jpg"))],
        {
            "foo": "foo",
            "cover": Path("destination.jpg"),
        },
    ),
    (
        ["cover", "detail"],
        {
            "foo": "foo",
            "cover": (Path("source.jpg"), Path("destination.jpg")),
        },
        [(Path("source.jpg"), Path("destination.jpg"))],
        {
            "foo": "foo",
            "cover": Path("destination.jpg"),
        },
    ),
    (
        ["cover", "detail"],
        {
            "foo": "foo",
            "cover": (Path("source.jpg"), Path("destination.jpg")),
            "detail": (Path("from.jpg"), Path("to.jpg")),
        },
        [
            (Path("source.jpg"), Path("destination.jpg")),
            (Path("from.jpg"), Path("to.jpg")),
        ],
        {
            "foo": "foo",
            "cover": Path("destination.jpg"),
            "detail": Path("to.jpg"),
        },
    ),
])
def test_collector_process_file_fields(fields, payload, expected_queue,
                                       expected_payload):
    """
    Method should push file field values to a queue list and alter payload to let only
    the source path as the field value.
    """
    collector = Collector(None)

    data = collector._process_file_fields(fields, payload)

    assert collector.file_storage_queue == expected_queue
    assert data == expected_payload


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


@pytest.mark.parametrize("files, expected_stored", [
    (
        [
            (Path("cover.png"), Path("dst_cover.png")),
            (Path("ping/pong/pang/cover.jpg"), Path("dst_cover.jpg")),
        ],
        [
            Path("dst_cover.png"),
            Path("dst_cover.jpg"),
        ],
    ),
])
def test_store_files(media_sample, files, expected_stored):
    """
    Files from queue list should be stored in storage directory (created if not
    exists).
    """
    collector = Collector(None)
    collector.file_storage_directory = media_sample / Path("thumbs")

    # Augment each source with sample path and destination with tmp destination dir
    stored = collector.store_files([
        ((media_sample / k), (collector.file_storage_directory / v))
        for k, v in files
    ])

    assert stored == [
        collector.file_storage_directory / item
        for item in expected_stored
    ]

    assert list(collector.file_storage_directory.iterdir()) == [
        collector.file_storage_directory / item
        for item in expected_stored
    ]


def test_collector_scan_directory_full(monkeypatch, media_sample):
    """
    Scanning from basepath should return recursive data for directories with media
    files.
    """
    monkeypatch.setattr(Collector, "timestamp_to_isoformat", timestamp_to_isoformat)

    def dummy_uuid4():
        return "dummy_uuid4"

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


def test_collector_run_dirmanifest(monkeypatch, media_sample):
    """
    Collector should correctly find directory manifest files, directory covers and
    add them to directory payload.

    We mock the hash modules to be able to retrieve created cover directory and cover
    files.
    """
    def dummy_uuid4():
        return "dummy_uuid4"

    class dummy_blake2b():
        def __init__(self, *args, **kwargs):
            pass

        def hexdigest(self, *args, **kwargs):
            return "dummy_blake2b"

    monkeypatch.setattr(Collector, "timestamp_to_isoformat", timestamp_to_isoformat)
    monkeypatch.setattr(uuid, "uuid4", dummy_uuid4)
    monkeypatch.setattr(hashlib, "blake2b", dummy_blake2b)

    collector = Collector(media_sample)

    dump_destination = media_sample / "dump.json"
    directory_storage = media_sample / "dump_dummy_blake2b"
    stats = collector.run(dump_destination)
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
