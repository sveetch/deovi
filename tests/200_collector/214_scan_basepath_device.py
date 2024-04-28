from deovi.collector import Collector


def test_collector_scan_basepath_device(media_sample):
    """
    Method should return informations about disk usage for given path.

    We do not check sizes since there are not stable data since they can change from a
    system to another. We only check that expected informations are there and not
    empty.
    """
    collector = Collector(media_sample)

    stats = collector.scan_basepath_device(collector.basepath)

    assert stats["total"] > 0
    assert stats["used"] > 0
    assert stats["free"] > 0
    assert stats["percentage"] > 0
