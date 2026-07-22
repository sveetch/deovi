import datetime
import json
from pathlib import Path

import datetime
import json
import hashlib

from .jsons import ExtendedJsonEncoder


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


def checksum_content(content):
    """
    Basic function to make a checksum of a given content string.

    Arguments:
        content (string): Content string to checksum.

    Returns:
        string: The file checksum as 40 characters.
    """
    return hashlib.blake2b(content.encode("utf-8")).hexdigest()


class ChecksumOperator:
    """
    Gather all methods which perform checksums.
    """
    def file(self, filepath):
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

    def filepath(self, filepath):
        """
        Compute a string made up of filepath name and a blake2b checksum (build from
        filepath name with current datetime) divided by a ``_``.

        .. Note::
            This is almost unused, only asset storage implement it but it is never
            enabled from collector.

        Arguments:
            filepath (pathlib.Path): Filepath used to compute a new name.

        Returns:
            string: New unique name.
        """
        return hashlib.blake2b(
            "{}_{}".format(
                filepath.name,
                datetime.datetime.now().isoformat(),
            ).encode("utf-8"),
            digest_size=10
        ).hexdigest()

    def payload_files(self, payload, files_fields=[], storage=None):
        """
        Patch directory payload to include all file checksum.

        Arguments:
            payload (dict): The directory information payload to patch. Note that given
                dictionnary is mutated by the patch.

        Keyword Arguments:
            files_fields (list): A list of item names assumed to be file items to
                checksum.
            storage (pathlib.Path): A path to prefix all file paths if given. This is
                to use if you are storing relative paths (instead of absolute) in
                payload so a filepath can be resolved using this base storage path.

        Returns:
            dict: Patched payload.
        """
        # Before serialize, files_fields have to be checksumed and payload altered with
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
                    payload[key] = self.file(filepath)
                else:
                    payload[key] = None

        return payload

    def directory_payload(self, payload_source, files_fields=[], storage=None):
        """
        Checksum directory informations including its files with blake2b.

        NOTE:
        File item are checksumed apart so they would change the directory information
        payload checksum if they change. So we keep the file item untouched so if the
        file name change, this also triggers a payload checksum difference.
        TODO: ???

        Arguments:
            payload_source (dict): The directory information payload to checksum.

        Keyword Arguments:
            files_fields (list): A list of item names assumed to be file items to
                checksum.
            storage (pathlib.Path): A path to prefix all file paths if given. This is
                to use if you are storing relative paths (instead of absolute) in
                payload so a filepath can be resolved using this base storage path.

        Returns:
            string: The payload checksum as 40 characters.
        """
        # We do not want mutating of given payload
        payload = payload_source.copy()

        # Patch file item to only retain source path
        for fieldname in files_fields:
            if payload.get(fieldname):
                source, destination = payload[fieldname]
                payload[fieldname] = source

        # Serialize to JSON
        serialized = json.dumps(
            payload,
            indent=4,
            sort_keys=True,
            cls=ExtendedJsonEncoder
        )
        # TODO: print JSON serialization and look for it in original collector test
        print("----> directory_payload")
        print(serialized)
        print("directory_payload <----")

        return hashlib.blake2b(serialized.encode("utf-8")).hexdigest()
