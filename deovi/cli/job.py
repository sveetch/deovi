import logging
from pathlib import Path

import click

from ..exceptions import JobValidationError
from ..renamer.jobs import Job


@click.command()
@click.argument("basepath", nargs=1, type=click.Path(exists=True, path_type=Path))
@click.option("--destination", type=click.Path(dir_okay=False, path_type=Path))
@click.pass_context
def job_command(context, basepath, destination):
    """
    Create a new empty Job file for given basepath (the directory where the Job will
    search files). If no destination is given, it will be the last basepath directory
    name slugified with ".json" extension.
    """
    logger = logging.getLogger("deovi")

    logger.debug("Basepath: {}".format(basepath))

    if destination:
        logger.debug("Destination: {}".format(destination))
    else:
        logger.debug("No destination given, automatic name from basepath will be used.")

    try:
        created = Job.create(basepath, destination=destination)
    except JobValidationError as e:
        logger.critical(e)
        raise click.Abort()
    else:
        logger.info("Created Job file: {}".format(created))
