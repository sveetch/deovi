import logging
from pathlib import Path

import click

from ..renamer.tasks import TaskMaster
from ..renamer.runner import JobRunner
from ..exceptions import JobValidationError


@click.command()
@click.argument("jobs", nargs=-1, type=click.Path(exists=True, path_type=Path))
@click.option('--commit', is_flag=True)
@click.pass_context
def rename_command(context, jobs, commit):
    """
    Rename multiple files with some tasks in a job file.

    A job file is a JSON file with some parameters and tasks to define formatting. Job
    does not recursively walk on files from its basepath directory.

    Default behavior is to not change anything, just list task it would do and
    you need to enable commit with the '--commit' argument.

    You can't mix job and init modes and so mix Job filepath and directory
    paths.

    Finally, if any job task fails all renamed file will be reversed to their
    original filename.
    """
    logger = logging.getLogger("deovi")

    if not jobs:
        logger.critical("There is no job file to process.")
        raise click.Abort()
    else:
        if commit:
            logger.info("Commit mode is enabled, file will be renamed.")
        else:
            logger.info("Dry run mode is enabled, no file will be renamed.")
        logger.info("")

        jobber = JobRunner(task_class=TaskMaster)

        try:
            jobs = jobber.run(jobs, dry_run=not(commit))
        except JobValidationError as e:
            logger.error("🚨 {}".format(str(e)))
            logger.error("")

            for jobpath, errors in e.validation_details.items():
                logger.error("📂 {}".format(jobpath))
                for item in errors:
                    logger.error(" • {}".format(item))
                logger.error("")

            raise click.Abort()
