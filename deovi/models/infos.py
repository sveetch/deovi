import datetime
import json
import logging
from pathlib import Path
from dataclasses import (
    dataclass,
    field as dataclasses_field,
    InitVar,
)
from typing import Any, ClassVar, Union

import yaml

from .manifests import CollectionManifest, MovieManifest, SerieManifest
from ..conf import settings
from ..exceptions import InformationModelError
from ..utils.jsons import ExtendedJsonEncoder
from .. import __pkgname__

from .abstracts import ChecksumAbstract, ExportAbstract


LOGGER = logging.getLogger(__pkgname__)


@dataclass
class BaseInformation(ChecksumAbstract, ExportAbstract):
    """
    Base model for information models.

    Inside Deovi, Information model is the base to collect a file structure, it contains
    some filesystem and directory structure about a directory or a file and possibly
    discover metadata from a manifest.

    .. Warning::
        The models does not any validation about given path. A ``DirectoryInformation``
        is expected to be a valid directory and ``MediaInformation`` to be a valid file.
        Allthough they can pass this expectation, computed values will be wrong in most
        cases and not supported in Deovi system.

        Also model information don't make any validation about manifest, however it is
        clear that :

        * A ``DirectoryInformation`` should only include a ``CollectionManifest`` or
          ``SerieManifest`` but never a ``MovieManifest``;
        * A ``MediaInformation`` should only include for a ``MovieManifest``;


    ``name``, ``absolute_dir``, ``relative_dir``, and ``title`` are computed
    automatically from given ``path`` if not given.

    Attributes:
        EXPORT_PRIVATES (list): List of strings for field names that won't be exported
            from ``as_dict`` and ``as_json`` methods. If you have recursive parenting
            you should care of this field.

    Arguments:
        path (pathlib.Path): Absolute path of this directory object.
        size (int): Directory size in octets (as an integer).
        mtime (datetime.datetime): Datetime of the last directory modification.
        basepath (pathlib.Path): The base directory for all directories to scan.
            Directories does not have to start directly from the basepath but must
            start from it. It is used to automatically computed many optional fields but
            it is not stored as this object attribute.

    Keyword Arguments:
        parent (DirectoryInformation): Directory object which this object belong to.
        name (str): This directory object name.
        absolute_dir (pathlib.Path): Absolute path which holds this directory object.
            Commonly it would look like the basepath but in some case it could be
            different.
        relative_dir (pathlib.Path): Directory path relatively to the basepath.
            Eg: For ``/foo/bar/home/`` the basepath would be ``/foo/bar/`` and ``home/``
            the relative directory.
        manifest (Object): todo (to carry tmdb infos)
        checksum (str): Checksum (this is expected to be a long blake2b string).
        autoload (bool): If enabled the model will try to discover and load a manifest
            file related to this object. This is disabled on default. Each model kind
            has its own way to discover a manifest.
        basepath (pathlib.Path): The basepath of this directory
    """
    EXPORT_PRIVATES: ClassVar[list[str]] = ["parent"]
    CHECKSUM_FIELD: ClassVar[str] = "path"
    basepath: InitVar[Path]
    path: Path
    size: int
    mtime: datetime.datetime
    parent: Any = None
    name: str = None
    absolute_dir: Path = None
    relative_dir: Path = None
    manifest: Any = None
    checksum: str = None
    autoload: InitVar[bool] = False
    autochecksum: InitVar[bool] = False
    cover_extensions: InitVar[list] = None

    def __post_init__(self, basepath, autoload, autochecksum, cover_extensions):
        if not self.name:
            self.name = self.path.name

        if not self.absolute_dir:
            self.absolute_dir = self.path.parents[0]

        if not self.relative_dir:
            self.relative_dir = self.compute_relative_dir(self.path, basepath)

        if autoload and not self.manifest:
            self.manifest = self.discover_manifest(cover_extensions)

        if autochecksum:
            self.set_checksum()

    def compute_relative_dir(self, path, basepath):
        """
        Make given path relative to given basepath.

        Arguments:
            path (Path): The path to make relative.
            basepath (Path): The base path which hold the ``path``.

        Raises:
            InformationModelError: If path is not a subset of basepath.

        Returns:
            Path: The relative path.
        """
        try:
            relative_dir = path.relative_to(basepath)
        except ValueError:
            msg = "You cannot use a directory which is out of given basepath: {}"
            raise InformationModelError(msg.format(basepath))

        return relative_dir

    def discover_manifest(self, cover_extensions=None):
        """
        Discover a possible manifest file matching the expected filename.

        Each manifest model should implement itself its method to discover and load
        a manifest file related to a model object.

        Returns:
            dict: Should return loaded manifest file data. Base implementation just
            returns the result of ``load_manifest`` with an empty value.
        """
        return self.load_manifest(None, None, cover_extensions=cover_extensions)

    def load_manifest(self, path, data, cover_extensions=None):
        """
        Load manifest payload as a manifest model object.

        The kind of manifest model to be used is guessed from 'tmdb_type'.
        """
        if data:
            if data["tmdb_type"] == "collection":
                return CollectionManifest(
                    path,
                    cover_extensions=cover_extensions,
                    **data
                )
            elif data["tmdb_type"] == "tv":
                return SerieManifest(path, cover_extensions=cover_extensions, **data)
            elif data["tmdb_type"] == "movie":
                return MovieManifest(path, cover_extensions=cover_extensions, **data)
            else:
                msg = "Manifest type is not supported: {}"
                raise NotImplementedError(msg.format(data.get("tmdb_type")))

            return None

        return None

    def get_yaml_manifest(self, path):
        """
        Open and load a YAML manifest.

        It should be safe to run with invalid manifests.

        NOTE: Previously this method was returning a {} if no valid was found/parsed,
        now it returns a null value.

        Arguments:
            path (pathlib.Path): The manifest filepath.

        Returns:
            dict: Loaded manifest file data.
        """
        manifest = None

        try:
            manifest = yaml.load(path.read_text(), Loader=yaml.FullLoader)
        except yaml.YAMLError:
            msg = "No YAML object could be decoded from manifest: {}"
            LOGGER.warning(msg.format(path))
        else:
            # Validate top level items against reserved keywords to avoid overriding
            # computed data from directory scan
            reserved = [
                name
                for name in settings.manifest_forbidden_vars
                if name in manifest
            ]
            if len(reserved) > 0:
                msg = (
                    "Ignored YAML manifest because it has forbidden keywords '{}': {}"
                )
                LOGGER.warning(msg.format(", ".join(reserved), path))
                return None

        if manifest.get("tmdb_type", None) not in settings.allowed_manifest_types:
            msg = (
                "YAML Manifest is missing the required 'tmdb_type' field: {}"
            )
            LOGGER.warning(msg.format(path))
            return None

        return manifest

    def get_json_manifest(self, path):
        """
        Open and load a JSON manifest.

        It should be safe to run with invalid manifests.

        NOTE: Collector method was returning a {} if no valid was found/parsed, now we
        return a None

        Arguments:
            path (pathlib.Path): The manifest filepath.

        Returns:
            dict: Loaded manifest file data.
        """
        manifest = None

        try:
            manifest = json.loads(path.read_text())
        except json.JSONDecodeError:
            msg = "No JSON object could be decoded from manifest: {}"
            LOGGER.warning(msg.format(path))
        else:
            # Validate top level items against reserved keywords to avoid overriding
            # computed data from directory scan
            reserved = [
                name
                for name in settings.manifest_forbidden_vars
                if name in manifest
            ]
            if len(reserved) > 0:
                msg = (
                    "Ignored JSON manifest because it has forbidden keywords '{}': {}"
                )
                LOGGER.warning(msg.format(", ".join(reserved), path))
                return None

        if manifest.get("tmdb_type", None) not in settings.allowed_manifest_types:
            msg = (
                "JSON Manifest is missing the required 'tmdb_type' field: {}"
            )
            LOGGER.warning(msg.format(path))
            return None

        return manifest


@dataclass
class DirectoryInformation(BaseInformation):
    """
    Model for directory information.

    NOTE: 'children_files' attribute has been renamed to 'medias'.

    .. Note: ::
        Deovi store information per directory even if each media can have some data in
        another model, so the directory information is crucial.

        This is not to be mistaken with the Manifest file stored in directory which only
        expose the data that will be computed by Deovi.

    Keyword Arguments:
        directories (list): List of DirectoryInformation objects that belong to this
            directory object.
        medias (list): List of MediaInformation objects that belong to this
            directory object.
    """
    directories: list[Any] = dataclasses_field(default_factory=list)
    medias: list[Any] = dataclasses_field(default_factory=list)

    def __post_init__(self, basepath, autoload, autochecksum, cover_extensions):
        super().__post_init__(basepath, autoload, autochecksum, cover_extensions)

        # Automatically link sub objects relations
        self.set_medias(self.medias, from_init=True)
        self.set_directories(self.directories, from_init=True)

    def set_checksum(self):
        """
        Directory checksum is a computation of its field values.
        Build the checksum of the file content and set it onto object attribute.

        TODO:
            The JSON payload need to convert Asset to source string, clean manifest ?
            clean media files ? ignore parent ? etc..

            We need to ensure this is working well in model test.
        """
        self.checksum = self.get_content_checksum(self.as_json())

        return self.checksum

    def can_be_scrapped(self):
        """
        Describe if possible manifest can be scrapped or not
        """
        if self.manifest and self.manifest.can_be_scrapped:
            return True

        return False

    def set_medias(self, medias, from_init=False):
        """
        Append media file to directory medias while linking them to this directory
        object.

        This is the recommended method to add media else you will have to perform
        addition and linking yourself.

        Arguments:
            medias (list): List of MediaInformation objects.

        Keyword Arguments:
            from_init (bool): If true this will not append objects to
                ``medias`` attribute. This is only useful when calling this
                method from class init and avoid recursion. Default value is false.
        """
        for item in medias:
            item.parent = self

        if not from_init:
            self.medias.extend(medias)

    def set_directories(self, directories, from_init=False):
        """
        Append directories to this directory object children while linking them to this
        directory object.

        This is the recommended method to add directories else you will have to perform
        addition and linking yourself.

        Arguments:
            directories (list): List of MediaInformation objects.

        Keyword Arguments:
            from_init (bool): If true this will not append objects to
                ``directories`` attribute. This is only useful when calling this
                method from class init and avoid recursion. Default value is false.
        """
        for item in directories:
            item.parent = self

        if not from_init:
            self.directories.extend(directories)

    def discover_manifest(self, cover_extensions=None):
        """
        The manifest file is expected to be just named ``manifest.json`` or
        ``manifest.yaml`` and in the directory itself (search won't go down through the
        directory tree), eg: ::

            /foo/
            /foo/manifest.json
            /foo/bar/
            /foo/bar/manifest.json

        JSON format has highest priority and YAML is only searched if there was no
        valid JSON manifest found.

        Returns:
            dict:
        """
        discovered_path = None
        data = None

        if (self.path / "manifest.json").exists():
            discovered_path = self.path / "manifest.json"
            data = self.get_json_manifest(discovered_path)

        if not data and (self.path / "manifest.yaml").exists():
            discovered_path = self.path / "manifest.yaml"
            data = self.get_yaml_manifest(discovered_path)

        return self.load_manifest(discovered_path, data, cover_extensions=cover_extensions)


@dataclass
class MediaInformation(BaseInformation):
    """
    Model for a media file information.

    NOTE: 'directory' attribute has been renamed to 'name_alt'.
    TODO: Finally 'name_alt' should be named 'dir_altname'.

    Attributes:
        EXPORT_PRIVATES (list): List of strings for field names that won't be exported
            from ``as_dict`` and ``as_json`` methods.

    Keyword Arguments:
        name_alt (str): The parent directory name but with an empty string instead of
            the basepath dirname when the file is at basepath root.
        extension (str): The file extension without leading dot. Computed automatically
            from given path.
        container (str): The media container name, like ``MPEG-4`` for ``mp4``.
            Computed automatically from settings if not given, this is recommended.
    """
    name_alt: str = None
    extension: str = None
    container: str = None

    def __post_init__(self, basepath, autoload, autochecksum, cover_extensions):
        super().__post_init__(basepath, autoload, autochecksum, cover_extensions)

        if not self.name_alt:
            self.name_alt = (
                ""
                if self.path.parent.name == basepath.name
                else self.path.parent.name
            )

        self.extension = self.path.suffix[1:].lower()

        # Get the media container label from file extension
        self.container = (
            settings.medias_containers[self.extension]
            if self.extension in settings.medias_containers
            else settings.default_container_name
        )

    def compute_relative_dir(self, path, basepath):
        """
        Media file relative directory has to be base on its parent directory instead
        of its own file path.
        """
        return super().compute_relative_dir(path.parent, basepath)

    def discover_manifest(self, cover_extensions=None):
        """
        The manifest file is expected to have the same filename that the media file
        but with extension replaced with either ``json`` or ``yaml`` and the manifest
        file must be located alongside the media file (in the same directory), eg: ::

            /foo.mp4
            /foo.json
            /bar.ping.avi
            /bar.ping.json

        JSON format has highest priority and YAML is only searched if there was no
        valid JSON manifest found.

        Returns:
            dict:
        """
        discovered_path = None
        data = None

        if (self.path.with_suffix(".json")).exists():
            discovered_path = self.path.with_suffix(".json")
            data = self.get_json_manifest(discovered_path)

        if not data and (self.path.with_suffix(".yaml")).exists():
            discovered_path = self.path.with_suffix(".yaml")
            data = self.get_yaml_manifest(discovered_path)

        return self.load_manifest(
            discovered_path,
            data,
            cover_extensions=cover_extensions
        )
