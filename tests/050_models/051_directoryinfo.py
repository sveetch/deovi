import datetime
import json
from pathlib import Path

from freezegun import freeze_time

from deovi.models import DirectoryInformation, MediaInformation


@freeze_time("2012-10-15 10:00:00.001007")
def test_creation():
    """
    Basic model creation
    """
    duckcity = DirectoryInformation(
        path=Path("/home/cities/duckcity"),
        basepath=Path("/home/cities"),
        size=42,
        mtime=datetime.datetime.now(),
        checksum="coin42coin001",
    )

    assert json.loads(duckcity.as_json()) == {
        "path": "/home/cities/duckcity",
        "size": 42,
        "mtime": "2012-10-15T10:00:00.001007",
        "name": "duckcity",
        "absolute_dir": "/home/cities",
        "relative_dir": "duckcity",
        "manifest": None,
        "checksum": "coin42coin001",
        "directories": [],
        "medias": [],
    }

    killmotor_hill = DirectoryInformation(
        path=Path("/home/cities/duckcity/killmotor_hill"),
        basepath=Path("/home/cities"),
        size=42,
        mtime=datetime.datetime.now(),
        checksum="coin42coin001",
    )
    duckcity.set_directories([killmotor_hill])
    assert killmotor_hill.parent == duckcity

    assert json.loads(duckcity.as_json()) == {
        "path": "/home/cities/duckcity",
        "size": 42,
        "mtime": "2012-10-15T10:00:00.001007",
        "name": "duckcity",
        "absolute_dir": "/home/cities",
        "relative_dir": "duckcity",
        "manifest": None,
        "checksum": "coin42coin001",
        "directories": [
            {
                "path": "/home/cities/duckcity/killmotor_hill",
                "size": 42,
                "mtime": "2012-10-15T10:00:00.001007",
                "name": "killmotor_hill",
                "absolute_dir": "/home/cities/duckcity",
                "relative_dir": "duckcity/killmotor_hill",
                "manifest": None,
                "checksum": "coin42coin001",
                "directories": [],
                "medias": []
            }
        ],
        "medias": [],
    }


@freeze_time("2012-10-15 10:00:00.001007")
def test_set_medias():
    """
    TODO
    """
    picsou = MediaInformation(
        path=Path("/home/cities/duckcity/picsou.mp4"),
        basepath=Path("/home/cities/duckcity"),
        size=42,
        mtime=datetime.datetime.now(),
    )

    donald = MediaInformation(
        path=Path("/home/cities/duckcity/donald.mp4"),
        basepath=Path("/home/cities/duckcity"),
        size=42,
        mtime=datetime.datetime.now(),
    )

    # Add a child during init
    duckcity = DirectoryInformation(
        path=Path("/home/cities/duckcity"),
        basepath=Path("/home/cities"),
        size=42,
        mtime=datetime.datetime.now(),
        checksum="coin42coin001",
        medias=[picsou],
    )

    # Child has been linked to parent
    assert picsou.parent == duckcity

    assert json.loads(duckcity.as_json()) == {
        "path": "/home/cities/duckcity",
        "size": 42,
        "mtime": "2012-10-15T10:00:00.001007",
        "name": "duckcity",
        "absolute_dir": "/home/cities",
        "relative_dir": "duckcity",
        "manifest": None,
        "checksum": "coin42coin001",
        "directories": [],
        "medias": [
            {
                "path": "/home/cities/duckcity/picsou.mp4",
                "size": 42,
                "mtime": "2012-10-15T10:00:00.001007",
                "name": "picsou.mp4",
                "absolute_dir": "/home/cities/duckcity",
                "relative_dir": ".",
                "manifest": None,
                "name_alt": "",
                "extension": "mp4",
                "container": "MPEG-4"
            }
        ],
    }

    # Adding a child after init with set_medias
    duckcity.set_medias([donald])
    assert json.loads(duckcity.as_json()) == {
        "path": "/home/cities/duckcity",
        "size": 42,
        "mtime": "2012-10-15T10:00:00.001007",
        "name": "duckcity",
        "absolute_dir": "/home/cities",
        "relative_dir": "duckcity",
        "manifest": None,
        "checksum": "coin42coin001",
        "directories": [],
        "medias": [
            {
                "path": "/home/cities/duckcity/picsou.mp4",
                "size": 42,
                "mtime": "2012-10-15T10:00:00.001007",
                "name": "picsou.mp4",
                "absolute_dir": "/home/cities/duckcity",
                "relative_dir": ".",
                "manifest": None,
                "name_alt": "",
                "extension": "mp4",
                "container": "MPEG-4"
            },
            {
                "path": "/home/cities/duckcity/donald.mp4",
                "size": 42,
                "mtime": "2012-10-15T10:00:00.001007",
                "name": "donald.mp4",
                "absolute_dir": "/home/cities/duckcity",
                "relative_dir": ".",
                "manifest": None,
                "name_alt": "",
                "extension": "mp4",
                "container": "MPEG-4"
            }
        ],
    }

    # Child has been linked to parent
    assert donald.parent == duckcity
