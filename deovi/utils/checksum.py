import datetime
import hashlib


def checksum_file_content(path):
    """
    Make a checksum of file content with blake2b.

    Operation is expected to be an efficient way for large files with blake2b.

    Borrowed from: https://stackoverflow.com/a/44873382

    Arguments:
        path (pathlib.Path): File path to open and checksum.

    Returns:
        string: The file checksum as 40 characters.
    """
    h = hashlib.blake2b()
    b = bytearray(128 * 1024)
    mv = memoryview(b)

    with open(path, "rb", buffering=0) as f:
        for n in iter(lambda: f.readinto(mv), 0):
            h.update(mv[:n])

    return h.hexdigest()


def checksum_content(content):
    """
    Basic function to make a checksum of a given content string.

    Arguments:
        content (string): Content string to checksum.

    Returns:
        string: The file checksum as 40 characters.
    """
    return hashlib.blake2b(content.encode("utf-8")).hexdigest()


def compute_checksum_file_path(path):
    """
    Compute a string made up of file name and a blake2b checksum.

    The checksum is done on the path name with the current datetime divided by
    character ``_``.

    .. Note::
        This is almost unused, only asset storage implement it but it is never
        enabled from collector.

    Arguments:
        path (pathlib.Path): Filepath used to compute a new name.

    Returns:
        string: The checksum value.
    """
    return hashlib.blake2b(
        "{}_{}".format(
            path.name,
            datetime.datetime.now().isoformat(),
        ).encode("utf-8"),
        digest_size=10
    ).hexdigest()
