import datetime
from shutil import disk_usage

from ..conf import settings
from ..exceptions import CollectorError
from ..models import (
    DirectoryInformation,
    MediaInformation,
    CollectionManifest,
    MovieManifest,
    SerieManifest,
)
from ..renamer.printer import PrinterInterface
from ..utils.jsons import ExtendedJsonEncoder
from ..utils.checksum import ChecksumOperator
from .storage import AssetStorage

class NewCollector(PrinterInterface):
    """
    Collect informations about media files.

    Attributes:
        registry (dict): The registry where is collected all informations from scanning.
        stats (dict): Global statistics for all collected directories, files and total
            size.
        file_storage_queue (list): A list where each item is a tuple with source and
            destination to use for copying files.

    Arguments:
        basepath (pathlib.Path): The base directory for all directories to scan.
            Directories does not have to start directly from the basepath but must
            start from it.

    Keyword Arguments:
        extensions (list): A list of file extensions to consider as media files. A
            file extension that is not in this list are ignored. Default list contains
            all common video file extensions.
        allow_empty_dir (bool): If True, even directory without direct media files are
            still collected in registry. Default is False, so only directories with
            direct media children are collected, the other directories are ignored from
            registry (but still scanned for children directories).
        manifest (string): Manifest filename to search for in a directory.
        cover_name (string): Cover file name (without extension) used to search for
            cover files.
        cover_extensions (list): Cover file extensions (with leading dot) used to
            search for cover files.
        allow_media_cover (bool): If False, cover files will be ignored from dump.
            By default this is True and so covers are managed and dumped.
    """
    def __init__(self, basepath, extensions=None, allow_empty_dir=False,
                 manifest=None, cover_name=None,
                 cover_extensions=None, allow_media_cover=True):
        super().__init__()

        self.checksum_op = ChecksumOperator()
        self.basepath = basepath
        self.extensions = extensions or settings.medias_extensions
        self.allow_empty_dir = allow_empty_dir
        self.manifest_filename = manifest or settings.manifest_filename
        self.cover_name = cover_name or settings.cover_name
        self.cover_extensions = cover_extensions or settings.cover_extensions
        self.allow_media_cover = allow_media_cover
        self.file_storage_queue = []

        # Build elligible file names for cover from cover base file name and enabled
        # cover extensions
        self.cover_files = [
            self.cover_name + item
            for item in self.cover_extensions
        ]

        self.reset()

    def reset(self):
        """
        Reset registry and global states.

        This is the method to use if you plan to make multiple usage of ``run`` or
        ``scan_directory`` for different basepath since registry and global states are
        cumulative.
        """
        self.storage = AssetStorage(allowed_cover_filenames=self.cover_files)
        self.file_storage_queue = []

        self.registry = {}
        self.stats = {
            "directories": 0,
            "files": 0,
            "size": 0,
            "asset_storage": None,
        }

    def timestamp_to_isoformat(self, timestamp):
        """
        Return datetime formatted from given timestamp.

        Arguments:
            timestamp (float): A timestamp as expected from date returned in
                ``Path.stat()``.

        Returns:
            string: Datetime formatted in ISO format without microseconds.
        """
        return datetime.datetime.fromtimestamp(
            timestamp,
            tz=datetime.timezone.utc
        ).isoformat(timespec="seconds")

    def _process_file_fields(self, fields, data):
        """
        Process field fields

        File field are collected as a tuple with file source path and destination path
        but only the destination path will be stored. The source path will just be
        used to copy the file source to its destination.

        Copying source file to destination is done through a queue to be performed
        after the end of collection.

        At this stage, we don't validate if a file item exist or not, since it has
        already be done during collection.

        Returns:
            dict: Given data possibly patched on file fields. Patch fields are
                transformed to just keep the final file path (not the original one).
        """
        for field in fields:
            if data.get(field):
                source, destination = data.get(field)
                self.file_storage_queue.append((source, destination))
                data[field] = destination

        return data

    def store(self, data):
        """
        Store given directory data.

        Arguments:
            data (dict): The data payload to store. It must have at least a ``path``
                item which will be used as the item key in the store.

        Returns:
            string: Item key name used to store the data.
        """
        key = str(data["path"].relative_to(self.basepath))

        self.registry[key] = self._process_file_fields(["cover"], data)

        return key

    def scan_file(self, path):
        """
        Scan a media file to get its informations.

        This implementation does not support file without any file extension.

        Arguments:
            path (pathlib.Path): File path to scan for informations.

        Returns:
            MediaInformation: Collected file informations.
        """
        # Get file stats informations
        stats = path.stat()

        relative_dir = path.parent.relative_to(self.basepath)

        dirname = path.parent.name
        # Prefer empty dirname instead of basepath dirname when file is at basepath
        # root
        if dirname == self.basepath.name:
            dirname = ""

        # Remove leading dot
        extension = path.suffix[1:].lower()
        # Get the media container label from file extension
        container = settings.default_container_name
        if extension in settings.medias_containers:
            container = settings.medias_containers[extension]

        data = {
            "path": path,
            "name": path.name,
            "absolute_dir": path.parents[0],
            "relative_dir": relative_dir,
            "directory": dirname,
            "extension": extension,
            "container": container,
            "size": stats.st_size,
            "mtime": self.timestamp_to_isoformat(stats.st_mtime),
        }

        self.stats["files"] += 1
        self.stats["size"] += data["size"]

        return data
