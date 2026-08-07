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
    def manifescrap_command(context):
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
        "basedir",
        nargs=1,
        type=click.Path(exists=True, path_type=Path)
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
            "file if there was a previous manifest file and "
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
    def manifescrap_command(context, basedir, key, filekey,
                            language, write_diff, formatter, dry):
        """
        Scrap informations and poster image from TMDb API for all manifest found.

        .. TODO::
            * Expect a directory;
            * rglob manifest.[json|yaml] to find all manifest;
            * Only proceed to unlocked tv and movie;
            * Scrap elligible manifest;
            * Replace manifest content with the scrapped one;
            * Replacement must not remove attributes that are not TMDB (like the lock
              option);

        Required arguments (in order):

        BASEDIR\n
            A directory path which contains manifest files to consider for scrapping.

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

        logger.info("basedir: {}".format(basedir))
        logger.debug("Manifest format: {}".format(formatter))
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

        connector.fetch_all_from_manifests(
            basedir,
            write_diff=write_diff,
        )
