"""
Pytest fixtures
"""
import shutil
from pathlib import Path

import pytest

import deovi
from deovi.logger import init_logger
from deovi.renamer.tasks import TaskMaster
from deovi.scrapper import TmdbScrapper

from tests.utils import get_tmdbapi_key


class FixturesSettingsTestMixin(object):
    """
    A mixin containing settings about application. This is almost about useful
    paths which may be used in tests.

    Attributes:
        application_path (str): Absolute path to the application directory.
        package_path (str): Absolute path to the package directory.
        tests_dir (str): Directory name which include tests.
        tests_path (str): Absolute path to the tests directory.
        datas_dir (str): Directory name which include tests datas.
        datas_path (str): Absolute path to the tests datas.
    """
    def __init__(self):
        self.application_path = Path(
            deovi.__file__
        ).parents[0].resolve()

        self.package_path = self.application_path.parent

        self.tests_dir = "tests"
        self.tests_path = self.package_path / self.tests_dir

        self.datas_dir = "data_fixtures"
        self.datas_path = self.tests_path / self.datas_dir

    def format(self, content):
        """
        Format given string to include some values related to this application.

        Arguments:
            content (str): Content string to format with possible values.

        Returns:
            str: Given string formatted with possible values.
        """
        return content.format(
            HOMEDIR=Path.home(),
            PACKAGE=str(self.package_path),
            APPLICATION=str(self.application_path),
            TESTS=str(self.tests_path),
            DATAS=str(self.datas_path),
            VERSION=deovi.__version__,
        )

    def tmdbapi_key(self):
        """
        Get TMDb API key retrieved from file ``tmdb-api-key.txt`` at this project
        root.

        Returns:
            string: Either the API key found from file if it exists else return
            None.
        """
        return get_tmdbapi_key()


@pytest.fixture(scope="function")
def temp_builds_dir(tmp_path):
    """
    Prepare a temporary build directory.

    DEPRECATED: You should use instead directly the "tmp_path" fixture in your tests.
    """
    return tmp_path


@pytest.fixture(scope="module")
def settings():
    """
    Initialize and return settings for tests.

    Example:
        You may use it like: ::

            def test_foo(settings):
                print(settings.package_path)
                print(settings.format("foo: {VERSION}"))
    """
    return FixturesSettingsTestMixin()


@pytest.fixture(scope="function")
def basic_sample(tmp_path, settings):
    """
    Copy the "basic sample" structure into a temporary directory.

    Returns:
        Path: The path to the copied structure in temp directory.
    """
    sample_dirname = "basic_sample"
    basic_sample_path = settings.datas_path / sample_dirname
    destination = tmp_path / sample_dirname

    shutil.copytree(basic_sample_path, destination)

    return destination


@pytest.fixture(scope="function")
def basic_suite(tmp_path, settings):
    """
    Copy the "basic_suite" structure into a temporary directory.

    Returns:
        Path: The path to the copied structure in temp directory.
    """
    sample_dirname = "basic_suite"
    basic_sample_path = settings.datas_path / sample_dirname
    destination = tmp_path / sample_dirname

    shutil.copytree(basic_sample_path, destination)

    return destination


@pytest.fixture(scope="function")
def various_filenames(tmp_path, settings):
    """
    Copy the "various_filenames" structure into a temporary directory.

    Returns:
        Path: The path to the copied structure in temp directory.
    """
    sample_dirname = "various_filenames"
    basic_sample_path = settings.datas_path / sample_dirname
    destination = tmp_path / sample_dirname

    shutil.copytree(basic_sample_path, destination)

    return destination


@pytest.fixture(scope="function")
def media_sample(tmp_path, settings):
    """
    Copy the "media_sample" structure into a temporary directory.

    Returns:
        Path: The path to the copied structure in temp directory.
    """
    sample_dirname = "media_sample"
    basic_sample_path = settings.datas_path / sample_dirname
    destination = tmp_path / sample_dirname

    shutil.copytree(basic_sample_path, destination)

    return destination


@pytest.fixture(scope="function")
def manifests_sample(tmp_path, settings):
    """
    Copy the "manifests" structure into a temporary directory.

    Returns:
        Path: The path to the copied structure in temp directory.
    """
    sample_dirname = "manifests"
    basic_sample_path = settings.datas_path / sample_dirname
    destination = tmp_path / sample_dirname

    shutil.copytree(basic_sample_path, destination)

    return destination


@pytest.fixture(scope="function")
def debug_logger():
    """
    Init the logger config at debug level.
    """
    return init_logger(
        "deovi",
        "DEBUG",
        printout=False,
    )


@pytest.fixture(scope="function")
def info_logger():
    """
    Init the logger config at info level.
    """
    return init_logger(
        "deovi",
        "INFO",
        printout=False,
    )


@pytest.fixture(scope="function")
def warning_logger():
    """
    Init the logger config at warning level.
    """
    return init_logger(
        "deovi",
        "WARNING",
        printout=False,
    )


@pytest.fixture(scope="function")
def task_manager():
    """
    Return initialized task manager
    """
    return TaskMaster()


@pytest.fixture(scope="function")
def disable_api(monkeypatch):
    """
    Fixture function to disable all method that would involves API or requests
    """
    def dummy_client(cls, *args, **kwargs):
        # No client object needed
        return None

    def dummy_configurations(cls):
        # Dummy media URL
        cls.secure_base_url = "nope://niet/"

    def dummy_poster(cls, *args, **kwargs):
        # Dummy poster path
        manifest, url = args
        if manifest.tmdb_type == "movie":
            return Path("/nope/niet/dummy_movie-cover.png")
        elif manifest.tmdb_type == "tv":
            return Path("/nope/niet/dummy_serie-cover.png")
        else:
            return None

    def dummy_tv_payload(cls, *args, **kwargs):
        """
        Return a dummy payload for a serie manifest.
        """
        return {
            "title": "changed-serie",
            "poster_path": "serie-cover.png",
            "bonus": "yep",
        }

    def dummy_movie_payload(cls, *args, **kwargs):
        # Return a dummy payload for a movie manifest
        return {
            "title": "changed-movie",
            "poster_path": "movie-cover.png",
            "bonus": "yep",
        }

    monkeypatch.setattr(TmdbScrapper, "get_client", dummy_client)
    monkeypatch.setattr(TmdbScrapper, "get_api_configurations", dummy_configurations)
    monkeypatch.setattr(TmdbScrapper, "fetch_poster", dummy_poster)
    monkeypatch.setattr(TmdbScrapper, "serialize_tv_payload", dummy_tv_payload)
    monkeypatch.setattr(TmdbScrapper, "serialize_movie_payload", dummy_movie_payload)
