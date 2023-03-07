import json
import hashlib
from pathlib import Path

from deovi.utils.checksum import directory_payload_checksum
from deovi.utils.tests import dummy_blake2b


def test_directory_checksum_content(monkeypatch, media_sample):
    """
    Directory informations should be correctly checksumed, also file field are
    checksumed apart and inserted in payload.
    """
    monkeypatch.setattr(hashlib, "blake2b", dummy_blake2b)

    checksum = directory_payload_checksum({
        "title": "Foo téléphônàç bar",
        "relative_dir": Path("foo/bar"),
        "size": 4096,
        "children_files": [
            "SampleVideo_360x240_1mb.mkv",
        ],
        # We use a plain text file so it's more reliable to check against.
        # Also payload must have a tuple for field file, but checksum only care about
        # the source one, so second item is dummy
        "cover": (Path("moo/boo/foo.txt"), "Dummy"),
    }, files_fields=["cover"], storage=media_sample)

    assert json.loads(checksum) == {
        "title": "Foo téléphônàç bar",
        "relative_dir": "foo/bar",
        "size": 4096,
        "children_files": [
            "SampleVideo_360x240_1mb.mkv"
        ],
        "cover": [
            "moo/boo/foo.txt",
            "Dummy"
        ],
        "cover_checksum": "dummy foo.txt\n",
    }
