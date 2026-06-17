import json
import requests
import shutil
from pathlib import Path

from deepdiff import DeepDiff

from tmdbv3api import Configuration, TMDb, TV, Movie

import yaml

from .utils.jsons import ExtendedJsonEncoder


class TmdbScrapper:
    """
    Class to scrap informations from TMDb API.

    Attributes:
        DEFAULT_LANGUAGE (string): Default value for ``language`` argument.
        DEFAULT_POSTER_SIZE (string): Default value for ``poster_size`` argument.
        DEFAULT_POSTER_FILENAME (string): Default value for ``poster_filename``
            argument.
        DEFAULT_MANIFEST_FORMAT (string): Default value for ``manifest_format``
            argument.

    Arguments:
        api_key (string): Private key needed to use API.

    Keyword Arguments:
        language (string): Used language for payload content.
        poster_size (string): Size name as supported from TMDb API.
        poster_filename (string): Filename to use to write download poster image,
            without any extension.
        dry (boolean): If enabled nothing will be written or removed. The JSON payload
            from the ``debug`` is always written no matter of the dry option.
        debug (boolean): If enabled the fetched payload from TmdbScrapper (not to
            confuse with the real TMDB payload) is saved on disk in a JSON file named
            after the media tmdb_id, file is saved in the current working directory.
    """
    DEFAULT_LANGUAGE = "fr"
    DEFAULT_POSTER_SIZE = "w780"
    DEFAULT_POSTER_FILENAME = "cover"
    DEFAULT_MANIFEST_FORMAT = "yaml"

    def __init__(self, api_key, language=None, poster_size=None,
                 poster_filename=None, manifest_format=None, dry=False, debug=False):
        self.dry = dry
        self.debug = debug
        self.poster_size = poster_size or self.DEFAULT_POSTER_SIZE
        self.poster_filename = poster_filename or self.DEFAULT_POSTER_FILENAME
        self.manifest_format = manifest_format or self.DEFAULT_MANIFEST_FORMAT

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
            "genres": [item["name"] for item in payload.genres],
            "casting": [
                [item["name"], item["character"]] for item in payload.credits.cast
            ],
            "crew": [
                [item["name"], item["job"]] for item in payload.credits.crew
            ],
        }

    def serialize_movie_payload(self, tmdb_id):
        """
        Get informations payload for given MOVIE ID.
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
            "genres": [item["name"] for item in payload.genres],
            "casting": [
                [item["name"], item["character"]] for item in payload.casts.cast
            ],
            "crew": [
                [item["name"], item["job"]] for item in payload.casts.crew
            ],
        }

    def fetch_poster(self, path, basepath):
        """
        Download poster from given url path and write it to basepath destination.
        """
        basefilepath = basepath / self.poster_filename

        url = self.get_poster_url(path)
        extension = Path(
            url.split("/")[-1]
        ).suffix

        destination = basefilepath.with_suffix(extension)

        # Go download the file
        with requests.get(url, stream=True) as r:
            if not self.dry:
                # Create destination directory if missing
                if not basepath.exists():
                    basepath.mkdir(parents=True, exist_ok=True)
                # Write file from stream
                with open(destination, "wb") as f:
                    shutil.copyfileobj(r.raw, f)

        return destination

    def write_manifest(self, sourcepath, data, write_diff=False):
        """
        Write given data to manifest and possibly create a log file about differences
        with previous manifest file if any.
        """
        diff_lines = []

        # Write differences if any
        if sourcepath.exists():
            original = yaml.load(sourcepath.read_text(), Loader=yaml.FullLoader)
            diffs = DeepDiff(original, data)
            diff_lines = diffs.pretty().splitlines()
            if not self.dry and write_diff and diff_lines:
                diffpath = sourcepath.with_suffix(".diff.txt")
                diffpath.write_text("\n".join(diff_lines))

        # Write/overwrite manifest
        if not self.dry:
            if self.manifest_format == "json":
                sourcepath.write_text(json.dumps(data, indent=4))
            else:
                sourcepath.write_text(
                    yaml.dump(data, Dumper=yaml.Dumper)
                )

        return diff_lines

    def fetch_tv(self, directory, tmdb_id, write_diff=False):
        """
        Get informations payload and medias for given TV ID.

        This downloads media files and build a YAML manifest to the given directory.

        DEPRECATED: In profit of 'fetch_media()' for the new scrapper.
        """
        # Fetch and serialize media informations
        data = self.serialize_tv_payload(tmdb_id)

        # Download possible poster image file in destination directory
        fetched_poster = None
        if data.get("poster_path", None):
            poster_path = data.pop("poster_path")
            fetched_poster = self.fetch_poster(poster_path, directory)

        # Build manifest file to destination directory
        if self.manifest_format == "json":
            manifest = directory / "manifest.json"
        else:
            manifest = directory / "manifest.yaml"

        diff = self.write_manifest(manifest, data, write_diff=write_diff)

        return (
            data,
            manifest,
            fetched_poster,
            diff,
        )

    def fetch_media(self, directory, tmdb_id, tmdb_type="tv", write_diff=False):
        """
        Get informations payload and images for given TMDB ID.

        This downloads images files and build a YAML manifest to the given directory.
        """
        # TODO: Here we should open the original manifest (if any) to find the option
        # which would define if the manifest is locked or not. If locked we should not
        # proceed to fetch payload and let the original manifest unchanged.
        # As a sample, the manifest is already opened and parsed from method
        # 'write_manifest()'

        # Fetch and serialize media informations
        if tmdb_type == "tv":
            data = self.serialize_tv_payload(tmdb_id)
        elif tmdb_type == "movie":
            data = self.serialize_movie_payload(tmdb_id)
        else:
            raise NotImplementedError("Given tmdb_type is not implemented: {}".format(
                tmdb_type
            ))

        # Download possible poster image file in destination directory
        fetched_poster = None
        if data.get("poster_path", None):
            poster_path = data.pop("poster_path")
            fetched_poster = self.fetch_poster(poster_path, directory)

        # Build manifest file to destination directory
        if self.manifest_format == "json":
            manifest = directory / "manifest.json"
        else:
            manifest = directory / "manifest.yaml"

        diff = self.write_manifest(manifest, data, write_diff=write_diff)

        return (
            data,
            manifest,
            fetched_poster,
            diff,
        )
