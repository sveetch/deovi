import json
import uuid
from pathlib import Path

from deovi.models import Asset
from deovi.utils.tests import dummy_uuid4


def test_creation(monkeypatch):
    """
    Basic model creation.
    """
    monkeypatch.setattr(uuid, "uuid4", dummy_uuid4)

    picsou = Asset(source=Path("/home/cities/duckcity/picsou.jpg"))

    assert picsou.as_coerced() == {
        "source": Path("/home/cities/duckcity/picsou.jpg"),
        "destination": Path("dummy_uuid4.jpg"),
        "checksum": None,
    }

    assert json.loads(picsou.as_json()) == {
        "source": "/home/cities/duckcity/picsou.jpg",
        "destination": "dummy_uuid4.jpg",
        "checksum": None,
    }


def test_checksum(monkeypatch, tmp_path):
    """
    Creation with a checksum.
    """
    monkeypatch.setattr(uuid, "uuid4", dummy_uuid4)

    image = tmp_path / "picsou.jpg"
    image.write_text("Image source picsou.jpg")

    picsou = Asset(source=image, autochecksum=True)

    assert json.loads(picsou.as_json()) == {
        "source": str(image),
        "destination": "dummy_uuid4.jpg",
        "checksum": (
            "b7f247c57ed66b98b0a5fa4913924c57ca619b283405617e8693f59751c53f879e4d5"
            "bb5fe00f4a8740a93f388b9c77472842721b0a4c6ced5940a4d5966d2af"
        ),
    }
