from pathlib import Path

import pytest

from deovi.collector import Collector


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
