import datetime
import json
from pathlib import Path

from freezegun import freeze_time
from freezegun.api import FakeDatetime

from deovi.models import DirectoryInformation, MediaInformation, SerializableList


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

    assert duckcity.as_dict(preserve=True) == {
        "absolute_dir": Path("/home/cities"),
        "checksum": "coin42coin001",
        "manifest": None,
        "medias": [],
        "mtime": FakeDatetime(2012, 10, 15, 10, 0, 0, 1007),
        "name": "duckcity",
        "path": Path("/home/cities/duckcity"),
        "relative_dir": Path("duckcity"),
        "size": 42,
    }

    assert json.loads(duckcity.as_json()) == {
        "path": "/home/cities/duckcity",
        "size": 42,
        "mtime": "2012-10-15T10:00:00.001007",
        "name": "duckcity",
        "absolute_dir": "/home/cities",
        "relative_dir": "duckcity",
        "manifest": None,
        "checksum": "coin42coin001",
        "medias": [],
    }


@freeze_time("2012-10-15 10:00:00.001007")
def test_set_medias():
    """
    Adding medias to a directory
    """
    picsou = MediaInformation(
        path=Path("/home/cities/duckcity/picsou.mp4"),
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

    # Ensure we strictly have the right expected types
    payload = duckcity.as_dict(preserve=True)
    assert isinstance(payload["medias"], list) is True
    assert isinstance(payload["medias"], SerializableList) is False
    assert isinstance(payload["medias"][0], dict) is True
    assert isinstance(payload["medias"][0], MediaInformation) is False
    assert payload == {
        "absolute_dir": Path("/home/cities"),
        "checksum": "coin42coin001",
        "manifest": None,
        "medias": [
            {
                "absolute_dir": Path("/home/cities/duckcity"),
                "checksum": None,
                "container": "MPEG-4",
                "extension": "mp4",
                "manifest": None,
                "mtime": FakeDatetime(2012, 10, 15, 10, 0, 0, 1007),
                "name": "picsou.mp4",
                "name_alt": "",
                "path": Path("/home/cities/duckcity/picsou.mp4"),
                "relative_dir": Path("."),
                "size": 42,
            },
        ],
        "mtime": FakeDatetime(2012, 10, 15, 10, 0, 0, 1007),
        "name": "duckcity",
        "path": Path("/home/cities/duckcity"),
        "relative_dir": Path("duckcity"),
        "size": 42,
    }

    assert json.loads(duckcity.as_json()) == {
        "path": "/home/cities/duckcity",
        "size": 42,
        "mtime": "2012-10-15T10:00:00.001007",
        "name": "duckcity",
        "absolute_dir": "/home/cities",
        "relative_dir": "duckcity",
        "manifest": None,
        "checksum": "coin42coin001",
        "medias": [
            {
                "path": "/home/cities/duckcity/picsou.mp4",
                "size": 42,
                "mtime": "2012-10-15T10:00:00.001007",
                "name": "picsou.mp4",
                "absolute_dir": "/home/cities/duckcity",
                "relative_dir": ".",
                "manifest": None,
                "checksum": None,
                "name_alt": "",
                "extension": "mp4",
                "container": "MPEG-4"
            }
        ],
    }

    # Adding a child after init with set_medias
    donald = MediaInformation(
        path=Path("/home/cities/duckcity/donald.mp4"),
        basepath=Path("/home/cities/duckcity"),
        size=42,
        mtime=datetime.datetime.now(),
    )
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
        "medias": [
            {
                "path": "/home/cities/duckcity/picsou.mp4",
                "size": 42,
                "mtime": "2012-10-15T10:00:00.001007",
                "name": "picsou.mp4",
                "absolute_dir": "/home/cities/duckcity",
                "relative_dir": ".",
                "manifest": None,
                "checksum": None,
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
                "checksum": None,
                "name_alt": "",
                "extension": "mp4",
                "container": "MPEG-4"
            }
        ],
    }

    # Child has been linked to parent
    assert donald.parent == duckcity
