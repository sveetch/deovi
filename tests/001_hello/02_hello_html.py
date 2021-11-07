import pytest

from deovi_client.hello import HelloHTML


def test_default_name():
    """
    When no argument is given, builder should greet the world in a HTML
    paragraph.
    """
    builder = HelloHTML()

    assert builder.greet() == "<p>Hello world!</p>"


@pytest.mark.parametrize("name,container,expected", [
    (
        None,
        "div",
        "<div>Hello world!</div>",
    ),
    (
        "you",
        None,
        "<p>Hello you!</p>",
    ),
    (
        "フランス",
        "h1",
        "<h1>Hello フランス!</h1>",
    ),
])
def test_custom_name(name, container, expected):
    """
    When name or container arguments are given, builder should use them to
    greet.
    """
    builder = HelloHTML(name=name, container=container)

    assert builder.greet() == expected
