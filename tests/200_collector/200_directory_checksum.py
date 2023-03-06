import json
import hashlib
from pathlib import Path

from deovi.utils.checksum import directory_payload_checksum


class dummy_blake2b():
    """
    Instead of generating a hash, will just returns given content unchanged.

    Support basic string content, or 'update()' method and 'memoryview' so to be able
    to work with efficient memory/buffer way from 'checksum_file()'
    """
    def __init__(self, *args, **kwargs):
        self.content = args[0] if args else bytes()

    def update(self, content):
        if isinstance(content, memoryview):
            self.content += bytes(content)
        else:
            self.content += content

    def hexdigest(self, *args, **kwargs):
        return self.content.decode("utf-8")


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
        # We use plain text so it's more reliable to check against
        "cover": Path("moo/boo/foo.txt"),
    }, files_fields=["cover"], storage=media_sample)

    assert json.loads(checksum) == {
        "title": "Foo téléphônàç bar",
        "relative_dir": "foo/bar",
        "size": 4096,
        "children_files": [
            "SampleVideo_360x240_1mb.mkv"
        ],
        "cover": "moo/boo/foo.txt",
        "cover_checksum": "dummy foo.txt\n",
    }
