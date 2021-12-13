from pathlib import Path

import pytest


def test_capitalize(caplog, debug_logger, task_manager):
    """
    Task 'capitalize' just use the String method "capitalize" without any expected
    options.
    """
    assert task_manager.task_capitalize(1, Path("foo")) == (
        Path("foo"), Path("Foo"),
    )
    assert task_manager.task_capitalize(1, Path("FOO")) == (
        Path("FOO"), Path("Foo"),
    )
    assert task_manager.task_capitalize(1, Path("/home/foo.gz")) == (
        Path("/home/foo.gz"), Path("/home/Foo.gz"),
    )

    expected_logs = [
        "├┄ [capitalize]  Foo",
        "├┄ [capitalize]  Foo",
        "├┄ [capitalize]  Foo.gz",
    ]
    assert expected_logs == [rec.message for rec in caplog.records]


def test_lowercase(caplog, debug_logger, task_manager):
    """
    Task 'lowercase' just use the String method "lower" without any expected
    options.
    """
    assert task_manager.task_lowercase(1, Path("Foo")) == (
        Path("Foo"), Path("foo"),
    )
    assert task_manager.task_lowercase(1, Path("FOO")) == (
        Path("FOO"), Path("foo"),
    )
    assert task_manager.task_lowercase(1, Path("/home/FOO.GZ")) == (
        Path("/home/FOO.GZ"), Path("/home/foo.gz"),
    )

    expected_logs = [
        "├┄ [lowercase]  foo",
        "├┄ [lowercase]  foo",
        "├┄ [lowercase]  foo.gz",
    ]
    assert expected_logs == [rec.message for rec in caplog.records]


def test_uppercase(caplog, debug_logger, task_manager):
    """
    Task 'uppercase' just use the String method "upper" without any expected
    options.
    """
    assert task_manager.task_uppercase(1, Path("foo")) == (
        Path("foo"), Path("FOO"),
    )
    assert task_manager.task_uppercase(1, Path("Foo")) == (
        Path("Foo"), Path("FOO"),
    )
    assert task_manager.task_uppercase(1, Path("/home/foo.gz")) == (
        Path("/home/foo.gz"), Path("/home/FOO.GZ"),
    )

    expected_logs = [
        "├┄ [uppercase]  FOO",
        "├┄ [uppercase]  FOO",
        "├┄ [uppercase]  FOO.GZ",
    ]
    assert expected_logs == [rec.message for rec in caplog.records]


@pytest.mark.parametrize("source, expected, expected_logs", [
    (
        "Foo",
        "Foo",
        ["├┄ [underscore_to_dash]  Foo"],
    ),
    (
        "Foo.txt",
        "Foo.txt",
        ["├┄ [underscore_to_dash]  Foo.txt"],
    ),
    (
        "Foo_-_Bar-ping.txt",
        "Foo_Bar-ping.txt",
        ["├┄ [underscore_to_dash]  Foo_Bar-ping.txt"],
    ),
    (
        "Foo_-_Bar_-_ping.txt",
        "Foo_Bar_ping.txt",
        ["├┄ [underscore_to_dash]  Foo_Bar_ping.txt"],
    ),
    (
        "/home/Foo_-_Bar_-_ping.txt",
        "/home/Foo_Bar_ping.txt",
        ["├┄ [underscore_to_dash]  Foo_Bar_ping.txt"],
    ),
])
def test_underscore_to_dash(caplog, debug_logger, task_manager, source,
                            expected, expected_logs):
    """
    Method should catch the divider segment and join them according to options.
    """
    result = task_manager.task_underscore_to_dash(1, Path(source))

    assert result == (
        Path(source),
        Path(expected),
    )

    assert expected_logs == [rec.message for rec in caplog.records]


def test_add_prefix(caplog, debug_logger, task_manager):
    """
    Task 'add_prefix' just add a prefix before source string.
    """
    assert task_manager.task_add_prefix(1, Path("Foo"), prefix="mip") == (
        Path("Foo"), Path("mipFoo"),
    )
    assert task_manager.task_add_prefix(1, Path("Foo"), prefix="_") == (
        Path("Foo"), Path("_Foo"),
    )
    assert task_manager.task_add_prefix(1, Path("/home/Foo.gz"), prefix="mip_") == (
        Path("/home/Foo.gz"), Path("/home/mip_Foo.gz"),
    )

    expected_logs = [
        "├┄ [add_prefix]  mipFoo",
        "├┄ [add_prefix]  _Foo",
        "├┄ [add_prefix]  mip_Foo.gz",
    ]
    assert expected_logs == [rec.message for rec in caplog.records]


@pytest.mark.parametrize("index, source, options, expected, expected_logs", [
    (
        1,
        "Foo",
        {"zfill": 2},
        "01_Foo",
        ["├┄ [numerate]  01_Foo"],
    ),
    (
        42,
        "Foo",
        {"zfill": 2},
        "42_Foo",
        ["├┄ [numerate]  42_Foo"],
    ),
    (
        42,
        "Foo",
        {"zfill": 1},
        "42_Foo",
        ["├┄ [numerate]  42_Foo"],
    ),
    (
        42,
        "Foo",
        {"zfill": -1},
        "42_Foo",
        ["├┄ [numerate]  42_Foo"],
    ),
    (
        3200,
        "Foo",
        {"zfill": 2},
        "3200_Foo",
        ["├┄ [numerate]  3200_Foo"],
    ),
    (
        3200,
        "Foo",
        {"zfill": 8},
        "00003200_Foo",
        ["├┄ [numerate]  00003200_Foo"],
    ),
    (
        1,
        "Foo",
        {"zfill": 2, "start": 0},
        "01_Foo",
        ["├┄ [numerate]  01_Foo"],
    ),
    (
        1,
        "Foo",
        {"zfill": 2, "start": 5},
        "06_Foo",
        ["├┄ [numerate]  06_Foo"],
    ),
    (
        32,
        "Foo",
        {"zfill": 1, "start": 5},
        "37_Foo",
        ["├┄ [numerate]  37_Foo"],
    ),
    (
        32,
        "/home/Foo.gz",
        {"zfill": 1, "start": 5},
        "/home/37_Foo.gz",
        ["├┄ [numerate]  37_Foo.gz"],
    ),
])
def test_numerate(caplog, debug_logger, task_manager, index, source, options, expected,
                  expected_logs):
    """
    Method should format index and add it at the start of the string.
    """
    result = task_manager.task_numerate(index, Path(source), **options)

    assert result == (
        Path(source),
        Path(expected),
    )

    assert expected_logs == [rec.message for rec in caplog.records]


@pytest.mark.parametrize("source, options, expected, expected_logs", [
    (
        "Foo",
        {
            "divider": ".",
            "slice_start": 0,
        },
        "Foo",
        ["├┄ [catch_segments]  Foo"],
    ),
    (
        "Foo.txt",
        {
            "divider": ".",
            "slice_start": 0,
        },
        "Foo.txt",
        ["├┄ [catch_segments]  Foo.txt"],
    ),
    (
        "One.two.three.four.five.txt",
        {
            "divider": ".",
            "slice_start": 0,
        },
        "One-two-three-four-five.txt",
        ["├┄ [catch_segments]  One-two-three-four-five.txt"],
    ),
    (
        "One.two.three.four.five..txt",
        {
            "divider": ".",
            "slice_start": 0,
        },
        "One-two-three-four-five-.txt",
        ["├┄ [catch_segments]  One-two-three-four-five-.txt"],
    ),
    (
        "One.two.three.four.last.txt",
        {
            "divider": ".",
            "slice_start": 0,
            "slice_end": -1,
        },
        "One-two-three-four.txt",
        ["├┄ [catch_segments]  One-two-three-four.txt"],
    ),
    (
        "One.two.txt",
        {
            "divider": ".",
            "slice_start": 0,
            "slice_end": 3,
        },
        "One-two.txt",
        ["├┄ [catch_segments]  One-two.txt"],
    ),
    (
        "One.two.three.nope.niet.txt",
        {
            "divider": ".",
            "slice_start": 0,
            "slice_end": 3,
        },
        "One-two-three.txt",
        ["├┄ [catch_segments]  One-two-three.txt"],
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
        ["├┄ [catch_segments]  One_two_three.txt"],
    ),
    (
        "One.two.three.four.five.six.txt",
        {
            "divider": ".",
            "joiner": "_",
            "slice_start": 2,
            "slice_end": 3,
        },
        "three.txt",
        ["├┄ [catch_segments]  three.txt"],
    ),
    (
        "One.two.three.four.five.six.txt",
        {
            "divider": ".",
            "joiner": "_",
            "slice_start": 2,
            "slice_end": -2,
        },
        "three_four.txt",
        ["├┄ [catch_segments]  three_four.txt"],
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
        ["├┄ [catch_segments]  One_two_three four_five.txt"],
    ),
])
def test_catch_segments(caplog, debug_logger, task_manager, source, options, expected,
                        expected_logs):
    """
    Method should catch the divider segment and join them according to options.
    """
    result = task_manager.task_catch_segments(1, Path(source), **options)

    assert result == (
        Path(source),
        Path(expected),
    )

    assert expected_logs == [rec.message for rec in caplog.records]


@pytest.mark.parametrize("source, options, expected, expected_logs", [
    (
        "Foo",
        {
            "from": "o",
            "to": "a",
        },
        "Faa",
        ["├┄ [replace]  Faa"],
    ),
    (
        "FooFoo",
        {
            "from": "Foo",
            "to": "Bar",
        },
        "BarBar",
        ["├┄ [replace]  BarBar"],
    ),
    (
        "Foo_Foo.Foo.txt",
        {
            "from": "Foo",
            "to": "Bar",
        },
        "Bar_Bar.Bar.txt",
        ["├┄ [replace]  Bar_Bar.Bar.txt"],
    ),
    (
        "Foo.txt",
        {
            "from": ".txt",
            "to": ".rst",
        },
        "Foo.rst",
        ["├┄ [replace]  Foo.rst"],
    ),
])
def test_replace(caplog, debug_logger, task_manager, source, options, expected,
                 expected_logs):
    """
    Method should replace every occurences of a string in source by another one.
    """
    result = task_manager.task_replace(1, Path(source), **options)

    assert result == (
        Path(source),
        Path(expected),
    )

    assert expected_logs == [rec.message for rec in caplog.records]
