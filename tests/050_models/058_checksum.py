import datetime
import uuid
from pathlib import Path

from freezegun import freeze_time
from freezegun.api import FakeDatetime

from deovi.models import DirectoryInformation, MediaInformation
from deovi.utils.tests import dummy_uuid4


@freeze_time("2012-10-15 10:00:00.001007")
def test_checksum(settings, monkeypatch):
    """
    Creation with a checksum.
    """
    monkeypatch.setattr(uuid, "uuid4", dummy_uuid4)

    media_sample = settings.datas_path / "media_sample"
    pong = media_sample / "ping/pong"

    movie_path = pong / "SampleVideo_720x480_1mb.mkv"

    picsou = MediaInformation(
        path=movie_path,
        basepath=media_sample,
        size=42,
        mtime=datetime.datetime.now(),
        autoload=True,
        autochecksum=True,
        cover_extensions=[".gif", ".jpg"],
    )

    # Add a child during init
    duckcity = DirectoryInformation(
        path=pong,
        basepath=media_sample,
        size=42,
        mtime=datetime.datetime.now(),
        medias=[picsou],
        autoload=True,
        autochecksum=True,
        cover_extensions=[".gif", ".jpg"],
    )

    assert duckcity.as_dict(preserve=True) == {
        "absolute_dir": media_sample / "ping",
        "checksum": (
            "182ab143510afa3dc28a49027da48c46522e2146e037e937f606cba48c7796468e62a2d"
            "2483dc77954709205c1b287172cf53c426b223ec694aa972b53909c57"
        ),
        "manifest": {
            "casting": [],
            "cover": {
                "checksum": (
                    "2921f3808efdd4b47f017ccf286e41968aa72d715668de6a8cfca555a71d242"
                    "6c8ac464825f864edd9e2c8c6ae0ebc95e6d58e3c95862dd101153c5dabab962f"
                ),
                "destination": Path("dummy_uuid4.gif"),
                "source": media_sample / "ping/pong/cover.gif",
            },
            "crew": [],
            "first_air_date": "",
            "genres": [],
            "locked": False,
            "number_of_episodes": None,
            "number_of_seasons": None,
            "original_language": None,
            "overview": None,
            "path": media_sample / "ping/pong/manifest.json",
            "status": None,
            "title": "Pong JSON",
            "tmdb_id": None,
            "tmdb_type": "tv",
        },
        "medias": [
            {
                "absolute_dir": media_sample / "ping/pong",
                "checksum": (
                    "f32113f9482f0066eda25ba8e4c0f55bff900c2763a7d44b66909c50a21fa19d"
                    "11680cda7e590d072e36119488f30e4e8257403b153417255baf0957773ea1e4"
                ),
                "container": "Matroska",
                "extension": "mkv",
                "manifest": {
                    "casting": [],
                    "cover": {
                        "checksum": (
                            "275cd96bc70879e4ff8bbfe06a823e3ae72953887ded2067da05f537"
                            "90fe5e826133051a60de7c47527b1bff9081de40348bbc61fd6cacfb"
                            "6cdf1e2f36534195"
                        ),
                        "destination": Path("dummy_uuid4.jpg"),
                        "source": (
                            media_sample / "ping/pong/SampleVideo_720x480_1mb.jpg"
                        ),
                    },
                    "crew": [],
                    "genres": [],
                    "locked": False,
                    "original_language": None,
                    "overview": None,
                    "path": media_sample / "ping/pong/SampleVideo_720x480_1mb.json",
                    "release_date": "",
                    "status": None,
                    "title": "Sample 720x480 1mb JSON",
                    "tmdb_id": None,
                    "tmdb_type": "movie",
                },
                "mtime": FakeDatetime(2012, 10, 15, 10, 0, 0, 1007),
                "name": "SampleVideo_720x480_1mb.mkv",
                "name_alt": "pong",
                "path": media_sample / "ping/pong/SampleVideo_720x480_1mb.mkv",
                "relative_dir": Path("ping/pong"),
                "size": 42,
            },
        ],
        "mtime": FakeDatetime(2012, 10, 15, 10, 0, 0, 1007),
        "name": "pong",
        "path": media_sample / "ping/pong",
        "relative_dir": Path("ping/pong"),
        "size": 42,
    }
