from freezegun import freeze_time

import deovi.utils.checksum as checksum_module
from deovi.utils.tests import dummy_checksumoperator_filepath


def test_checksum_file(media_sample):
    """
    File checksum should be a string of exactly 128 characters.
    """
    checksum = checksum_module.checksum_file_content(media_sample / "cover.png")
    assert isinstance(checksum, str) is True
    assert len(checksum) == 128

    checksum = checksum_module.checksum_file_content(
        media_sample / "SampleVideo_1280x720_1mb.mkv"
    )
    assert isinstance(checksum, str) is True
    assert len(checksum) == 128


@freeze_time("2012-10-15 10:00:00")
def test_checksum_file_mocked(monkeypatch, media_sample):
    """
    Mockup should still returns a string but with file name + datetime.
    """
    monkeypatch.setattr(
        checksum_module,
        "checksum_file_content",
        dummy_checksumoperator_filepath
    )

    checksum = checksum_module.checksum_file_content(media_sample / "cover.png")
    assert isinstance(checksum, str) is True
    assert checksum == "cover.png_2012-10-15T10:00:00"

    checksum = checksum_module.checksum_file_content(
        media_sample / "SampleVideo_1280x720_1mb.mkv"
    )
    assert isinstance(checksum, str) is True
    assert checksum == "SampleVideo_1280x720_1mb.mkv_2012-10-15T10:00:00"


def test_checksum_filepath(media_sample):
    """
    Patch checksum should be a string of exactly 20 characters.
    """
    checksum = checksum_module.compute_checksum_file_path(media_sample / "cover.png")
    assert isinstance(checksum, str) is True
    assert len(checksum) == 20

    checksum = checksum_module.compute_checksum_file_path(
        media_sample / "SampleVideo_1280x720_1mb.mkv"
    )
    assert isinstance(checksum, str) is True
    assert len(checksum) == 20


@freeze_time("2012-10-15 10:00:00")
def test_checksum_filepath_mocked(monkeypatch, media_sample):
    """
    Mockup should still returns a string but with file name + datetime.
    """
    monkeypatch.setattr(
        checksum_module,
        "compute_checksum_file_path",
        dummy_checksumoperator_filepath
    )

    checksum = checksum_module.compute_checksum_file_path(media_sample / "cover.png")
    assert isinstance(checksum, str) is True
    assert checksum == "cover.png_2012-10-15T10:00:00"

    checksum = checksum_module.compute_checksum_file_path(
        media_sample / "SampleVideo_1280x720_1mb.mkv"
    )
    assert isinstance(checksum, str) is True
    assert checksum == "SampleVideo_1280x720_1mb.mkv_2012-10-15T10:00:00"
