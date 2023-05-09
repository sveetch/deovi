import datetime


DUMMY_ISO_DATETIME = "1977-06-02T07:35:15"


def timestamp_to_isoformat(*args, **kwargs):
    """
    A function which always returns the same string with datetime formatted to
    ISO format without microseconds.

    It is aimed to be used to mockup ``Collector.timestamp_to_isoformat`` in tests
    to patch file created/modified datetime since it is not stable through an
    installation to another, so we force it to a stable one.
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
        """
        Arguments and keyword arguments are the same than original method.

        Returns:
            string: Given content, eventually decoded to string if it was a bytes.
        """
        # Convert to byte since hashlib do not accept string/unicode
        if isinstance(self.content, bytes):
            print("🐛 dummy_blake2b:", self.content, type(self.content))
            return self.content.decode("utf-8")

        return self.content


def dummy_checksum_file(cls, filepath):
    """
    A function to mockup ``checksum_file()``

    Instead of generating a hash from a file it just return the given file path.

    This may be required in tests which involves checksum_file with real file that
    will result to UnicodeDecodeError because of trying to decode binary as utf-8.

    Arguments:
        filepath (pathlib.Path): File path to open and checksum.

    Returns:
        string: The given file path.
    """
    print("🔖 dummy_checksum_file:", filepath, type(filepath))
    return str(filepath)


def dummy_checksumoperator_filepath(cls, filepath):
    """
    Support both ChecksumOperator.file and ChecksumOperator.filepath for monkey
    patching.

    Arguments and keyword arguments are the same than original methods.

    since the two
    receive a file Path object and will return path.

    Returns:
        string: Path from given file Path object.
    """
    content = "{}_{}".format(
        filepath.name,
        datetime.datetime.now().isoformat(),
    )

    print("✨ dummy_checksumoperator_filepath:", content, type(content))

    return content


def dummy_checksumoperator_directory_payload(cls, payload, files_fields=[],
                                             storage=None):
    """
    Support ``ChecksumOperator.directory_payload`` for monkey patching.

    Arguments and keyword arguments are the same than original method.

    Returns:
        string: JSON payload as done from ``ChecksumOperator.payload_files()``.
    """
    return cls.payload_files(
        payload,
        files_fields=files_fields,
        storage=storage
    )
