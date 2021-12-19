import json
from pathlib import Path

from ..exceptions import TaskValidationError


def validate_task_options(task_name, required, **options):
    """
    Validate that all options respect the task requirements.

    Arguments:
        task_name (string): Task name to output in possible error.
        required (list): List of required option names .
        **options (dict): Given task options.

    Raises:
        TaskValidationError: If required options are missing from given ``options``.
    """
    fields = []
    if required:
        for name in set(required):
            if name not in options:
                fields.append(name)

        if fields:
            msg = "Task '{name}' require option(s): {fields}".format(
                name=task_name,
                fields=", ".join(sorted(fields)),
            )
            raise TaskValidationError(msg)

    return True


def validate_job_file(filepath):
    """
    Validate if a Job files exist, is valid JSON and have required parameters.

    Arguments:
        filepath (pathlib.Path): Path to a file to check.

    Returns:
        list: Error messages if any.
    """
    errors = []

    # Don't continue checking if file does not exists
    if not filepath.exists():
        errors.append("Configuration file does not exists: {}".format(filepath))
    # Proceed to file checks
    else:
        # Don't continue checking if invalid JSON
        try:
            with filepath.open("r") as fp:
                data = json.load(fp)
        except json.decoder.JSONDecodeError as e:
            errors.append(
                "Configuration file is not a valid JSON file: {}\n{}".format(
                    filepath,
                    "   {}".format(str(e)),
                )
            )
        # Proceed to rules checking
        else:
            if "basepath" not in data:
                errors.append(
                    (
                        "Configuration file is missing required 'basepath' item: {}"
                    ).format(filepath)
                )
            # Validate if basepath exists and is a directory
            else:
                p = Path(data["basepath"])
                if not p.is_absolute():
                    p = (filepath.parents[0] / p).resolve()

                if not p.exists():
                    errors.append(
                        (
                            "Configuration file value for 'basepath' is not an "
                            "existing path: {}".format(p.resolve())
                        )
                    )
                elif not p.is_dir():
                    errors.append(
                        (
                            "Configuration file value for 'basepath' is not a "
                            "directory: {}".format(p)
                        )
                    )

            if "tasks" not in data:
                # NOTE: Task can still be an empty list, this is a behavior to permit
                #       to run a job just for listing basepath.
                errors.append(
                    (
                        "Configuration file miss required 'tasks' item: {}"
                    ).format(filepath)
                )

    return errors


def validate_jobs(filepaths):
    """
    Validate all jobs from given file paths.

    Arguments:
        filepaths (pathlib.Path): Path to a file to check.

    Returns:
        dict: All job errors where errors are indexed on their job files.
    """
    errors = {}

    for path in filepaths:
        results = validate_job_file(path)
        if results:
            errors[str(path)] = results

    return errors


def is_allowed_file(source, extensions=[]):
    """
    Check if source path is a file and allowed against a set of file extensions.

    A source file which does not exists on filesystem is not valid. Allowed extensions
    are compared only to the last file extension since some file names can contain dots
    as word divider but still recognized as extensions.

    Also, the comparaison is case insensitive.

    NOTE:
        Double extension like "tar.gz" won't work because of how this have been
        implemented. We match against extensions with the last suffix from Path object
        and so can only be "gz", this was done to be compatible with
        "dotted.file.names". But a new implementation may work correctly for double
        extension if using string method "endswith" instead of "Path.suffixes[-1]".

    Arguments:
        source (pathlib.Path): Path to a file.

    Keyword Arguments:
        extensions (list): A list of extensions to check against. If empty, every
            source filepaths are returned. Default to empty.
    """
    if not source.is_file():
        return False

    # If no extensions, no further check
    if not extensions:
        return True

    ext = source.suffixes[-1].lower()
    if ext and ext.startswith("."):
        ext = ext[1:]

    if ext not in extensions:
        return False

    return True
