from pathlib import Path

import pytest

from deovi.collector import Collector


@pytest.mark.parametrize("filepath, parent, basename", [
    ("dump.json", Path("."), "dump"),
    ("foo/dump.json", Path("foo"), "dump"),
    ("/home/foo/dump.bar.json", Path("/home/foo"), "dump"),
])
def test_collector_get_directory_storage(filepath, parent, basename):
    """
    A directory should be computed from given filename plus a hashid with an exact
    length.
    """
    collector = Collector(None)
    dirname = collector.get_directory_storage(Path(filepath))

    name, hashid = str(dirname).split("_")

    assert dirname.parent == parent
    assert Path(name).stem == basename
    assert len(hashid) == 20
