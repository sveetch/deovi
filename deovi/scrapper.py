import json
import time
import requests
import shutil
from pathlib import Path

from tmdbv3api import Configuration, TMDb, TV

import yaml


class TmdbScrapper:
    def __init__(self, api_key, language="fr", poster_size="w780",
                 poster_filename="cover"):
        # Private account key needed to use API
        self.api_key = api_key
        # Used language for payload content
        self.language = language
        # Size name as supported from TMDb API
        self.poster_size = poster_size
        # Filename to use to write download poster image, without any extension
        self.poster_filename = poster_filename

        # Set TMDb client
        tmdb = TMDb()
        tmdb.api_key = self.api_key
        tmdb.language = self.language
        tmdb.debug = True

        # Get some config attributes from API
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

    def serialize_tv_payload(self, provider, directory, tv_id):
        """
        Get informations payload and medias for given TV ID.

        This downloads media files and build a YAML manifest to the given directory.
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
        # print("* destination directory:", directory)

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
            # Create destination directory if missing
            if not basepath.exists():
                basepath.mkdir(parents=True, exist_ok=True)
            # Write file from stream
            with open(destination, "wb") as f:
                shutil.copyfileobj(r.raw, f)

        return destination

    def fetch_tv(self, directory, tv_id):
        """
        Get informations payload and medias for given TV ID.

        This downloads media files and build a YAML manifest to the given directory.
        """
        provider = self.get_provider()

        # Fetch and serialize TV show informations
        data = self.serialize_tv_payload(provider, directory, tv_id)

        # Download possible poster image file in destination directory
        fetched_poster = None
        if data.get("poster_path", None):
            poster_path = data.pop("poster_path")
            fetched_poster = self.fetch_poster(poster_path, directory)
            # print("* Fetched poster:", fetched_poster)

        # Build YAML manifest file to destination directory
        manifest = directory / "manifest.yaml"
        manifest.write_text(
            yaml.dump(data, Dumper=yaml.Dumper)
        )

        return (
            data,
            manifest,
            fetched_poster,
        )


if __name__ == "__main__":
    API_KEY = "c8a1f464dca620cde9037eda3f105425"
    connector = TmdbScrapper(API_KEY, language="fr")

    #connector.serialize_tv_payload(
    connector.fetch_tv(
        Path("/home/emencia/Projects/Apps/deovi/dist/StarTrek_Strange-New-Worlds"),
        "103516"
    )
    connector.fetch_tv(
        Path("/home/emencia/Projects/Apps/deovi/dist/Au dela du reel"),
        "21567"
    )
