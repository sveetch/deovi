import uuid
import hashlib
from pathlib import Path

import pytest

from freezegun import freeze_time

from deovi.collector import AssetStorage
from deovi.utils.tests import dummy_uuid4, dummy_blake2b


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
def test_storage_base_paths(monkeypatch, basepath, expected_basepath,
                            expected_attachment):
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
def test_storage_set_basepath(monkeypatch):
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
def test_storage_set_basepath_blake2b():
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


@freeze_time("2012-10-15 10:00:00")
def test_storage_get_directory_asset(monkeypatch, media_sample):
    """
    Asset should be found from given path when it matches allowed asset filenames.
    """
    monkeypatch.setattr(uuid, "uuid4", dummy_uuid4)
    monkeypatch.setattr(hashlib, "blake2b", dummy_blake2b)

    basepath = media_sample / "dump.json"

    # Predicted name since we use freeze_time and no checksum
    storage_assets = Path("dump_20121015T100000")

    # No allowed filename can be found from given path
    storage = AssetStorage(basepath)
    assert storage.get_directory_asset(
        media_sample,
        ["cover.jpg"],
    ) is None

    # An allowed filename have been found from given path
    storage = AssetStorage(basepath)
    assert storage.get_directory_asset(
        media_sample,
        ["cover.jpg", "cover.png"],
    ) == (
        media_sample / "cover.png",
        storage_assets / "dummy_uuid4.png",
    )


def test_storage_store_assets(monkeypatch, media_sample):
    """
    Storage should correctly store asset files
    """
    monkeypatch.setattr(uuid, "uuid4", dummy_uuid4)

    basepath = media_sample / "dump.json"

    storage = AssetStorage(
        basepath,
        allowed_cover_filenames=["cover.jpg", "cover.png"],
    )

    # Get full path to the assets directory
    assets_destination = media_sample / storage.storage_assets

    # At this point the assets directory does not exists yet
    assert assets_destination.exists() is False

    # Get some proper asset items from sample structure
    assets = [
        storage.get_directory_cover(media_sample),
        storage.get_directory_cover(media_sample / "ping/pong/pang"),
    ]

    # Stored file are named with an uuid (but here it's a fake one from mockup)
    assert storage.store_assets(assets) == [
        assets_destination / "dummy_uuid4.png",
        assets_destination / "dummy_uuid4.jpg",
    ]

    # Ensure stored files have correctly written in the right dir
    assert list(assets_destination.iterdir()) == [
        assets_destination / "dummy_uuid4.png",
        assets_destination / "dummy_uuid4.jpg",
    ]
