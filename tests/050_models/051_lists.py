from pathlib import Path

from deovi.models.assets import Asset
from deovi.models.lists import SerializableList


def test_serializablelist_fundamentals():
    """
    Ensure SerializableList is working like a list.
    """
    empty = SerializableList()
    assert len(empty) == 0

    # Basic functions
    pistache = SerializableList(["youpi", "niet"])
    pistache.append("piou")
    pistache.remove("niet")
    pistache.extend(["flip"])
    assert [v for v in pistache] == ["youpi", "piou", "flip"]
    assert len(pistache) == 3
    assert set(pistache) is not None
    assert ("niet" in pistache) is False
    assert ("piou" in pistache) is True

    # Sorted is working but return a list, not SerializableList anymore
    assert sorted(pistache) == ["flip", "piou", "youpi"]


def test_serializablelist_preserved():
    """
    Preserve option on method 'as_dict()' is working as expected.

    NOTE: preserve option name may not be the best because it does the inverse behavior
    (preserve model object when False, turn model object to Python builtin when True)
    """
    ping = Asset(source=Path("/home/foo/ping.png"))
    pong = Asset(source=Path("/home/foo/pong.png"))

    pistache = SerializableList(["youpi", ping, "niet", pong])
    assert len(pistache) == 4

    # Without enabled option, model objects are preserved
    flat_list = pistache.as_dict()
    assert flat_list[0] == "youpi"
    assert flat_list[2] == "niet"
    assert isinstance(flat_list[1], Asset) is True
    assert isinstance(flat_list[3], Asset) is True
    assert flat_list[1].source == ping.source
    assert flat_list[3].source == pong.source

    # Without enable option, model objects with as_dict are serialized to Python
    # builtins
    flat_list = pistache.as_dict(preserve=True)
    assert flat_list[0] == "youpi"
    assert flat_list[2] == "niet"
    assert isinstance(flat_list[1], dict) is True
    assert isinstance(flat_list[3], dict) is True
    assert flat_list[1]["source"] == ping.source
    assert flat_list[3]["source"] == pong.source
