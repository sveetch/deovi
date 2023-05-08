import hashlib
import json
import uuid
from pathlib import Path

import pytest

from freezegun import freeze_time

from deovi.utils.checksum import ChecksumOperator
from deovi.utils.jsons import ExtendedJsonEncoder
from deovi.utils.tests import (
    dummy_uuid4, dummy_blake2b, dummy_checksumoperator_filepath,
)



def test_checksum_file(media_sample):
    """
    File checksum should be a string of exactly 128 characters.
    """
    checksum_op = ChecksumOperator()

    checksum = checksum_op.file(media_sample / "cover.png")
    assert isinstance(checksum, str) is True
    assert len(checksum) == 128

    checksum = checksum_op.file(media_sample / "SampleVideo_1280x720_1mb.mkv")
    assert isinstance(checksum, str) is True
    assert len(checksum) == 128


@freeze_time("2012-10-15 10:00:00")
def test_checksum_file_mocked(monkeypatch, media_sample):
    """
    Mockup should still returns a string but with file name + datetime.
    """
    monkeypatch.setattr(ChecksumOperator, "file", dummy_checksumoperator_filepath)
    checksum_op = ChecksumOperator()

    checksum = checksum_op.file(media_sample / "cover.png")
    assert isinstance(checksum, str) is True
    assert checksum == "cover.png_2012-10-15T10:00:00"

    checksum = checksum_op.file(media_sample / "SampleVideo_1280x720_1mb.mkv")
    assert isinstance(checksum, str) is True
    assert checksum == "SampleVideo_1280x720_1mb.mkv_2012-10-15T10:00:00"


def test_checksum_filepath(media_sample):
    """
    Patch checksum should be a string of exactly 20 characters.
    """
    checksum_op = ChecksumOperator()

    checksum = checksum_op.filepath(media_sample / "cover.png")
    assert isinstance(checksum, str) is True
    assert len(checksum) == 20

    checksum = checksum_op.filepath(media_sample / "SampleVideo_1280x720_1mb.mkv")
    assert isinstance(checksum, str) is True
    assert len(checksum) == 20


@freeze_time("2012-10-15 10:00:00")
def test_checksum_filepath_mocked(monkeypatch, media_sample):
    """
    Mockup should still returns a string but with file name + datetime.
    """
    monkeypatch.setattr(ChecksumOperator, "filepath", dummy_checksumoperator_filepath)
    checksum_op = ChecksumOperator()

    checksum = checksum_op.filepath(media_sample / "cover.png")
    assert isinstance(checksum, str) is True
    assert checksum == "cover.png_2012-10-15T10:00:00"

    checksum = checksum_op.filepath(media_sample / "SampleVideo_1280x720_1mb.mkv")
    assert isinstance(checksum, str) is True
    assert checksum == "SampleVideo_1280x720_1mb.mkv_2012-10-15T10:00:00"


def test_checksum_payload_files_no_file(media_sample):
    """
    When there is not file item defined, payload is left unchanged.
    """
    checksum_op = ChecksumOperator()

    payload_source = {
        "title": "Foo bar",
        "cover": [
            media_sample / "cover.png",
            Path("foo.jpg"),
        ],
        "thumb": [
            Path("source.jpg"),
            Path("destination.jpg"),
        ],
    }

    # Nothing has been changed since there is no defined file item
    result = checksum_op.payload_files(payload_source.copy())
    assert json.dumps(
        payload_source,
        indent=4,
        sort_keys=True,
        cls=ExtendedJsonEncoder
    ) == result


def test_checksum_payload_files_notfound(media_sample):
    """
    When a file item contain a path which can not be found, payload will be patch
    to include ``***_checksum`` field but empty since file can not be found to perform
    checksum.
    """
    checksum_op = ChecksumOperator()

    payload_source = {
        "title": "Foo bar",
        "cover": [
            media_sample / "cover.png",
            Path("foo.jpg"),
        ],
        "thumb": [
            Path("source.jpg"),
            Path("destination.jpg"),
        ],
    }

    # "thumb_checksum" item have been added since thumb is defined as a file item but
    # it is None and no checksum have been done since given path can not be found
    result = checksum_op.payload_files(
        payload_source.copy(),
        files_fields=["thumb", "nope"],
        storage=None
    )
    expected = payload_source.copy()
    expected["thumb_checksum"] = None
    assert json.dumps(
        expected,
        indent=4,
        sort_keys=True,
        cls=ExtendedJsonEncoder
    ) == result


def test_checksum_payload_files_checksumed(media_sample):
    """
    Payload with proper file item should be patched to add file checksum
    """
    checksum_op = ChecksumOperator()

    result = checksum_op.payload_files(
        {
            "title": "Foo bar",
            "cover": [
                media_sample / "cover.png",
                Path("foo.jpg"),
            ],
            "thumb": [
                Path("source.jpg"),
                Path("destination.jpg"),
            ],
        },
        files_fields=["cover"],
        storage=None
    )
    patched = json.loads(result)
    # Take checksum item apart
    cover_checksum = patched.pop("cover_checksum")
    assert patched == {
        "title": "Foo bar",
        "cover": [
            str(media_sample / "cover.png"),
            "foo.jpg",
        ],
        "thumb": ["source.jpg", "destination.jpg"],
    }
    assert isinstance(cover_checksum, str) is True
    assert len(cover_checksum) == 128


def test_checksum_payload_files_storage(media_sample):
    """
    Given storage is enough to find file with relative path so checksum can be
    performed
    """
    checksum_op = ChecksumOperator()

    result = checksum_op.payload_files(
        {
            "title": "Foo bar",
            "cover": [
                "cover.png",
                Path("foo.jpg"),
            ],
        },
        files_fields=["cover"],
        storage=media_sample,
    )
    patched = json.loads(result)
    cover_checksum = patched.pop("cover_checksum")

    # Path in payload is left unchanged
    assert patched["cover"] == ["cover.png", "foo.jpg"]

    # However given storage is enough to find file and checksum it correctly
    assert isinstance(cover_checksum, str) is True
    assert len(cover_checksum) == 128


def test_checksum_directory_payload(media_sample):
    """
    Given JSON payload should be checksumed to a string of exactly 128 characters.
    """
    checksum_op = ChecksumOperator()

    result = checksum_op.directory_payload(
        {
            "title": "Foo bar",
            "cover": [
                "cover.png",
                Path("foo.jpg"),
            ],
        },
        files_fields=["cover"],
        storage=media_sample,
    )

    assert isinstance(result, str) is True
    assert len(result) == 128
