import requests
import shutil
from pathlib import Path

from deepdiff import DeepDiff

from tmdbv3api import Configuration, TMDb, TV

import yaml


class TmdbScrapper:
    """
    Class to scrap informations from TMDb API.

    Arguments:
        api_key (string): Private key needed to use API.

    Keyword Arguments:
        language (string): Used language for payload content.
        poster_size (string): Size name as supported from TMDb API.
        poster_filename (string): Filename to use to write download poster image,
            without any extension.
        dry (boolean): If enabled nothing will be written or removed.
    """
    def __init__(self, api_key, language="fr", poster_size="w780",
                 poster_filename="cover", dry=False):
        self.dry = dry
        self.poster_size = poster_size
        self.poster_filename = poster_filename

        # Set TMDb client options
        self.client = self.get_client(api_key, language)

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
        _api_configuration = Configuration()
        _api_infos = _api_configuration.info()

        # Entry point from TMDb API to download medias
        self.secure_base_url = _api_infos.images["secure_base_url"]

    def get_provider(self):
        """
        Shortcut to get the TV provider object from API client.
        """
        return TV()

    def get_poster_url(self, path):
        """
        Build URL to download poster image from API using its entrypoint and size
        """
        return "".join([
            self.secure_base_url,
            self.poster_size,
            path
        ])

    def serialize_tv_payload(self, provider, tv_id):
        """
        Get informations payload for given TV ID.
        """
        # Fetch payload from API
        payload = provider.details(tv_id)

        # print()
        # print("- id:", tv_id)
        # print("- name:", payload.name)
        # print("- status:", payload.status)
        # print("- episode_run_time:", payload.episode_run_time)
        # print("- first_air_date:", payload.first_air_date)
        # print("- number_of_episodes:", payload.number_of_episodes)
        # print("- number_of_seasons:", payload.number_of_seasons)
        # print("- poster_path:", payload.poster_path)
        # print("- genres:", [item["name"] for item in payload.genres])
        # print("- poster_url:", self.get_poster_url(payload.poster_path))

        return {
            "tmdb_id": tv_id,
            "tmdb_type": "tv",
            "title": payload.name,
            "status": payload.status,
            "poster_path": payload.poster_path,
            "first_air_date": payload.first_air_date,
            "number_of_seasons": payload.number_of_seasons,
            "number_of_episodes": payload.number_of_episodes,
            "genres": [item["name"] for item in payload.genres],
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
            sourcepath.write_text(
                yaml.dump(data, Dumper=yaml.Dumper)
            )

        return diff_lines

    def fetch_tv(self, directory, tv_id, write_diff=False):
        """
        Get informations payload and medias for given TV ID.

        This downloads media files and build a YAML manifest to the given directory.
        """
        provider = self.get_provider()

        # Fetch and serialize TV show informations
        data = self.serialize_tv_payload(provider, tv_id)

        # Download possible poster image file in destination directory
        fetched_poster = None
        if data.get("poster_path", None):
            poster_path = data.pop("poster_path")
            fetched_poster = self.fetch_poster(poster_path, directory)

        # Build YAML manifest file to destination directory
        manifest = directory / "manifest.yaml"
        diff = self.write_manifest(manifest, data, write_diff=write_diff)

        return (
            data,
            manifest,
            fetched_poster,
            diff,
        )
