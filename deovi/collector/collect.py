import datetime
import json
from shutil import disk_usage

import yaml

from ..renamer.printer import PrinterInterface
from ..utils.jsons import ExtendedJsonEncoder
from ..utils.checksum import ChecksumOperator
from ..exceptions import CollectorError
from .storage import AssetStorage

# Non exhaustive list of Video containers with their file extension and name
# NOTE: May also describe some music only containers
MEDIAS_CONTAINERS = {
    "3gp": "3GPP",
    "asf": "Advanced Systems Format",
    "avi": "AVI",
    "flv": "Flash Video",
    "f4v": "Flash Video",
    "mov": "QuickTime",
    "mp4": "MPEG-4",
    "mkv": "Matroska",
    "mpg": "MPEG",
    "mpeg": "MPEG",
    "mpv": "MPEG",
    "mts": "MPEG Transport Stream",
    "qt": "QuickTime",
    "rm": "RealMedia",
    "ts": "MPEG Transport Stream",
    "vob": "Vob",
    "webm": "WebM",
    "wmv": "Windows Media Video",
}


# Default container label when extension does not match default container list
MEDIAS_DEFAULT_CONTAINER_NAME = "Unknow"


# List of unique file extensions for medias
MEDIAS_EXTENSIONS = set(MEDIAS_CONTAINERS.keys())


# Manifest filename to search in a directory
MANIFEST_FILENAME = "manifest.yaml"


# Forbidden/reserved keyword from manifest corresponding to computed values from
# collection (obviously excepted the ones from manifest)
MANIFEST_FORBIDDEN_VARS = {
    "path",
    "name",
    "absolute_dir",
    "relative_dir",
    "size",
    "mtime",
    "checksum",
    "children_files",
    "cover",
}


# File name to use with allowed extensions to search for a cover
COVER_NAME = "cover"


# Allowed file extensions to search for a cover. The order define the priority when
# there is multiple cover files in the same directory. The first extension will always
# have highest priority against other extensions.
COVER_EXTENSIONS = [
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
]


class Collector(PrinterInterface):
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
        allow_empty_dir (list): If True, even directory without direct media files are
            still collected in registry. Default is False, so only directories with
            direct media children are collected, the other directories are ignored from
            registry (but still scanned for children directories).
        manifest (string): Manifest filename to search for in a directory.
        cover_name (string): Cover file name (without extension) used to search for
            cover files.
        cover_extensions (list): Cover file extensions (with leading dot) used to
            search for cover files.
        allow_media_cover (boolean): If False, cover files will be ignored from dump.
            By default this is True and so covers are managed and dumped.
    """
    def __init__(self, basepath, extensions=MEDIAS_EXTENSIONS, allow_empty_dir=False,
                 manifest=MANIFEST_FILENAME, cover_name=COVER_NAME,
                 cover_extensions=COVER_EXTENSIONS, allow_media_cover=True):
        super().__init__()

        self.checksum_op = ChecksumOperator()
        self.basepath = basepath
        self.extensions = extensions
        self.allow_empty_dir = allow_empty_dir
        self.manifest_filename = manifest
        self.cover_name = cover_name
        self.cover_extensions = cover_extensions
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

        Implemention does not support file without any suffix (file extension).

        Arguments:
            path (pathlib.Path): File path to scan for informations.

        Returns:
            dict: Collected file informations.
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
        container = MEDIAS_DEFAULT_CONTAINER_NAME
        if extension in MEDIAS_CONTAINERS:
            container = MEDIAS_CONTAINERS[extension]

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

    def get_directory_manifest(self, path):
        """
        Search for a YAML manifest to load medias informations related to
        given directory path.

        It should be safe to run with invalid manifests.

        Arguments:
            path (pathlib.Path): A Path object for the directory where to find
                manifest.

        Returns:
            dict: Manifest content.
        """
        manifest = {}
        manifest_path = path / self.manifest_filename

        if manifest_path.exists():
            try:
                manifest = yaml.load(manifest_path.read_text(), Loader=yaml.FullLoader)
            except yaml.YAMLError:
                msg = "No YAML object could be decoded for manifest: {}"
                self.log_warning(msg.format(str(manifest_path)))
            else:
                # Validate top level items against reserved keywords to avoid overriding
                # computed data from directory scan
                reserved = [
                    name
                    for name in MANIFEST_FORBIDDEN_VARS
                    if name in manifest
                ]
                if len(reserved) > 0:
                    msg = (
                        "Ignored manifest because it has forbidden keywords '{}': {}"
                    )
                    self.log_warning(msg.format(
                        ", ".join(reserved),
                        str(manifest_path),
                    ))
                    manifest = {}

        return manifest

    def scan_directory(self, path, checksum=False):
        """
        Scan a directory to get its media files.

        Arguments:
            path (pathlib.Path): Directory to scan for informations, for direct children
                files and to recursively search for children directories.

        Raises:
            CollectorError: If given path is not a directory inside
                basepath directory.

        Returns:
            dict: Directory information payload.
        """
        self.log_debug("Scanning {}".format(str(path)))

        try:
            relative_dir = path.relative_to(self.basepath)
        except ValueError:
            msg = "You cannot scan a directory which is out of given basepath: {}"
            raise CollectorError(msg.format(str(self.basepath)))

        # Get directory stats informations
        stats = path.stat()

        data = {
            "path": path,
            "name": path.name,
            "absolute_dir": path.parents[0],
            "relative_dir": relative_dir,
            "size": stats.st_size,
            "mtime": self.timestamp_to_isoformat(stats.st_mtime),
            "children_files": [],
        }

        for child in path.iterdir():
            if child.is_dir():
                self.scan_directory(child, checksum=checksum)
            else:
                if child.suffix and child.suffix.lower()[1:] in self.extensions:
                    data["children_files"].append(self.scan_file(child))

        # Only append directory datas if there is at least one file or empty dir is
        # allowed
        if self.allow_empty_dir or len(data["children_files"]) > 0:
            self.stats["directories"] += 1
            self.stats["size"] += data["size"]

            # Get possible manifest to extend data
            data.update(**self.get_directory_manifest(path))

            # Discover cover if any
            if self.allow_media_cover:
                data["cover"] = self.storage.get_directory_cover(path)

            # Perform content checksum if enabled
            if checksum:
                # Add file checksums
                self.checksum_op.payload_files(
                    data,
                    files_fields=["cover"],
                    storage=self.storage.storage_path,
                )
                # Then build directory info checksum
                data["checksum"] = self.checksum_op.directory_payload(
                    data,
                    files_fields=["cover"],
                    storage=self.storage.storage_path,
                )

            # Store collected data
            self.store(data)

        return data

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

    def run(self, destination=None, checksum=False):
        """
        Recursively scan everything from basepath to produce a registry of collected
        informations.

        Keyword Arguments:
            destination (pathlib.Path): Destination path to write a JSON file with
                every collected informations. Default is ``None`` so no JSON dump
                file will be written to the filesystem.
            checksum (boolean): Whether to enable directory checksums or not. Default
                to False, no checksum are done.

        Returns:
            dict: Dictionnary of global states for collected directories and files.
        """
        # Set storage basepath from destination location
        self.storage.set_basepath(destination, checksum=checksum)

        device_stats = self.scan_basepath_device(self.basepath)
        self.scan_directory(self.basepath, checksum=checksum)

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
            container, stored = self.storage.store_assets(self.file_storage_queue)
            if container:
                self.stats["asset_storage"] = container

        return self.stats
