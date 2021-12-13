import json

import pytest

from deovi_client.exceptions import JobValidationError
from deovi_client.renamer.jobs import Job
from deovi_client.renamer.runner import JobRunner
from deovi_client.renamer.printer import PrinterInterface
from deovi_client.renamer.tasks import TaskMaster


class DummyTestTaskMaster(PrinterInterface):
    """
    Dummy Task container for test purpose.

    Included task are dummy.
    """
    def nope(self):
        return

    def task_foo(self, index, source, **options):
        """
        Just prepend "foo." to source
        """
        return (source, "foo." + source.name)

    def task_bar(self, index, source, **options):
        """
        Just prepend "bar." to source required attribute are not used.
        """
        return (source, "bar." + source.name)
    task_bar.required = ["ping", "pong"]


def test_jobrunner_get_available_tasks():
    """
    Method "get_available_tasks" should retrieve every task methods and inspect them
    to get their possible rules.
    """
    jobber = JobRunner(task_class=DummyTestTaskMaster)

    assert jobber.get_available_tasks() == {
        "bar": ["ping", "pong"],
        "foo": [],
    }


def test_jobrunner_get_jobs_errors(basic_sample):
    """
    Method "get_jobs" with invalid Job files should return errors for each invalid job.
    """
    jobber = JobRunner(task_class=DummyTestTaskMaster)

    # Create some jobs
    job_basic = basic_sample / "job_basic.json"

    doesnotexist = basic_sample / "nope.json"

    invalid_json = basic_sample / "invalid.json"
    invalid_json.write_text("Wrong")

    missing_rules = basic_sample / "missing_rules.json"
    with missing_rules.open("w") as fp:
        json.dump({}, fp, indent=4)

    with pytest.raises(JobValidationError) as excinfo:
        jobber.get_jobs([
            job_basic,
            invalid_json,
            missing_rules,
            doesnotexist,
        ])

    assert str(excinfo.value) == "Error(s) occured during job(s) validation"
    assert len(excinfo.value.validation_details) == 3
    assert len(excinfo.value.validation_details[str(invalid_json)]) == 1
    assert len(excinfo.value.validation_details[str(missing_rules)]) == 2
    assert len(excinfo.value.validation_details[str(doesnotexist)]) == 1


def test_jobrunner_get_job_tasks_errors(basic_sample):
    """
    Method "get_jobs" with invalid job tasks should return errors for each job.
    """
    jobber = JobRunner(task_class=DummyTestTaskMaster)

    # Create some jobs
    sample1_source = basic_sample / "job_1.json"
    with sample1_source.open("w") as fp:
        json.dump({
            "basepath": "files",
            "tasks": [
                ["nope", {}],
                ["foo", {}],
                ["bar", {}],
            ],
        }, fp, indent=4)

    sample2_source = basic_sample / "job_2.json"
    with sample2_source.open("w") as fp:
        json.dump({
            "basepath": "files",
            "tasks": [
                [
                    "bar",
                    {"ping": 42},
                ],
            ],
        }, fp, indent=4)

    with pytest.raises(JobValidationError) as excinfo:
        jobber.get_jobs([
            sample1_source,
            sample2_source,
        ])

    assert str(excinfo.value) == "Error(s) occured during job(s) task(s) validation"
    assert len(excinfo.value.validation_details) == 2
    assert len(excinfo.value.validation_details[str(sample1_source)]) == 2
    assert len(excinfo.value.validation_details[str(sample2_source)]) == 1


def test_jobrunner_get_jobs_success(basic_sample):
    """
    Method "get_jobs" should return every Job model objects when there is no errors.
    """
    jobber = JobRunner(task_class=DummyTestTaskMaster)

    # Create some jobs
    sample1_source = basic_sample / "job_1.json"
    with sample1_source.open("w") as fp:
        json.dump({
            "basepath": "files",
            "tasks": [
                ["foo", {}],
            ],
        }, fp, indent=4)

    sample2_source = basic_sample / "job_2.json"
    with sample2_source.open("w") as fp:
        json.dump({
            "basepath": "files",
            "tasks": [
                ["foo", {}],
                ["bar", {"ping": 42, "pong": True}],
            ],
        }, fp, indent=4)

    jobs = jobber.get_jobs([
        sample1_source,
        sample2_source,
    ])

    assert jobs[0].name == Job.DEFAULT_NAME.format(sample1_source)
    assert jobs[0].source == sample1_source
    assert jobs[0].basepath == sample1_source.parents[0] / "files"
    assert jobs[0].tasks == [
        ["foo", {}],
    ]

    assert jobs[1].name == Job.DEFAULT_NAME.format(sample2_source)
    assert jobs[1].source == sample2_source
    assert jobs[1].basepath == sample2_source.parents[0] / "files"
    assert jobs[1].tasks == [
        ["foo", {}],
        ["bar", {"ping": 42, "pong": True}],
    ]


def test_jobrunner_run_success(caplog, debug_logger, basic_sample, basic_suite):
    """
    Method "run" should correctly run every job tasks if there is no critical error.
    """
    jobber = JobRunner(task_class=TaskMaster)

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

    jobber.run([
        sample1_source,
        sample2_source,
    ], dry_run=True)

    # All expected logs from both run modes
    expected_logs = [
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
