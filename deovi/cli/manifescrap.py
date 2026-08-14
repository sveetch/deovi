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
    from ..conf import settings
    from ..scrapper import TmdbScrapper

    @click.command()
    @click.argument(
        "basedir",
        nargs=1,
        type=click.Path(
            path_type=Path,
            exists=True,
            file_okay=False,
            dir_okay=True,
        )
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
            path_type=Path,
            exists=True,
            file_okay=True,
            dir_okay=False,
            resolve_path=False,
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
        "--chunk",
        type=click.INT,
        metavar="INTEGER",
        help=(
            "Amount of items to process in a chunk. This is used with 'pause' "
            "to play well with the TMDB API request limit."
        ),
        default=settings.chunk_size,
    )
    @click.option(
        "--pause",
        type=click.INT,
        metavar="INTEGER",
        help=(
            "Time in seconds to pause processing. This is only used if the amount of "
            "items to process is over the 'chunk' size limit. You can set it to '0' "
            "to avoid pause but it is not recommended."
        ),
        default=settings.batch_pause,
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
        "--dry",
        is_flag=True,
        help=(
            "If enabled, everything is runned but nothing will be written or removed."
        ),
    )
    @click.pass_context
    def manifescrap_command(context, basedir, key, filekey, language, chunk, pause,
                            write_diff, dry):
        """
        Scrap informations and poster image from TMDb API for all manifest found from
        a path.

        This will recursively walk through the given base directory to find any
        valid manifest files (almost all '*.json' and '*.yaml' with expected structure)
        then scrap information for each valid manifest.

        Updated manifests are overwritten with the new data returned from API. Possible
        cover is downloaded and stored along the manifest.

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
        logger.debug("Language: {}".format(language))
        logger.debug("Chunk size: {}".format(chunk))
        logger.debug("Pause time: {}".format(pause))
        logger.debug("API Key {}".format(
            "from file" if filekey else "from string",
        ))

        connector = TmdbScrapper(
            key,
            language=language,
            chunk_size=chunk,
            batch_pause=pause,
            dry=dry,
            debug=False,
        )

        scrapped = connector.fetch_from_path(
            basedir,
            write_diff=write_diff,
        )

        for item in scrapped:
            manifest = item[0]
            logger.info("Successfuly scrapped: {}".format(manifest.path))
            logger.info("├─ ID: {}".format(manifest.tmdb_id))
            logger.info("├─ Type: {}".format(manifest.tmdb_type))
            logger.info("├─ Title: {}".format(manifest.title))
            logger.info("┕━ Cover: {}".format(manifest.cover))
