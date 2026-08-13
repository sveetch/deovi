import hashlib
from pathlib import Path

import pytest

from freezegun import freeze_time

from deovi.collector import AssetStorage
from deovi.models import Asset
from deovi.utils.tests import dummy_blake2b


@freeze_time("2012-10-15 10:00:00")
@pytest.mark.parametrize("basepath, expected_basepath, expected_attachment", [
    (
        None,
        "",
        # blake2b mockup just returns given string so this does not lookup like real
        # computed path outside of tests. It would have been something like:
        # 'attachment_f9566a49dd4c0f32995b'
        "attachment_attachment_2012-10-15T10:00:00",
    ),
    (
        Path(""),
        "",
        "attachment_attachment_2012-10-15T10:00:00",
    ),
    (
        Path("foo"),
        "",
        "foo_foo_2012-10-15T10:00:00",
    ),
    (
        Path("foo.json"),
        "",
        "foo_foo.json_2012-10-15T10:00:00",
    ),
    (
        Path("bar/foo.json"),
        "bar",
        "foo_foo.json_2012-10-15T10:00:00",
    ),
    (
        Path("/bar/foo.json"),
        "/bar",
        "foo_foo.json_2012-10-15T10:00:00",
    ),
])
def test_base_paths(monkeypatch, basepath, expected_basepath, expected_attachment):
    """
    Should compute correct storage basepath and attachment directory name from
    given basepath.
    """
    monkeypatch.setattr(hashlib, "blake2b", dummy_blake2b)

    storage = AssetStorage(basepath)
    storage.set_basepath(basepath, checksum=True)

    assert storage.storage_path == Path(expected_basepath)
    assert storage.storage_assets == Path(expected_attachment)


@freeze_time("2012-10-15 10:00:00")
def test_set_basepath(monkeypatch):
    """
    Method 'set_basepath' should set a new basepath, some related computed paths and
    checksum behavior.
    """
    monkeypatch.setattr(hashlib, "blake2b", dummy_blake2b)

    storage = AssetStorage()

    assert storage.storage_path == Path("")
    assert storage.storage_assets == Path("attachment_20121015T100000")

    storage.set_basepath(Path("foo/bar/"))
    assert storage.storage_path == Path("foo")
    assert storage.storage_assets == Path("bar_20121015T100000")

    storage.set_basepath(Path(""), checksum=True)
    assert storage.storage_path == Path("")
    assert storage.storage_assets == Path("attachment_attachment_2012-10-15T10:00:00")

    storage.set_basepath(Path("foo/bar/"), checksum=True)
    assert storage.storage_path == Path("foo")
    assert storage.storage_assets == Path("bar_bar_2012-10-15T10:00:00")


@freeze_time("2012-10-15 10:00:00")
def test_set_basepath_blake2b():
    """
    Basic test on set_basepath with "real" blake2b to check result format.
    """
    storage = AssetStorage(checksum=True)

    assert storage.storage_path == Path("")

    name, hashid = str(storage.storage_assets).split("_")
    assert name == "attachment"
    assert len(hashid) == 20

    # Change to a new path
    storage.set_basepath(Path("foo/bar.json"), checksum=True)
    name, hashid = str(storage.storage_assets).split("_")
    assert name == "bar"
    assert len(hashid) == 20


def test_store(media_sample):
    """
    Storage should correctly store asset files
    """
    basepath = media_sample / "dump.json"

    storage = AssetStorage(basepath)

    # Get full path to the assets directory
    assets_destination = media_sample / storage.storage_assets

    # At this point the assets directory does not exists yet
    assert assets_destination.exists() is False

    # Set some asset items from sample structure
    storage.queue = [
        Asset(
            source=(media_sample / "ping/pong/cover.gif"),
            destination="foo/cover.gif",
        ),
        Asset(
            source=(media_sample / "ping/pong/pang/cover.jpg"),
            destination="zip/zap/cover.jpg",
        ),
    ]

    assert storage.store() == (
        assets_destination,
        [
            assets_destination / "foo/cover.gif",
            assets_destination / "zip/zap/cover.jpg",
        ],
    )

    # Check tree content of 'assets_destination'
    tree = sorted(
        [
            str(f.relative_to(assets_destination))
            for f in assets_destination.rglob('*')
        ]
    )
    assert tree == [
        "foo",
        "foo/cover.gif",
        "zip",
        "zip/zap",
        "zip/zap/cover.jpg",
    ]
