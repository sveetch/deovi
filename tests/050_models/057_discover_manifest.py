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

    TODO: Should use caplog to see the error from invalid manifest
    """
    base_samplepath = settings.datas_path / "media_sample"

    # foo/ does not have any manifest file
    foo = DirectoryInformation(
        path=(base_samplepath / "foo"),
        basepath=base_samplepath,
        size=42,
        mtime=datetime.datetime.now(),
        autoload=True,
    )

    assert foo.manifest is None

    # ping/ only have an invalid manifest
    ping = DirectoryInformation(
        path=(base_samplepath / "ping"),
        basepath=base_samplepath,
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
    base_samplepath = settings.datas_path / "media_sample"

    root = DirectoryInformation(
        path=base_samplepath,
        basepath=base_samplepath,
        size=42,
        mtime=datetime.datetime.now(),
        autoload=True,
    )
    assert root.manifest == CollectionManifest(
        path=base_samplepath / "manifest.yaml",
        title="Media sample root YAML",
    )
    assert caplog.record_tuples == [
        (
            __pkgname__,
            logging.WARNING,
            "JSON Manifest is missing the required 'tmdb_type' field: {}".format(
                base_samplepath / "manifest.json"
            ),
        ),
    ]


@freeze_time("2012-10-15 10:00:00.001007")
def test_manifest_dir_loaded_json(settings, caplog):
    """
    JSON is loaded if found and valid
    """
    base_samplepath = settings.datas_path / "media_sample"

    pong = DirectoryInformation(
        path=(base_samplepath / "ping/pong"),
        basepath=base_samplepath,
        size=42,
        mtime=datetime.datetime.now(),
        autoload=True,
    )
    assert caplog.record_tuples == []

    # Yaml manifest has been discovered since the JSON one is not valid
    assert pong.manifest == SerieManifest(
        path=base_samplepath / "ping/pong/manifest.json",
        title="Pong JSON",
    )


@freeze_time("2012-10-15 10:00:00.001007")
def test_manifest_media_loaded_json(settings, caplog):
    """
    MediaInformation manifest is named after its own name
    """
    base_samplepath = settings.datas_path / "media_sample"

    sample720 = MediaInformation(
        path=(base_samplepath / "ping/pong/SampleVideo_720x480_1mb.mkv"),
        basepath=base_samplepath,
        size=42,
        mtime=datetime.datetime.now(),
        autoload=True,
    )
    assert caplog.record_tuples == []

    # JSON manifest has been discovered
    assert sample720.manifest == MovieManifest(
        path=base_samplepath / "ping/pong/SampleVideo_720x480_1mb.json",
        title="Sample 720x480 1mb JSON",
    )
