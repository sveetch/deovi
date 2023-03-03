from pathlib import Path

import pytest

from deovi.collector import Collector


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
