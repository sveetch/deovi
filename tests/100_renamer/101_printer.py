import logging

import pytest

from deovi_client.renamer.printer import PrinterInterface


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
    assert result == " ┍━ {1} Foo"

    result = printer._row_format(message="Foo")
    assert result == " ├─ Foo"

    result = printer._row_format(message="Foo", state="debug")
    assert result == " ├┄ Foo"

    result = printer._row_format(message="Foo", state="end")
    assert result == " ┕━ Foo"

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
        " ┍━ [foo]        Foo bar",
        " ┍━ [ping pong]  Pang pang",
    ]


def test_printer_log(caplog, debug_logger):
    """
    Method "log" should log message at required level and optional formatting
    depending keyword arguments.
    """
    printer = PrinterInterface()

    result = printer.log("debug", "Foo!")
    assert [(logging.DEBUG, "Foo!")] == [
        (rec.levelno, rec.message) for rec in caplog.records
    ]
    caplog.clear()

    result = printer.log("info", "Bar!")
    assert [(logging.INFO, "Bar!")] == [
        (rec.levelno, rec.message) for rec in caplog.records
    ]
    caplog.clear()

    result = printer.log("info", "Chu", label="Pika", state="start")
    assert [(logging.INFO, " ┍━ [Pika]  Chu")] == [
        (rec.levelno, rec.message) for rec in caplog.records
    ]
    caplog.clear()

    result = printer.log("warning", "Tchip", state="end")
    assert [(logging.WARNING, " ┕━ Tchip")] == [
        (rec.levelno, rec.message) for rec in caplog.records
    ]
    caplog.clear()


def test_printer_log_levels(caplog, debug_logger):
    """
    Shortcut logging level methods should log message in their own level only and with
    possible formatting.
    """
    printer = PrinterInterface()

    result = printer.log_debug("Foo!")
    assert [(logging.DEBUG, "Foo!")] == [
        (rec.levelno, rec.message) for rec in caplog.records
    ]
    caplog.clear()

    result = printer.log_info("Bar!")
    assert [(logging.INFO, "Bar!")] == [
        (rec.levelno, rec.message) for rec in caplog.records
    ]
    caplog.clear()

    result = printer.log_info("Chu", label="Pika", state="start")
    assert [(logging.INFO, " ┍━ [Pika]  Chu")] == [
        (rec.levelno, rec.message) for rec in caplog.records
    ]
    caplog.clear()

    result = printer.log_warning("Tchip", state="end")
    assert [(logging.WARNING, " ┕━ Tchip")] == [
        (rec.levelno, rec.message) for rec in caplog.records
    ]
    caplog.clear()
