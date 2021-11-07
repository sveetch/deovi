import pytest

from deovi_client.hello import HelloBase
from deovi_client.exceptions import DummyError


def test_default_name():
    """
    When name argument is not given, builder should greet the world.
    """
    builder = HelloBase()

    assert builder.greet() == "Hello world!"


@pytest.mark.parametrize("name,expected", [
    (
        "you",
        "Hello you!",
    ),
    (
        "Jean Michel",
        "Hello Jean Michel!",
    ),
    (
        "フランス",
        "Hello フランス!",
    ),
])
def test_custom_name(name, expected):
    """
    When name argument is given, builder should greet given name.
    """
    builder = HelloBase(name=name)

    assert builder.greet() == expected


def test_bye():
    """
    Hello builder does not like to say goodbye and so raise an error.
    """
    builder = HelloBase()

    with pytest.raises(DummyError) as excinfo:
        builder.bye()

    assert "I don't like to say goodbye." == str(excinfo.value)
