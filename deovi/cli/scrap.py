import logging
from pathlib import Path

import click

from ..conf import settings
from ..scrapper import TmdbScrapper


@click.command()
@click.argument(
    "tmdb_type",
    required=True,
)
@click.argument(
    "tmdb_id",
    required=True,
)
@click.argument(
    "destination",
    type=click.Path(exists=False, path_type=Path),
)
@click.option(
    "--key",
    metavar="STRING",
    help=(
        "TMDb API private key as a string."
    ),
    default=None,
)
@click.option(
    "--filekey",
    type=click.Path(
        file_okay=True, dir_okay=False, resolve_path=False, path_type=Path,
        exists=True,
    ),
    help=(
        "TMDb API private key from a file, the file must only contain the key "
        "without anything else."
    ),
)
@click.option(
    "--language",
    metavar="STRING",
    help=(
        "Language code to get content."
    ),
    default="fr",
)
@click.option(
    "--write-diff",
    is_flag=True,
    help=(
        "If enabled, a file 'manifest.diff.txt' will be written along manifest "
        "file if there was a previous manifest file in destination directory and "
        "it got differences with the new one. This is not incremental, previous "
        "manifest difference file may be overwritten from a scrap job to another."
    ),
)
@click.option(
    "--formatter",
    metavar="STRING",
    help=(
        "Manifest output format, either 'yaml' or 'json'."
    ),
    default="yaml",
)
@click.option(
    "--dry",
    is_flag=True,
    help=(
        "If enabled, everything is runned but nothing will be written or removed."
    ),
)
@click.pass_context
def scrap_command(context, tmdb_type, tmdb_id, destination, key, filekey,
                  language, write_diff, formatter, dry):
    """
    Scrap TV show informations and poster image of a single resource from TMDb API.

    Required arguments (in order):

    TMDB_TYPE\n
        The kind of media from TMDb, it can be either 'tv' or 'movie'. Trying to
        scrap a 'tmdb_id' with the wrong type (with 'tv' while it is a movie) will
        lead to an error.

    TMDB_ID\n
        The media ID from TMDb, it is expected to be an integer like '14009'.

    DESTINATION\n
        Destination directory path where to write manifest and cover files.
        If path does not exist it will be created.

    And finally a valid API Key is mandatory, give it either from option '--key'
    or '--filekey'.
    """
    logger = logging.getLogger("deovi")

    if not key and not filekey:
        logger.critical(
            "A TMDb API key is required either from 'key' or 'filekey' option."
        )
        raise click.Abort()
    elif filekey:
        key = filekey.read_text().strip()

    try:
        tmdb_id = int(tmdb_id)
    except ValueError:
        logger.critical(
            "Given TMDB ID is not a valid integer: {}".format(tmdb_id)
        )
        raise click.Abort()

    if tmdb_type not in settings.scrapped_manifest_types:
        logger.critical(
            "Given TMDB TYPE is not a valid type to scrap: {}".format(tmdb_type)
        )
        raise click.Abort()

    logger.info("TMDB Type: {}".format(tmdb_type))
    logger.info("TMDB ID: {}".format(tmdb_id))
    logger.debug("Manifest format: {}".format(formatter))
    logger.debug("Destination: {}".format(destination))
    logger.debug("Language: {}".format(language))
    logger.debug("API Key {}".format(
        "from file" if filekey else "from string",
    ))

    connector = TmdbScrapper(
        key,
        manifest_format=formatter,
        language=language,
        dry=dry,
        debug=False,
    )

    manifest, diffs = connector.fetch_from_id(
        destination,
        tmdb_id,
        tmdb_type=tmdb_type,
        write_diff=write_diff,
    )

    cover = None
    if manifest.cover:
        cover = manifest.path.parent / manifest.cover

    logger.info("Manifest: {}".format(manifest.path))
    logger.info("Title: {}".format(manifest.title))
    logger.info("Cover: {}".format(cover))

    if diffs:
        logger.info("There were differences with previous manifest file:")
        for line in diffs:
            logger.info("- {}".format(line))
