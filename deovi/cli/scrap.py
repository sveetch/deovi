import logging
from pathlib import Path

import click


try:
    import deepdiff  # NOQA: F401
    import tmdbv3api  # NOQA: F401
except ImportError:
    """
    Install is missing requirements from scrapping feature
    """
    @click.command()
    @click.pass_context
    def new_scrap_command(context):
        """
        The scrapping feature has not been installed and so this command is not
        available. See 'Install' documentation for details.
        """
        logger = logging.getLogger("deovi")

        logger.critical(
            "The scrapping feature has not been installed and so its command is not "
            "available. See 'Install' documentation for details."
        )

        raise click.Abort()
else:
    """
    Scrapping feature requirements are available
    """
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
        Scrap TV show informations and poster image from TMDb API.

        Required arguments (in order):

        TMDB_TYPE\n
            The kind of media from TMDb, it can be either 'tv' or 'movie'. Trying to
            scrap a 'tmdb_id' with the wrong type (with 'tv' while it is a movie) will
            lead to an error.

        TMDB_ID\n
            The media ID from TMDb, it may looks like an integer, exemple: 14009.

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

        data, manifest, poster, diffs = connector.fetch_media(
            destination,
            tmdb_id,
            tmdb_type=tmdb_type,
            write_diff=write_diff,
        )
        logger.info("Title: {}".format(data["title"]))
        logger.info("Poster: {}".format(poster))
        if diffs:
            logger.info("There were differences with previous manifest file:")
            for line in diffs:
                logger.info("- {}".format(line))
