import json
import logging

from click.testing import CliRunner

from deovi.collector import Collector
from deovi.cli.entrypoint import cli_frontend
from deovi.utils.tests import DUMMY_ISO_DATETIME, timestamp_to_isoformat


APPLABEL = "deovi"


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


def test_job_success(monkeypatch, caplog, media_sample):
    """
    With correct required arguments, command should succeed to write a registry from
    given source into a JSON file at given destination.
    """
    monkeypatch.setattr(Collector, "timestamp_to_isoformat", timestamp_to_isoformat)

    runner = CliRunner()

    source = media_sample / "foo/bar"
    destination = media_sample / "registry.json"

    # Without any args
    result = runner.invoke(cli_frontend, [
        "collect",
        str(source),
        str(destination),
        "--extension", "mkv",
    ])

    assert result.exit_code == 0
    assert caplog.record_tuples == [
        (
            APPLABEL,
            logging.INFO,
            "Source: {}".format(str(source)),
        ),
        (
            APPLABEL,
            logging.INFO,
            "Destination: {}".format(str(destination)),
        ),
        (
            APPLABEL,
            logging.INFO,
            "Extensions: mkv",
        ),
        (
            APPLABEL,
            logging.INFO,
            "Registry saved to: {}".format(str(destination)),
        ),
        (
            APPLABEL,
            logging.INFO,
            "Registered directories: 1",
        ),
        (
            APPLABEL,
            logging.INFO,
            "Registered files: 1",
        ),
        (
            APPLABEL,
            logging.INFO,
            "Total directories and files size: 1059817",
        ),
    ]

    with destination.open() as fp:
        content = json.load(fp)

    assert content == {
        ".": {
            "path": str(source),
            "name": "bar",
            "title": "Foo bar",
            "absolute_dir": str(media_sample / "foo"),
            "relative_dir": ".",
            "size": 4096,
            "mtime": DUMMY_ISO_DATETIME,
            "children_files": [
                {
                    "path": str(source / "SampleVideo_360x240_1mb.mkv"),
                    "name": "SampleVideo_360x240_1mb.mkv",
                    "absolute_dir": str(source),
                    "relative_dir": ".",
                    "directory": "",
                    "extension": "mkv",
                    "container": "Matroska",
                    "size": 1055721,
                    "mtime": DUMMY_ISO_DATETIME
                }
            ]
        }
    }
