import pytest

from deovi.collector import Collector


@pytest.mark.parametrize("timestamp, expected", [
    (
        1642296817.279053,
        "2022-01-16T01:33:37+00:00",
    ),
    (
        1642296817.3030524,
        "2022-01-16T01:33:37+00:00",
    ),
    (
        1541793812.3030524,
        "2018-11-09T20:03:32+00:00",
    ),
])
def test_collector_timestamp_to_isoformat(timestamp, expected):
    """
    Given timestamp should be correctly formatted to datetime in ISO format.
    """
    collector = Collector(None)

    assert collector.timestamp_to_isoformat(timestamp) == expected
