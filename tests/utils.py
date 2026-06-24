"""
Although we choosed very old media, the sample payload may change because TMDB still
edit their data sometime for some unknow reason.
"""
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
        "Sci-Fi & Fantasy",
    ],
    "original_language": "en",
    "overview": "The Outer Limits is an anthology tv series of self-contained "
    "sci-fi-horror stories, sometimes with a plot twist at the end.",
    "casting": [],
    "crew": [
        [
            "Leslie Stevens",
            "Executive Producer",
        ],
        [
            "Lou Morheim",
            "Producer",
        ],
        [
            "Sam White",
            "Producer",
        ],
    ],
}


# Sample TV serie 'The Pit and the Pendulum' in english
SAMPLE_MOVIE_ID = "273204"
SAMPLE_MOVIE_PAYLOAD = {
    "tmdb_id": "273204",
    "tmdb_type": "movie",
    "title": "The Pit and the Pendulum",
    "status": "Released",
    "release_date": "1964-01-09",
    "original_language": "fr",
    "overview": (
        "A haunting short version of Edgar Allan Poe's famous story about a cruel and"
        " unusual punishment inflicted on a victim of the Spanish Inquisition..."
    ),
    "genres": [
        "Drama",
        "Horror"
    ],
    "casting": [
        [
            "Maurice Ronet",
            "Le condamné à mort"
        ]
    ],
    "crew": [
        [
            "Alexandre Astruc",
            "Writer"
        ],
        [
            "Alexandre Astruc",
            "Director"
        ],
        [
            "Edgar Allan Poe",
            "Short Story"
        ],
        [
            "Antoine Duhamel",
            "Original Music Composer"
        ],
        [
            "Nicolas Hayer",
            "Director of Photography"
        ],
        [
            "Yves Kovacs",
            "Assistant Director"
        ],
        [
            "Pierre-André Boutang",
            "Assistant Director"
        ],
        [
            "Paul Bonnefond",
            "Sound"
        ],
        [
            "Marie Thérèse Respens",
            "Costume Design"
        ]
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
