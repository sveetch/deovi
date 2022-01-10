import logging
from pathlib import Path

import click

from ..collector import MEDIAS_EXTENSIONS, Collector


@click.command()
@click.argument("source", nargs=1, type=click.Path(exists=True, path_type=Path))
@click.argument("destination", nargs=1, type=click.Path(exists=False, path_type=Path))
@click.option("--extension", "-e", multiple=True)
@click.pass_context
def collect_command(context, source, destination, extension):
    """
    Recursively collect every media files from a basepath.
    """
    logger = logging.getLogger("deovi")

    if not extension:
        extension = MEDIAS_EXTENSIONS

    logger.info("Source: {}".format(source))
    logger.info("Destination: {}".format(destination))
    logger.info("Extensions: {}".format(", ".join(extension)))

    collector = Collector(source, extensions=extension)

    stats = collector.run(destination=destination)

    logger.info("Registered directories: {}".format(stats["directories"]))
    logger.info("Registered files: {}".format(stats["files"]))
    logger.info("Total directories and files size: {}".format(stats["size"]))
