import logging

import pytest

from click.testing import CliRunner

from deovi_client.cli.entrypoint import cli_frontend


APPLABEL = "deovi-client"


def test_greet_basic(caplog):
    """
    The command is executable without any arguments and then should greet the
    world in plain text.
    """
    runner = CliRunner()

    # Invoke the commandline from the CliRunner
    result = runner.invoke(cli_frontend, ["greet"])

    # To debug logs on fail
    # Commandline full output
    print("=> result.output <=")
    print(result.output)
    print()
    # Recorded logs as tuples
    print("=> caplog.record_tuples <=")
    print(caplog.record_tuples)
    print()
    # Raise possible exception from commandline, useful when there is an
    # unexpected exception during execution
    print("=> result.exception <=")
    print(result.exception)
    if result.exception:
        raise result.exception

    # Success signal from execution
    assert result.exit_code == 0

    # Expected basic output
    assert result.output == "Hello world!\n"

    # Empty logs is expected
    assert caplog.record_tuples == []


def test_greet_custom_name(caplog):
    """
    The command is executable without any arguments and then should greet the
    world in plain text.
    """
    runner = CliRunner()

    # Invoke the commandline from the CliRunner
    result = runner.invoke(cli_frontend, ["greet", "foobar"])

    # Success signal from execution
    assert result.exit_code == 0

    # Expected basic output
    assert result.output == "Hello foobar!\n"

    # Empty logs is expected
    assert caplog.record_tuples == []


def test_greet_basic_verbose(caplog):
    """
    Without any arguments and verbose logs should return some
    debugging informations.
    """
    runner = CliRunner()

    result = runner.invoke(cli_frontend, [
        "-v", "5",
        "greet",
    ])

    assert result.exit_code == 0

    # Expected logs
    assert caplog.record_tuples == [
        (APPLABEL, logging.DEBUG, "Required format: plain"),
        (APPLABEL, logging.DEBUG, "Required container: None"),
    ]


def test_greet_html_default(caplog):
    """
    With argument "format" set for HTML the command should return its text in
    default paragraph element.
    """
    runner = CliRunner()

    result = runner.invoke(cli_frontend, [
        "greet",
        "-f", "html",
    ])

    assert result.exit_code == 0

    # Expected basic output
    assert result.output == "<p>Hello world!</p>\n"

    assert caplog.record_tuples == []


def test_greet_html_div(caplog):
    """
    With argument "format" set for HTML an container to "div" the command
    should return its text in a "div" element.
    """
    runner = CliRunner()

    result = runner.invoke(cli_frontend, [
        "greet",
        "-f", "html",
        "-c", "div"
    ])

    assert result.exit_code == 0

    # Expected basic output
    assert result.output == "<div>Hello world!</div>\n"

    assert caplog.record_tuples == []


def test_greet_plain_div(caplog):
    """
    Without "format" argument set to "html", the "container" argument has no
    sense and will output a warning.
    """
    runner = CliRunner()

    result = runner.invoke(cli_frontend, [
        "greet",
        "-c", "div"
    ])

    assert result.exit_code == 0

    assert caplog.record_tuples == [
        (
            APPLABEL,
            logging.WARNING,
            "Defining a HTML container in plain format has no sense."
        )
    ]


@pytest.mark.parametrize("options,name,expected", [
    (
        [],
        None,
        "Hello world!\n",
    ),
    (
        [
            "-f", "plain",
        ],
        None,
        "Hello world!\n",
    ),
    (
        [
            "-f", "html",
        ],
        "foobar",
        "<p>Hello foobar!</p>\n",
    ),
    (
        [
            "-f", "html",
            "-c", "strong",
        ],
        "foobar",
        "<strong>Hello foobar!</strong>\n",
    ),
    (
        [
            "--format", "html",
            "--container", "strong",
        ],
        "téléphone",
        "<strong>Hello téléphone!</strong>\n",
    ),
])
def test_greet_various_cases(caplog, options, name, expected):
    """
    Various cases successful demonstrations with parametrize.
    """
    runner = CliRunner()

    cli_args = ["greet"] + options
    if name:
        cli_args = cli_args + [name]

    result = runner.invoke(cli_frontend, cli_args)

    assert expected == result.output

    assert result.exit_code == 0

    assert caplog.record_tuples == []
