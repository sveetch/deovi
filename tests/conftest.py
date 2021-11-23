"""
Pytest fixtures
"""
import shutil
from pathlib import Path

import pytest

import deovi_client
from deovi_client.logger import init_logger
from deovi_client.renamer.tasks import TaskMaster


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
            deovi_client.__file__
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
            VERSION=deovi_client.__version__,
        )


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
def debug_logger():
    """
    Init the logger config at debug level.
    """
    return init_logger(
        "deovi-client",
        "DEBUG",
        printout=False,
    )


@pytest.fixture(scope="function")
def info_logger():
    """
    Init the logger config at info level.
    """
    return init_logger(
        "deovi-client",
        "INFO",
        printout=False,
    )


@pytest.fixture(scope="function")
def warning_logger():
    """
    Init the logger config at warning level.
    """
    return init_logger(
        "deovi-client",
        "WARNING",
        printout=False,
    )


@pytest.fixture(scope="function")
def task_manager():
    """
    Return initialized task manager

    TODO: Since there is no more a formatter to init, this fixture seems useless. Keep
    tests simple and just use "TaskMaster()" in them.
    """
    return TaskMaster()
