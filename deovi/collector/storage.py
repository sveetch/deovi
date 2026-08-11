import datetime
import shutil
from pathlib import Path

from ..printer import PrinterInterface
from ..utils.checksum import compute_checksum_file_path


class AssetStorage(PrinterInterface):
    """
    Implement the asset storage logic.

    You can use the same instance for different basepaths but you will need to
    set each new base path with ``AssetStorage.set_basepath()``.

    Keyword Arguments:
        basepath (pathlib.Path): A directory or file path that will be used as the
            base path to store files. Note than asset files are not directly
            stored in the base path, they commonly are in their own subdirector
            from basepath. If argument is empty it will be assumed to be
            the current working directory.
        checksum (boolean): Whether to enable checksum or not. Default
            to False, asset storage paths won't any checksum included in their name.
    """
    # Name used when given basepath is an empty Path
    DEFAULT_BASE_PATH = "attachment"

    def __init__(self, basepath=None, checksum=False):
        super().__init__()

        self.queue = []

        self.set_basepath(basepath, checksum=checksum)

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
                to False, assets storage path won't include any checksum in its
                name.

        Returns:
            pathlib.Path: A filename composed from the filepath filename (without dirs
            or extension) and possibly a computed unique hash.
        """
        if not filepath or str(filepath) == ".":
            filepath = Path(self.DEFAULT_BASE_PATH)

        if checksum:
            # Build hash from name + current ISO datetime
            suffix = compute_checksum_file_path(filepath)
        else:
            # Build a simple datetime stamp
            suffix = datetime.datetime.now().isoformat(
                sep="T"
            ).replace(".", "").replace("-", "").replace(":", "")

        # Merge path stem with suffix
        return Path("{}_{}".format(filepath.stem, suffix))

    def store(self):
        """
        Store all assets files from storage queue into the assets directory.

        Assets are written to their destination path as given as second item of each
        asset, (first item is the source path).

        Destination path parent directories are created if it does not already exists.

        TODO: For security, we should resolve destination path to ensure it does not
        contains syntax to go up before the destination path node such as with something
        like "../foo/".

        Returns:
            tuple: The asset storage path and the list of stored files in their final
            destination.
        """
        container = None
        stored = []

        if len(self.queue) > 0:
            container = self.storage_path / self.storage_assets

            if not container.exists():
                container.mkdir(parents=True, exist_ok=True)

            for asset in self.queue:
                destination_path = container / asset.destination

                # Check source
                if not asset.source.exists():
                    msg = "File to store does not exists from your filesystem: {}"
                    self.log_warning(msg.format(asset.source))

                # Check destination
                if not destination_path.parent.exists():
                    destination_path.parent.mkdir(parents=True, exist_ok=True)

                # Copy files and register it in the 'done' list
                shutil.copy(asset.source, destination_path)
                stored.append(destination_path)

        return (
            container,
            stored,
        )
