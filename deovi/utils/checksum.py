import json
import hashlib

from .jsons import ExtendedJsonEncoder


def checksum_file(filepath):
    """
    Checksum a file in an efficient way for large files with blake2b.

    Borrowed from: https://stackoverflow.com/a/44873382

    Arguments:
        filepath (pathlib.Path): File path to open and checksum.

    Returns:
        string: The file checksum as 40 characters.
    """
    h = hashlib.blake2b()
    b = bytearray(128 * 1024)
    mv = memoryview(b)

    with open(filepath, "rb", buffering=0) as f:
        for n in iter(lambda: f.readinto(mv), 0):
            h.update(mv[:n])

    return h.hexdigest()


def directory_payload_checksum(payload, files_fields=[], storage=None):
    """
    A standardized way to checksum directory informations including its files with
    blake2b.

    File item are checksumed apart so they would change payload checksum if they
    change, we keep the file item untouched so if the file name change, this also
    triggers a payload checksum difference.

    Arguments:
        payload (dict): The directory information payload to checksum.

    Keyword Arguments:
        files_fields (list): A list of item names to manage as files if they exist in
            given payload.
        storage (pathlib.Path): A path to prefix all file paths if given. This is to
            use if you are storing relative paths in payload.

    Returns:
        string: The payload checksum as 40 characters.
    """
    # Before serialize, files_fields have to checksumed and payload altered with
    # their checksum
    for fieldname in files_fields:
        # Proceed on non empty field
        if payload.get(fieldname):
            # Get proper file path
            source, destination = payload[fieldname]
            if storage:
                filepath = storage / source
            else:
                filepath = source

            # Checksum the file if it exists
            key = "{}_checksum".format(fieldname)
            if filepath.exists():
                payload[key] = checksum_file(filepath)
            else:
                payload[key] = None

    # Once payload is ready, serialize it to JSON to give as a content to hash
    serialized = json.dumps(payload, indent=4, sort_keys=True, cls=ExtendedJsonEncoder)

    return hashlib.blake2b(serialized.encode("utf-8")).hexdigest()
