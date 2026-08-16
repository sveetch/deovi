import datetime
import logging

from freezegun import freeze_time

from deovi import __pkgname__
from deovi.models import (
    DirectoryInformation,
    MediaInformation,
    CollectionManifest,
    MovieManifest,
    SerieManifest,
)


@freeze_time("2012-10-15 10:00:00.001007")
def test_manifest_no_valid(settings):
    """
    When the directory does not have any valid manifest file
    """
    basepath = settings.datas_path / "media_sample"

    # foo/ does not have any manifest file
    foo = DirectoryInformation(
        path=(basepath / "foo"),
        basepath=basepath,
        size=42,
        mtime=datetime.datetime.now(),
        autoload=True,
    )

    assert foo.manifest is None

    # ping/ only have an invalid manifest
    ping = DirectoryInformation(
        path=(basepath / "ping"),
        basepath=basepath,
        size=42,
        mtime=datetime.datetime.now(),
        autoload=True,
    )

    assert ping.manifest is None


@freeze_time("2012-10-15 10:00:00.001007")
def test_manifest_fallback_on_yaml(settings, caplog):
    """
    Yaml manifest is discovered since the JSON one is not valid
    """
    caplog.set_level(logging.DEBUG)

    basepath = settings.datas_path / "media_sample"

    root = DirectoryInformation(
        path=basepath,
        basepath=basepath,
        size=42,
        mtime=datetime.datetime.now(),
        autoload=True,
    )
    assert root.manifest == CollectionManifest(
        path=basepath / "manifest.yaml",
        title="Media sample root YAML",
    )

    expected_msg = (
        "Ignored JSON manifest because it misses the required 'tmdb_type' "
        "field: {}"
    )
    assert caplog.record_tuples == [
        (
            __pkgname__,
            logging.DEBUG,
            expected_msg.format(basepath / "manifest.json"),
        ),
    ]


@freeze_time("2012-10-15 10:00:00.001007")
def test_manifest_dir_loaded_json(settings, caplog):
    """
    JSON is loaded if found and valid
    """
    basepath = settings.datas_path / "media_sample"

    pong = DirectoryInformation(
        path=(basepath / "ping/pong"),
        basepath=basepath,
        size=42,
        mtime=datetime.datetime.now(),
        autoload=True,
    )
    assert caplog.record_tuples == []

    # Yaml manifest has been discovered since the JSON one is not valid
    assert pong.manifest == SerieManifest(
        path=basepath / "ping/pong/manifest.json",
        title="Pong JSON",
        tmdb_id=21567,
    )


@freeze_time("2012-10-15 10:00:00.001007")
def test_manifest_media_loaded_json(settings, caplog):
    """
    MediaInformation manifest is named after its own name
    """
    basepath = settings.datas_path / "media_sample"

    sample720 = MediaInformation(
        path=(basepath / "ping/pong/SampleVideo_720x480_1mb.mkv"),
        basepath=basepath,
        size=42,
        mtime=datetime.datetime.now(),
        autoload=True,
    )
    assert caplog.record_tuples == []

    # JSON manifest has been discovered
    assert sample720.manifest == MovieManifest(
        path=basepath / "ping/pong/SampleVideo_720x480_1mb.json",
        title="Sample 720x480 1mb JSON",
        tmdb_id=273204,
    )
