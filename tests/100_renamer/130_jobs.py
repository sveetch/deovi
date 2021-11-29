import json
import logging
from pathlib import Path

import pytest

from deovi_client.renamer.jobs import Job
from deovi_client.renamer.runner import JobRunner


def test_job_model():
    """
    Job model should be correctly instanciated from given args and kwargs.
    """
    source = "/dummy/path.json"
    basepath = "/dummy/files"

    job = Job(
        Path(source),
        Path(basepath),
    )

    assert job.name == Job.DEFAULT_NAME.format(source)
    assert job.tasks == []

    job = Job(
        Path(source),
        Path(basepath),
        name="Hello world",
    )

    assert job.name == "Hello world"


def test_job_load(basic_sample):
    """
    Method should correctly load a JSON job file into a Job model instance.
    """
    source = basic_sample / "job.json"
    basepath = basic_sample / "files"

    with source.open("w") as fp:
        json.dump({
            "basepath": "files",
            "tasks": [],
        }, fp, indent=4)

    job = Job.load(str(source))

    assert job.name == Job.DEFAULT_NAME.format(source)
    assert job.source == source
    assert job.basepath == basepath
    assert job.tasks == []


def test_job_get_target_files(basic_sample):
    """
    Method should retrieve all target files.
    """
    source = basic_sample / "job.json"
    basepath = basic_sample / "files"

    # Without extensions, all files
    job = Job(
        Path(source),
        Path(basepath),
    )
    targets = job.get_target_files()
    assert targets == [
        basepath / "bar.mpeg4",
        basepath / "barriton.mp4",
        basepath / "fake-barriton.mp4.txt",
        basepath / "foo.txt",
        basepath / "ping.avi",
        basepath / "plop.rst",
    ]

    # With no matching extension
    job = Job(
        Path(source),
        Path(basepath),
        extensions=["pdf"],
    )
    targets = job.get_target_files()
    assert targets == []

    # With a single extension
    job = Job(
        Path(source),
        Path(basepath),
        extensions=["txt"],
    )
    targets = job.get_target_files()
    assert targets == [
        basepath / "fake-barriton.mp4.txt",
        basepath / "foo.txt",
    ]

    # With multiple extensions
    job = Job(
        Path(source),
        Path(basepath),
        extensions=["mpeg4", "mp4", "avi"],
    )
    targets = job.get_target_files()
    assert targets == [
        basepath / "bar.mpeg4",
        basepath / "barriton.mp4",
        basepath / "ping.avi",
    ]


def test_job_run_modes(caplog, info_logger, task_manager, basic_sample):
    """
    Method "run" should correctly perform all of its tasks and depending "dry run"
    mode should perform or not renaming.
    """
    source = basic_sample / "job.json"
    basepath = basic_sample / "files"

    # Only a single extension to avoid too many outputs
    job = Job(
        Path(source),
        Path(basepath),
        extensions=[],
        tasks = [
            ["capitalize", {}],
            ["add_prefix", {"prefix": "blip_"}],
        ],
    )

    # A simple run dry run
    results = job.run(task_manager, dry_run=True)

    expected_original_store = [
        basepath / "bar.mpeg4",
        basepath / "barriton.mp4",
        basepath / "fake-barriton.mp4.txt",
        basepath / "foo.txt",
        basepath / "ping.avi",
        basepath / "plop.rst",
    ]
    expected_rename_store = [
        basepath / "blip_Bar.mpeg4",
        basepath / "blip_Barriton.mp4",
        basepath / "blip_Fake-barriton.mp4.txt",
        basepath / "blip_Foo.txt",
        basepath / "blip_Ping.avi",
        basepath / "blip_Plop.rst",
    ]
    assert sorted(results["original_store"]) == sorted(expected_original_store)

    assert sorted(results["rename_store"]) == sorted(expected_rename_store)

    # In dry run, original are still there
    for item in expected_original_store:
        assert item.exists() is True

    # ..and renamed have not be written to FS
    for item in expected_rename_store:
        assert item.exists() is False

    # Again without dry run
    job.run(task_manager, dry_run=False)

    # Original have moved
    for item in expected_original_store:
        assert item.exists() is False

    # ..to the renamed ones
    for item in expected_rename_store:
        assert item.exists() is True

    # All expected logs from both run modes
    expected_logs = [
        "📂 Working on: {path}".format(path=basepath),
        " • Allowed file extension(s): All",
        " • 6 files to process",
        "",
        "[1]━┍━ From: bar.mpeg4",
        "    ┕━ ✨ To: blip_Bar.mpeg4",
        "",
        "[2]━┍━ From: barriton.mp4",
        "    ┕━ ✨ To: blip_Barriton.mp4",
        "",
        "[3]━┍━ From: fake-barriton.mp4.txt",
        "    ┕━ ✨ To: blip_Fake-barriton.mp4.txt",
        "",
        "[4]━┍━ From: foo.txt",
        "    ┕━ ✨ To: blip_Foo.txt",
        "",
        "[5]━┍━ From: ping.avi",
        "    ┕━ ✨ To: blip_Ping.avi",
        "",
        "[6]━┍━ From: plop.rst",
        "    ┕━ ✨ To: blip_Plop.rst",
        "",
        "📂 Working on: {path}".format(path=basepath),
        " • Allowed file extension(s): All",
        " • 6 files to process",
        "",
        "[1]━┍━ From: bar.mpeg4",
        "    ┕━ ✅ To: blip_Bar.mpeg4",
        "",
        "[2]━┍━ From: barriton.mp4",
        "    ┕━ ✅ To: blip_Barriton.mp4",
        "",
        "[3]━┍━ From: fake-barriton.mp4.txt",
        "    ┕━ ✅ To: blip_Fake-barriton.mp4.txt",
        "",
        "[4]━┍━ From: foo.txt",
        "    ┕━ ✅ To: blip_Foo.txt",
        "",
        "[5]━┍━ From: ping.avi",
        "    ┕━ ✅ To: blip_Ping.avi",
        "",
        "[6]━┍━ From: plop.rst",
        "    ┕━ ✅ To: blip_Plop.rst",
        "",
    ]
    assert expected_logs == [rec.message for rec in caplog.records]


def test_job_run_errors(caplog, debug_logger, task_manager, basic_sample):
    """
    Method "run" should correctly perform all of its tasks even when there is
    non-critical errors which result in warning logs.
    """
    source = basic_sample / "job.json"
    basepath = basic_sample / "files"

    # New file which may result in conflict name errors
    twice_file = basic_sample / "files" / "BARRITON.MP4"
    twice_file.write_text("Foo!")

    # Only a single extension to avoid too many outputs
    job = Job(
        Path(source),
        Path(basepath),
        extensions=["mp4", "mpeg4", "avi"],
        tasks = [
            ["uppercase", {}],
        ],
    )

    # A simple run dry run
    results = job.run(task_manager, dry_run=False)

    expected_rename_store = [
        basepath / "BAR.MPEG4",
        basepath / "PING.AVI",
    ]
    expected_unchanged = [
        basepath / "BARRITON.MP4",
        basepath / "barriton.mp4",
    ]

    assert sorted(results["rename_store"]) == sorted(expected_rename_store)

    # Original source unchanged are still there since they were in conflicts
    for item in expected_unchanged:
        assert item.exists() is True

    # Effectively renamed sources
    for item in expected_rename_store:
        assert item.exists() is True

    # All expected logs from both run modes
    expected_logs = [
        "📂 Working on: {path}".format(path=basepath),
        " • Allowed file extension(s): mp4, mpeg4, avi",
        " • 4 files to process",
        "",
        "[1]━┍━ From: BARRITON.MP4",
        "    ├┄ [uppercase]  BARRITON.MP4",
        "    ┕━ ❗ Source and destination paths are identical, nothing to rename.",
        "",
        "[2]━┍━ From: bar.mpeg4",
        "    ├┄ [uppercase]  BAR.MPEG4",
        "    ┕━ ✅ To: BAR.MPEG4",
        "",
        "[3]━┍━ From: barriton.mp4",
        "    ├┄ [uppercase]  BARRITON.MP4",
        "    ┕━ ❗ Destination already exists and won't be overwritten: BARRITON.MP4",
        "",
        "[4]━┍━ From: ping.avi",
        "    ├┄ [uppercase]  PING.AVI",
        "    ┕━ ✅ To: PING.AVI",
        "",
    ]
    assert expected_logs == [rec.message for rec in caplog.records]
