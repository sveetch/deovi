DUMMY_ISO_DATETIME = "1977-06-02T07:35:15"


def timestamp_to_isoformat(*args, **kwargs):
    """
    A dummy function which always returns the same string with datetime formatted to
    ISO format without microseconds.

    It is aimed to be used to mockup ``Collector.timestamp_to_isoformat`` in tests
    since sample files datetime are not stable through an installation to another.
    """
    return DUMMY_ISO_DATETIME


def dummy_uuid4():
    """
    A very dummy function to use to mockup ``uuid.uuid4()``.
    """
    return "dummy_uuid4"


class dummy_blake2b():
    """
    A class to mockup ``hashlib.blake2b()``.

    Instead of generating a hash it returns given content unchanged.

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
