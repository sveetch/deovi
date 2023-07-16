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
    def scrap_command(context):
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
        "--dry",
        is_flag=True,
        help=(
            "If enabled, everything is runned but nothing will be written or removed."
        ),
    )
    @click.pass_context
    def scrap_command(context, tvid, destination, key, filekey, language, write_diff,
                      dry):
        """
        Scrap TV show informations and poster image from TMDb API.

        Required arguments:

        TVID\n
            The TV Show ID from TMDb, it may looks like an integer ('14009').

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

        logger.info("TV ID: {}".format(tvid))
        logger.debug("Destination: {}".format(destination))
        logger.debug("Language: {}".format(language))
        logger.debug("API Key {}".format(
            "from file" if filekey else "from string",
        ))

        connector = TmdbScrapper(key, language=language, dry=dry)

        data, manifest, poster, diffs = connector.fetch_tv(
            destination,
            tvid,
            write_diff=write_diff,
        )
        logger.info("Title: {}".format(data["title"]))
        logger.info("Poster: {}".format(poster))
        if diffs:
            logger.info("There were differences with previous manifest file:")
            for line in diffs:
                logger.info("- {}".format(line))
