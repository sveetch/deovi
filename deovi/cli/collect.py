import logging
from pathlib import Path

import click

from ..collector.collect import Collector
from ..conf import settings


@click.command()
@click.argument(
    "source",
    nargs=1,
    type=click.Path(exists=True, path_type=Path)
)
@click.argument(
    "destination",
    nargs=1,
    type=click.Path(exists=False, path_type=Path)
)
@click.option(
    "--extension",
    "-e",
    multiple=True,
    help=(
        "Give a specific file extension (without leading dot) to search for. You can "
        "use this argument multiple times for all extension you want to allow. On "
        "default the collector will use: {}".format(
            ", ".join(settings.medias_extensions)
        )
    ),
)
@click.option(
    "--checksum",
    is_flag=True,
    help=(
        "If enabled, collector will compute a checksum for each directory base on its "
        "collected informations, any directory change will have a different checksum "
        "from a dump to another."
    ),
)
@click.pass_context
def collect_command(context, source, destination, extension, checksum):
    """
    Recursively collect every elligible directories with manifests, covers and media
    files and dump it to a JSON file.

    SOURCE\n
        The path where to start searching.

    DESTINATION\n
        A file path where to write the JSON dump.
    """
    logger = logging.getLogger("deovi")

    if not extension:
        extension = settings.medias_extensions

    logger.info("Source: {}".format(source))
    logger.info("Destination: {}".format(destination))
    logger.info("Extensions: {}".format(", ".join(extension)))

    collector = Collector(
        source,
        extensions=extension,
        autoload_manifests=True,
        autochecksum=True
    )
    stats = collector.run(destination=destination)

    logger.info("Registered directories: {}".format(stats["directories"]))
    logger.info("Registered files: {}".format(stats["files"]))
    logger.info("Total directories and files size: {}".format(stats["size"]))
