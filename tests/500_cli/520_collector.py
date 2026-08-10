import json
import logging

from freezegun import freeze_time

from click.testing import CliRunner

from deovi import __pkgname__
from deovi.collector.new_collect import NewCollector
from deovi.cli.entrypoint import cli_frontend
from deovi.utils.tests import DUMMY_ISO_DATETIME, timestamp_to_isoformat


def test_job_required_arguments(caplog, media_sample):
    """
    Command require exactly two arguments (source and destination).
    """
    runner = CliRunner()

    # Without any arg
    result = runner.invoke(cli_frontend, ["collect"])

    assert result.exit_code == 2
    assert caplog.record_tuples == []

    # Only the source arg
    result = runner.invoke(cli_frontend, [
        "collect",
        str(media_sample),
    ])

    assert result.exit_code == 2
    assert caplog.record_tuples == []


@freeze_time("2012-10-15 10:00:00.001007")
def test_job_success(monkeypatch, caplog, settings, tmp_path):
    """
    With correct required arguments, command should succeed to write a registry from
    given source into a JSON file at given destination.
    """
    monkeypatch.setattr(NewCollector, "timestamp_to_isoformat", timestamp_to_isoformat)
    media_sample = settings.datas_path / "media_sample"

    runner = CliRunner()

    source = media_sample / "foo/bar"
    destination = tmp_path / "registry.json"

    # Without any args
    result = runner.invoke(cli_frontend, [
        "-v", "5",
        "collect",
        str(source),
        str(destination),
        "--extension", "mkv",
    ])

    assert result.exit_code == 0
    assert caplog.record_tuples == [
        (
            __pkgname__,
            logging.INFO,
            "Source: {}".format(str(source)),
        ),
        (
            __pkgname__,
            logging.INFO,
            "Destination: {}".format(str(destination)),
        ),
        (
            __pkgname__,
            logging.INFO,
            "Extensions: mkv",
        ),
        (
            __pkgname__,
            logging.DEBUG,
            "Scanning {}".format(source),
        ),
        (
            __pkgname__,
            logging.DEBUG,
            (
                "Ignored YAML manifest because it misses the required 'tmdb_type' "
                "field: {}/manifest.yaml"
            ).format(source),
        ),
        (
            __pkgname__,
            logging.DEBUG,
            (
                "Ignored JSON manifest because it misses the required 'tmdb_type' "
                "field: {}/SampleVideo_360x240_1mb.json"
            ).format(source),
        ),
        (
            __pkgname__,
            logging.DEBUG,
            (
                "Ignored YAML manifest because it misses the required 'tmdb_type' "
                "field: {}/SampleVideo_360x240_1mb.yaml"
            ).format(source),
        ),
        (
            __pkgname__,
            logging.INFO,
            "Registry saved to: {}".format(str(destination)),
        ),
        (
            __pkgname__,
            logging.INFO,
            "Registered directories: 1",
        ),
        (
            __pkgname__,
            logging.INFO,
            "Registered files: 1",
        ),
        (
            __pkgname__,
            logging.INFO,
            "Total directories and files size: 1059817",
        ),
    ]

    with destination.open() as fp:
        content = json.load(fp)

    assert "device" in content
    assert content["registry"] == {
        ".": {
            "path": str(source),
            "name": "bar",
            "absolute_dir": str(media_sample / "foo"),
            "relative_dir": ".",
            "size": 4096,
            "mtime": DUMMY_ISO_DATETIME,
            "manifest": None,
            "checksum": (
                "19eeccbae3d525a004abef1e039a52c4759412acc3680daa9812e4f516cacb46e5"
                "a8c349128246bb4f0ee843cad5b80ba31259cd2c76b4537ddf13cd03893a9a"
            ),
            "medias": [
                {
                    "path": str(source / "SampleVideo_360x240_1mb.mkv"),
                    "name": "SampleVideo_360x240_1mb.mkv",
                    "absolute_dir": str(source),
                    "relative_dir": ".",
                    "name_alt": "",
                    "manifest": None,
                    "checksum": (
                        "bb0ca8dd15c875f617df993b8fce624bfe74ed49a11207056b55c0a2b58a"
                        "471bd1aa7d02f10de70c4bd88d0b9e770214ef8c5912703e77dfd67566923"
                        "ba672e1"
                    ),
                    "extension": "mkv",
                    "container": "Matroska",
                    "size": 1055721,
                    "mtime": DUMMY_ISO_DATETIME
                }
            ],
        }
    }
