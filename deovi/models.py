"""
TODO: Models here have been made to replace some code in collector and scrapper.
Once working code refactorizing for model implementation should start.

NOTE: Models should not include processing operation methods like file reading, file
stats, file existence, etc.. except for manifest discovering/loading/parsing
"""
import datetime
import json
import logging
from pathlib import Path
from dataclasses import (
    dataclass,
    field as dataclasses_field,
    fields as dataclasses_fields,
    InitVar,
)
from typing import Any, ClassVar, Union

import yaml

from . import __pkgname__
from .conf import settings
from .exceptions import InformationModelError
from .utils.jsons import ExtendedJsonEncoder


LOGGER = logging.getLogger(__pkgname__)


@dataclass
class BaseManifest:
    """
    Base model for manifest models includes all common fields for all manifest models.

    These fields are largely inspired after the TMDB API ones plus some others for
    Deovi usage.

    Attributes:
        EXPORT_PRIVATES (list): List of strings for field names that won't be exported
            from ``as_dict`` and ``as_json`` methods. If you have recursive parenting
            you should care of this field.

    Arguments:
        path (pathlib.Path): Absolute path of manifest file.

    Keyword Arguments:
        parent (DirectoryInformation or MediaInformation): Directory object which this
            object belong to.
        tmdb_id (str): The identifier from TMDB allow to scrap metadata from its API.
            Without this identifier, the metadata in this manifest will be used but
            there won't be any update possible from TMDB.
        tmdb_type (str): Mandatory if tmdb_id is filled, it should be "tv" or "movie",
            any other value is not compatible with TMDB scrapping.
        title (str): The media display title.
        overview (str):
        cover (Path): Path to the cover image file.
        status (str): Airing/Release status.
        original_language (str): The original language of this media.
        casting (list):
        crew (list):
        genres (list): List of genre names.
        locked (bool): If enabled, even with a proper TMDB id and type there won't be
            any scrapping. This is to be used on media you already got enough metadata
            in this manifest and you don't want to be update from TMDB.
    """
    EXPORT_PRIVATES: ClassVar[list[str]] = ["parent"]
    path: Path
    parent: Any = None
    tmdb_id: int = None
    tmdb_type: str = None
    locked: bool = False
    title: str = None
    overview: str = None
    status: str = None
    original_language: str = None
    cover: Path = None
    casting: list[list] = dataclasses_field(default_factory=list)
    crew: list[list] = dataclasses_field(default_factory=list)
    genres: list[str] = dataclasses_field(default_factory=list)

    def __post_init__(self):
        if not self.title:
            self.title = self.path.name

    def as_dict(self):
        """
        A safe way to convert to a dict without recursion issues.

        Returns:
            dict: This model object attribute serialized in a dictionnary, items named
                after one of names from EXPORT_PRIVATES won't be in the output.
        """
        return {
            f.name: getattr(self, f.name)
            for f in dataclasses_fields(self)
            if f.name not in self.EXPORT_PRIVATES
        }

    def as_json(self):
        return json.dumps(self.as_dict(), indent=4, cls=ExtendedJsonEncoder)

    def can_be_scrapped(self):
        """
        Describe if this manifest can be scrapped or not
        """
        if self.tmdb_id and not self.locked:
            return True

        return False


@dataclass
class SerieManifest(BaseManifest):
    """
    A metadata manifest for a TV show.

    This is metadata for a serie of episodes within a season.
    """
    first_air_date: str = ""
    number_of_seasons: int = None
    number_of_episodes: int = None

    def __post_init__(self):
        super().__post_init__()

        self.tmdb_type = "tv"


@dataclass
class MovieManifest(BaseManifest):
    """
    A metadata manifest for a Movie.

    This is metadata for a single movie.
    """
    release_date: str = ""

    def __post_init__(self):
        super().__post_init__()

        self.tmdb_type = "movie"


@dataclass
class CollectionManifest(BaseManifest):
    """
    A metadata manifest for a collection of movies.

    This is metadata about a serie of movies.

    .. Note: ::
        This uses the tmdb_type ``collection`` but it won't involves any scrapping
        because there is not so much collections on TMDB. It will be instead to be
        filled manually only, helping to describe a saga.

    Keyword Arguments:
        movies (list): List of MovieManifest objects that belong to this
            collection object.
    """
    movies: list[MovieManifest] = dataclasses_field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()

        self.tmdb_type = "collection"

        # Automatically link sub objects relations
        self.set_movies(self.movies, from_init=True)

    def set_movies(self, movies, from_init=False):
        """
        Append movie to collection while linking them to this collection object.

        This is the recommended method to add movies else you will have to perform
        addition and linking yourself.

        Arguments:
            movies (list): List of MovieManifest objects.

        Keyword Arguments:
            from_init (bool): If true this will not append objects to
                ``movies`` attribute. This is only useful when calling this
                method from class init and avoid recursion. Default value is false.
        """
        for item in movies:
            item.parent = self

        if not from_init:
            self.movies.extend(movies)


@dataclass
class BaseInformation:
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
        autoload (bool): If enabled the model will try to discover and load a manifest
            file related to this object. This is disabled on default. Each model kind
            has its own way to discover a manifest.
        basepath (pathlib.Path): The basepath of this directory
    """
    EXPORT_PRIVATES: ClassVar[list[str]] = ["parent"]
    basepath: InitVar[Path]
    path: Path
    size: int
    mtime: datetime.datetime
    parent: Any = None
    name: str = None
    absolute_dir: Path = None
    relative_dir: Path = None
    manifest: Union[CollectionManifest, MovieManifest, SerieManifest] = None
    autoload: InitVar[bool] = False

    def __post_init__(self, basepath, autoload):
        if not self.name:
            self.name = self.path.name

        if not self.absolute_dir:
            self.absolute_dir = self.path.parents[0]

        if not self.relative_dir:
            self.relative_dir = self.compute_relative_dir(self.path, basepath)

        if autoload and not self.manifest:
            self.manifest = self.discover_manifest()

    def compute_relative_dir(self, path, basepath):
        try:
            relative_dir = path.relative_to(basepath)
        except ValueError:
            msg = "You cannot use a directory which is out of given basepath: {}"
            raise InformationModelError(msg.format(basepath))

        return relative_dir

    def as_dict(self):
        """
        A safe way to convert to a dict without recursion issues.

        Returns:
            dict: This model object attribute serialized in a dictionnary, items named
                after one of names from EXPORT_PRIVATES won't be in the output.
        """
        return {
            f.name: getattr(self, f.name)
            for f in dataclasses_fields(self)
            if f.name not in self.EXPORT_PRIVATES
        }

    def as_json(self):
        return json.dumps(self.as_dict(), indent=4, cls=ExtendedJsonEncoder)

    def discover_manifest(self):
        """
        Discover a possible manifest file matching the expected filename.

        Each manifest model should implement itself its method to discover and load
        a manifest file related to a model object.

        Returns:
            dict: Should return loaded manifest file data. Base implementation just
            returns the result of ``load_manifest`` with an empty value.
        """
        return self.load_manifest(None, None)

    def load_manifest(self, path, data):
        """
        Load manifest payload as a manifest model object.

        The kind of manifest model to be used is guessed from 'tmdb_type'.
        """
        if data:
            manifest_type = data["tmdb_type"]
            print("tmdb_type:", manifest_type)

            if manifest_type == "collection":
                return CollectionManifest(path, **data)
            elif manifest_type == "tv":
                return SerieManifest(path, **data)
            elif manifest_type == "movie":
                return MovieManifest(path, **data)
            else:
                msg = "Manifest type is not supported: {}"
                raise NotImplementedError(msg.format(data.get("tmdb_type")))

            return None

        return None

    def get_yaml_manifest(self, path):
        """
        Open and load a YAML manifest.

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
        checksum (str): Required checksum (long blake2b string).
        directories (list): List of DirectoryInformation objects that belong to this
            directory object.
        medias (list): List of MediaInformation objects that belong to this
            directory object.
    """
    checksum: str = None
    directories: list[Any] = dataclasses_field(default_factory=list)
    medias: list[Any] = dataclasses_field(default_factory=list)

    def __post_init__(self, basepath, autoload):
        super().__post_init__(basepath, autoload)

        # Automatically link sub objects relations
        self.set_medias(self.medias, from_init=True)
        self.set_directories(self.directories, from_init=True)

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

    def discover_manifest(self):
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
            print("📝 discovered_path JSON:", discovered_path, discovered_path.exists())
            data = self.get_json_manifest(discovered_path)
            print(data)

        if not data and (self.path / "manifest.yaml").exists():
            discovered_path = self.path / "manifest.yaml"
            data = self.get_yaml_manifest(discovered_path)

        return self.load_manifest(discovered_path, data)


@dataclass
class MediaInformation(BaseInformation):
    """
    Model for a media file information.

    NOTE: 'directory' attribute has been renamed to 'name_alt'.

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

    def __post_init__(self, basepath, autoload):
        super().__post_init__(basepath, autoload)

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
        return path.parent.relative_to(basepath)

    def discover_manifest(self):
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

        return self.load_manifest(discovered_path, data)
