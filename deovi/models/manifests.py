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

from .assets import Asset
from ..conf import settings
from ..utils.jsons import ExtendedJsonEncoder
from .. import __pkgname__


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
        status (str): Airing/Release status.
        original_language (str): The original language of this media.
        cover (Asset, Path): Path to the cover image file. This accept a Path object
            but that will be transformed to an Asset object.
        cover_extensions (list): List of allowed file extension such as ``.png`` to
            discover a cover file. No cover will be discovered if this is empty.
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
    cover: Union[Asset, Path] = None
    cover_extensions: InitVar[list] = None
    casting: list[list] = dataclasses_field(default_factory=list)
    crew: list[list] = dataclasses_field(default_factory=list)
    genres: list[str] = dataclasses_field(default_factory=list)

    def __post_init__(self, cover_extensions):
        if not self.title:
            self.title = self.path.name

        #if self.cover and not isinstance(self.cover, Asset):
            #self.cover = Asset(self.cover)

        if not self.cover and cover_extensions:
            self.cover = self.discover_cover(cover_extensions)

    def as_dict(self, preserve=False):
        """
        A safe way to convert to a dict without recursion issues.

        Keyword Arguments:
            preserve (bool): If enabled all values which have the method ``as_dict()``
                will use it instead of returning their object. This is almost only
                implemented internally in Deovi models so you can get an output of
                ``as_dict()`` only with Python builtin types.

        Returns:
            dict: This model object attribute serialized in a dictionnary, items named
                after one of names from EXPORT_PRIVATES won't be in the output.
        """
        return {
            f.name: (
                getattr(self, f.name).as_dict(preserve=preserve)
                if preserve is True and hasattr(getattr(self, f.name), "as_dict")
                else getattr(self, f.name)
            )
            for f in dataclasses_fields(self)
            if f.name not in self.EXPORT_PRIVATES
        }

    def as_json(self):
        """
        Returns the output of ``as_dict()`` in a JSON string.
        """
        return json.dumps(self.as_dict(), indent=4, cls=ExtendedJsonEncoder)

    def can_be_scrapped(self):
        """
        Describe if this manifest can be scrapped or not
        """
        if self.tmdb_id and not self.locked:
            return True

        return False

    def get_cover_holder(self):
        """
        Return the directory path where the cover have to be searched.

        This default implementation search for a cover file in this object path.
        """
        return self.path.parent

    def discover_asset(self, filename_patterns):
        """
        Search for an asset file from allowed filenames.

        The first matching filename an allowed asset filename is returned. Order
        of ``filename_patterns`` defines matching order.

        Arguments:
            filename_patterns (list): A list of strings for asset filenames to search
                in directory.

        Returns:
            tuple: A tuple of two items ``(source, destination)`` where 'source' is the
                source cover file (Path object) resolved to an absolute path
                and 'destination' a filename (Path object) with a uuid4 instead of
                original source file name but with original source file extensions
                keeped.
        """
        # Discover file from possible pattern
        for filename in filename_patterns:
            filepath = self.get_cover_holder() / filename

            # If file matches
            if filepath.exists():
                return Asset(source=filepath.resolve())

        return None

    def discover_cover(self, cover_extensions):
        """
        Discover a possible cover file for allowed extensions.

        This default implementation use the current object path with suffix appended.

        Returns:
            Asset: Asset object if a cover was found. Only the source attribute is
            filled, destination is still empty.
        """
        filename_patterns = [
            self.path.stem + v
            for v in cover_extensions
        ]
        return self.discover_asset(filename_patterns)


@dataclass
class MovieManifest(BaseManifest):
    """
    A metadata manifest for a Movie.

    This is metadata for a single movie.

    Practically this is used for a file.
    """
    release_date: str = ""

    def __post_init__(self, cover_extensions):
        super().__post_init__(cover_extensions)

        self.tmdb_type = "movie"


@dataclass
class SerieManifest(BaseManifest):
    """
    A metadata manifest for a TV show.

    This is metadata for a serie of episodes within a season.

    Practically this is used for a directory.
    """
    first_air_date: str = ""
    number_of_seasons: int = None
    number_of_episodes: int = None

    def __post_init__(self, cover_extensions):
        super().__post_init__(cover_extensions)

        self.tmdb_type = "tv"

    def discover_cover(self, cover_extensions):
        """
        Discover a possible cover file for allowed extensions.

        This implementation use hardcoded value ``cover`` with suffix appended to search
        for a file.

        Returns:
            Asset: Asset object if a cover was found. Only the source attribute is
            filled, destination is still empty.
        """
        filename_patterns = [
            "cover" + v
            for v in cover_extensions
        ]
        foo = self.discover_asset(filename_patterns)
        return foo


@dataclass
class CollectionManifest(BaseManifest):
    """
    A metadata manifest for a collection of movies.

    This is metadata about a serie of movies.

    Practically this is used for a directory.

    .. Note: ::
        This uses the tmdb_type ``collection`` but it won't involves any scrapping
        because there is not so much collections on TMDB. It will be instead to be
        filled manually only, helping to describe a saga.

    Keyword Arguments:
        movies (list): List of MovieManifest objects that belong to this
            collection object.
    """
    movies: list[MovieManifest] = dataclasses_field(default_factory=list)

    def __post_init__(self, cover_extensions):
        super().__post_init__(cover_extensions)

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

    def discover_cover(self, cover_extensions):
        """
        Discover a possible cover file for allowed extensions.

        This implementation use hardcoded value ``cover`` with suffix appended to search
        for a file.

        Returns:
            Asset: Asset object if a cover was found. Only the source attribute is
            filled, destination is still empty.
        """
        filename_patterns = [
            "cover" + v
            for v in cover_extensions
        ]
        return self.discover_asset(filename_patterns)
