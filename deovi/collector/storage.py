import datetime
import shutil
import uuid
from pathlib import Path

from ..renamer.printer import PrinterInterface
from ..utils.checksum import ChecksumOperator


class AssetStorage(PrinterInterface):
    """
    Implement the asset storage logic.

    You can use the same instance for different basepaths but you will need to
    set each new base path with ``AssetStorage.set_basepath()``.

    Keyword Arguments:
        path (pathlib.Path): A directory or file path that will be used as the
            base path to store files. Note than asset files are not directly
            stored in the base path, they commonly are in their own subdirector
            from basepath. This argument can be empty but that will resolve
            basepath to the currently working directory which may not be very
            stable from code to another code.
        checksum (boolean): Whether to enable checksum or not. Default
            to False, asset storage paths won't any checksum included in their name.
        allowed_cover_filenames (list): List of filenames elligible as a directory
            cover file.
    """
    # Name used when given basepath is an empty Path
    DEFAULT_BASE_PATH = "attachment"

    def __init__(self, basepath=None, checksum=False, allowed_cover_filenames=None):
        super().__init__()

        self.checksum_op = ChecksumOperator()

        self.set_basepath(basepath, checksum=checksum)

        self.allowed_cover_filenames = allowed_cover_filenames or []

    def set_basepath(self, path=None, checksum=False):
        """
        Configure instance attributes for given base path.

        Keyword Arguments:
            path (pathlib.Path): A directory or file path that will be used as the
                base path to store files.
        """
        self.basepath = path
        self.storage_path = self.build_base_storage(self.basepath)
        self.storage_assets = self.build_assets_storage(
            self.basepath,
            checksum=checksum,
        )

    def build_base_storage(self, filepath):
        """
        Build base directory path.

        Nothing is writed on FS.

        Arguments:
            filepath (pathlib.Path):

        Returns:
            pathlib.Path: Either an empty Path or the filepath parent depending
            filepath is an empty Path or not.
        """
        if not filepath or str(filepath) == ".":
            return Path()

        return filepath.parent

    def build_assets_storage(self, filepath, checksum=False):
        """
        Build storage directory name from given filename and current datetime.

        Nothing is writed on FS.

        Arguments:
            filepath (pathlib.Path):

        Keyword Arguments:
            checksum (boolean): Whether to enable checksum or not. Default
                to False, asset storage paths won't any checksum included in its
                name.

        Returns:
            pathlib.Path: A filename composed from the filepath filename (without dirs
            or extension) and a computed unique hash.
        """
        if not filepath or str(filepath) == ".":
            filepath = Path(self.DEFAULT_BASE_PATH)

        if checksum:
            # Build hash from name + current ISO datetime
            suffix = self.checksum_op.filepath(filepath)
        else:
            # Build a simple datetime stamp
            suffix = datetime.datetime.now().isoformat(
                sep="T"
            ).replace(".", "").replace("-", "").replace(":", "")

        # Merge path stem with suffix
        return Path("{}_{}".format(filepath.stem, suffix))

    def get_directory_asset(self, path, filename_patterns):
        """
        Search for an asset file from given path.

        The first filename which match an allowed asset filename is returned. Order
        of ``filename_patterns`` defines matching order.

        Arguments:
            path (pathlib.Path): A Path object for the directory where to find
                cover image file.
            filename_patterns (list): A list of strings for asset filenames to search
                in directory.

        Returns:
            tuple: A tuple of two items ``(source, destination)`` where 'source' is the
                source cover file (Path object) resolved to an absolute path
                and 'destination' a filename (Path object) with a uuid4 instead of
                original source file name but with original source file extensions
                keeped.
        """
        for filename in filename_patterns:
            filepath = path / filename

            if filepath.exists():
                return (
                    filepath.resolve(),
                    self.storage_assets / Path(
                        "".join([str(uuid.uuid4()), filepath.suffix])
                    ),
                )

        return None

    def get_directory_cover(self, path):
        """
        Shortand around ``get_directory_asset`` to check for cover filenames.

        Arguments:
            path (pathlib.Path): A Path object for the directory where to find
                cover image file.

        Returns:
            tuple: A tuple with the format as from ``get_directory_asset`` returns.
        """
        return self.get_directory_asset(
            path,
            self.allowed_cover_filenames,
        )

    def store_assets(self, assets):
        """
        Store all given assets files into the assets directory.

        Assets are written to their destination path as given as second item of each
        asset, (first item is the source path).

        Arguments:
            assets (list): List of tuple ``(source, destination)`` where both items are
                Path objects as returned from ``Collector.get_directory_asset()``.

        Returns:
            tuple: The asset storage path and the list of stored files in their final
            destination.
        """
        container = None
        stored = []

        if len(assets) > 0:
            container = self.storage_path / self.storage_assets

            if not container.exists():
                container.mkdir(parents=True, exist_ok=True)

            for source, destination in assets:
                if not source.exists():
                    msg = "File to store does not exists from your filesystem: {}"
                    self.log_warning(msg.format(source))

                # Destination path should be a relative path (from base) which already
                # include the assets directory
                shutil.copy(source, self.storage_path / destination)
                stored.append(self.storage_path / destination)

        return (
            container,
            stored,
        )
