import logging
from pathlib import Path

import click

from ..scrapper import TmdbScrapper
from ..exceptions import JobValidationError


@click.command()
@click.argument(
    "tvid",
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
        "TMDb API private key from a file, the file must only contain the key without."
        "anything else."
    ),
)
@click.option(
    "--language",
    metavar="STRING",
    help=(
        "Language code to use to get content."
    ),
    default="fr",
)
@click.pass_context
def scrap_command(context, tvid, destination, key, filekey, language):
    """
    Scrap TV show informations and poster image from TMDb API.

    Expect exactly two arguments:

    - tvid: The TV Show ID from TMDb, it may looks like an integer ('14009').

    - destination: Destination directory path where to write manifest and cover files.
    If path does not exist it will be created.

    And finally an API Key either directly as a string from option 'key' or from a
    file from option 'filekey'.
    """
    logger = logging.getLogger("deovi")

    if not key and not filekey:
        logger.critical(
            "A TMDb API key is required either from 'key' or 'filekey' option."
        )
        raise click.Abort()
    elif filekey:
        key = filekey.read_text().strip()

    logger.info("TV ID: {}".format(tvid))
    logger.debug("Destination: {}".format(destination))
    logger.debug("Language: {}".format(language))
    logger.debug("API Key ({}): {}".format(
        "from file" if filekey else "from string",
        key,
    ))

    connector = TmdbScrapper(key, language=language)

    data, manifest, poster =connector.fetch_tv(destination, tvid)
    logger.info("Title: {}".format(data["title"]))
    logger.info("Poster: {}".format(poster))
