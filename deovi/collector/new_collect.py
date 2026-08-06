import datetime
import json
from shutil import disk_usage

from ..conf import settings
from ..exceptions import CollectorError
from ..models import DirectoryInformation, MediaInformation
from ..renamer.printer import PrinterInterface
from ..utils.jsons import ExtendedJsonEncoder
from .new_storage import NewAssetStorage


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
        autoload_manifests (bool): If enabled, the manifest are discovered and used
            to collect additional data from directories or files.
        autochecksum (bool): Whether to enable content checksums or not. Default
            to False, no checksum are done.
        allow_media_cover (bool): If False, cover files will be ignored from dump.
            By default this is True and so covers are managed and dumped.
            Deprecated, since cover is now enabled from non empty 'cover_extensions'
            which is passed to manifest discovering.
    """
    def __init__(self, basepath, extensions=None, allow_empty_dir=False,
                 manifest=None, cover_name=None,
                 cover_extensions=None, allow_media_cover=True,
                 autoload_manifests=False, autochecksum=False):
        super().__init__()

        self.basepath = basepath
        self.extensions = extensions or settings.medias_extensions
        self.allow_empty_dir = allow_empty_dir
        self.cover_extensions = cover_extensions or settings.cover_extensions
        self.autoload_manifests = autoload_manifests
        self.autochecksum = autochecksum

        self.reset()

    def reset(self):
        """
        Reset registry, global states and initialize blank storage.

        This is the method to use if you plan to make multiple usage of ``run`` or
        ``scan_directory`` for different basepath since registry and global states are
        cumulative.
        """
        self.storage = NewAssetStorage()

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

    def scan_basepath_device(self, path):
        """
        Collect basepath device information.

        .. Note:
            This only compute information for the device which basepath belong to, this
            does not compute the basepath information itself.

        Arguments:
            path (pathlib.Path): Path to use to get the device to scan.

        Returns:
            dict: A dictionnary of device informations (total size, used size,
            free space size and occupancy percentage).
        """
        path = path.resolve()
        stats = disk_usage(path)

        return {
            "total": stats.total,
            "used": stats.used,
            "free": stats.free,
            "percentage": (stats.used / stats.total) * 100,
        }

    def scan_file(self, path):
        """
        Scan a media file to get its informations.

        This implementation does not support file without any file extension.

        .. Note::
            Opposed to ``scan_directory``, this method is not intended to be runned
            directly and rather from inside of ``scan_directory``. So this method does
            not store data directly to the registry.

        Arguments:
            path (pathlib.Path): File path to scan for informations.

        Returns:
            MediaInformation: Collected file informations.
        """
        # Get file stats informations
        stats = path.stat()

        data = MediaInformation(
            path=path,
            basepath=self.basepath,
            size=stats.st_size,
            mtime=self.timestamp_to_isoformat(stats.st_mtime),
            autoload=self.autoload_manifests,
            autochecksum=self.autochecksum,
            cover_extensions=self.cover_extensions,
        )

        self.stats["files"] += 1
        self.stats["size"] += data.size

        # Push cover asset in storage queue
        if getattr(data, "manifest"):
            for field in ["cover"]:
                value = getattr(getattr(data, "manifest"), field)
                if value:
                    self.storage.queue.append(value)

        return data

    def scan_directory(self, path, parent=None):
        """
        Scan a directory to get its media files.

        Arguments:
            path (pathlib.Path): Directory to scan for informations, for direct children
                files and to recursively search for children directories.

        Keyword Arguments:
            parent (DirectoryInformation): The parent directory model object.

        Raises:
            CollectorError: If given path is not a directory inside
                basepath directory.

        Returns:
            dict: Directory information payload.
        """
        self.log_debug("Scanning {}".format(str(path)))

        try:
            path.relative_to(self.basepath)
        except ValueError:
            msg = "You cannot scan a directory which is out of given basepath: {}"
            raise CollectorError(msg.format(str(self.basepath)))

        # Get directory stats informations
        stats = path.stat()

        data = DirectoryInformation(
            path=path,
            basepath=self.basepath,
            size=stats.st_size,
            mtime=self.timestamp_to_isoformat(stats.st_mtime),
            autoload=self.autoload_manifests,
            autochecksum=self.autochecksum,
            cover_extensions=self.cover_extensions,
        )

        # Process all possible children
        for child_path in path.iterdir():
            if child_path.is_dir():
                self.scan_directory(child_path, parent=data)
            else:
                # Attach file to its parent directory
                if (
                    child_path.suffix
                    and child_path.suffix.lower()[1:] in self.extensions
                ):
                    data.set_medias([self.scan_file(child_path)])

        # Only append directory datas if there is at least one file or empty dir is
        # allowed
        if self.allow_empty_dir or len(data.medias) > 0:
            self.stats["directories"] += 1
            self.stats["size"] += data.size

            # Store collected data
            key = str(data.path.relative_to(self.basepath))
            self.registry[key] = data

            # Push cover asset in storage queue
            if getattr(data, "manifest"):
                for field in ["cover"]:
                    value = getattr(getattr(data, "manifest"), field)
                    if value:
                        self.storage.queue.append(value)

        return data

    def run(self, destination=None):
        """
        Recursively scan everything from basepath to produce a registry of collected
        informations.

        Keyword Arguments:
            destination (pathlib.Path): Destination path to write a JSON file with
                every collected informations. Default is ``None`` so no JSON dump
                file will be written to the filesystem.

        Returns:
            dict: Dictionnary of global states for collected directories and files.
        """
        # Set storage basepath from destination location
        self.storage.set_basepath(destination, checksum=self.autochecksum)

        device_stats = self.scan_basepath_device(self.basepath)
        self.scan_directory(self.basepath)

        if self.registry and destination:
            with destination.open("w") as fp:
                json.dump(
                    {
                        "device": device_stats,
                        "registry": self.registry,
                    },
                    fp,
                    indent=4,
                    cls=ExtendedJsonEncoder
                )
                self.log_info("Registry saved to: {}".format(str(destination)))

            # Proceed to copy queued files into storage dir
            container, stored = self.storage.store()
            if container:
                self.stats["asset_storage"] = container

        return self.stats
