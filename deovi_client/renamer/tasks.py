import os

from deovi_client.exceptions import TaskValidationError

"""
NOTE:

    * "task_options_validator" may not be used inside task functions, since original
      implementation perform validation before launching effective job tasks and not
      during job alike its currently implemented here.
    * Benefit of validation inside the task is that validation rules stay inside the
      function instead of managing it an outside reference as originally implemented;
    * printer is excepted to be a callable for "AsciiOutputFormatter._format_row"
"""

def task_options_validator(funcname, required, **options):
    """
    Validate required task options.

    Arguments:
        funcname (string): Task function name to output in possible error.
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
            msg = "🔖 Task '{name}' require option(s): {fields}".format(
                name=funcname,
                fields=", ".join(sorted(fields)),
            )
            raise TaskValidationError(msg)

    return True


def capitalize(index, source, verbose=False, printer=None, **options):
    """
    Capitalize file name (work on the whole filename including extension).

    Arguments:
        index (integer): Index integer for current item in the walked list. Mostly used
            for print out message.

        source (string): Source filename.
        **options (dict): Tasks options, this task does not expect any options.

    Keyword Arguments:
        verbose (string): To enable or disable verbosity, when disable not any output
            will be printed out. Default to False.
        printer (function): A function to use to print out message. If not set,
            ``verbose`` argument is useless. Default to None.

    Returns:
        tuple: A tuple of current filename and new filename.
    """
    new_filename = source.capitalize()

    if verbose and printer:
        printer(
            index,
            label="capitalize",
            message=new_filename,
            state="debug",
        )

    return (source, new_filename)


def lowercase(index, source, verbose=False, printer=None, **options):
    """
    Lowercase file name(work on the whole filename including extension).

    Arguments:
        index (integer): Index integer for current item in the walked list. Mostly used
            for print out message.

        source (string): Source filename.
        **options (dict): Tasks options, this task does not expect any options.

    Keyword Arguments:
        verbose (string): To enable or disable verbosity, when disable not any output
            will be printed out. Default to False.
        printer (function): A function to use to print out message. If not set,
            ``verbose`` argument is useless. Default to None.

    Returns:
        tuple: A tuple of current filename and new filename.
    """
    new_filename = source.lower()

    if verbose and printer:
        printer(
            index,
            label="lowercase",
            message=new_filename,
            state="debug",
        )

    return (source, new_filename)


def uppercase(index, source, verbose=False, printer=None, **options):
    """
    Uppercase file name(work on the whole filename including extension).

    Arguments:
        index (integer): Index integer for current item in the walked list. Mostly used
            for print out message.

        source (string): Source filename.
        **options (dict): Tasks options, this task does not expect any options.

    Keyword Arguments:
        verbose (string): To enable or disable verbosity, when disable not any output
            will be printed out. Default to False.
        printer (function): A function to use to print out message. If not set,
            ``verbose`` argument is useless. Default to None.

    Returns:
        tuple: A tuple of current filename and new filename.
    """
    new_filename = source.upper()

    if verbose and printer:
        printer(
            index,
            label="uppercase",
            message=new_filename,
            state="debug",
        )

    return (source, new_filename)


def convert_underscore_to_dash(index, source, verbose=False, printer=None, **options):
    """
    Convert every filenames with rules.

    * "_" to "-";
    * "---" to "_";

    So "ping_-_foo_bar.mp4" will be converted to "ping_foo-bar.mp4".

    Arguments:
        index (integer): Index integer for current item in the walked list. Mostly used
            for print out message.

        source (string): Source filename.
        **options (dict): Tasks options, this task does not expect any options.

    Keyword Arguments:
        verbose (string): To enable or disable verbosity, when disable not any output
            will be printed out. Default to False.
        printer (function): A function to use to print out message. If not set,
            ``verbose`` argument is useless. Default to None.

    Returns:
        tuple: A tuple of current filename and new filename.
    """
    new_filename = source.replace("_", "-").replace("---", "_")

    if verbose and printer:
        printer(
            index,
            label="underscore_to_dash",
            message=new_filename,
            state="debug",
        )

    return (source, new_filename)


def add_prefix(index, source, verbose=False, printer=None, **options):
    """
    Add a prefix before each file from given directory path.

    Arguments:
        index (integer): Index integer for current item in the walked list. Mostly used
            for print out message.

        source (string): Source filename.
        **options (dict): Tasks options, expect an option "prefix".

    Keyword Arguments:
        verbose (string): To enable or disable verbosity, when disable not any output
            will be printed out. Default to False.
        printer (function): A function to use to print out message. If not set,
            ``verbose`` argument is useless. Default to None.

    Returns:
        tuple: A tuple of current filename and new filename.
    """
    task_options_validator("add_prefix", ["prefix"], **options)

    prefix = options["prefix"]

    new_filename = prefix + source

    if verbose and printer:
        printer(
            index,
            label="add_prefix",
            message=new_filename,
            state="debug",
        )

    return (source, new_filename)


def numerate(index, source, verbose=False, printer=None, **options):
    """
    Add current index position of item in file list.

    Index number is filled (from given zfill length) to the right with '0' and
    divided from filename with given divider string.

    Arguments:
        index (integer): Index integer for current item in the walked list. Mostly used
            for print out message.

        source (string): Source filename.
        **options (dict): Tasks options, expect option "zfill" and optional
            "start" and "divider".

    Keyword Arguments:
        verbose (string): To enable or disable verbosity, when disable not any output
            will be printed out. Default to False.
        printer (function): A function to use to print out message. If not set,
            ``verbose`` argument is useless. Default to None.

    Returns:
        tuple: A tuple of current filename and new filename.
    """
    task_options_validator("numerate", ["zfill"], **options)

    zfill = options["zfill"]
    start = options.get("start", 0)
    divider = options.get("divider", "_")

    new_filename = "{index}{divider}{filename}".format(
        index=str(start+index).zfill(zfill),
        divider=divider,
        filename=source,
    )

    if verbose and printer:
        printer(
            index,
            label="numerate",
            message=new_filename,
            state="debug",
        )

    return (source, new_filename)


def catch_segments(index, source, verbose=False, printer=None, **options):
    """
    Catch segments from filename.

    Filename is splitted on a divider and only required segments from given rules are
    retained then joined.

    This only apply on the file name part, not the extension parts.

    Joiner option  can use a custom string to join segments, default string if not
    given is "-".

    Arguments:
        index (integer): Index integer for current item in the walked list. Mostly used
            for print out message.
        source (string): Source filename.
        **options (dict): Tasks options, require options "divider" and "slice_start" and
            accept optional "slice_end" and "joiner".

    Keyword Arguments:
        verbose (string): To enable or disable verbosity, when disable not any output
            will be printed out. Default to False.
        printer (function): A function to use to print out message. If not set,
            ``verbose`` argument is useless. Default to None.

    Returns:
        tuple: A tuple of current filename and new filename.
    """
    task_options_validator("catch_segments", ["divider", "slice_start"], **options)

    divider = options["divider"]
    joiner = options.get("joiner", "-")
    slice_start = options["slice_start"]
    slice_end = options.get("slice_end", None)

    # Split source to get distinct name from extensions
    root, exts = os.path.splitext(source)

    # Split name on divider
    segments = root.split(divider)
    # Only remove segment if there is more than one
    if len(segments) > 1:
        if slice_end:
            segments = segments[slice_start:slice_end]
        else:
            segments = segments[slice_start:]

    new_filename = joiner.join(segments) + exts


    if verbose and printer:
        printer(
            index,
            label="catch_segments",
            message=new_filename,
            state="debug",
        )

    return (source, new_filename)


def replace(index, source, verbose=False, printer=None, **options):
    """
    Replace all occurences of a string (from) by another one (to).

    Just use the common String.replace() method. This is applied on the whole
    filename, including the file extensions.

    Arguments:
        index (integer): Index integer for current item in the walked list. Mostly used
            for print out message.
        source (string): Source filename.
        **options (dict): Tasks options, expect options "from" and "to".

    Keyword Arguments:
        verbose (string): To enable or disable verbosity, when disable not any output
            will be printed out. Default to False.
        printer (function): A function to use to print out message. If not set,
            ``verbose`` argument is useless. Default to None.

    Returns:
        tuple: A tuple of current filename and new filename.
    """
    task_options_validator("replace", ["from", "to"], **options)

    from_string = options["from"]
    to_string = options["to"]

    new_filename = source.replace(from_string, to_string)


    if verbose and printer:
        printer(
            index,
            label="replace",
            message=new_filename,
            state="debug",
        )

    return (source, new_filename)
