import datetime
import json
from pathlib import Path

from freezegun import freeze_time

from deovi.models import MediaInformation


@freeze_time("2012-10-15 10:00:00.001007")
def test_creation():
    """
    Basic model creation
    """
    picsou = MediaInformation(
        path=Path("/home/cities/duckcity/picsou.mp4"),
        basepath=Path("/home/cities/duckcity"),
        size=42,
        checksum="plop",
        mtime=datetime.datetime.now(),
    )

    assert json.loads(picsou.as_json()) == {
        "path": "/home/cities/duckcity/picsou.mp4",
        "size": 42,
        "mtime": "2012-10-15T10:00:00.001007",
        "name": "picsou.mp4",
        "absolute_dir": "/home/cities/duckcity",
        "relative_dir": ".",
        "manifest": None,
        "checksum": "plop",
        "container": "MPEG-4",
        "name_alt": "",
        "extension": "mp4",
    }
