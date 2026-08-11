import json
import logging

import yaml

from ... import __pkgname__
from ...conf import settings
from ..manifests import CollectionManifest, MovieManifest, SerieManifest


LOGGER = logging.getLogger(__pkgname__)


class ManifestLoaderMixin:
    def load_manifest(self, path, data, cover_extensions=None, autochecksum=None):
        """
        Load manifest payload as a manifest model object.

        The kind of manifest model to be used is guessed from 'tmdb_type'.
        """
        if data:
            if data["tmdb_type"] == "collection":
                return CollectionManifest(
                    path,
                    cover_extensions=cover_extensions,
                    autochecksum=autochecksum,
                    **data
                )
            elif data["tmdb_type"] == "tv":
                return SerieManifest(
                    path,
                    cover_extensions=cover_extensions,
                    autochecksum=autochecksum,
                    **data
                )
            elif data["tmdb_type"] == "movie":
                return MovieManifest(
                    path,
                    cover_extensions=cover_extensions,
                    autochecksum=autochecksum,
                    **data
                )
            else:
                msg = "Manifest type is not supported: {}"
                raise NotImplementedError(msg.format(data.get("tmdb_type")))

            return None

        return None

    def get_yaml_manifest(self, path):
        """
        Open and load the YAML manifest data.

        It should be safe to run with invalid manifests.

        NOTE: Previously this method was returning a {} if no valid was found/parsed,
        now it returns a None value.

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
            LOGGER.debug(msg.format(path))
            return None
        else:
            # Filter out the forbidden attributes
            manifest = {
                k: v
                for k, v in manifest.items()
                if k not in settings.manifest_forbidden_vars
            }

        if manifest.get("tmdb_type", None) not in settings.allowed_manifest_types:
            msg = (
                "Ignored YAML manifest because it misses the required 'tmdb_type' "
                "field: {}"
            )
            LOGGER.debug(msg.format(path))
            return None

        return manifest

    def get_json_manifest(self, path):
        """
        Open and load the JSON manifest data.

        It should be safe to run with invalid manifests.

        NOTE: Previously this method was returning a {} if no valid was found/parsed,
        now it returns a None value.

        Arguments:
            path (pathlib.Path): The manifest filepath.

        Returns:
            dict: The loaded manifest file data.
        """
        manifest = None

        try:
            manifest = json.loads(path.read_text())
        except json.JSONDecodeError:
            msg = "No JSON object could be decoded from manifest: {}"
            LOGGER.debug(msg.format(path))
            return None
        else:
            # Filter out the forbidden attributes
            manifest = {
                k: v
                for k, v in manifest.items()
                if k not in settings.manifest_forbidden_vars
            }

        if manifest.get("tmdb_type", None) not in settings.allowed_manifest_types:
            msg = (
                "Ignored JSON manifest because it misses the required 'tmdb_type' "
                "field: {}"
            )
            LOGGER.debug(msg.format(path))
            return None

        return manifest
