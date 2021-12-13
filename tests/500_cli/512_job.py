import logging
from pathlib import Path

from click.testing import CliRunner

from deovi_client.cli.entrypoint import cli_frontend


APPLABEL = "deovi-client"


def test_job_required_basepath(caplog):
    """
    Basepath argument is required.
    """
    runner = CliRunner()

    result = runner.invoke(cli_frontend, ["job"])

    assert result.exit_code == 2
    assert caplog.record_tuples == []


def test_job_error(caplog, basic_sample):
    """
    JobValidationError is correctly managed.
    """
    basepath = basic_sample / "files"
    destination = "/home/foo/files.json"

    runner = CliRunner()

    result = runner.invoke(cli_frontend, [
        "-v 5",
        "job",
        str(basepath),
        "--destination",
        str(destination),
    ])

    assert result.exit_code == 1

    assert caplog.record_tuples == [
        (
            APPLABEL,
            logging.DEBUG,
            "Basepath: {}".format(basepath),
        ),
        (
            APPLABEL,
            logging.DEBUG,
            "Destination: {}".format(destination),
        ),
        (
            APPLABEL,
            logging.CRITICAL,
            (
                "🚨 Destination path must point into an existing "
                "directory: {}".format(destination)
            ),
        ),
    ]


def test_job_success(monkeypatch, caplog, basic_sample):
    """
    Sucessfully create a new Job for given basepath.
    """
    basepath = basic_sample / "files"
    destination = basic_sample / "files.json"

    # Mock cwd() to always return the sample tmp dir
    def mockreturn():
        return basic_sample

    runner = CliRunner()

    with monkeypatch.context() as m:
        m.setattr(Path, "cwd", mockreturn)
        result = runner.invoke(cli_frontend, [
            "-v 5",
            "job",
            str(basepath),
        ])

    assert result.exit_code == 0

    assert destination.exists() is True

    assert caplog.record_tuples == [
        (
            APPLABEL,
            logging.DEBUG,
            "Basepath: {}".format(basepath),
        ),
        (
            APPLABEL,
            logging.DEBUG,
            "No destination given, automatic name from basepath will be used.",
        ),
        (
            APPLABEL,
            logging.INFO,
            "Created Job file: {}".format(destination),
        ),
    ]


def test_job_success_with_destination(monkeypatch, caplog, basic_sample):
    """
    Sucessfully create a new Job for given basepath and destination.
    """
    basepath = basic_sample / "files"
    destination = basepath / "foo.json"

    # Mock cwd() to always return the sample tmp dir
    def mockreturn():
        return basic_sample

    runner = CliRunner()

    with monkeypatch.context() as m:
        m.setattr(Path, "cwd", mockreturn)
        result = runner.invoke(cli_frontend, [
            "-v 5",
            "job",
            str(basepath),
            "--destination",
            str(destination),
        ])

    assert result.exit_code == 0

    assert destination.exists() is True

    assert caplog.record_tuples == [
        (
            APPLABEL,
            logging.DEBUG,
            "Basepath: {}".format(basepath),
        ),
        (
            APPLABEL,
            logging.DEBUG,
            "Destination: {}".format(destination),
        ),
        (
            APPLABEL,
            logging.INFO,
            "Created Job file: {}".format(destination),
        ),
    ]
