from pathlib import Path

import deovi


API_FILEKEY_FILENAME = "tmdb-api-key.txt"


# Sample TV serie 'The Outer Limits' in english
SAMPLE_TV_ID = "21567"
SAMPLE_TV_PAYLOAD = {
    "tmdb_id": "21567",
    "tmdb_type": "tv",
    "title": "The Outer Limits",
    "status": "Ended",
    "first_air_date": "1963-09-16",
    "number_of_seasons": 2,
    "number_of_episodes": 49,
    "genres": [
        "Drama",
        "Sci-Fi & Fantasy"
    ]
}


def get_tmdbapi_key():
    """
    Get TMDb API key retrieved from file ``tmdb-api-key.txt`` at this project
    root.

    Returns:
        string: Either the API key found from file if it exists else return
        None.
    """
    package_path = Path(
        deovi.__file__
    ).parents[0].resolve().parent

    filekey = package_path / API_FILEKEY_FILENAME
    if filekey.exists():
        key = filekey.read_text().strip()
        if key:
            return key

    return None
