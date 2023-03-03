from pathlib import Path

import pytest

from deovi.collector import Collector


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
