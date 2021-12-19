import logging

import pytest

from deovi.renamer.printer import PrinterInterface


@pytest.mark.parametrize("length, template, expected_indent, expected_indice", [
    (
        0, "{{{i}}}━",
        4, "{0}━"
    ),
    (
        1, "{{{i}}}━",
        4, "{1}━"
    ),
    (
        42, "{{{i}}}━",
        5, "{42}━"
    ),
    (
        130, "{{{i}}}━",
        6, "{130}━"
    ),
    (
        42, "{i}",
        2, "42"
    ),
    (
        42, "-[{i}]-",
        6, "-[42]-"
    ),
])
def test_get_indentation_infos(length, template, expected_indent, expected_indice):
    """
    Method should return correctly indentation length to use and indice formatter
    function.
    """
    printer = PrinterInterface()

    indent_length, indicer = printer.get_indentation_infos(length, template)

    assert indent_length == expected_indent
    assert indicer(length) == expected_indice


@pytest.mark.parametrize("length, value, expected_indice", [
    (
        0, 1, "[1]"
    ),
    (
        1, 9, "[9]"
    ),
    (
        20, 9, "[09]"
    ),
    (
        20, 19, "[19]"
    ),
    (
        100, 9, "[009]"
    ),
    (
        100, 19, "[019]"
    ),
    (
        100, 101, "[101]"
    ),
])
def test_get_indentation_infos_zfill(length, value, expected_indice):
    """
    Ensure zfill is correctly computed and used in indice formatter function.
    """
    printer = PrinterInterface()

    template = "[{i}]"

    indent_length, indicer = printer.get_indentation_infos(length, template)

    assert indicer(value) == expected_indice


def test_printer_set_label_length():
    """
    Method should return the longest length from keys.
    """
    printer = PrinterInterface()

    assert printer.set_label_length([
        ("foo", True),
        ("ping pong", True),
    ]) == 9


def test_printer_formatter():
    """
    Method should output formatted string as expected.
    """
    printer = PrinterInterface()

    result = printer._row_format(message="{1} Foo", state="start")
    assert result == "┍━ {1} Foo"

    result = printer._row_format(message="Foo")
    assert result == "├─ Foo"

    result = printer._row_format(message="Foo", state="debug")
    assert result == "├┄ Foo"

    result = printer._row_format(message="Foo", state="end")
    assert result == "┕━ Foo"

    data = [
        ("foo", "Foo bar"),
        ("ping pong", "Pang pang"),
    ]
    printer.max_label = printer.set_label_length(data)

    results = []
    for i, item in enumerate(data):
        results.append(
            printer._row_format(label=item[0], message=item[1], state="start")
        )

    assert results == [
        "┍━ [foo]        Foo bar",
        "┍━ [ping pong]  Pang pang",
    ]


def test_printer_log(caplog, debug_logger):
    """
    Method "log" should log message at required level and optional formatting
    depending keyword arguments.
    """
    printer = PrinterInterface()

    printer.log("debug", "Foo!")
    assert [(logging.DEBUG, "Foo!")] == [
        (rec.levelno, rec.message) for rec in caplog.records
    ]
    caplog.clear()

    printer.log("info", "Bar!")
    assert [(logging.INFO, "Bar!")] == [
        (rec.levelno, rec.message) for rec in caplog.records
    ]
    caplog.clear()

    printer.log("info", "Chu", label="Pika", state="start")
    assert [(logging.INFO, "┍━ [Pika]  Chu")] == [
        (rec.levelno, rec.message) for rec in caplog.records
    ]
    caplog.clear()

    printer.log("warning", "Tchip", state="end")
    assert [(logging.WARNING, "┕━ Tchip")] == [
        (rec.levelno, rec.message) for rec in caplog.records
    ]
    caplog.clear()


def test_printer_log_levels(caplog, debug_logger):
    """
    Shortcut logging level methods should log message in their own level only and with
    possible formatting.
    """
    printer = PrinterInterface()

    printer.log_debug("Foo!")
    assert [(logging.DEBUG, "Foo!")] == [
        (rec.levelno, rec.message) for rec in caplog.records
    ]
    caplog.clear()

    printer.log_info("Bar!")
    assert [(logging.INFO, "Bar!")] == [
        (rec.levelno, rec.message) for rec in caplog.records
    ]
    caplog.clear()

    printer.log_info("Chu", label="Pika", state="start")
    assert [(logging.INFO, "┍━ [Pika]  Chu")] == [
        (rec.levelno, rec.message) for rec in caplog.records
    ]
    caplog.clear()

    printer.log_warning("Tchip", state="end")
    assert [(logging.WARNING, "┕━ Tchip")] == [
        (rec.levelno, rec.message) for rec in caplog.records
    ]
    caplog.clear()
