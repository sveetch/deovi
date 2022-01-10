import datetime
import json

from ..renamer.printer import PrinterInterface
from ..utils.jsons import ExtendedJsonEncoder
from ..exceptions import CollectorError


# Non exhaustive list of Video containers with their file extension and name
# Should also describe some music only containers
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


class Collector(PrinterInterface):
    """
    Collect informations about media files.

    Attributes:
        registry (dict): The registry where is collected all informations from scanning.
        stats (dict): Global statistics for all collected directories, files and total
            size.

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
    """
    def __init__(self, basepath, extensions=MEDIAS_EXTENSIONS, allow_empty_dir=False):
        super().__init__()

        self.basepath = basepath
        self.extensions = extensions
        self.allow_empty_dir = allow_empty_dir
        self.reset()

    def reset(self):
        """
        Reset registry and global states.

        This is the method to use if you plan to make multiple usage of ``run`` or
        ``scan_directory`` for different basepath since registry and global states are
        cumulative.
        """
        self.registry = {}
        self.stats = {
            "directories": 0,
            "files": 0,
            "size": 0,
        }

    def store(self, data):
        """
        Store given directory data.

        Arguments:
            data (dict):
        """
        key = str(data["path"].relative_to(self.basepath))
        self.registry[key] = data

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

        # Get ISO formatted datetime but without microseconds
        mtime = datetime.datetime.fromtimestamp(
            stats.st_mtime
        ).isoformat(
            timespec="seconds"
        )

        data = {
            "path": path,
            "name": path.name,
            "absolute_dir": path.parents[0],
            "relative_dir": relative_dir,
            "directory": dirname,
            "extension": extension,
            "container": container,
            "size": stats.st_size,
            "mtime": mtime,
        }

        self.stats["files"] += 1
        self.stats["size"] += data["size"]

        return data

    def scan_directory(self, path):
        """
        Scan a directory to get its media files.

        Does not return anything, the directories informations (and possible media files
        informations) are stored in ``Collector.registry``.

        Arguments:
            path (pathlib.Path): Directory to scan for informations, for direct children
                files and to recursively search for children directories.

        Raises:
            CollectorError: If given path is not a directory inside
                basepath directory.
        """
        self.log_debug("Scanning {}".format(str(path)))

        try:
            relative_dir = path.relative_to(self.basepath)
        except ValueError:
            msg = "You cannot scan a directory which is out of given basepath: {}"
            raise CollectorError(msg.format(str(self.basepath)))

        # Get directory stats informations
        stats = path.stat()

        # Get ISO formatted datetime but without microseconds
        mtime = datetime.datetime.fromtimestamp(
            stats.st_mtime
        ).isoformat(
            timespec="seconds"
        )

        data = {
            "path": path,
            "name": path.name,
            "absolute_dir": path.parents[0],
            "relative_dir": relative_dir,
            "size": stats.st_size,
            "mtime": mtime,
            "children_files": [],
        }

        for child in path.iterdir():
            if child.is_dir():
                self.scan_directory(child)
            else:
                if child.suffix and child.suffix.lower()[1:] in self.extensions:
                    data["children_files"].append(self.scan_file(child))

        if self.allow_empty_dir or len(data["children_files"]) > 0:
            self.stats["directories"] += 1
            self.stats["size"] += data["size"]
            self.store(data)

    def run(self, destination=None):
        """
        Recursively scan everything from basepath to produce a registry of collected
        informations.

        Keyword Arguments:
            destination (pathlib.Path): Destination path to write a JSON file with
                every collected informations. Default is ``None`` so no JSON registry
                file will be written to the filesystem.

        Returns:
            dict: Dictionnary of global states for collected directories and files.
        """
        self.scan_directory(self.basepath)

        if self.registry and destination:
            with destination.open("w") as fp:
                json.dump(self.registry, fp, indent=4, cls=ExtendedJsonEncoder)
                self.log_info("Registry saved to: {}".format(str(destination)))

        return self.stats
