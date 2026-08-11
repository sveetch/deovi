import json
import logging
import requests
import shutil
from collections import defaultdict
from pathlib import Path

from deepdiff import DeepDiff

from tmdbv3api import Configuration, TMDb, TV, Movie

import yaml

from .models import MovieManifest, SerieManifest
from .models.mixins.loader import ManifestLoaderMixin
from .utils.jsons import ExtendedJsonEncoder


class TmdbScrapper:
    """
    Class to scrap informations from TMDb API.

    .. Note::
        The scrapper is not aware of any custom Manifest variables to
        remember when overwriting an existing manifest. If original manifest was
        storing one or many custom Manifest variables that are not in API payload
        they will be lost on update.

        Actually in practice this is not a subject of concern because manifest model
        don't have 'non-payload' variables to keep persistent.

    Attributes:
        DEFAULT_LANGUAGE (string): Default value for ``language`` argument.
        DEFAULT_POSTER_SIZE (string): Default value for ``poster_size`` argument.
        DEFAULT_MANIFEST_FORMAT (string): Default value for ``manifest_format``
            argument.

    Arguments:
        api_key (string): Private key needed to use API.

    Keyword Arguments:
        language (string): Used language for payload content.
        poster_size (string): Size name as supported from TMDb API.
        manifest_format (string): Manifest file format to use for creation. Note than
            method ``fetch_all_from_manifests`` will prefer to re use the same format
            for existing ones.
        dry (boolean): If enabled nothing will be written or removed. The JSON payload
            from the ``debug`` is always written no matter of the dry option.
        debug (boolean): If enabled the fetched payload from TmdbScrapper (not to
            confuse with the real TMDB payload) is saved on disk in a JSON file named
            after the media tmdb_id, file is saved in the current working directory.
    """
    # TODO: Most of these attrs should come from settings
    DEFAULT_LANGUAGE = "fr"
    DEFAULT_POSTER_SIZE = "w780"
    DEFAULT_MANIFEST_FORMAT = "yaml"

    def __init__(self, api_key, language=None, poster_size=None,
                 manifest_format=None, dry=False, debug=False):
        self.dry = dry
        self.debug = debug
        self.poster_size = poster_size or self.DEFAULT_POSTER_SIZE
        self.manifest_format = manifest_format or self.DEFAULT_MANIFEST_FORMAT
        self.logger = logging.getLogger("deovi")

        # Set TMDb client options
        self.client = self.get_client(api_key, (language or self.DEFAULT_LANGUAGE))

        # Get some config attributes from API
        self.get_api_configurations()

    def get_client(self, api_key, language):
        """
        Get client and set some options
        """
        # Set TMDb client
        tmdb = TMDb()
        tmdb.api_key = api_key
        tmdb.language = language
        tmdb.debug = True

        return tmdb

    def get_api_configurations(self):
        """
        Get configuration options returned by API

        This can only be done once the client has been initialized.
        """
        _api_infos = Configuration().api_configuration()

        # Entry point from TMDb API to download medias
        self.secure_base_url = _api_infos.images["secure_base_url"]

    def get_poster_url(self, path):
        """
        Build URL to download poster image from API using its entrypoint and size
        """
        return "".join([
            self.secure_base_url,
            self.poster_size,
            path
        ])

    def store_debug_payload(self, tmdb_id, payload):
        """
        Store fetched payload from TmdbScrapper as a JSON file in current working
        directory, the file will be named with its TMDB ID.

        This is mostly for debug purpose and to enable manually in code when needed.
        """
        path = Path("fetch_samples/{}.json".format(tmdb_id))
        path.write_text(
            json.dumps(payload, indent=4, cls=ExtendedJsonEncoder)
        )
        return path

    def serialize_tv_payload(self, tmdb_id):
        """
        Get informations payload for given TV ID.

        Included list values are sorted to help enforcing some stability.

        Arguments:
            tmdb_id (integer): The TMDB ID of the serie to get.

        Returns:
            dict: Serialized payload, not all content from TMDB API are serialized,
            only the ones we support.
        """
        # Fetch payload from API
        payload = TV().details(tmdb_id)

        if self.debug:
            self.store_debug_payload(tmdb_id, payload)

        return {
            "tmdb_id": tmdb_id,
            "tmdb_type": "tv",
            "title": payload.name,
            "status": payload.status,
            "poster_path": payload.poster_path,
            "first_air_date": payload.first_air_date,
            "number_of_seasons": payload.number_of_seasons,
            "number_of_episodes": payload.number_of_episodes,
            "original_language": payload.original_language,
            "overview": payload.overview,
            "genres": sorted([
                item["name"]
                for item in payload.genres
            ]),
            "casting": sorted([
                [item["name"], item["character"]]
                for item in payload.credits.cast
            ]),
            "crew": sorted([
                [item["name"], item["job"]]
                for item in payload.credits.crew
            ]),
        }

    def serialize_movie_payload(self, tmdb_id):
        """
        Get informations payload for given MOVIE ID.

        Included list values are sorted to help enforcing some stability.

        Arguments:
            tmdb_id (integer): The TMDB ID of the movie to get.

        Returns:
            dict: Serialized payload, not all content from TMDB API are serialized,
            only the ones we support.
        """
        # Fetch payload from API
        payload = Movie().details(tmdb_id)

        if self.debug:
            self.store_debug_payload(tmdb_id, payload)

        return {
            "tmdb_id": tmdb_id,
            "tmdb_type": "movie",
            "title": payload.title,
            "status": payload.status,
            "poster_path": payload.poster_path,
            "release_date": payload.release_date,
            "original_language": payload.original_language,
            "overview": payload.overview,
            "genres": sorted([
                item["name"]
                for item in payload.genres
            ]),
            "casting": sorted([
                [item["name"], item["character"]]
                for item in payload.casts.cast
            ]),
            "crew": sorted([
                [item["name"], item["job"]]
                for item in payload.casts.crew
            ]),
        }

    def find_elligible_manifest_file(self, basedir):
        """
        Recursively find all manifest files from a directory.

        We start to search for every JSON or YAML files, group them on their filepath
        without extension, then for each group we try to validate firstly the JSON one
        and validation fails we try the YAML one.

        During validation the manifest content is deserialized into a manifest model.

        Arguments:
            basedir (Path): Where to search for manifests.

        Returns:
            dict: All found elligible manifest file grouped by their branch (meaning
                the full filepath without the file extension).
        """
        branches = defaultdict(list)

        # Group found files per branch
        # Order of collect per extension will be the priority order for file processing
        # so here the JSON is the priority format.
        for v in list(basedir.rglob("*.json")) + list(basedir.rglob("*.yaml")):
            branch = str(v.parent / v.stem)
            branches[branch].append(v)

        return branches

    def load_original_manifests(self, branches):
        """
        Retrieve all valid manifests from branches.

        * In a branch, the first valid manifest file win;
        * An invalid manifest is ignored and a possible following one will be loaded (if
          valid);
        * 'locked' option only ignore the current file item, not the branch, other
          elligible manifest in a branch may be considered as valid;

        Arguments:
            branches (dict): A dictionnary in format returned by
                ``find_elligible_manifest_file``.

        Returns:
            list: List of manifest model objects.
        """
        manifests = []

        loader = ManifestLoaderMixin()

        self.logger.info("Validating manifests")

        for branch, files in branches.items():
            # Try each file from branch
            for fileitem in files:
                data = None

                # Load format from file extension
                if fileitem.suffix == ".json":
                    data = loader.get_json_manifest(fileitem)

                elif fileitem.suffix == ".yaml":
                    data = loader.get_yaml_manifest(fileitem)

                else:
                    raise NotImplementedError("Unsupported format extension: {}".format(
                        fileitem.suffix
                    ))

                # Try to load current file as a manifest model
                manifest = loader.load_manifest(
                    fileitem,
                    data,
                    cover_extensions=[],
                    autochecksum=False,
                )

                # output a debug log for locked manifest
                if (
                    manifest
                    and manifest.locked is not True
                ):
                    msg = (
                        "Ignored manifest because it is locked: {}"
                    )
                    self.logger.debug(msg.format(manifest.path))

                # Only valid manifests, unlocked and not a collection are scrapped
                if (
                    manifest
                    and manifest.locked is not True
                    and manifest.tmdb_id is not None
                    and manifest.tmdb_type != "collection"
                ):
                    manifests.append(manifest)
                    # Store the first valid one and ignore the latter ones
                    break

        return manifests

    def fetch_poster(self, manifest, url):
        """
        Download poster from given url path and write it to basepath destination.

        Arguments:
            manifest (MovieManifest, SerieManifest): The related manifest object.
            url (string): URL of the cover image file to download.

        Returns:
            Path: The path of the downloaded image file.
        """
        # NOTE: Manifest models could include a dedicated method to return just the
        # cover filename
        if manifest.tmdb_type == "movie":
            filename = manifest.path.stem
        else:
            filename = "cover"

        url = self.get_poster_url(url)
        extension = Path(
            url.split("/")[-1]
        ).suffix

        destination = manifest.path.parent / (filename + extension)

        # Download image file
        with requests.get(url, stream=True) as r:
            if not self.dry:
                # Write file from stream
                with open(destination, "wb") as f:
                    shutil.copyfileobj(r.raw, f)

        return destination

    def write_manifest_data(self, manifest, original=None, write_diff=False):
        """
        Write given data to a manifest file and possibly create a log of differences
        with possible original (previous) manifest.

        Arguments:
            manifest (MovieManifest, SerieManifest): The manifest object to write.

        Keyword Arguments:
            original (dict): A dictionnary for original manifest exported. This is
                only used if given manifest file exists (assumed it is the current
                original).
            write_diff (bool): Enable creation of difference file between possible
                original data and fetched data.

        Returns:
            list: List of difference logs if there was some.
        """
        diff_lines = []
        original = original or {}

        new_data = json.loads(manifest.as_json())

        # Only compare differences if there was an existing original manifest file
        if manifest.path.exists():
            diffs = DeepDiff(original, new_data)
            diff_lines = diffs.pretty().splitlines()

            # If there are some diff, we are not in dry mode and writing diff is enabled
            if write_diff and not self.dry and diff_lines:
                diffpath = manifest.path.with_suffix(".diff.txt")
                diffpath.write_text("\n".join(diff_lines))

        # Write or overwrite manifest
        if not self.dry:
            # Create missing directory if needed
            if not manifest.path.parent.exists():
                manifest.path.parent.mkdir()

            # Serialize to the right format
            if manifest.path.suffix == ".json":
                manifest.path.write_text(json.dumps(new_data, indent=4))

            elif manifest.path.suffix == ".yaml":
                manifest.path.write_text(
                    yaml.dump(new_data, Dumper=yaml.Dumper)
                )

        return diff_lines

    def process_manifest(self, manifest, write_diff=False):
        """
        Get informations payload and images for given TMDB ID.

        This downloads images files and build a manifest to the given directory.

        NOTE:
            New method to scrap an item on TMDB ID, once finished 'fetch_media' should
            use it or be totally deprecated.

            This one stands only on manifest model. 'fetch_media' would need to craft
            a dummy manifest before using 'process_manifest'.

        Arguments:
            manifest (MovieManifest, SerieManifest): The manifest object where to get
                the TMDB type and ID, also its path will be used to write manifest file.

        Keyword Arguments:
            write_diff (bool): Enable creation of difference file between possible
                original data and fetched data.

        Returns:
            tuple:
        """
        original_data = json.loads(manifest.as_json())

        # Fetch and serialize media informations
        if manifest.tmdb_type == "tv":
            data = self.serialize_tv_payload(manifest.tmdb_id)
        elif manifest.tmdb_type == "movie":
            data = self.serialize_movie_payload(manifest.tmdb_id)
        else:
            raise NotImplementedError("Given 'tmdb_type' is not implemented: {}".format(
                manifest.tmdb_type
            ))

        # Update manifest object with serialized data
        for k, v in data.items():
            setattr(manifest, k, v)

        # Download possible cover image file in destination directory
        if data.get("poster_path", None):
            cover_filepath = self.fetch_poster(manifest, data.pop("poster_path"))
            manifest.cover = cover_filepath.name

        diff = self.write_manifest_data(
            manifest,
            original=original_data,
            write_diff=write_diff,
        )

        return (manifest, diff)

    def fetch_media(self, destination, tmdb_id, tmdb_type="tv", filename=None,
                    write_diff=False):
        """
        Get information and cover for given TMDB ID an type.

        TODO: Rename to 'fetch_from_id'.

        Arguments:
            destination (Path): Directory path where to write manifest and possible
                cover files.
            tmdb_id (string):

        Keyword Arguments:
            tmdb_type (string):
            filename (Path): A file path to use to define a custom manifest filename.
                It can be relative path, absolute or even a simple filename. Commonly
                this should only be used for a Movie.
            write_diff (bool): Enable creation of difference file between possible
                original data and fetched data.

        Returns:
            tuple: The manifest object and list of differences (if enabled).
        """
        if tmdb_type == "tv":
            model = SerieManifest
        elif tmdb_type == "movie":
            model = MovieManifest
        else:
            raise NotImplementedError("Given 'tmdb_type' is not implemented: {}".format(
                tmdb_type
            ))

        # Build manifest
        filename = filename.stem if filename else "manifest"
        manifest_path = destination / "{}.{}".format(filename, self.manifest_format)
        manifest = model(path=manifest_path, tmdb_id=tmdb_id)

        manifest, diff = self.process_manifest(manifest, write_diff=write_diff)

        return (manifest, diff)

    def fetch_all_from_manifests(self, basedir, write_diff=False):
        """
        Get information from TMDB for all manifests.

        TODO: Rename to 'fetch_from_manifests'.

        Arguments:
            basedir (Path): Where to search for manifests.

        Keyword Arguments:
            write_diff (bool): Enable creation of difference file between possible
                original data and fetched data for each manifest.

        Returns:
            list: List of processed items. Each item is a tuple with the manifest
                object and list of differences (if enabled).
        """

        branches = self.find_elligible_manifest_file(basedir)

        manifests = self.load_original_manifests(branches)

        return [
            self.process_manifest(manifest, write_diff=write_diff)
            for manifest in manifests
        ]
