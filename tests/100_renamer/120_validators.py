import json
from pathlib import Path

import pytest

from deovi_client.exceptions import TaskValidationError
from deovi_client.renamer.validators import (
    validate_task_options, validate_job_file, validate_jobs, is_allowed_file,
)
from deovi_client.renamer.tasks import TaskMaster


@pytest.mark.parametrize("required, options", [
    (
        [],
        {},
    ),
    (
        ["plip"],
        {
            "ping": ".",
            "plip": True,
        },
    ),
    (
        ["plip", "ping"],
        {
            "ping": ".",
            "plip": True,
        },
    ),
])
def test_validate_task_options_success(required, options):
    """
    Validator should not raise error when required options are respected.
    """
    assert validate_task_options("Foo", required, **options) is True


@pytest.mark.parametrize("required, options, expected", [
    (
        ["plip"],
        {},
        "Task 'Foo' require option(s): plip"
    ),
    (
        ["plip", "ping"],
        {
            "ping": ".",
        },
        "Task 'Foo' require option(s): plip"
    ),
    (
        ["plip", "ping", "ping"],
        {},
        "Task 'Foo' require option(s): ping, plip"
    ),
    (
        ["c", "a", "b"],
        {},
        "Task 'Foo' require option(s): a, b, c"
    ),
])
def test_validate_task_options_error(required, options, expected):
    """
    Validator should raise error for missing options.
    """
    with pytest.raises(TaskValidationError) as excinfo:
        validate_task_options("Foo", required, **options)

    assert str(excinfo.value) == expected


def test_validate_job_file(basic_sample, settings):
    """
    Validation should catch any supported errors.
    """
    # Not existing
    p = basic_sample / "nope.json"
    validation = validate_job_file(p)

    assert len(validation) == 1
    assert validation[0] == (
        "Configuration file does not exists: {}/nope.json".format(basic_sample)
    )

    # Invalid JSON
    p = basic_sample / "invalid.json"
    p.write_text("Wrong")
    validation = validate_job_file(p)

    assert len(validation) == 1
    assert validation[0].startswith(
        (
            "Configuration file is not a valid JSON file: {}/invalid.json"
        ).format(
            basic_sample
        )
    )

    # Empty config missing required rules
    p = basic_sample / "missing_rules.json"
    with p.open("w") as fp:
        json.dump({}, fp, indent=4)
    validation = validate_job_file(p)

    assert len(validation) == 2
    assert validation[0] == (
        "Configuration file is missing required 'basepath' item: {}".format(p)
    )
    assert validation[1] == (
        "Configuration file miss required 'tasks' item: {}".format(p)
    )

    # With basepath that does not exist
    p = basic_sample / "basepath_doesnotexists.json"
    with p.open("w") as fp:
        json.dump({
            "basepath": "nope/niet",
            "tasks": [],
        }, fp, indent=4)
    validation = validate_job_file(p)

    assert len(validation) == 1
    assert validation[0] == (
        (
            "Configuration file value for 'basepath' is not an existing path: "
            "{}/nope/niet"
        ).format(
            basic_sample
        )
    )

    # With basepath that is a file
    p = basic_sample / "basepath_doesnotexists.json"
    dummy = basic_sample / "notadir"
    dummy.write_text("I'm not a directory")
    with p.open("w") as fp:
        json.dump({
            "basepath": "notadir",
            "tasks": [],
        }, fp, indent=4)
    validation = validate_job_file(p)

    assert len(validation) == 1
    assert validation[0] == (
        "Configuration file value for 'basepath' is not a directory: {}".format(
            dummy
        )
    )

    # Correct config file using relative path resolved to absolute from config file
    # directory
    p = basic_sample / "job_basic.json"
    validation = validate_job_file(p)
    assert len(validation) == 0

    # Correct config file with an absolute path
    p = basic_sample / "job_absolute.json"
    with p.open("w") as fp:
        json.dump({
            "basepath": str(basic_sample / "files"),
            "tasks": [],
        }, fp, indent=4)
    validation = validate_job_file(p)

    assert len(validation) == 0


def test_validate_jobs(basic_sample, settings):
    """
    All error from jobs should be raised.
    """
    # Create some jobs
    job_basic = basic_sample / "job_basic.json"

    invalid_json = basic_sample / "invalid.json"
    invalid_json.write_text("Wrong")

    missing_rules = basic_sample / "missing_rules.json"
    with missing_rules.open("w") as fp:
        json.dump({}, fp, indent=4)

    # Validate them
    errors = validate_jobs([
        job_basic,
        invalid_json,
        missing_rules,
    ])

    assert len(errors) == 2
    assert (str(job_basic) not in errors) is True

    assert len(errors[str(invalid_json)]) == 1
    assert errors[str(invalid_json)][0].startswith(
        "Configuration file is not a valid JSON file: {}".format(invalid_json)
    )
    assert len(errors[str(missing_rules)]) == 2
    assert errors[str(missing_rules)][0] == (
        "Configuration file is missing required 'basepath' item: {}".format(
            missing_rules
        )
    )
    assert errors[str(missing_rules)][1] == (
        "Configuration file miss required 'tasks' item: {}".format(missing_rules)
    )


def test_numerate_validation():
    """
    Task 'numerate' options should be correctly validated
    """
    container = TaskMaster()

    with pytest.raises(TaskValidationError) as excinfo:
        validate_task_options(
            "numerate",
            container.task_numerate.required,
        )

    assert str(excinfo.value) == (
        "Task 'numerate' require option(s): zfill"
    )


def test_add_prefix_validation():
    """
    Task 'add_prefix' options should be correctly validated
    """
    container = TaskMaster()

    with pytest.raises(TaskValidationError) as excinfo:
        validate_task_options(
            "add_prefix",
            container.task_add_prefix.required,
        )

    assert str(excinfo.value) == (
        "Task 'add_prefix' require option(s): prefix"
    )


def test_catch_segments_validation():
    """
    Task 'catch_segments' options should be correctly validated
    """
    container = TaskMaster()

    with pytest.raises(TaskValidationError) as excinfo:
        validate_task_options(
            "catch_segments",
            container.task_catch_segments.required,
        )

    assert str(excinfo.value) == (
        "Task 'catch_segments' require option(s): divider, slice_start"
    )


def test_replace_validation():
    """
    Task 'replace' options should be correctly validated
    """
    container = TaskMaster()

    with pytest.raises(TaskValidationError) as excinfo:
        validate_task_options(
            "replace",
            container.task_replace.required,
        )

    assert str(excinfo.value) == (
        "Task 'replace' require option(s): from, to"
    )

@pytest.mark.parametrize("source, extensions, expected", [
    (Path("foo"), [], True),
    (Path("bar"), [], False),
    (Path("moo.txt"), ["mp4"], False),
    (Path("ping.gz"), ["tar.gz"], False),
    (Path("pang.tar.gz"), ["gz"], True),
    (Path("pang.tar.gz"), ["tar.gz"], False),
    (Path("pang.tar.gz"), ["gz", "jpeg"], True),
    (Path("plop.JPEG"), ["jpeg"], True),
    (Path("ping.gz"), ["jpeg", "gz"], True),
    (Path("longer.file.with.dot.as.separator.txt"), ["txt", "gz"], True),
])
def test_is_allowed_file(various_filenames, source, extensions, expected):
    """
    Method should correctly check if file is allowed or not.
    """
    # Rewrite relative path from "expected" to absolute to temporary dir
    source = various_filenames.joinpath(source)

    assert is_allowed_file(source, extensions=extensions) == expected
