DUMMY_ISO_DATETIME = "1977-06-02T07:35:15"


def timestamp_to_isoformat(*args, **kwargs):
    """
    A dummy function which always returns the same string with datetime formatted to
    ISO format without microseconds.

    It is aimed to be used to mockup ``Collector.timestamp_to_isoformat`` in tests
    since sample files datetime are not stable through an installation to another.
    """
    return DUMMY_ISO_DATETIME
