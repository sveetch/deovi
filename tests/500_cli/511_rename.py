import json
import logging

from click.testing import CliRunner

from deovi import __pkgname__
from deovi.cli.entrypoint import cli_frontend


def test_rename_required_job_option(caplog):
    """
    At least one job option is required.

    NOTE: We do not test job filepath validation since it's a Click feature.
    """
    runner = CliRunner()

    result = runner.invoke(cli_frontend, ["rename"])

    assert result.exit_code == 1

    assert caplog.record_tuples == [
        (
            __pkgname__,
            logging.CRITICAL,
            "There is no job file to process.",
        )
    ]


def test_rename_required_success(caplog, basic_sample, basic_suite):
    """
    Just test successful jobs input and output
    """
    # Create sample job in basic sample
    sample1_source = basic_sample / "job_1.json"
    with sample1_source.open("w") as fp:
        json.dump({
            "basepath": "files",
            "extensions": ["txt"],
            "tasks": [
                ["uppercase", {}],
                ["add_prefix", {"prefix": "basic-"}],
            ],
        }, fp, indent=4)

    # Create another job file in basic sample but point its basepath to an absolute
    # path in another directory
    sample2_source = basic_sample / "job_2.json"
    with sample2_source.open("w") as fp:
        json.dump({
            "basepath": str(basic_suite / "files"),
            "extensions": ["mp4"],
            "tasks": [
                ["lowercase", {}],
                ["catch_segments", {
                    "divider": ".",
                    "slice_start": 0,
                    "slice_end": 1,
                }],
            ],
        }, fp, indent=4)

    runner = CliRunner()

    result = runner.invoke(cli_frontend, [
        "-v 5",
        "rename",
        str(sample1_source),
        str(sample2_source),
    ])

    assert result.exit_code == 0

    # All expected logs from both run modes
    expected_logs = [
        "Dry run mode is enabled, no file will be renamed.",
        "",
        "📂 Working on: {}".format(str(basic_sample / "files")),
        " • Allowed file extension(s): txt",
        " • 2 files to process",
        "",
        "[1]━┍━ From: fake-barriton.mp4.txt",
        "    ├┄ [uppercase]  FAKE-BARRITON.MP4.TXT",
        "    ├┄ [add_prefix]  basic-FAKE-BARRITON.MP4.TXT",
        "    ┕━ ✨ To: basic-FAKE-BARRITON.MP4.TXT",
        "",
        "[2]━┍━ From: foo.txt",
        "    ├┄ [uppercase]  FOO.TXT",
        "    ├┄ [add_prefix]  basic-FOO.TXT",
        "    ┕━ ✨ To: basic-FOO.TXT",
        "",
        "📂 Working on: {}".format(str(basic_suite / "files")),
        " • Allowed file extension(s): mp4",
        " • 4 files to process",
        "",
        "[1]━┍━ From: Item.S01.E01.mp4",
        "    ├┄ [lowercase]  item.s01.e01.mp4",
        "    ├┄ [catch_segments]  item.mp4",
        "    ┕━ ✨ To: item.mp4",
        "",
        "[2]━┍━ From: Item.S01.E02.mp4",
        "    ├┄ [lowercase]  item.s01.e02.mp4",
        "    ├┄ [catch_segments]  item.mp4",
        "    ┕━ ❗ This destination is already planned from another file: item.mp4",
        "",
        "[3]━┍━ From: Item.S02.E01.mp4",
        "    ├┄ [lowercase]  item.s02.e01.mp4",
        "    ├┄ [catch_segments]  item.mp4",
        "    ┕━ ❗ This destination is already planned from another file: item.mp4",
        "",
        "[4]━┍━ From: Item.S02.E02.mp4",
        "    ├┄ [lowercase]  item.s02.e02.mp4",
        "    ├┄ [catch_segments]  item.mp4",
        "    ┕━ ❗ This destination is already planned from another file: item.mp4",
        "",
    ]
    assert expected_logs == [rec.message for rec in caplog.records]
