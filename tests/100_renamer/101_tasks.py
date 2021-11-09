import pytest

from deovi_client.exceptions import TaskValidationError
from deovi_client.renamer.tasks import (
    task_options_validator, capitalize, lowercase, uppercase,
    convert_underscore_to_dash, add_prefix, numerate, catch_segments, replace
)


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
def test_task_options_validator_success(required, options):
    """
    Validator should not raise error when required options are respected.
    """
    assert task_options_validator("Foo", required, **options) is True


@pytest.mark.parametrize("required, options, expected", [
    (
        ["plip"],
        {},
        "🔖 Task 'Foo' require option(s): plip"
    ),
    (
        ["plip", "ping"],
        {
            "ping": ".",
        },
        "🔖 Task 'Foo' require option(s): plip"
    ),
    (
        ["plip", "ping", "ping"],
        {},
        "🔖 Task 'Foo' require option(s): ping, plip"
    ),
    (
        ["c", "a", "b"],
        {},
        "🔖 Task 'Foo' require option(s): a, b, c"
    ),
])
def test_task_options_validator_error(required, options, expected):
    """
    Validator should raise error for missing options.
    """
    with pytest.raises(TaskValidationError) as excinfo:
        task_options_validator("Foo", required, **options)

    assert str(excinfo.value) == expected


def test_numerate_validation():
    """
    Task 'numerate' options should be correctly validated
    """
    with pytest.raises(TaskValidationError) as excinfo:
        numerate(1, "Foo")

    assert str(excinfo.value) == (
        "🔖 Task 'numerate' require option(s): zfill"
    )


def test_add_prefix_validation():
    """
    Task 'add_prefix' options should be correctly validated
    """
    with pytest.raises(TaskValidationError) as excinfo:
        add_prefix(1, "Foo")

    assert str(excinfo.value) == (
        "🔖 Task 'add_prefix' require option(s): prefix"
    )


def test_catch_segments_validation():
    """
    Task 'catch_segments' options should be correctly validated
    """
    with pytest.raises(TaskValidationError) as excinfo:
        catch_segments(1, "Foo")

    assert str(excinfo.value) == (
        "🔖 Task 'catch_segments' require option(s): divider, slice_start"
    )


def test_replace_validation():
    """
    Task 'replace' options should be correctly validated
    """
    with pytest.raises(TaskValidationError) as excinfo:
        replace(1, "Foo")

    assert str(excinfo.value) == (
        "🔖 Task 'replace' require option(s): from, to"
    )


def test_capitalize():
    """
    Task 'capitalize' just use the String method "capitalize" without any expected
    options.
    """
    assert capitalize(1, "foo")[1] == "Foo"
    assert capitalize(1, "FOO")[1] == "Foo"


def test_lowercase():
    """
    Task 'lowercase' just use the String method "lower" without any expected
    options.
    """
    assert lowercase(1, "Foo")[1] == "foo"
    assert lowercase(1, "FOO")[1] == "foo"


def test_uppercase():
    """
    Task 'uppercase' just use the String method "upper" without any expected
    options.
    """
    assert uppercase(1, "foo")[1] == "FOO"
    assert uppercase(1, "Foo")[1] == "FOO"


def test_add_prefix():
    """
    Task 'add_prefix' just add a prefix before source string.
    """
    assert add_prefix(1, "Foo", prefix="mip")[1] == "mipFoo"
    assert add_prefix(1, "Foo", prefix="_")[1] == "_Foo"


@pytest.mark.parametrize("source, expected", [
    (
        "Foo",
        "Foo",
    ),
    (
        "Foo.txt",
        "Foo.txt",
    ),
    (
        "Foo_-_Bar-ping.txt",
        "Foo_Bar-ping.txt",
    ),
    (
        "Foo_-_Bar_-_ping.txt",
        "Foo_Bar_ping.txt",
    ),
])
def test_convert_underscore_to_dash(source, expected):
    """
    Method should catch the divider segment and join them according to options.
    """
    result = convert_underscore_to_dash(1, source)

    assert result[1] == expected


@pytest.mark.parametrize("source, options, expected", [
    (
        "Foo",
        {
            "divider": ".",
            "slice_start": 0,
        },
        "Foo",
    ),
    (
        "Foo.txt",
        {
            "divider": ".",
            "slice_start": 0,
        },
        "Foo.txt",
    ),
    (
        "One.two.three.four.five.txt",
        {
            "divider": ".",
            "slice_start": 0,
        },
        "One-two-three-four-five.txt",
    ),
    (
        "One.two.three.four.five..txt",
        {
            "divider": ".",
            "slice_start": 0,
        },
        "One-two-three-four-five-.txt",
    ),
    (
        "One.two.three.four.last.txt",
        {
            "divider": ".",
            "slice_start": 0,
            "slice_end": -1,
        },
        "One-two-three-four.txt",
    ),
    (
        "One.two.txt",
        {
            "divider": ".",
            "slice_start": 0,
            "slice_end": 3,
        },
        "One-two.txt",
    ),
    (
        "One.two.three.nope.niet.txt",
        {
            "divider": ".",
            "slice_start": 0,
            "slice_end": 3,
        },
        "One-two-three.txt",
    ),
    (
        "One.two.three.nope.niet.txt",
        {
            "divider": ".",
            "joiner": "_",
            "slice_start": 0,
            "slice_end": 3,
        },
        "One_two_three.txt",
    ),
    (
        "One-two-three four-five.txt",
        {
            "divider": "-",
            "joiner": "_",
            "slice_start": 0,
            "slice_end": 4,
        },
        "One_two_three four_five.txt",
    ),
])
def test_catch_segments(source, options, expected):
    """
    Method should catch the divider segment and join them according to options.
    """
    result = catch_segments(1, source, **options)

    assert result[1] == expected


@pytest.mark.parametrize("index, source, options, expected", [
    (
        1,
        "Foo",
        {"zfill": 2},
        "01_Foo",
    ),
    (
        42,
        "Foo",
        {"zfill": 2},
        "42_Foo",
    ),
    (
        42,
        "Foo",
        {"zfill": 1},
        "42_Foo",
    ),
    (
        42,
        "Foo",
        {"zfill": -1},
        "42_Foo",
    ),
    (
        3200,
        "Foo",
        {"zfill": 2},
        "3200_Foo",
    ),
    (
        3200,
        "Foo",
        {"zfill": 8},
        "00003200_Foo",
    ),
    (
        1,
        "Foo",
        {"zfill": 2, "start": 0},
        "01_Foo",
    ),
    (
        1,
        "Foo",
        {"zfill": 2, "start": 5},
        "06_Foo",
    ),
    (
        32,
        "Foo",
        {"zfill": 1, "start": 5},
        "37_Foo",
    ),
])
def test_numerate(index, source, options, expected):
    """
    Method should format index and add it at the start of the string.
    """
    result = numerate(index, source, **options)

    assert result[1] == expected


@pytest.mark.parametrize("source, options, expected", [
    (
        "Foo",
        {
            "from": "o",
            "to": "a",
        },
        "Faa",
    ),
    (
        "FooFoo",
        {
            "from": "Foo",
            "to": "Bar",
        },
        "BarBar",
    ),
    (
        "Foo_Foo.Foo.txt",
        {
            "from": "Foo",
            "to": "Bar",
        },
        "Bar_Bar.Bar.txt",
    ),
    (
        "Foo.txt",
        {
            "from": ".txt",
            "to": ".rst",
        },
        "Foo.rst",
    ),
])
def test_replace(source, options, expected):
    """
    Method should replace every occurences of a string in source by another one.
    """
    result = replace(1, source, **options)

    assert result[1] == expected
