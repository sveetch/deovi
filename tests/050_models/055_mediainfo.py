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


@freeze_time("2012-10-15 10:00:00.001007")
def test_checksum(tmp_path):
    """
    Creation with a checksum.
    """
    movie = tmp_path / "picsou.mp4"
    movie.write_text("Movie source picsou.mp4")

    picsou = MediaInformation(
        path=movie,
        basepath=tmp_path,
        size=42,
        mtime=datetime.datetime.now(),
        autochecksum=True,
    )

    assert json.loads(picsou.as_json()) == {
        "path": str(movie),
        "size": 42,
        "mtime": "2012-10-15T10:00:00.001007",
        "name": "picsou.mp4",
        "absolute_dir": str(tmp_path),
        "relative_dir": ".",
        "manifest": None,
        "checksum": (
            "cae6f0286d8b66328019f09707ec9493e405b2549436714022dbd1d38b1deb606e74cd"
            "942fab40bb08d464e57a273315b3af34694faa6e3c3c3419060d035a61"
        ),
        "container": "MPEG-4",
        "name_alt": "",
        "extension": "mp4",
    }
