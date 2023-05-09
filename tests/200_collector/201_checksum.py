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


def test_checksum_payload_files_no_file_item(media_sample):
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

    result = checksum_op.payload_files(payload_source.copy())

    assert payload_source == result


def test_checksum_payload_files_notfound(media_sample):
    """
    When a file item contain a path which can not be found, payload is patched
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

    result = checksum_op.payload_files(
        payload_source.copy(),
        files_fields=["thumb", "nope"],
        storage=None
    )

    # In expected payload file item should only keep the file destination and have a
    # new item for file checksum (but empty since source file does not exist)
    expected = payload_source.copy()
    expected["thumb_checksum"] = None

    assert expected == result


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

    # Take checksum item apart
    cover_checksum = result.pop("cover_checksum")

    assert result == {
        "title": "Foo bar",
        "cover": [
            media_sample / "cover.png",
            Path("foo.jpg"),
        ],
        # Thumb is not defined as a file item, so it is ignored and left unchanged
        "thumb": [
            Path("source.jpg"),
            Path("destination.jpg")
        ],
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
    patched = result.copy()
    cover_checksum = patched.pop("cover_checksum")

    # Destination is well removed from cover item
    assert patched["cover"] == ["cover.png", Path("foo.jpg")]

    # However given storage is enough to find file and checksum it correctly
    assert isinstance(cover_checksum, str) is True
    assert len(cover_checksum) == 128


def test_checksum_directory_payload_stable_checksum(media_sample):
    """
    Given JSON payload should be altered to remove file destination (since they may
    contain variadic content like UUID) and finally used to make a checksum to a
    string of exactly 128 characters.
    """
    checksum_op = ChecksumOperator()

    first = checksum_op.directory_payload(
        {
            "cover": [
                "cover.png",
                Path("foo_1.jpg"),
            ],
            "cover_checksum": "plip4plop",
        },
        files_fields=["cover"],
        storage=media_sample,
    )

    assert isinstance(first, str) is True
    assert len(first) == 128

    # Use similar payload but with different cover destination
    second = checksum_op.directory_payload(
        {
            "cover": [
                "cover.png",
                Path("foo_2.jpg"),
            ],
            "cover_checksum": "plip4plop",
        },
        files_fields=["cover"],
        storage=media_sample,
    )

    assert isinstance(second, str) is True
    assert len(second) == 128

    # File destination is ignored from checksum operation, so even with different
    # destination the resulting checksum is the same
    assert first == second
